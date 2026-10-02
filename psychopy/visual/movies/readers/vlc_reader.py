#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Movie reader using VLC.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'VLCMovieFileReader',
]

import ctypes
import sys
import threading
import time
import weakref

from psychopy import logging
from ..exceptions import MovieFileFormatError
from ..frame import FRAME_BYTES_PER_PIXEL, _RGBFrameAdapter
from ._base import MovieFileReader, defaultTimeout

# How far the frame-counted playback position may differ from the position VLC
# reports before it is re-anchored to VLC's own clock. VLC reports its position
# in coarse steps (a quarter of a second or so), so this has to be well clear
# of that to be measuring drift rather than the size of those steps.
VLC_PTS_RESYNC_THRESHOLD = 1.0  # seconds

# How long to wait for VLC to present the frame at a position just seeked to.
# Seeking has to decode forward from the nearest keyframe before it can render
# anything, so it takes appreciably longer than a frame arriving during
# ordinary playback.
VLC_SEEK_TIMEOUT = 0.5  # seconds

# How many frames VLC must present after a seek before one of them is taken as
# the frame at the new position. The picture from the old position can still be
# presented once after the seek is issued, so more than one is needed.
VLC_SEEK_SETTLE_FRAMES = 2

# Longest to wait for a pause to work its way through VLC. Seeking before it
# has lands the player somewhere unrelated to the position asked for, so this
# is a correctness matter rather than a tidiness one.
VLC_PAUSE_SETTLE_TIMEOUT = 0.25  # seconds

# Shortest a pause is given to take hold, whatever the movie's frame rate.
# Waiting for VLC to present a frame is the signal that it has noticed the
# pause, but on its own that proved to come too early to seek on.
VLC_PAUSE_SETTLE_MIN = 0.05  # seconds

