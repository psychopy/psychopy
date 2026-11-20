#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Streaming playback of a movie's audio track, decoded from the movie file as
it plays.

`MovieStim` plays the audio of movies whose decoder doesn't play it itself
(the `pyav` and `opencv` backends) through PsychoPy's own audio output. By
default it does so with a `MovieAudioStream`, which reads the audio stream from
the movie file with PyAV, decoding it a little ahead of where it is playing and
feeding it to the speaker as it goes. Playback can start as soon as the movie
is loaded whatever its length, and only a second or two of audio is held in
memory at once. With `MovieStim(extractAudioTrack=True)` the whole track is
decoded into a `Sound` up front instead.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'MovieAudioStream',
    'getAudioStreamBackend',
    'closeAllAudioStreams']

import atexit
import math
import threading
import time
import weakref

import numpy as np

from psychopy import logging
from .exceptions import MovieAudioError

# How far ahead of playback the audio is decoded, in seconds.
AUDIO_STREAM_QUEUE_SECS = 2.0

# How much audio is handed to the `ptb` backend ahead of playback, in seconds.
# This is the length of the ring buffer PTB plays from, which a background
# thread refills as it plays, so it is how long that thread can be held up for
# (e.g. waiting on the GIL) before the audio glitches.
AUDIO_STREAM_RING_SECS = 0.5

# How much audio the `sounddevice` backend needs decoded before it starts
# playing, in seconds. It pulls audio as it plays, so needn't wait for more.
AUDIO_STREAM_PREFILL_SECS = 0.1

# How often the background thread refills PTB's ring buffer, in seconds.
AUDIO_STREAM_PUMP_INTERVAL = 0.005

# How often the background thread checks for room to decode more into, when
# it has none, in seconds.
AUDIO_STREAM_POLL_INTERVAL = 0.02

# How little audio may be left in PTB's ring buffer, in seconds, when there is
# no more decoded yet, before silence is written to it. PTB plays the ring
# buffer round and round, so would otherwise replay old audio.
AUDIO_STREAM_LOW_WATER_SECS = 0.05

# How far before a position seeked to decoding starts from, in seconds, so
# that decoders which need a frame or two to settle have done so by then.
AUDIO_STREAM_SEEK_PREROLL = 0.05

# Longest `play()` waits for audio to be decoded to start from, in seconds.
AUDIO_STREAM_READY_TIMEOUT = 5.0

# Least audio worth handing to PTB at once, in samples.
_PTB_MIN_REFILL = 256

# Streams open now, closed on exit so that PyAV isn't left decoding while the
# interpreter shuts down.
_openAudioStreams = weakref.WeakSet()


def getAudioStreamBackend():
    """Get the audio backend a `MovieAudioStream` would play through.

    This is the backend `psychopy.sound.Sound` plays through, as set by the
    `audioLib` preference.

    Returns
    -------
    str or None
        `'ptb'` or `'sounddevice'`, or `None` if the backend is one audio can't
        be streamed through (or none can be loaded).

    """
    from psychopy import sound

    try:
        backend = sound.Sound.resolveBackend()
    except Exception:
        return None

    return {
        'backend_ptb': 'ptb',
        'backend_sounddevice': 'sounddevice'
    }.get(getattr(backend, '__name__', '').rsplit('.', 1)[-1])


def _makeAudioOutput(speaker=None, volume=1.0):
    """Make the audio output a `MovieAudioStream` plays through, for the
    backend `getAudioStreamBackend()` gives."""
    backend = getAudioStreamBackend()
    if backend == 'ptb':
        return _PTBAudioOutput(speaker=speaker, volume=volume)
    if backend == 'sounddevice':
        return _SoundDeviceAudioOutput(speaker=speaker, volume=volume)

    raise MovieAudioError(
        "Movie audio can't be streamed through this audio library, only "
        "through 'ptb' or 'sounddevice'.")


