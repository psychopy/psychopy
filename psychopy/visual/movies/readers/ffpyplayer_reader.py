#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Movie reader using `ffpyplayer`.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'FFPyPlayerMovieFileReader',
]

import time

from psychopy import logging
from ..frame import FRAME_PIXEL_FORMAT
from ._base import MovieFileReader, defaultTimeout

# constants for use with ffpyplayer
FFPYPLAYER_STATUS_EOF = 'eof'
FFPYPLAYER_STATUS_PAUSED = 'paused'

class FFPyPlayerMovieFileReader(MovieFileReader):
    """Read movie frames from a file with `ffpyplayer`.

    FFPyPlayer decodes in the background on a clock of its own, synced to the
    movie's audio track, which it plays itself through SDL2. See
    `MovieFileReader` for parameters.

    """
    _decoderLib = 'ffpyplayer'

    def __init__(self, filename, decoderLib=None, decoderOpts=None):
        super().__init__(filename, decoderLib, decoderOpts)

        self._player = None  # ffpyplayer.player.MediaPlayer
        # PTS of an in-flight seek, used to discard frames still arriving from
        # the pre-seek position (`None` when no seek is pending)
        self._pendingSeekPTS = None
        # cached `SWScale` instance, rebuilt only when the source pixel format
        # or frame size changes
        self._swsContext = None
        self._swsContextKey = None

    def _open(self):
        """Open a movie reader using FFPyPlayer.

        This function opens the movie file and extracts metadata about the movie
        file. Metadata will be accessible via the `getMetadata()` method.

        """
        # import in the class too avoid hard dependency on ffpyplayer
        try:
            from ffpyplayer.player import MediaPlayer
        except ImportError:
            raise ImportError(
                'The `ffpyplayer` library is required to read movie files with '
                '`decoderLib=ffpyplayer`. Note that `ffpyplayer` is not '
                'available on Python 3.14 and later; use `decoderLib=pyav` '
                'instead (this is the default on those Python versions).')

        logging.info("Opening movie file: {}".format(self._filename))

        # Using sync to audio since it allows us to poll the player for frames
        # any number of frames and allows the audio to be played at the correct 
        # rate if using the SDL2 interface
        syncMode = 'audio' 

        # default options
        defaultFFOpts = {
            'paused': True,
            'sync': syncMode,  # always use audio sync
            'an': False,
            'volume': 0.0,  # mute
            'loop': 1,  # number of replays (0=infinite, 1=once, 2=twice, etc.)
            'infbuf': True,
            'out_fmt': FRAME_PIXEL_FORMAT  # so frames need no conversion here
        }

        # merge user settings with defaults, user settings take precedence
        defaultFFOpts.update(self._decoderOpts)
        self._decoderOpts = defaultFFOpts

        # create media player interface
        self._player = MediaPlayer(
            self._filename,
            ff_opts=self._decoderOpts)

        self._player.set_mute(True)  # mute the player first
        self._player.set_pause(False)

        # Get metadata and 'warm-up' the player to ensure it is responsive 
        # before we start decoding frames.

        # wait for valid metadata to be available
        logging.debug("Waiting for movie metadata...")
        startTime = time.time()
        while time.time() - startTime < defaultTimeout:  # 5 second timeout
            movieMetadata = self._player.get_metadata()
            # keep calling until we get a valid frame size
            if movieMetadata['src_vid_size'] != (0, 0):
                break
            time.sleep(0.001)  # yield, don't spin the CPU while waiting
        else:
            raise RuntimeError(
                'FFPyPlayer failed to extract metadata from the movie. Check '
                'the movie file and decoder options.')

        # warmup, takes a while before the video starts playing
        startTime = time.time()
        while time.time() - startTime < defaultTimeout:  # 5 second timeout
            frame, _ = self._player.get_frame()
            if frame is not None:
                break
            time.sleep(0.001)  # yield, don't spin the CPU while waiting
        else:
            raise RuntimeError(
                'FFPyPlayer failed to start decoding the movie. Check the '
                'movie file and decoder options.')
        
        # go back to first frame
        self._player.set_pause(True)  # pause the player again
        self._player.set_mute(False)  # unmute the player

        # seek to the beginning of the movie
        self._player.seek(0.0, relative=False, accurate=False)
        
        # wait until the player actually seeks to zero, this gets its own
        # timeout budget since the warm-up above may have consumed most of it
        startTime = time.time()
        while time.time() - startTime < defaultTimeout:
            curPts = self._player.get_pts()
            if abs(curPts) < 1e-6:
                break
            time.sleep(0.001)  # wait a bit before checking again
        else:
            logging.warning(
                "FFPyPlayer did not report seeking back to the start of the "
                "movie within {} seconds; the first frame presented may not "
                "be the first frame of the movie.".format(defaultTimeout))

        # compute frame rate and interval
        numer, denom = movieMetadata['frame_rate']
        if not denom or not numer:
            raise RuntimeError(
                'FFPyPlayer could not determine the frame rate of the movie '
                'file (reported {}/{}).'.format(numer, denom))
        frameRate = numer / denom

        duration = movieMetadata['duration']
        if not duration > 0.0:
            raise RuntimeError(
                'FFPyPlayer could not determine the duration of the movie '
                'file (reported {}).'.format(duration))

        # Report the pixel format frames are actually delivered in rather
        # than `src_pix_fmt` (the format of the *source* stream). Frames are
        # always converted to `FRAME_PIXEL_FORMAT`, whatever `out_fmt` the user
        # passed, so reporting the source format here would disagree with
        # what `getFrame()` returns and with the other decoder backends.
        img, curPts = frame
        initialFrameRGB = self._convertFrameToRGB(img)
        deliveredPixFmt = initialFrameRGB.get_pixel_format()

        # populate the metadata object with the movie metadata we got
        self._setMovieProperties(
            movieMetadata['src_vid_size'], frameRate, duration,
            deliveredPixFmt)

        logging.debug("FFPyPlayer metadata: {}".format(movieMetadata))

        # store the frame we got during warmup so it shows when the movie is
        # stopped+idle but not paused
        self._frameStore.append(
            (initialFrameRGB, curPts, FFPYPLAYER_STATUS_PAUSED))
    
    def _seek(self, reqPTS):
        """FFPyPlayer specific seek routine.

        This is called by `seek()` when the `ffpyplayer` backend is in use. 
        Video decoding will be paused after calling this function.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) to seek to in seconds.

        Returns
        -------
        float
            The presentation timestamp (PTS) requested in seconds. FFPyPlayer
            seeks asynchronously, so the decoder may still be delivering frames
            from the previous position when this returns; `_getFrame`
            discards those before returning a frame.

        """
        reqPTS = min(max(0.0, reqPTS), self._metadata.duration)

        if self._player is None:
            return
        
        # clear the frame store
        self._cleanUpFrameStore()

        # seek to the desired PTS
        self._player.seek(
            reqPTS, 
            relative=False, 
            seek_by_bytes=False, 
            accurate=True)

        # Mark the seek as in-flight. `get_pts()` reports the *requested*
        # position as soon as the seek is issued, so it cannot tell us when the
        # decoder has caught up; instead `_getFrame` drops frames
        # that arrive from ahead of this target until the seek lands.
        self._pendingSeekPTS = reqPTS

        return reqPTS
    
    def _convertFrameToRGB(self, frame):
        """Convert a frame to RGBA format.

        This function converts a frame to `FRAME_PIXEL_FORMAT`. The player is
        asked for frames in that format already (see `out_fmt` in
        `_open`), so this only converts if a user-supplied `out_fmt`
        overrode it. The result will be in the correct format to upload to
        OpenGL as a texture.

        Parameters
        ----------
        frame : FFPyPlayer frame
            The frame to convert.

        Returns
        -------
        ffpyplayer.pic.Image
            The converted frame in RGBA format.

        """
        srcPixFmt = frame.get_pixel_format()

        if srcPixFmt == FRAME_PIXEL_FORMAT:  # already converted
            return frame

        from ffpyplayer.pic import SWScale

        # Use the frame's own dimensions rather than the metadata size, which
        # can disagree with what the decoder actually emits.
        width, height = frame.get_size()

        # Building an `SWScale` allocates a colour conversion context, so reuse
        # it across frames and only rebuild when the format or size changes.
        contextKey = (srcPixFmt, width, height)
        if self._swsContext is None or self._swsContextKey != contextKey:
            self._swsContext = SWScale(
                width, height, srcPixFmt, ofmt=FRAME_PIXEL_FORMAT)
            self._swsContextKey = contextKey

        return self._swsContext.scale(frame)

    def _bufferFrames(self, start=0.0, end=None, units='seconds',
                                maxFrames=1024):
        """Buffer frames from the movie file using FFPyPlayer.
        
        Parameters
        ----------
        start : float or int
            The start position to buffer frames from, interpreted according to
            `units`.
        end : float or int or None
            The end position to buffer frames to, interpreted according to
            `units`. If `None`, the end of the movie is used.
        units : str
            The units `start` and `end` are given in, either `'seconds'`
            (default) or `'frames'`. If `'frames'`, they are interpreted as
            frame indices.
        maxFrames : int
            Maximum number of frames to buffer. Decoded frames are held in
            memory as RGB24, so an unbounded range can exhaust memory on long
            or high resolution movies (a minute of 1080p is roughly 11 GB).
            Buffering stops once this many frames have been collected.

        """
        if self._player is None:
            return

        if units not in ('seconds', 'frames'):
            raise ValueError(
                "`units` must be either 'seconds' or 'frames', got "
                "'{}'.".format(units))

        # check if we have a valid start time
        if start < 0.0:
            raise ValueError('Start time must be greater than or equal to 0.0.')

        # check if we have a valid end time
        if end is None:
            end = self._metadata.duration if units == 'seconds' else \
                self._timestampToFrameIndex(self._metadata.duration)
        elif end < 0.0:
            raise ValueError('End time must be greater than or equal to 0.0.')

        # convert the start and end frame indices to timestamps
        if units == 'frames':
            start = self._frameIndexToTimestamp(start)
            end = self._frameIndexToTimestamp(end)

        if end < start:
            raise ValueError(
                'End time must be greater than or equal to the start time.')

        # seek to the start time
        self._seek(start)

        # buffer frames from the movie file
        buffered = 0
        getFrameAttempts = 0
        staleDrops = 0
        maxStaleDrops = 240
        # FFPyPlayer paces delivery to the playback clock, so `get_frame()`
        # returns `None` on most polls; retry rather than stopping at the first
        # one. The budget is per-frame (reset below on each frame received) and
        # generous since buffering is a bulk operation with no timing demands.
        maxBufferAttempts = self._maxGetFrameAttempts * 3

        while buffered < maxFrames:
            frame, status = self._player.get_frame()

            if status == FFPYPLAYER_STATUS_EOF:
                break

            if frame is None:
                if getFrameAttempts < maxBufferAttempts:
                    time.sleep(0.001)
                    getFrameAttempts += 1
                    continue
                logging.warning(
                    "FFPyPlayer stopped delivering frames while buffering; "
                    "buffered {} frame(s).".format(buffered))
                break

            getFrameAttempts = 0  # frame received, reset the retry budget

            img, curPts = frame

            # drop frames still arriving from before the seek above
            if self._pendingSeekPTS is not None:
                if curPts > self._pendingSeekPTS + self._metadata.frameInterval:
                    staleDrops += 1
                    if staleDrops < maxStaleDrops:
                        continue
                self._pendingSeekPTS = None

            if curPts >= end:
                break
            if curPts >= start:
                # convert the frame to RGB format
                rgbImg = self._convertFrameToRGB(img)
                self._frameStore.append((rgbImg, curPts, 'playing'))
                buffered += 1
        else:
            logging.warning(
                "Stopped buffering after reaching the {} frame limit; request "
                "a narrower range or raise `maxFrames`.".format(maxFrames))

    def _getFrame(self, reqPTS=0.0, blocking=True, deferDecoding=False):
        """Get a frame from the movie file using FFPyPlayer.

        This method gets the desired frame from the movie file. If it has not
        been decoded yet, this function will ensure the frame is decoded and 
        made available.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) of the frame to get in seconds.
            This hints the reader to which frame to decode and return.
        blocking : bool
            Whether to wait for the decoder to catch up. FFPyPlayer hands over
            frames on its own schedule, so by default this waits up to a frame
            interval for one. Pass `False` to give up immediately instead and
            leave the caller showing the previous frame, which keeps a drawing
            loop responsive while a seek is still resolving.
        deferDecoding : bool
            Unused, FFPyPlayer decoding on a schedule of its own.

        Returns
        -------
        tuple
            Video data (`ndarray`), presentation timestamp (PTS), and status.
            The status value may be backend specific.

        """        
        # check if we have a player object, return None if not
        if self._player is None:
            return None
            # raise ValueError('Movie reader is not open. Cannot grab frame.')
        
        # normalzie the PTS to be between 0 and the duration of the movie
        reqPTS = min(max(0.0, reqPTS), 
                     self._metadata.duration + self._metadata.frameInterval)
        
        # check if we have the frame in the store
        frame = self._getFrameFromStore(reqPTS)
        if frame is not None:
            return frame
        
        getFrameAttempts = 0
        # bound on frames discarded while waiting for a seek to land, so a
        # seek that never takes effect cannot hang the caller
        staleDrops = 0
        maxStaleDrops = 240
        while 1:  # keep getting frames until we reach the desired PTS           
            frame, status = self._player.get_frame()

            if status == FFPYPLAYER_STATUS_EOF:
                if self._streamEOFCallback is not None:
                    self._streamEOFCallback()
                self._cleanUpFrameStore()
                self._pendingSeekPTS = None
                self._seeking = False  # nothing left to seek to
                break
            elif status == FFPYPLAYER_STATUS_PAUSED:
                # A paused decoder will not deliver the frame a seek is waiting
                # on, so stop reporting the seek as outstanding. This is what
                # happens when a movie is seeked past its own end, since
                # reaching the end pauses playback.
                self._seeking = False
                break
            
            # If we get `None` for the frame, the player isn't ready to give us
            # one yet, so wait a moment and try again. Give up after
            # `_maxGetFrameAttempts` *consecutive* misses and let the caller
            # show the previous frame; `MovieStim.updateVideoFrame` already
            # treats `None` as 'keep the last frame on screen'. Raising here
            # would abort the experiment over a transient decoder stall.
            if frame is None:
                maxAttempts = self._maxGetFrameAttempts
                if not blocking:
                    maxAttempts = max(1, maxAttempts // 8)

                if getFrameAttempts < maxAttempts:
                    time.sleep(0.001)  # wait a bit before trying again
                    getFrameAttempts += 1
                    continue   # keep retrying
                
                if blocking:
                    logging.warning(
                        "FFPyPlayer failed to return a frame after {} "
                        "attempts, keeping the previous frame.".format(
                            getFrameAttempts))
                break
            
            # the decoder gave us a frame, so reset the retry budget; it counts
            # consecutive misses, not misses accumulated over a long decode
            getFrameAttempts = 0
            
            img, curPts = frame  # extract frame information

            # Discard frames still in flight from before a seek. An accurate
            # seek never lands ahead of its target, so anything ahead of it is
            # left over from the previous position and would otherwise be
            # stored against the wrong PTS (breaking backward seeks).
            if self._pendingSeekPTS is not None:
                if curPts > self._pendingSeekPTS + self._metadata.frameInterval:
                    staleDrops += 1
                    if staleDrops < maxStaleDrops:
                        continue  # stale, keep draining
                    logging.warning(
                        "FFPyPlayer did not settle at the requested seek "
                        "position after discarding {} frames; using the "
                        "current position instead.".format(staleDrops))
                self._pendingSeekPTS = None  # seek has landed (or gave up)

            # if we have gotten the frame we are looking for, return it
            if curPts + self._metadata.frameInterval >= reqPTS:
                self._frameStore.append(
                    (self._convertFrameToRGB(img), curPts,
                     'playing'))
                break
        
        toReturn = self._getFrameFromStore(reqPTS)

        self._cleanUpFrameStore(reqPTS)  # clean up the frame store

        return toReturn
    
    def _freePlayer(self):
        if self._player is None:
            return

        self._player.set_mute(True)  # mute the player
        self._player.set_pause(True)  # pause the player
        self._player.close_player()

        self._player = None
        self._pendingSeekPTS = None
        self._swsContext = None
        self._swsContextKey = None

    def pause(self, state=True):
        if self._player is None:
            return

        self._player.set_pause(bool(state))

    def mute(self, state=True):
        super().mute(state)

        if self._player is None:
            return

        self._player.set_mute(self._muted)

    @property
    def muted(self):
        if self._player is not None:
            return bool(self._player.get_mute())

        return super().muted

    def _getVolume(self):
        """Get the volume of the movie player using the ffpyplayer library.

        Returns
        -------
        float
            The volume level of the movie player, between 0.0 (mute) and 1.0 (full volume).
        """
        if self._player is None:
            return 0.0

        return self._player.get_volume()

    def _setVolume(self, volume):
        """Set the volume of the movie player using the ffpyplayer library.

        Parameters
        ----------
        volume : float
            The volume level to set, between 0.0 (mute) and 1.0 (full volume).

        """
        if self._player is None:
            return

        self._player.set_volume(volume)