class VLCMovieFileReader(MovieFileReader):
    """Read movie frames from a file with VLC.

    VLC decodes in the background on a clock of its own and plays the movie's
    audio track itself, on the default output device. Frames are handed over
    as VLC reaches them, so `getFrame()` returns whichever frame VLC has most
    recently decoded rather than the one at exactly the requested timestamp.
    This requires VLC itself to be installed, of an architecture matching the
    Python interpreter running PsychoPy. See `MovieFileReader` for parameters.

    """
    _decoderLib = 'vlc'

    # WARNING: `libvlc` is not thread-safe and the video callbacks below are
    # invoked from VLC's own decoding thread. Calling into the `libvlc` API
    # from any of them deadlocks the player, so they only ever touch plain
    # Python state guarded by `_vlcFrameLock`. Everything which does call
    # `libvlc` (seeking, pausing, reading the clock) runs on the thread which
    # owns this reader, never inside a callback.

    def __init__(self, filename, decoderLib=None, decoderOpts=None):
        super().__init__(filename, decoderLib, decoderOpts)

        self._vlcInstance = None  # vlc.Instance
        self._vlcPlayer = None  # vlc.MediaPlayer
        self._vlcMedia = None  # vlc.Media being played
        self._vlcEventManager = None  # vlc.EventManager for the player
        # Guards the frame buffers below, which VLC's decoding thread writes
        # into through the video callbacks while this thread reads them out.
        self._vlcFrameLock = threading.RLock()
        # `True` between the lock and unlock callbacks, so that an unlock
        # arriving for a lock which bailed out cannot release a lock it never
        # took
        self._vlcLockHeld = False
        # VLC decodes into one buffer while the other is read from, the two
        # being swapped once a frame is complete (see `_makeVLCCallbacks`)
        self._vlcWriteBuffer = None
        self._vlcReadBuffer = None
        self._vlcFrameNBytes = 0  # bytes of a buffer a frame occupies
        self._vlcFrameReady = False  # a frame is waiting to be picked up
        # Counts every frame VLC presents, including the repeats of the current
        # picture it keeps sending while paused. Used to tell that VLC has
        # moved on rather than to time anything.
        self._vlcDisplayCount = 0
        # display count a seek has to reach before the picture is taken to be
        # the one at the new position (`None` when no seek is outstanding)
        self._vlcSeekSettleAt = None
        self._vlcStreamEnded = False  # set by the end-of-stream event callback
        self._vlcPaused = True  # whether VLC is presently producing frames
        # when the current pause was asked for, and the frame count at that
        # point, so that `_vlcPauseHasSettled` can tell whether it has had time
        # to take hold (`_vlcPausedAt` is `None` while playing)
        self._vlcPausedAt = None
        self._vlcPausedAtCount = 0
        # position a seek is waiting to be applied at, see `_seek`
        self._vlcPendingSeekPTS = None
        # Playback position is counted in frames from a known point in the
        # movie rather than read from VLC every frame, see `_ptsForNextVLCFrame`
        self._vlcPTSAnchor = 0.0  # movie time the count below starts from
        self._vlcFramesSinceAnchor = 0
        # the video callbacks, which must stay referenced while VLC holds them
        self._vlcLockCb = self._vlcUnlockCb = self._vlcDisplayCb = None

    def _makeVLCCallbacks(self):
        """Build the video callbacks VLC writes frames through.

        The callbacks are created per reader instance and close over a weak
        reference to it, which keeps the reader collectable (a strong
        reference would be kept alive by the callback objects it stores) and
        lets a callback firing during teardown bail out instead of touching a
        half-freed reader.

        Returns
        -------
        tuple
            The lock, unlock and display callbacks, as `ctypes` function
            objects. These must be kept referenced for as long as VLC holds
            them, otherwise they are garbage collected and VLC calls into
            freed memory.

        """
        import vlc

        selfRef = weakref.ref(self)

        @vlc.CallbackDecorators.VideoLockCb
        def lockCallback(userData, planes):
            """Hand VLC the buffer to decode the next frame into."""
            reader = selfRef()
            if reader is None or reader._vlcWriteBuffer is None:
                # Nothing to decode into. Returning without taking the lock
                # is safe because `unlockCallback` only releases it when this
                # callback recorded that it took it.
                return None

            reader._vlcFrameLock.acquire()
            reader._vlcLockHeld = True
            planes[0] = ctypes.cast(reader._vlcWriteBuffer, ctypes.c_void_p)

            return None

        @vlc.CallbackDecorators.VideoUnlockCb
        def unlockCallback(userData, picture, planes):
            """Called once VLC has finished writing the frame."""
            reader = selfRef()
            if reader is None or not reader._vlcLockHeld:
                return

            reader._vlcLockHeld = False
            reader._vlcFrameLock.release()

        @vlc.CallbackDecorators.VideoDisplayCb
        def displayCallback(userData, picture):
            """Called when the frame just written is due to be shown.

            VLC has released the frame buffer by this point, so the buffers can
            be swapped: the frame which was just written becomes the one
            `_pullFrameVLC` reads, and VLC decodes the next frame into the one
            it had been reading.

            """
            reader = selfRef()
            if reader is None:
                return

            with reader._vlcFrameLock:
                reader._vlcWriteBuffer, reader._vlcReadBuffer = (
                    reader._vlcReadBuffer, reader._vlcWriteBuffer)
                reader._vlcFrameReady = True
                reader._vlcDisplayCount += 1

        return lockCallback, unlockCallback, displayCallback

    def _onVLCEndReached(self, event):
        """Handle VLC reaching the end of the stream.

        This runs on a VLC thread, so it only raises a flag which
        `_serviceVLCStreamEnd` acts on from the reader's own thread. Calling
        the `libvlc` API here would deadlock the player.

        """
        self._vlcStreamEnded = True

    def _open(self):
        """Open a movie reader using VLC.

        This function opens the movie file using the `python-vlc` bindings to a
        local `libvlc` installation and extracts metadata about the movie file.
        Metadata will be accessible via the `getMetadata()` method.

        Like `ffpyplayer`, VLC decodes in the background on its own clock and
        plays the movie's audio track itself, rather than handing frames over
        on demand the way `pyav` and `opencv` do. Frames arrive by way of the
        video callbacks set up here, which write into buffers owned by this
        reader.

        """
        logging.info("Using VLC for reading movie frames.")
        try:
            import vlc
        except Exception as err:
            # `python-vlc` raises rather than failing to import when it cannot
            # find a `libvlc` of a matching architecture, so the error is
            # reported here alongside the usual missing-package case.
            raise ImportError(
                'The `python-vlc` library and a local VLC installation are '
                'required to read movie files with `decoderLib=vlc`. Make '
                'sure the VLC install matches the architecture of the Python '
                'interpreter running PsychoPy. Original error: {}'.format(err))

        logging.info("Opening movie file: {}".format(self._filename))

        # `an` is set by `MovieStim` when the audio track is being played back
        # by something other than the decoder, or not at all
        noAudio = bool(self._decoderOpts.get('an', False))
        # infinite looping is requested when `loop` is explicitly `0`,
        # mirroring the `ffpyplayer` convention used elsewhere in this file
        loopInfinitely = self._decoderOpts.get('loop', 1) == 0

        instanceArgs = ['--quiet', '--no-video-title-show']
        if noAudio:
            instanceArgs.append('--no-audio')
        if sys.platform.startswith('linux'):
            # nothing is drawn through X here (frames come back through the
            # callbacks below), so keep VLC from initialising Xlib alongside
            # the window backend PsychoPy is already using
            instanceArgs.append('--no-xlib')
        instanceArgs.extend(self._decoderOpts.get('options', []))

        self._vlcInstance = vlc.Instance(instanceArgs)
        if self._vlcInstance is None:
            raise RuntimeError(
                'Failed to create a VLC instance. Check that VLC is installed '
                'and that its architecture matches the Python interpreter.')

        self._vlcPlayer = self._vlcInstance.media_player_new()
        self._vlcMedia = self._vlcInstance.media_new(self._filename)

        if loopInfinitely:
            # Let VLC do the looping. It wraps the stream itself without ever
            # reporting the end of it, which keeps its clock in step with the
            # caller's, and keeps the audio track looping along with the video.
            self._vlcMedia.add_option(':input-repeat=65535')

        self._vlcPlayer.set_media(self._vlcMedia)

        # Read the movie's properties. Parsing is what populates them, and it
        # has to happen before playback starts since the frame size is needed
        # to set the output format up.
        self._vlcMedia.parse()

        width, height = self._vlcPlayer.video_get_size(0)
        if not width or not height:
            self._freePlayer()
            raise MovieFileFormatError(self._filename)

        frameRate = float(self._vlcPlayer.get_fps())
        if not frameRate > 0.0:
            self._freePlayer()
            raise RuntimeError(
                'VLC could not determine the frame rate of the movie file. '
                'Try `movieLib="pyav"` instead for this file.')

        # VLC reports the duration in milliseconds
        duration = self._vlcMedia.get_duration() / 1000.0
        if not duration > 0.0:
            self._freePlayer()
            raise RuntimeError(
                'VLC could not determine the duration of the movie file. '
                'Try `movieLib="pyav"` instead for this file.')

        self._setMovieProperties((width, height), frameRate, duration)

        # Ask VLC for packed RGBA so frames arrive in the format the rest of
        # this class works in and no colour conversion is needed per frame.
        # `RGBA` is VLC's name for it and is laid out R, G, B, A in memory.
        pitch = width * FRAME_BYTES_PER_PIXEL
        self._vlcPlayer.video_set_format('RGBA', width, height, pitch)

        # Two buffers so VLC can decode the next frame while the last one is
        # being read, see `displayCallback` above. The spare bytes guard
        # against a decoder writing past the end of the last row.
        bufferSize = pitch * height + pitch
        self._vlcWriteBuffer = (ctypes.c_ubyte * bufferSize)()
        self._vlcReadBuffer = (ctypes.c_ubyte * bufferSize)()
        self._vlcFrameNBytes = pitch * height

        # these have to stay referenced for as long as VLC holds them
        (self._vlcLockCb,
         self._vlcUnlockCb,
         self._vlcDisplayCb) = self._makeVLCCallbacks()

        self._vlcPlayer.video_set_callbacks(
            self._vlcLockCb, self._vlcUnlockCb, self._vlcDisplayCb, None)

        self._vlcEventManager = self._vlcPlayer.event_manager()
        self._vlcEventManager.event_attach(
            vlc.EventType.MediaPlayerEndReached, self._onVLCEndReached)

        # Warm the decoder up. VLC does not produce frames until playback
        # starts, so it is started muted, run until the first frame lands, then
        # paused and rewound so the movie is sitting on frame 0 ready to play.
        self._vlcPlayer.audio_set_mute(True)
        if self._vlcPlayer.play() == -1:
            self._freePlayer()
            raise MovieFileFormatError(self._filename)

        startTime = time.time()
        while time.time() - startTime < defaultTimeout:
            if self._vlcFrameReady:
                break
            time.sleep(0.001)  # yield, don't spin the CPU while waiting
        else:
            self._freePlayer()
            raise RuntimeError(
                'VLC failed to decode the first frame of the movie within {} '
                'seconds. Check the movie file.'.format(defaultTimeout))

        firstFrameBytes = self._takeVLCFrameBytes()

        self._setVLCPaused(True)
        self._waitForVLCPauseToSettle()  # rewinding before this lands nowhere
        self._discardPendingVLCFrame()
        self._vlcPlayer.set_time(0)
        self._vlcStreamEnded = False
        self._anchorVLCPTS(0.0)
        self._vlcPlayer.audio_set_mute(self._muted or noAudio)

        # Hold the first frame at a PTS of exactly zero so that it is the frame
        # found for the start of the movie, as with the other backends.
        self._frameStore.append(
            (_RGBFrameAdapter(firstFrameBytes), 0.0, 'paused'))

    def _takeVLCFrameBytes(self):
        """Copy the most recently decoded frame out of the read buffer.

        The copy is made while holding `_vlcFrameLock` so that a buffer swap
        cannot hand this buffer back to VLC part way through it. VLC's decoding
        thread only blocks on that lock if it happens to be starting the next
        frame, and only for as long as the copy takes.

        Returns
        -------
        bytes or None
            Raw RGB24 pixel data for the frame, or `None` if VLC has not
            delivered a new one since the last call.

        """
        with self._vlcFrameLock:
            if not self._vlcFrameReady or self._vlcReadBuffer is None:
                return None

            self._vlcFrameReady = False

            return bytes(memoryview(self._vlcReadBuffer)[:self._vlcFrameNBytes])

    def _discardPendingVLCFrame(self):
        """Drop the frame VLC has waiting to be picked up, if there is one.

        Used when moving to a new position in the movie, where whatever has
        already been decoded belongs to where playback used to be.

        """
        with self._vlcFrameLock:
            self._vlcFrameReady = False

    def _setVLCPaused(self, state):
        """Pause or resume VLC, noting when a pause was asked for.

        `_waitForVLCPauseToSettle` needs to know how long ago playback was
        paused, since seeking before a pause has taken hold lands the player
        somewhere unrelated to the position asked for.

        Parameters
        ----------
        state : bool
            `True` to pause playback, `False` to resume it.

        """
        state = bool(state)

        self._vlcPlayer.set_pause(int(state))
        self._vlcPaused = state
        self._vlcPausedAt = time.time() if state else None
        self._vlcPausedAtCount = self._vlcDisplayCount

    def _vlcPauseHasSettled(self):
        """Whether a pause has had time to work its way through VLC (`bool`).

        A seek issued while a pause is still in progress is mishandled by VLC:
        rather than landing late, or not at all, the player ends up at a
        position unrelated to the one asked for. Nothing reports the pause as
        complete (`get_state()` says `Paused` straight away, well before it is
        safe to seek), but VLC presents a frame once it has noticed, so that
        is taken as the signal along with a short floor, neither being enough
        on its own.

        """
        if self._vlcPausedAt is None:
            return True  # playing, so there is no pause to wait on

        elapsed = time.time() - self._vlcPausedAt

        if elapsed >= VLC_PAUSE_SETTLE_TIMEOUT:
            return True  # asked for long enough ago to have certainly landed

        # `_vlcDisplayCount` is only ever read for progress, so it is read
        # without taking the lock rather than contending with the decoding
        # thread over it
        framesSince = self._vlcDisplayCount - self._vlcPausedAtCount

        return framesSince >= 1 and \
            elapsed >= max(self._frameInterval, VLC_PAUSE_SETTLE_MIN)

    def _waitForVLCPauseToSettle(self):
        """Wait for a pause to work its way through VLC before seeking.

        See `_vlcPauseHasSettled` for why this is needed.

        """
        deadline = time.time() + VLC_PAUSE_SETTLE_TIMEOUT

        while not self._vlcPauseHasSettled():
            if time.time() > deadline:
                logging.debug(
                    "VLC did not settle within {} seconds of being paused; a "
                    "seek made now may not land where asked.".format(
                        VLC_PAUSE_SETTLE_TIMEOUT))
                return

            time.sleep(0.001)  # yield, don't spin the CPU while waiting

    def _pullFrameVLC(self):
        """Take the frame VLC has most recently decoded, if there is a new one.

        The frame store for this backend only ever holds the newest frame.
        Unlike the on-demand backends there is no way to ask VLC for a frame at
        a particular position, so there is nothing to be gained from keeping
        the ones which have already gone past.

        Returns
        -------
        bool
            `True` if a new frame was taken and stored.

        """
        if self._vlcSeekSettleAt is not None:
            if self._vlcDisplayCount < self._vlcSeekSettleAt:
                # still being shown the position which was seeked away from
                return False

            self._vlcSeekSettleAt = None

        frameBytes = self._takeVLCFrameBytes()
        if frameBytes is None:
            return False

        self._frameStore[:] = [
            (_RGBFrameAdapter(frameBytes), self._ptsForNextVLCFrame(),
             'playing')]

        return True

    def _anchorVLCPTS(self, pts):
        """Peg the frame-counted playback position to a known movie time.

        Parameters
        ----------
        pts : float
            The movie time, in seconds, the next frame VLC delivers will be at.

        """
        self._vlcPTSAnchor = pts
        self._vlcFramesSinceAnchor = 0

    def _ptsForNextVLCFrame(self):
        """Work out the movie time of the frame just delivered by VLC.

        VLC reports its position in coarse steps, roughly a quarter of a second
        at a time, which is far too blunt to timestamp individual frames with.
        Since VLC hands frames over as it reaches them, counting them from a
        known position gives a much better estimate. The count is re-pegged to
        VLC's own clock whenever the two drift apart, which also picks up the
        wrap-around when VLC loops the movie.

        Returns
        -------
        float
            The presentation timestamp (PTS) of the frame, in seconds.

        """
        curPts = self._vlcPTSAnchor + \
            self._vlcFramesSinceAnchor * self._frameInterval

        if not self._vlcPaused:
            # While paused VLC keeps presenting the picture it is sitting on,
            # and those repeats are the same frame over again rather than the
            # movie moving on.
            self._vlcFramesSinceAnchor += 1

        # `get_time()` is a `libvlc` call, so it happens here on the reader's
        # own thread rather than in the display callback. It reports where
        # playback has reached, in milliseconds.
        reportedPts = self._vlcPlayer.get_time() / 1000.0

        if reportedPts >= 0.0 and \
                abs(curPts - reportedPts) > VLC_PTS_RESYNC_THRESHOLD:
            # The count has come adrift of where VLC actually is, either
            # because frames were dropped or because VLC has looped back to the
            # start of the movie. Believe VLC.
            self._anchorVLCPTS(reportedPts)
            self._vlcFramesSinceAnchor = 1
            curPts = reportedPts

        return curPts

    def _serviceVLCStreamEnd(self):
        """Act on VLC having reached the end of the stream.

        The event callback cannot do this itself, since notifying the caller
        may lead back into the `libvlc` API which must not be called from a VLC
        thread.

        """
        if not self._vlcStreamEnded:
            return

        self._vlcStreamEnded = False
        self._vlcPaused = True  # a finished player is not going to produce more

        # nothing further will arrive, so a seek waiting on a frame never lands
        self._seeking = False

        if self._streamEOFCallback is not None:
            self._streamEOFCallback()

    def _seek(self, reqPTS):
        """VLC specific seek routine.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) to seek to in seconds.

        Returns
        -------
        float
            The presentation timestamp (PTS) requested in seconds. The player
            is not moved here, only marked as needing to be; see
            `_applyPendingVLCSeek`. Once it is, VLC renders the frame for the
            new position through the usual callbacks, so `_getFrame` may
            need to be called a few times before it arrives.

        """
        if self._vlcPlayer is None:
            return

        import vlc

        reqPTS = min(max(0.0, reqPTS), self._metadata.duration)

        # A player which has run off the end of the stream ignores any new
        # position until it has been restarted; `play()` on its own is not
        # enough to revive it.
        if self._vlcPlayer.get_state() == vlc.State.Ended:
            self._vlcPlayer.stop()
            self._vlcPlayer.play()
            self._vlcStreamEnded = False

            # the new position cannot be set until playback is running again
            startTime = time.time()
            while time.time() - startTime < defaultTimeout:
                if self._vlcPlayer.get_state() == vlc.State.Playing:
                    break
                time.sleep(0.001)
            else:
                logging.warning(
                    "VLC did not restart within {} seconds after reaching the "
                    "end of the movie; the seek to {:.3f} seconds may not have "
                    "taken effect.".format(defaultTimeout, reqPTS))

            self._vlcPaused = False
            self._vlcPausedAt = None

        # Let go of what has already been decoded at the old position.
        self._discardPendingVLCFrame()
        self._cleanUpFrameStore()
        self._anchorVLCPTS(reqPTS)

        # Moving the player is left to `_applyPendingVLCSeek`, which runs when
        # a frame is next asked for. It may have to wait for a pause to take
        # hold first, and doing that waiting here would charge it to the
        # caller's movie clock, leaving the movie that much past the position
        # it asked for.
        self._vlcPendingSeekPTS = reqPTS

        return reqPTS

    def _applyPendingVLCSeek(self, blocking=True):
        """Move the player to the position a seek has asked for.

        Parameters
        ----------
        blocking : bool
            Whether to wait for a pause which has yet to take hold, since the
            position cannot be set until it has. Pass `False` to return
            without moving in that case, leaving the seek to be applied on a
            later call rather than holding the caller up.

        Returns
        -------
        bool
            `True` if the player was moved.

        """
        if self._vlcPendingSeekPTS is None:
            return False

        # Playback being under way is itself enough for a seek to be handled
        # properly, so this only bites when the caller paused a moment ago.
        if not self._vlcPauseHasSettled():
            if not blocking:
                return False  # try again when next asked for a frame

            self._waitForVLCPauseToSettle()

        reqPTS = self._vlcPendingSeekPTS
        self._vlcPendingSeekPTS = None

        # anything presented up to now belongs to the position being left
        self._discardPendingVLCFrame()

        self._vlcPlayer.set_time(int(round(reqPTS * 1000.0)))
        self._anchorVLCPTS(reqPTS)

        # VLC presents the picture from the old position once more before
        # putting up the one at the new position, so skip that first one and
        # take the next, which is the frame seeked to.
        self._vlcSeekSettleAt = self._vlcDisplayCount + VLC_SEEK_SETTLE_FRAMES

        return True

    def _convertFrameToRGB(self, frame):
        """Convert a VLC frame to RGB format.

        VLC is asked for `RGBA` frames in `_open`, which is already the
        packed RGBA layout used throughout this class, so frames are wrapped
        as they are taken from the buffer and nothing is left to do here.

        Parameters
        ----------
        frame : `_RGBFrameAdapter`
            The frame to convert.

        Returns
        -------
        _RGBFrameAdapter
            The frame, unchanged.

        """
        return frame

    def _getFrame(self, reqPTS=0.0, blocking=True, deferDecoding=False):
        """Get a frame from the movie file using VLC.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) of the frame to get in seconds.
        blocking : bool
            Whether to wait for VLC to deliver a frame if none has arrived
            since the last call. Pass `False` to return `None` straight away
            and leave the caller showing the previous frame.
        deferDecoding : bool
            Unused, VLC decoding on a schedule of its own.

        Returns
        -------
        tuple or None
            Video data (`_RGBFrameAdapter`), presentation timestamp (PTS), and
            status.

        """
        if self._vlcPlayer is None:
            return None

        reqPTS = min(
            max(0.0, reqPTS),
            self._metadata.duration + self._metadata.frameInterval)

        self._serviceVLCStreamEnd()
        self._applyPendingVLCSeek(blocking=blocking)

        gotNewFrame = self._pullFrameVLC()

        # VLC decodes to its own clock, so there is nothing to prod along by
        # asking again; either a frame has arrived or one has not. Waiting is
        # only worth it while frames are still coming, otherwise a paused movie
        # would stall the caller for a frame interval on every draw. A seek is
        # the exception: the player may be paused and still owe a frame for the
        # position just moved to.
        waited = False
        if blocking and not gotNewFrame and (not self._vlcPaused or
                                             self._seeking):
            waited = True
            # a seek has to decode forward from a keyframe before it can render
            # anything, which takes longer than a frame is due within during
            # ordinary playback
            deadline = time.time() + (
                VLC_SEEK_TIMEOUT if self._seeking else self._frameInterval)
            while time.time() < deadline:
                time.sleep(0.001)  # yield, don't spin the CPU while waiting
                if self._pullFrameVLC():
                    gotNewFrame = True
                    break

        if self._seeking and waited and not gotNewFrame:
            # VLC has had long enough to render the frame for the new position
            # and has not produced one, which is what happens when the seek ran
            # to the end of the movie and there is no further frame to render.
            # Leaving the seek marked as outstanding would have the caller
            # waiting on a frame which is never going to arrive.
            self._seeking = False
            self._vlcSeekSettleAt = None
            self._vlcPendingSeekPTS = None

        toReturn = self._getFrameFromStore(reqPTS)

        if toReturn is None and gotNewFrame and self._frameStore:
            # VLC runs the movie on its own clock, so the position it reports
            # can differ from the caller's by more than a frame interval,
            # leaving the lookup above with nothing. The frame just decoded is
            # still the one which should be on-screen, so hand that back rather
            # than freezing the video until the two clocks happen to agree.
            img, pts, status = self._frameStore[-1]
            toReturn = (self._convertFrameToRGB(img), pts, status)

        return toReturn

    def _freePlayer(self):
        """Tear down the VLC player and release everything it holds.

        Ordering matters here. The video callbacks run on VLC's decoding
        thread and write into buffers owned by this reader, so the player is
        stopped first (which waits for that thread), then the callbacks are
        unbound, and only then are the buffers dropped.

        Never call this while holding `_vlcFrameLock`: stopping the player
        waits on the decoding thread, which may be waiting for that very lock.

        """
        if self._vlcPlayer is not None:
            import vlc

            if self._vlcEventManager is not None:
                self._vlcEventManager.event_detach(
                    vlc.EventType.MediaPlayerEndReached)
                self._vlcEventManager = None

            self._vlcPlayer.stop()

            # Unbind before the buffers the callbacks write into are dropped.
            # Leaving them bound also keeps the interpreter from shutting down
            # cleanly.
            self._vlcPlayer.video_set_callbacks(None, None, None, None)
            self._vlcPlayer.set_media(None)
            self._vlcPlayer.release()
            self._vlcPlayer = None

        if self._vlcMedia is not None:
            self._vlcMedia.release()
            self._vlcMedia = None

        if self._vlcInstance is not None:
            self._vlcInstance.release()
            self._vlcInstance = None

        # safe now that the player has stopped and the callbacks are unbound
        self._vlcLockCb = self._vlcUnlockCb = self._vlcDisplayCb = None
        self._vlcWriteBuffer = self._vlcReadBuffer = None
        self._vlcFrameNBytes = 0
        self._vlcFrameReady = False
        self._vlcLockHeld = False
        self._vlcSeekSettleAt = None
        self._vlcStreamEnded = False
        self._vlcPaused = True
        self._vlcPausedAt = None
        self._vlcPendingSeekPTS = None

    def pause(self, state=True):
        if self._vlcPlayer is None:
            return

        self._setVLCPaused(state)

    def mute(self, state=True):
        super().mute(state)

        if self._vlcPlayer is None:
            return

        self._vlcPlayer.audio_set_mute(self._muted)

    @property
    def muted(self):
        if self._vlcPlayer is not None:
            # VLC reports `-1` when it cannot say, in which case fall back to
            # the last state asked for
            isMuted = self._vlcPlayer.audio_get_mute()
            if isMuted >= 0:
                return bool(isMuted)

        return super().muted

    def _getVolume(self):
        """Get the volume of the movie player using VLC.

        Returns
        -------
        float
            The volume level of the movie player, between 0.0 (mute) and 1.0
            (full volume).

        """
        if self._vlcPlayer is None:
            return 0.0

        # VLC reports the volume as a percentage, and `-1` if it cannot
        volume = self._vlcPlayer.audio_get_volume()
        if volume < 0:
            return self._decoderOpts.get('volume', 0.0)

        return volume / 100.0

    def _setVolume(self, volume):
        """Set the volume of the movie player using VLC.

        Parameters
        ----------
        volume : float
            The volume level to set, between 0.0 (mute) and 1.0 (full volume).

        """
        if self._vlcPlayer is None:
            return

        self._vlcPlayer.audio_set_volume(int(round(volume * 100.0)))