class _SampleQueue:
    """Queue of audio samples, as a ring buffer.

    This doesn't lock anything itself, being used under the lock of the
    `MovieAudioStream` it belongs to.

    Parameters
    ----------
    capacity : int
        Most samples the queue holds.
    channels : int
        Number of channels each sample has.

    """
    def __init__(self, capacity, channels):
        self._buffer = np.zeros((int(capacity), int(channels)), np.float32)
        self._start = 0  # index of the first sample in the queue
        self._count = 0  # number of samples in the queue

    def __len__(self):
        return self._count

    @property
    def capacity(self):
        """Most samples the queue holds (`int`)."""
        return len(self._buffer)

    @property
    def space(self):
        """Samples there's room for (`int`)."""
        return self.capacity - self._count

    def clear(self):
        """Empty the queue."""
        self._start = self._count = 0

    def push(self, samples):
        """Add samples to the end of the queue, as many as there's room for.

        Returns the number added.

        """
        n = min(len(samples), self.space)
        end = (self._start + self._count) % self.capacity
        first = min(n, self.capacity - end)
        self._buffer[end:end + first] = samples[:first]
        self._buffer[:n - first] = samples[first:n]
        self._count += n

        return n

    def pop(self, n):
        """Take up to `n` samples from the front of the queue, as a new array.
        """
        n = min(int(n), self._count)
        first = min(n, self.capacity - self._start)
        out = np.empty((n, self._buffer.shape[1]), np.float32)
        out[:first] = self._buffer[self._start:self._start + first]
        out[first:] = self._buffer[:n - first]
        self.skip(n)

        return out

    def skip(self, n):
        """Drop up to `n` samples from the front of the queue."""
        n = min(int(n), self._count)
        self._start = (self._start + n) % self.capacity
        self._count -= n

        return n


class MovieAudioStream:
    """Plays a movie's audio track, decoding it from the movie file as it
    plays.

    The track is read from the movie file with PyAV on a background thread,
    resampled to the rate and channels of the speaker it plays on, and kept a
    couple of seconds ahead of where it is playing (`AUDIO_STREAM_QUEUE_SECS`).
    Playing it feeds that to the speaker through the `ptb` or `sounddevice`
    audio backend, whichever `psychopy.sound.Sound` uses.

    This plays in place of a `Sound` holding the whole track, so is controlled
    the same way: `play()`, `pause()`, `stop()`, `seek()` and `volume`. Times
    are in seconds from the start of the track. Use `open()` to make one.

    Parameters
    ----------
    container : av.container.InputContainer
        Movie file to decode from, which this takes over and closes once done.
    audioStream : av.audio.stream.AudioStream
        Track to play.
    speaker : SpeakerDevice, str, int or None
        Speaker to play on, as for `Sound`, or `None` for the default.
    volume : float
        Volume to play at, from 0 to 1.

    """
    def __init__(self, container, audioStream, speaker=None, volume=1.0):
        self.filename = getattr(container, 'name', '')
        self._container = container
        self._audioStream = audioStream

        # not fatal if the codec doesn't support decoding with threads
        try:
            audioStream.thread_type = 'AUTO'
        except Exception:
            pass

        # Decode the first frame here, both to find where the track starts
        # (which time zero is, as for an extracted track), and so a track
        # which can't be decoded at all raises an error on loading the movie.
        self._frames = container.decode(audioStream)
        first = next(self._frames, None)
        if first is None:
            raise MovieAudioError(
                "No audio could be decoded from the audio track of: "
                "{}".format(self.filename))
        self._origin = first.time or 0.0
        self._preDecoded = [first]

        self._volume = volume
        self._output = _makeAudioOutput(speaker=speaker, volume=volume)
        self.sampleRate = int(self._output.sampleRate)
        self.channels = int(self._output.channels)
        # decoded in mono or stereo, padded with silence to more channels
        self._decodeLayout = 'mono' if self.channels == 1 else 'stereo'
        self._decodeChannels = 1 if self.channels == 1 else 2
        self._prefillSamples = int(self._output.prefillSamples)

        # Shared with the background thread, under `_cond`
        self._cond = threading.Condition()
        self._queue = _SampleQueue(
            max(int(AUDIO_STREAM_QUEUE_SECS * self.sampleRate),
                2 * self._prefillSamples),
            self.channels)
        self._generation = 0  # incremented by each seek
        self._target = 0.0  # position seeked to last
        self._consumed = 0  # samples taken from the queue since the seek
        self._eof = False  # queue holds the rest of the track
        self._deficit = 0  # samples of silence played for want of audio
        self._closing = False
        # error decoding the track before anything could be, see `play()`
        self.error = None

        # Taken around anything done with the audio output, which the
        # background thread refills (with `ptb`) as the main thread starts and
        # stops it. Always taken before `_cond`, never while holding it.
        self._outputLock = threading.RLock()
        self._playStart = 0.0  # position playback last started from
        self._underflowWarned = False

        self._thread = threading.Thread(
            target=self._run, name='MovieAudioStream', daemon=True)
        _openAudioStreams.add(self)
        self._thread.start()

    @classmethod
    def open(cls, filename, speaker=None, volume=1.0):
        """Open a movie file's audio track to play.

        Parameters
        ----------
        filename : str
            Movie file.
        speaker : SpeakerDevice, str, int or None
            Speaker to play on, as for `Sound`, or `None` for the default.
        volume : float
            Volume to play at, from 0 to 1.

        Returns
        -------
        MovieAudioStream or None
            The stream, or `None` if the movie has no audio track.

        """
        import av

        container = av.open(filename)
        try:
            if not container.streams.audio:
                container.close()
                return None

            return cls(container, container.streams.audio[0], speaker=speaker,
                       volume=volume)
        except BaseException:
            container.close()
            raise

    # --------------------------------------------------------------------------
    # Playback control, from the main thread
    #

    @property
    def isPlaying(self):
        """`True` while the track is playing, or waiting to at a time given to
        `play()` (`bool`)."""
        return self._output.isPlaying

    @property
    def isReady(self):
        """`True` once there is audio decoded to start playing from, at the
        position last seeked to (`bool`)."""
        with self._cond:
            return self._isReadyLocked()

    def _isReadyLocked(self):
        return (self._eof or self._closing or self.error is not None or
                len(self._queue) >= min(self._prefillSamples,
                                        self._queue.capacity))

    def waitUntilReady(self, timeout=None):
        """Wait for there to be audio decoded to start playing from.

        Parameters
        ----------
        timeout : float or None
            Longest to wait, in seconds, or `None` to wait as long as it takes.

        Returns
        -------
        bool
            `isReady`, which is `False` if it timed out.

        """
        with self._cond:
            return self._cond.wait_for(self._isReadyLocked, timeout)

    @property
    def volume(self):
        """Volume the track plays at, from 0 to 1 (`float`)."""
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value
        with self._outputLock:
            self._output.setVolume(value)

    def play(self, when=None, **kwargs):
        """Start playing from the current position.

        Parameters
        ----------
        when : float, Window-like or None
            When to start, as for `Sound.play()`: an absolute time in seconds
            on the clock `psychopy.clock.getTime()` reads, or an object with a
            `getFutureFlipTime()` method (such as a window) to ask for it. If
            `None`, playback starts straight away.

        """
        if self.isPlaying:
            return

        with self._cond:
            finished = self._consumed and self._eof and not len(self._queue)
        if finished:  # play it again, as a `Sound` would
            self.seek(0.0)

        if not self.waitUntilReady(AUDIO_STREAM_READY_TIMEOUT):
            logging.warning(
                "Movie audio for {} took longer than {} seconds to decode, "
                "so starts with silence.".format(
                    self.filename, AUDIO_STREAM_READY_TIMEOUT))

        with self._outputLock:
            with self._cond:
                self._playStart = self._target + \
                    self._consumed / float(self.sampleRate)
                self._underflowWarned = False
            self._output.start(self, when=when)

        with self._cond:
            self._cond.notify_all()  # to start refilling the output

    def pause(self, **kwargs):
        """Stop playing, to carry on from here when played again."""
        with self._outputLock:
            if not self.isPlaying:
                return
            nPlayed = self._output.stop()

        # Decode again from where it got to, since the queue has been read
        # past that to feed the output ahead of playback
        self.seek(self._playStart + nPlayed / float(self.sampleRate))

    def stop(self, reset=True, **kwargs):
        """Stop playing, going back to the start unless `reset` is `False`."""
        if not reset:
            self.pause()
            return

        with self._outputLock:
            if self.isPlaying:
                self._output.stop()

        self.seek(0.0)

    def seek(self, t):
        """Move to `t` seconds into the track, carrying on playing from there
        if it is playing.

        The audio for the new position is decoded in the background, which
        `play()` waits for (see `isReady`).

        """
        t = max(0.0, float(t))

        with self._outputLock:
            wasPlaying = self.isPlaying
            if wasPlaying:
                self._output.stop()

        with self._cond:
            alreadyThere = (
                not wasPlaying and not self._consumed and
                abs(t - self._target) < 0.5 / self.sampleRate)
            if not alreadyThere:
                self._generation += 1
                self._target = t
                self._queue.clear()
                self._consumed = 0
                self._eof = False
                self._deficit = 0
                self.error = None
                self._cond.notify_all()

        if wasPlaying:
            self.play()

    def close(self):
        """Stop playing and decoding, and close the movie file."""
        with self._cond:
            self._closing = True
            self._cond.notify_all()

        if self._thread.is_alive() and \
                self._thread is not threading.current_thread():
            self._thread.join(AUDIO_STREAM_READY_TIMEOUT)
            if self._thread.is_alive():
                logging.warning(
                    "Movie audio decoding did not stop within {} "
                    "seconds.".format(AUDIO_STREAM_READY_TIMEOUT))

        with self._outputLock:
            self._output.close()

        _openAudioStreams.discard(self)

    # --------------------------------------------------------------------------
    # For the audio output, from whichever thread feeds it
    #

    def _read(self, n, padUnderflow=True):
        """Take up to `n` samples to play.

        Parameters
        ----------
        n : int
            Samples wanted.
        padUnderflow : bool
            If there aren't `n` decoded yet, make up the rest with silence
            (unless at the end of the track), and skip as much audio once it
            has been, so that the track stays in time.

        Returns
        -------
        tuple
            The samples, as 32-bit floats shaped `(samples, channels)`, and
            whether the end of the track has been reached.

        """
        with self._cond:
            if self._deficit:
                skipped = self._queue.skip(self._deficit)
                self._deficit -= skipped
                self._consumed += skipped
            samples = self._queue.pop(n)
            self._consumed += len(samples)
            atEnd = self._eof and not len(self._queue)

        if padUnderflow and not atEnd and len(samples) < n:
            missing = n - len(samples)
            samples = np.concatenate(
                [samples, np.zeros((missing, self.channels), np.float32)])
            self._addDeficit(missing)

        return samples, atEnd

    def _addDeficit(self, n):
        """Count `n` samples of silence played for want of decoded audio,
        which are skipped once decoded to stay in time."""
        with self._cond:
            self._deficit += n
            warn = not self._underflowWarned
            self._underflowWarned = True

        if warn:
            logging.warning(
                "Movie audio for {} couldn't be decoded fast enough to keep "
                "up, so is playing silence until it catches up.".format(
                    self.filename))

    # --------------------------------------------------------------------------
    # Decoding, on the background thread
    #

    def _run(self):
        try:
            with self._container:
                self._decodeLoop()
        except BaseException as err:
            logging.error("Movie audio decoding for {} stopped: {}".format(
                self.filename, err))
        finally:
            with self._cond:
                self._eof = True
                self._cond.notify_all()
            _openAudioStreams.discard(self)

    def _decodeLoop(self):
        generation = 0
        self._startDecoding(0.0, seek=False)
        pending = None  # samples waiting for room in the queue
        while True:
            with self._cond:
                if self._closing:
                    return
                seekTo = None
                if self._generation != generation:
                    generation = self._generation
                    seekTo = self._target

            if seekTo is not None:
                pending = None
                self._startDecoding(seekTo)

            if self._output.needsPump and self._output.isPlaying:
                with self._outputLock:
                    self._output.pump(self)

            if pending is None and not self._decoderDone:
                pending = self._decodeNext()
                if pending is not None and not len(pending):
                    pending = None
                    continue  # nothing out of that frame, so on to the next

            with self._cond:
                if self._generation != generation:
                    continue  # seeked meanwhile, so these are no use

                if pending is not None:
                    wasReady = self._isReadyLocked()
                    nPushed = self._queue.push(pending)
                    pending = pending[nPushed:] if nPushed < len(pending) \
                        else None
                    if not wasReady and self._isReadyLocked():
                        # only now, since waking `waitUntilReady` before then
                        # only holds this up handing the GIL back and forth
                        self._cond.notify_all()

                if pending is None and self._decoderDone and not self._eof:
                    self._eof = True
                    self._cond.notify_all()

                if pending is None and not self._decoderDone:
                    continue  # decode more straight away

                # Wait for room in the queue, or for something to do once the
                # whole track is in it, refilling the output meanwhile
                if self._output.needsPump and self._output.isPlaying:
                    timeout = AUDIO_STREAM_PUMP_INTERVAL
                elif pending is not None:
                    timeout = AUDIO_STREAM_POLL_INTERVAL
                else:
                    timeout = None
                self._cond.wait(timeout)

    def _startDecoding(self, t, seek=True):
        """Get ready to decode from `t` seconds into the track."""
        self._decoderDone = False
        self._resampler = None
        self._decodeTarget = t
        self._dropSamples = None  # set from the first frame decoded
        self._decodedSinceSeek = False

        if not seek:
            return  # carrying on from the frame decoded to open the track

        self._preDecoded = []
        try:
            timeBase = self._audioStream.time_base
            start = self._origin + max(0.0, t - AUDIO_STREAM_SEEK_PREROLL)
            self._container.seek(
                int(math.floor(start / timeBase)), stream=self._audioStream,
                backward=True, any_frame=False)
            self._frames = self._container.decode(self._audioStream)
        except Exception as err:
            self._onDecodeError(err)

    def _decodeNext(self):
        """Decode the next frame of the track.

        Returns
        -------
        ndarray or None
            Samples for the queue, shaped `(samples, channels)`, which may be
            none at all (as when the resampler holds on to them), or `None`
            once the track has all been decoded.

        """
        try:
            if self._preDecoded:
                frame = self._preDecoded.pop(0)
            else:
                frame = next(self._frames, None)

            if frame is None:  # end of the track, so flush the resampler
                self._decoderDone = True
                if self._resampler is None:
                    return None
                resampled = self._resampler.resample(None)
            else:
                if self._dropSamples is None:
                    # Decoding starts a little before the position asked for,
                    # so drop what comes before it (or, should the track only
                    # start after it, play silence until then)
                    frameTime = frame.time
                    tFrame = frameTime - self._origin \
                        if frameTime is not None else self._decodeTarget
                    self._dropSamples = int(round(
                        (self._decodeTarget - tFrame) * self.sampleRate))
                resampled = self._resample(frame)
        except Exception as err:
            self._onDecodeError(err)
            return None

        samples = self._toSamples(resampled)
        self._decodedSinceSeek = True

        drop = self._dropSamples or 0
        if drop > 0:
            nDropped = min(drop, len(samples))
            samples = samples[nDropped:]
            self._dropSamples -= nDropped
        elif drop < 0:
            samples = np.concatenate(
                [np.zeros((-drop, self.channels), np.float32), samples])
            self._dropSamples = 0

        return samples

    def _resample(self, frame):
        """Resample a decoded frame to play, returning the frames that gives.
        """
        from av.audio.resampler import AudioResampler

        if self._resampler is None:
            self._resampler = AudioResampler(
                format='flt', layout=self._decodeLayout, rate=self.sampleRate)

        try:
            return self._resampler.resample(frame)
        except ValueError:
            # The track changed format, rate or layout partway, which the
            # resampler can't take, so finish with it and start another
            flushed = self._resampler.resample(None)
            self._resampler = AudioResampler(
                format='flt', layout=self._decodeLayout, rate=self.sampleRate)

            return list(flushed) + list(self._resampler.resample(frame))

    def _toSamples(self, frames):
        """Samples from resampled frames, for the queue."""
        nChannels = self._decodeChannels
        blocks = [
            np.frombuffer(f.planes[0], np.float32, f.samples * nChannels)
            .reshape(f.samples, nChannels)
            for f in frames if f.samples]
        if not blocks:
            return np.zeros((0, self.channels), np.float32)
        samples = np.concatenate(blocks) if len(blocks) > 1 else \
            blocks[0].copy()

        if self.channels > nChannels:  # silence on the speaker's others
            samples = np.pad(samples, ((0, 0), (0, self.channels - nChannels)))

        return samples

    def _onDecodeError(self, err):
        """Stop decoding after an error. One before anything could be decoded
        is raised by `MovieStim.play()`, others only logged."""
        self._decoderDone = True
        if not self._decodedSinceSeek:
            with self._cond:
                self.error = err
                self._cond.notify_all()
        logging.error("Error decoding movie audio for {}: {}".format(
            self.filename, err))


class _PTBAudioOutput:
    """Plays a `MovieAudioStream` through the `ptb` audio backend.

    The audio plays from a ring buffer on a PTB slave of the speaker's stream,
    as a `Sound` on it would, set playing round and round. The stream's
    background thread refills the buffer behind where it's playing
    (`pump()`).

    """
    needsPump = True

    def __init__(self, speaker=None, volume=1.0):
        from psychtoolbox import audio as ptbAudio
        from psychopy.hardware.speaker.speaker_psychtoolbox import \
            PsychtoolboxSpeakerDevice

        self._PsychPortAudio = ptbAudio.PsychPortAudio
        speaker = PsychtoolboxSpeakerDevice._fromSpeaker(speaker)
        # mono or stereo, as `Sound` opens it
        speaker.open(channels=min(2, speaker.channels))
        self.speaker = speaker
        self.sampleRate = int(speaker.sampleRateHz)
        self.channels = int(speaker.channels)

        self._ringSize = int(AUDIO_STREAM_RING_SECS * self.sampleRate)
        self.prefillSamples = self._ringSize
        self._lowWater = int(AUDIO_STREAM_LOW_WATER_SECS * self.sampleRate)

        self._slave = ptbAudio.Slave(
            speaker.stream.handle, mode=1, volume=volume)

        self._playing = False
        self._written = 0  # samples written since playback started
        self._end = None  # sample the track ends at, once it's been written
        self._nPlayed = 0  # samples played when last stopped

    @property
    def isPlaying(self):
        return self._playing

    @property
    def _isOpen(self):
        """Whether the slave is still open. PTB closes it on exit, which can
        come before the stream is closed."""
        return not getattr(self._slave, '_closed', False)

    def setVolume(self, volume):
        if self._isOpen:
            self._slave.volume = volume

    def _elapsed(self):
        """Samples played since playback started."""
        status = self._PsychPortAudio('GetStatus', self._slave.handle)

        return int(status['ElapsedOutSamples'])

    def start(self, source, when=None):
        # the time to start, on PTB's clock (`psychopy.clock.getTime()`)
        if hasattr(when, 'getFutureFlipTime'):
            when = when.getFutureFlipTime(clock='ptb')
        elif when is None:
            when = 0  # straight away

        # the ring buffer is first filled outright, which sets its length
        samples, atEnd = source._read(self._ringSize, padUnderflow=False)
        self._end = len(samples) if atEnd else None
        if len(samples) < self._ringSize:
            missing = self._ringSize - len(samples)
            samples = np.concatenate(
                [samples, np.zeros((missing, self.channels), np.float32)])
            if not atEnd:
                source._addDeficit(missing)

        handle = self._slave.handle
        self._PsychPortAudio('Stop', handle, 0, 1)
        self._PsychPortAudio('FillBuffer', handle, samples)
        self._written = len(samples)
        self._nPlayed = 0
        self._PsychPortAudio('Start', handle, 0, when, 0)  # round and round
        self._playing = True

    def pump(self, source):
        """Refill the ring buffer behind where it is playing."""
        if not self._playing:
            return
        if not self._isOpen:
            self._playing = False
            return

        elapsed = self._elapsed()
        if self._end is not None and elapsed >= self._end:
            self.stop()  # played to the end of the track
            return

        queued = self._written - elapsed
        space = self._ringSize - queued
        if space < _PTB_MIN_REFILL:
            return

        samples, atEnd = source._read(space, padUnderflow=False)
        n = len(samples)
        if n < space:
            if atEnd:
                if self._end is None:
                    self._end = self._written + n
                missing = space - n  # silence until it's stopped
            elif queued + n < self._lowWater:
                # nearly run out, so silence for now to keep from replaying
                # what's already been played
                missing = min(space, 2 * self._lowWater) - n
                source._addDeficit(missing)
            else:
                missing = 0
            if missing > 0:
                samples = np.concatenate(
                    [samples, np.zeros((missing, self.channels), np.float32)])

        if len(samples):
            self._PsychPortAudio(
                'FillBuffer', self._slave.handle,
                np.ascontiguousarray(samples, dtype=np.float32), 1)
            self._written += len(samples)

    def stop(self):
        """Stop playing, returning the number of samples played."""
        if self._playing and self._isOpen:
            elapsed = self._elapsed()
            self._PsychPortAudio('Stop', self._slave.handle, 0, 1)
            self._nPlayed = elapsed if self._end is None else \
                min(elapsed, self._end)
        self._playing = False

        return self._nPlayed

    def close(self):
        self.stop()
        if self._isOpen:
            self._slave.close()


class _SoundDeviceAudioOutput:
    """Plays a `MovieAudioStream` through the `sounddevice` audio backend.

    This joins the output stream of the speaker, which every `Sound` on it
    plays through, as one of them would. The stream asks it for each block of
    audio to play, which it takes from the `MovieAudioStream` as it goes
    (`_nextBlock()`).

    """
    needsPump = False

    def __init__(self, speaker=None, volume=1.0):
        from psychopy.sound import backend_sounddevice
        from psychopy.hardware.speaker.speaker_sounddevice import \
            SoundDeviceSpeakerDevice

        self._backend = backend_sounddevice
        speaker = SoundDeviceSpeakerDevice._fromSpeaker(speaker)
        self.speaker = speaker
        streams = backend_sounddevice.streams
        self._streamLabel, stream = streams.getDeviceStream(
            backend_sounddevice._getOutputDevice(speaker))
        self.sampleRate = int(stream.sampleRate)
        self.channels = int(stream.channels)
        self.prefillSamples = int(AUDIO_STREAM_PREFILL_SECS * self.sampleRate)

        # what the stream reads of each sound playing through it
        self.volume = volume
        self._tSoundRequestPlay = -1.0
        self._blockOffset = -1

        self._source = None
        self._playing = False
        self._nPlayed = 0  # samples handed to the stream since starting

    @property
    def _stream(self):
        return self._backend.streams[self._streamLabel]

    @property
    def isPlaying(self):
        return self._playing

    def setVolume(self, volume):
        self.volume = volume

    def start(self, source, when=None):
        from psychopy import clock

        # the time to start, on the clock the stream schedules sounds with, as
        # `SoundDeviceSound.play()` works it out
        tRequest = time.monotonic()
        if hasattr(when, 'getFutureFlipTime'):
            tRequest += when.getFutureFlipTime(clock='now')
        elif when is not None:
            tRequest += float(when) - clock.getTime()

        self._source = source
        self._nPlayed = 0
        self._tSoundRequestPlay = tRequest
        self._blockOffset = -1  # onset not yet placed in the output stream
        self._playing = True  # last, as the stream may play it straight away
        self._stream.add(self)

    def _nextBlock(self, blockSize):
        """Next block of audio to play, called by the stream from its own
        thread. A short block ends playback."""
        source = self._source
        if not self._playing or source is None:
            return None

        samples, atEnd = source._read(blockSize)
        self._nPlayed += len(samples)
        if atEnd and len(samples) < blockSize:
            self._playing = False

        return samples

    def stop(self):
        """Stop playing, returning the number of samples played."""
        self._playing = False
        self._stream.remove(self)

        return self._nPlayed

    def close(self):
        self.stop()
        self._source = None


def closeAllAudioStreams():
    """Close every `MovieAudioStream` still open. Called on exit, so that
    PyAV isn't left decoding while the interpreter shuts down."""
    for stream in list(_openAudioStreams):
        try:
            stream.close()
        except Exception:
            pass


atexit.register(closeAllAudioStreams)


if __name__ == "__main__":
    pass
