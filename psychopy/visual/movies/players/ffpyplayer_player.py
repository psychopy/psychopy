#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for movie player interfaces.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'FFPyPlayer'
]

import sys

from ffpyplayer.player import MediaPlayer  # very first thing to import
import time
import psychopy.logging as logging
import math
import numpy as np
import threading
import queue
from psychopy.core import getTime
from ._base import BaseMoviePlayer
from ..metadata import MovieMetadata
from ..frame import MovieFrame, NULL_MOVIE_FRAME_INFO
from psychopy.constants import (
    FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED, STOPPING, INVALID, SEEKING)
from psychopy.tools.filetools import pathToString
import atexit


# Options that PsychoPy devs picked to provide better performance, these can
# be overridden, but it might result in undefined behavior.
DEFAULT_FF_OPTS = {
    'sync': 'audio',    # sync to audio
    'paused': True,     # start paused
    'autoexit': False,  # don't exit ffmpeg automatically
    'loop': 0           # enable looping
}

# default queue size for the stream reader
DEFAULT_FRAME_QUEUE_SIZE = 1

# event to close all opened movie reader threads
_evtCleanUpMovieEvent = threading.Event()
_evtCleanUpMovieEvent.clear()


# Cleanup routines for threads. This allows the app to crash gracefully rather
# than locking up on error.
def _closeMovieThreads():
    """Callback function when the application exits which cleans up movie
    threads. When this function is called, any outstanding movie threads will
    be closed automatically. This must not be called at any other point of the
    program.
    """
    global _evtCleanUpMovieEvent
    _evtCleanUpMovieEvent.set()


atexit.register(_closeMovieThreads)  # register the function


class StreamStatus:
    """Descriptor class for stream status.

    This class is used to report the current status of the movie stream at the
    time the movie frame was obtained.

    Parameters
    ----------
    status : int
        Status flag for the stream.
    streamTime : float
        Current stream (movie) time in seconds. Resets after a loop has
        completed.
    frameIndex : int
        Current frame index, increases monotonically as a movie plays and resets
        when finished or beginning another loop.
    loopCount : int
        If looping is enabled, this value increases by 1 each time the movie
        loops. Initial value is 0.

    """
    __slots__ = ['_status',
                 '_streamTime',
                 '_frameIndex',
                 '_loopCount']

    def __init__(self,
                 status=NOT_STARTED,
                 streamTime=0.0,
                 frameIndex=-1,
                 loopCount=-1):

        self._status = int(status)
        self._streamTime = float(streamTime)
        self._frameIndex = frameIndex
        self._loopCount = loopCount

    @property
    def status(self):
        """Status flag for the stream (`int`).
        """
        return self._status

    @property
    def streamTime(self):
        """Current stream time in seconds (`float`).

        This value increases monotonically and is common timebase for all
        cameras attached to the system.
        """
        return self._streamTime

    @property
    def frameIndex(self):
        """Current frame in the stream (`float`).

        This value increases monotonically as the movie plays. The first frame
        has an index of 0.
        """
        return self._frameIndex

    @property
    def loopCount(self):
        """Number of times the movie has looped (`float`).

        This value increases monotonically as the movie plays. This is
        incremented when the movie finishes.
        """
        return self._loopCount


class StreamData:
    """Descriptor class for movie stream data.

    Instances of this class are produced by the movie stream reader thread
    which contains metadata about the stream, frame image data (i.e. pixel
    values), and the stream status.

    Parameters
    ----------
    metadata : MovieMetadata
        Stream metadata.
    frameImage : object
        Video frame image data.
    streamStatus : StreamStatus
        Video stream status.
    cameraLib : str
        Camera library in use to process the stream.

    """
    __slots__ = ['_metadata',
                 '_frameImage',
                 '_streamStatus',
                 '_cameraLib']

    def __init__(self, metadata, frameImage, streamStatus, cameraLib):
        self._metadata = metadata
        self._frameImage = frameImage
        self._streamStatus = streamStatus
        self._cameraLib = cameraLib

    @property
    def metadata(self):
        """Stream metadata at the time the video frame was acquired
        (`MovieMetadata`).
        """
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        if not isinstance(value, MovieMetadata) or value is not None:
            raise TypeError("Incorrect type for property `metadata`, expected "
                            "`MovieMetadata` or `None`.")

        self._metadata = value

    @property
    def frameImage(self):
        """Frame image data from the codec (`ffpyplayer.pic.Image`).
        """
        return self._frameImage

    @frameImage.setter
    def frameImage(self, value):
        self._frameImage = value

    @property
    def streamStatus(self):
        """Stream status (`StreamStatus`).
        """
        return self._streamStatus

    @streamStatus.setter
    def streamStatus(self, value):
        if not isinstance(value, StreamStatus) or value is not None:
            raise TypeError("Incorrect type for property `streamStatus`, "
                            "expected `StreamStatus` or `None`.")

        self._streamStatus = value

    @property
    def cameraLib(self):
        """Camera library in use to obtain the stream (`str`). Value is
        blank if `metadata` is `None`.
        """
        if self._metadata is not None:
            return self._metadata.movieLib

        return u''


class MovieStreamThreadFFPyPlayer(threading.Thread):
    """Class for reading movie streams asynchronously.

    The rate of which frames are read is controlled dynamically based on values
    within stream metadata. This will ensure that CPU load is kept to a minimum,
    only polling for new frames at the rate they are being made available.

    Parameters
    ----------
    player : `ffpyplayer.player.MediaPlayer`
        Media player instance, should be configured and initialized. Note that
        player instance methods might not be thread-safe after handing off the
        object to this thread.
    bufferFrames : int
        Number of frames to buffer. Sets the frame queue size for the thread.
        Use a queue size >1 for video recorded with a framerate above 60Hz.

    """

    def __init__(self, player, bufferFrames=DEFAULT_FRAME_QUEUE_SIZE):
        threading.Thread.__init__(self)
        # Make this thread daemonic since we don't yet have a way of tracking
        # them down. Since we're only reading resources, it's unlikely that
        # we'll break or corrupt something. Good practice is to call `stop()`
        # before exiting, this thread will join as usual and cleanly free up
        # any resources.
        self.daemon = True

        self._player = player  # player interface to FFMPEG
        self._frameQueue = queue.Queue(maxsize=bufferFrames)
        self._cmdQueue = queue.Queue()  # queue for player commands

        # some values the user might want
        self._status = NOT_STARTED
        self._streamTime = 0.0
        self._isIdling = False
        self._isFinished = False

        # Locks for syncing the player and main application thread
        self._warmUpLock = threading.Lock()
        self._warmUpLock.acquire(blocking=False)

    def run(self):
        """Main sub-routine for this thread.

        When the thread is running, data about captured frames are put into the
        `frameQueue` as `(metadata, img, pts)`. If the queue is empty, that
        means the main application thread is running faster than the encoder
        can get frames. Recommended behaviour in such cases it to return the
        last valid frame when the queue is empty.

        """
        global _evtCleanUpMovieEvent
        if self._player is None:
            return  # exit thread if no player

        # these should stay within the scope of this subroutine
        frameInterval = 0.004        # frame interval, start at 4ms (250Hz)
        frameData = None             # frame data from the reader
        val = ''                     # status value from reader
        statusFlag = NOT_STARTED     # status flag for stream reader state
        frameIndex = -1              # frame index, 0 == first frame
        loopCount = 0                # number of movie loops so far
        mustShutdown = False         # player thread should shut down

        # Subroutines for various player functions -----------------------------

        def seekTo(player, ptsTarget, maxAttempts=16):
            """Seek to a position in the video. Return the frame at that
            position.

            Parameters
            ----------
            player : `MediaPlayer`
                Handle to player.
            ptsTarget : float
                Location in the movie to seek to. Must be a positive number.
            maxAttempts : int
                Number of attempts to converge.

            Returns
            -------
            tuple
                Frame data and value from the `MediaPlayer` after seeking to the
                position.

            """
            wasPaused = player.get_pause()
            player.set_pause(False)
            player.set_mute(True)

            # issue seek command to the player
            player.seek(ptsTarget, relative=False, accurate=True)
            # wait until we are at the seek position
            n = 0
            ptsLast = float(2 ** 32)
            while n < maxAttempts:  # converge on position
                frameData_, val_ = player.get_frame(show=True)
                if frameData_ is None:
                    time.sleep(0.0025)
                    n += 1
                    continue

                _, pts_ = frameData_
                ptsClock = player.get_pts()
                # Check if the PTS is the same as the last attempt, if so
                # we are likely not going to converge on some other value.
                if math.isclose(ptsClock, ptsLast):
                    break

                # If the PTS is different than the last one, check if it's
                # close to the target.
                if math.isclose(pts_, ptsTarget) and math.isclose(
                        ptsClock, ptsTarget):
                    break

                ptsLast = ptsClock
                n += 1

            else:
                frameData_, val_ = None, ''

            player.set_mute(False)
            player.set_pause(wasPaused)

            return frameData_, val_

        def calcFrameIndex(pts_, frameInterval_):
            """Calculate the frame index from the presentation time stamp and
            frame interval.

            Parameters
            ----------
            pts_ : float
                Presentation timestamp.
            frameInterval_ : float
                Frame interval of the movie in seconds.

            Returns
            -------
            int
                Frame index.

            """
            return int(math.floor(pts_ / frameInterval_)) - 1

        # ----------------------------------------------------------------------
        # Initialization
        #
        # Warmup the reader and get the first frame, this will be presented when
        # the player is first initialized, we should block until this process
        # completes using a lock object. To get the first frame we start the
        # video, acquire the frame, then seek to the beginning. The frame will
        # remain in the queue until accessed. The first frame is important since
        # it is needed to configure the texture buffers in the rendering thread.
        #

        # We need to start playback to access the first frame. This can be done
        # "silently" by muting the audio and playing the video for a single
        # frame. We then seek back to the beginning and pause the video. This
        # will ensure the first frame is presented.
        #
        self._player.set_mute(True)
        self._player.set_pause(False)

        # consume frames until we get a valid one, need its metadata
        while frameData is None or val == 'not ready':
            frameData, val = self._player.get_frame(show=True)
            # end of the file? ... at this point? something went wrong ...
            if val == 'eof':
                break
            time.sleep(frameInterval)  # sleep a bit to avoid mashing the CPU

        # Obtain metadata from the frame now that we have a flowing stream. This
        # data is needed by the main thread to process to configure additional
        # resources needed to present the video.
        metadata = self._player.get_metadata()

        # Compute the frame interval that will be used, this is dynamically set
        # to reduce the amount of CPU load when obtaining new frames. Aliasing
        # may occur sometimes, possibly looking like a frame is being skipped,
        # but we're not sure if this actually happens in practice.
        frameRate = metadata['frame_rate']
        numer, denom = frameRate
        try:
            frameInterval = 1.0 / (numer / float(denom))
        except ZeroDivisionError:
            # likely won't happen since we always get a valid frame before
            # reaching here, but you never know ...
            raise RuntimeError(
                "Cannot play movie. Failed to acquire metadata from video "
                "stream!")

        # Get the movie duration, needed to determine when we get to the end of
        # movie. We need to reset some params when there. This is in seconds.
        duration = metadata['duration']

        # Get color and timestamp data from the returned frame object, this will
        # be encapsulated in a `StreamData` object and passed back to the main
        # thread with status information.
        colorData, pts = frameData

        # Build up the object which we'll pass to the application thread. Stream
        # status information hold timestamp and playback information.
        streamStatus = StreamStatus(
            status=statusFlag,    # current status flag, should be `NOT_STARTED`
            streamTime=pts)       # frame timestamp

        # Put the frame in the frame queue so the main thread can read access it
        # safely. The main thread should hold onto any frame it gets when the
        # queue is empty.
        if self._frameQueue.full():
            raise RuntimeError(
                "Movie decoder frame queue is full and it really shouldn't be "
                "at this point.")

        # Object to pass video frame data back to the application thread for
        # presentation or processing.
        lastFrame = StreamData(
            metadata,
            colorData,
            streamStatus,
            u'ffpyplayer')

        # Pass the object to the main thread using the frame queue.
        self._frameQueue.put(lastFrame)  # put frame data in here

        # Rewind back to the beginning of the file, we should have the first
        # frame and metadata from the file by now.
        self._player.set_pause(True)  # start paused
        self._player.set_mute(False)
        # frameData, val = seekTo(self._player, 0.0)

        # set the volume again because irt doesn't seem to remember it
        self._player.set_volume(self._player.get_volume())

        # Release the lock to unblock the parent thread once we have the first
        # frame and valid metadata from the stream. After this returns the
        # main thread should call `getRecentFrame` to get the frame data.
        self._warmUpLock.release()

        # ----------------------------------------------------------------------
        # Playback
        #
        # Main playback loop, this will continually pull frames from the stream
        # and push them into the frame queue. The user can pause and resume
        # playback. Avoid blocking anything outside the use of timers to prevent
        # stalling the thread.
        #
        while 1:
            # pull a new frame
            frameData, val = self._player.get_frame()
            # if no frame, just pause the thread and restart the loop
            if val == 'eof':  # end of stream/file
                self._isFinished = self._isIdling = True
                time.sleep(frameInterval)
            elif frameData is None or val == 'paused':  # paused or not ready
                self._isIdling = True
                self._isFinished = False
                time.sleep(frameInterval)
            else:  # playing
                self._isIdling = self._isFinished = False
                colorData, pts = frameData  # got a valid frame

                # updated last valid frame data
                lastFrame = StreamData(
                    metadata,
                    colorData,
                    StreamStatus(
                        status=statusFlag,  # might remove
                        streamTime=pts,
                        frameIndex=calcFrameIndex(pts, frameInterval),
                        loopCount=loopCount),
                    u'ffpyplayer')

                # is the next frame the last? increment the number of loops then
                if pts + frameInterval * 1.5 >= duration:
                    loopCount += 1  # inc number of loops

                if isinstance(val, float):
                    time.sleep(val)  # time to sleep
                else:
                    time.sleep(frameInterval)

                # If the queue is full, just discard the frame and get the
                # next one to allow us to catch up.
                try:
                    self._frameQueue.put_nowait(lastFrame)
                except queue.Full:
                    pass  # do nothing

            # ------------------------------------------------------------------
            # Process playback controls
            #
            # Check the command queue for playback commands. Process all
            # commands in the queue before progressing. A command is a tuple put
            # into the queue where the first value is the op-code and the second
            # is the value:
            #
            #   OPCODE, VALUE = COMMAND
            #
            # The op-code is a string specifying the command to execute, while
            # the value can be any object needed to carry out the command.
            # Possible opcodes and their values are shown in the table below:
            #
            #   OPCODE      | VALUE              |  DESCRIPTION
            #   ------------+--------------------+------------------------------
            #   'volume'    | float (0.0 -> 1.0) | Set the volume
            #   'mute'      | bool               | Enable/disable sound
            #   'play'      | None               | Play a stream
            #   'pause'     | None               | Pause a stream
            #   'stop'      | None               | Pause and restart
            #   'seek'      | pts, bool          | Seek to a movie position
            #   'shutdown'  | None               | Kill the thread
            #
            needsWait = False
            if not self._cmdQueue.empty():
                cmdOpCode, cmdVal = self._cmdQueue.get_nowait()

                # process the command
                if cmdOpCode == 'volume':  # set the volume
                    self._player.set_volume(float(cmdVal))
                    needsWait = True
                elif cmdOpCode == 'mute':
                    self._player.set_mute(bool(cmdVal))
                    needsWait = True
                elif cmdOpCode == 'play':
                    self._player.set_mute(False)
                    self._player.set_pause(False)
                elif cmdOpCode == 'pause':
                    self._player.set_mute(True)
                    self._player.set_pause(True)
                elif cmdOpCode == 'seek':
                    seekToPts, seekRel = cmdVal
                    self._player.seek(
                        seekToPts,
                        relative=seekRel,
                        accurate=True)
                    time.sleep(0.1)  # long wait for seeking
                elif cmdOpCode == 'stop':  # stop playback, return to start
                    self._player.set_mute(True)
                    self._player.seek(
                        -1.0,  # seek to beginning
                        relative=False,
                        accurate=True)
                    self._player.set_pause(True)
                    loopCount = 0  # reset loop count
                    time.sleep(0.1)
                elif cmdOpCode == 'shutdown':  # shutdown the player
                    mustShutdown = True

                # signal to the main thread that the command has been processed
                if not mustShutdown:
                    self._cmdQueue.task_done()
                else:
                    break

            # if the command needs some additional processing time
            if needsWait:
                time.sleep(frameInterval)

        # close the player when the thread exits
        self._player.close_player()
        self._cmdQueue.task_done()

    @property
    def isFinished(self):
        """Is the movie done playing (`bool`)? This is `True` if the movie
        stream is at EOF.
        """
        return self._isFinished

    @property
    def isIdling(self):
        """Is the movie reader thread "idling" (`bool`)? If `True`, the movie is
        finished playing and no frames are being polled from FFMPEG.
        """
        return self._isIdling

    @property
    def isReady(self):
        """`True` if the stream reader is ready (`bool`).
        """
        return not self._warmUpLock.locked()

    def begin(self):
        """Call this to start the thread and begin reading frames. This will
        block until we get a valid frame.
        """
        self.start()  # start the thread, will begin decoding frames
        # hold until the lock is released when the thread gets a valid frame
        # this will prevent the main loop for executing until we're ready
        self._warmUpLock.acquire(blocking=True)

    def play(self):
        """Start playing the video from the stream.
        """
        cmd = ('play', None)
        self._cmdQueue.put(cmd)
        self._cmdQueue.join()

    def pause(self):
        """Stop recording frames to the output file.
        """
        cmd = ('pause', None)
        self._cmdQueue.put(cmd)
        self._cmdQueue.join()

    def seek(self, pts, relative=False):
        """Seek to a position in the video.
        """
        cmd = ('seek', (pts, relative))
        self._cmdQueue.put(cmd)
        self._cmdQueue.join()

    def stop(self):
        """Stop playback, reset the movie to the beginning.
        """
        cmd = ('stop', None)
        self._cmdQueue.put(cmd)
        self._cmdQueue.join()

    def shutdown(self):
        """Shutdown the movie reader thread.
        """
        cmd = ('shutdown', None)
        self._cmdQueue.put(cmd)
        self._cmdQueue.join()

    def isDone(self):
        """Check if the video is done playing.

        Returns
        -------
        bool
            Is the video done?

        """
        return not self.is_alive()

    def getVolume(self):
        """Get the current volume level."""
        if self._player is not None:
            return self._player.get_volume()

        return 0.0

    def setVolume(self, volume):
        """Set the volume for the video.

        Parameters
        ----------
        volume : float
            New volume level, ranging between 0 and 1.

        """
        cmd = ('volume', volume)
        self._cmdQueue.put(cmd)
        self._cmdQueue.join()

    def setMute(self, mute):
        """Set the volume for the video.

        Parameters
        ----------
        mute : bool
            Mute state. If `True`, audio will be muted.

        """
        cmd = ('mute', mute)
        self._cmdQueue.put(cmd)
        self._cmdQueue.join()

    def getRecentFrame(self):
        """Get the most recent frame data from the feed (`tuple`).

        Returns
        -------
        tuple or None
            Frame data formatted as `(metadata, frameData, val)`. The `metadata`
            is a `dict`, `frameData` is a `tuple` with format (`colorData`,
            `pts`) and `val` is a `str` returned by the
            `MediaPlayer.get_frame()` method. Returns `None` if there is no
            frame data.

        """
        if self._frameQueue.empty():
            return None

        # hold only last frame and return that instead of None?
        return self._frameQueue.get()


class FFPyPlayer(BaseMoviePlayer):
    """Interface class for the FFPyPlayer library for use with `MovieStim`.

    This class also serves as the reference implementation for classes which
    interface with movie codec libraries for use with `MovieStim`. Creating new
    player classes which closely replicate the behaviour of this one should
    allow them to smoothly plug into `MovieStim`.

    """
    _movieLib = 'ffpyplayer'

    def __init__(self, parent):
        self._filename = u""

        self.parent = parent

        # handle to `ffpyplayer`
        self._handle = None

        # thread for reading frames asynchronously
        self._tStream = None

        # data from stream thread
        self._lastFrame = NULL_MOVIE_FRAME_INFO
        self._frameIndex = -1
        self._loopCount = 0
        self._metadata = None  # metadata from the stream

        self._lastPlayerOpts = DEFAULT_FF_OPTS.copy()

        # options from the parent
        if self.parent.loop:  # infinite loop
            self._lastPlayerOpts['loop'] = 0
        else:
            self._lastPlayerOpts['loop'] = 1  # play once

        if hasattr(self.parent, '_noAudio'):
            self._lastPlayerOpts['an'] = self.parent._noAudio

        # status flags
        self._status = NOT_STARTED

    def start(self, log=True):
        """Initialize and start the decoder. This method will return when a
        valid frame is made available.

        """
        # clear queued data from previous streams
        self._lastFrame = None
        self._frameIndex = -1

        # open the media player
        handle = MediaPlayer(self._filename, ff_opts=self._lastPlayerOpts)
        handle.set_pause(True)

        # Pull the first frame to get metadata. NB - `_enqueueFrame` should be
        # able to do this but the logic in there depends on having access to
        # metadata first. That may be rewritten at some point to reduce all of
        # this to just a single `_enqeueFrame` call.
        #
        self._status = NOT_STARTED

        # hand off the player interface to the thread
        self._tStream = MovieStreamThreadFFPyPlayer(handle)
        self._tStream.begin()

        # make sure we have metadata
        self.update()

    def load(self, pathToMovie):
        """Load a movie file from disk.

        Parameters
        ----------
        pathToMovie : str
            Path to movie file, stream (URI) or camera. Must be a format that
            FFMPEG supports.

        """
        # set the file path
        self._filename = pathToString(pathToMovie)

        # Check if the player is already started. Close it and load a new
        # instance if so.
        if self._tStream is not None:  # player already started
            # make sure it's the correct type
            # if not isinstance(self._handle, MediaPlayer):
            #     raise TypeError(
            #         'Incorrect type for `FFMovieStim._player`, expected '
            #         '`ffpyplayer.player.MediaPlayer`. Got type `{}` '
            #         'instead.'.format(type(self._handle).__name__))

            # close the player and reset
            self.unload()

            # self._selectWindow(self.win)  # free buffers here !!!

        self.start()

        self._status = NOT_STARTED

    def unload(self):
        """Unload the video stream and reset.
        """
        self._tStream.shutdown()
        self._tStream.join()  # wait until thread exits
        self._tStream = None

        # if self._handle is not None:
        #     self._handle.close_player()
        #     self._handle = None  # reset

        self._filename = u""
        self._frameIndex = -1
        self._handle = None  # reset

    # @property
    # def handle(self):
    #     """Handle to the `MediaPlayer` object exposed by FFPyPlayer. If `None`,
    #     no media player object has yet been initialized.
    #     """
    #     return self._handle

    @property
    def isLoaded(self):
        return self._tStream is not None

    @property
    def metadata(self):
        """Most recent metadata (`MovieMetadata`).
        """
        return self.getMetadata()

    def getMetadata(self):
        """Get metadata from the movie stream.

        Returns
        -------
        MovieMetadata
            Movie metadata object. If no movie is loaded, `NULL_MOVIE_METADATA`
            is returned. At a minimum, fields `duration`, `size`, and
            `frameRate` are populated if a valid movie has been previously
            loaded.

        """
        self._assertMediaPlayer()

        metadata = self._metadata

        # write metadata to the fields of a `MovieMetadata` object
        toReturn = MovieMetadata(
            mediaPath=self._filename,
            title=metadata['title'],
            duration=metadata['duration'],
            frameRate=metadata['frame_rate'],
            size=metadata['src_vid_size'],
            pixelFormat=metadata['src_pix_fmt'],
            movieLib=self._movieLib,
            userData=None
        )

        return toReturn

    def _assertMediaPlayer(self):
        """Ensure the media player instance is available. Raises a
        `RuntimeError` if no movie is loaded.
        """
        if self._tStream is not None:
            return  # nop if we're good

        raise RuntimeError(
            "Calling this class method requires a successful call to "
            "`load` first.")

    @property
    def status(self):
        """Player status flag (`int`).
        """
        return self._status

    @property
    def isPlaying(self):
        """`True` if the video is presently playing (`bool`)."""
        # Status flags as properties are pretty useful for users since they are
        # self documenting and prevent the user from touching the status flag
        # attribute directly.
        #
        return self.status == PLAYING

    @property
    def isNotStarted(self):
        """`True` if the video has not be started yet (`bool`). This status is
        given after a video is loaded and play has yet to be called.
        """
        return self.status == NOT_STARTED

    @property
    def isStopped(self):
        """`True` if the movie has been stopped.
        """
        return self.status == STOPPED

    @property
    def isPaused(self):
        """`True` if the movie has been paused.
        """
        self._assertMediaPlayer()

        return self._status == PAUSED

    @property
    def isFinished(self):
        """`True` if the video is finished (`bool`).
        """
        # why is this the same as STOPPED?
        return self._status == FINISHED

    def play(self, log=False):
        """Start or continue a paused movie from current position.

        Parameters
        ----------
        log : bool
            Log the play event.

        Returns
        -------
        int or None
            Frame index playback started at. Should always be `0` if starting at
            the beginning of the video. Returns `None` if the player has not
            been initialized.

        """
        self._assertMediaPlayer()

        self._tStream.play()
        self._status = PLAYING

    def stop(self, log=False):
        """Stop the current point in the movie (sound will stop, current frame
        will not advance). Once stopped the movie cannot be restarted - it must
        be loaded again.

        Use `pause()` instead if you may need to restart the movie.

        Parameters
        ----------
        log : bool
            Log the stop event.

        """
        self._tStream.stop()
        self._status = STOPPED

    def pause(self, log=False):
        """Pause the current point in the movie. The image of the last frame
        will persist on-screen until `play()` or `stop()` are called.

        Parameters
        ----------
        log : bool
            Log this event.

        """
        self._assertMediaPlayer()

        self._tStream.pause()
        self._enqueueFrame()

        self._status = PAUSED

        return False

    def seek(self, timestamp, log=False):
        """Seek to a particular timestamp in the movie.

        Parameters
        ----------
        timestamp : float
            Time in seconds.
        log : bool
            Log the seek event.

        """
        self._assertMediaPlayer()
        self._tStream.seek(timestamp, relative=False)
        self._enqueueFrame()

    def rewind(self, seconds=5, log=False):
        """Rewind the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to rewind from the current position. Default is 5
            seconds.
        log : bool
            Log this event.

        Returns
        -------
        float
            Timestamp after rewinding the video.

        """
        self._assertMediaPlayer()
        self._tStream.seek(-seconds, relative=True)

    def fastForward(self, seconds=5, log=False):
        """Fast-forward the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to fast forward from the current position. Default
            is 5 seconds.
        log : bool
            Log this event.

        """
        self._assertMediaPlayer()
        self._tStream.seek(seconds, relative=True)

    def replay(self, autoStart=False, log=False):
        """Replay the movie from the beginning.

        Parameters
        ----------
        autoStart : bool
            Start playback immediately. If `False`, you must call `play()`
            afterwards to initiate playback.
        log : bool
            Log this event.

        """
        self._assertMediaPlayer()
        self.pause(log=log)
        self.seek(0.0, log=log)

        if autoStart:
            self.play(log=log)

    def restart(self, autoStart=True, log=False):
        """Restart the movie from the beginning.

        Parameters
        ----------
        autoStart : bool
            Start playback immediately. If `False`, you must call `play()`
            afterwards to initiate playback.
        log : bool
            Log this event.

        Notes
        -----
        * This tears down the current media player instance and creates a new
          one. Similar to calling `stop()` and `loadMovie()`. Use `seek(0.0)` if
          you would like to restart the movie without reloading.

        """
        lastMovieFile = self._filename
        self.load(lastMovieFile)  # will play if auto start

    # --------------------------------------------------------------------------
    # Audio stream control methods
    #

    # @property
    # def muted(self):
    #     """`True` if the stream audio is muted (`bool`).
    #     """
    #     return self._handle.get_mute()  # thread-safe?
    #
    # @muted.setter
    # def muted(self, value):
    #     self._tStream.setMute(value)

    def volumeUp(self, amount):
        """Increase the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to increase the volume relative to the current volume.

        """
        self._assertMediaPlayer()

        # get the current volume from the player
        self.volume = self.volume + amount

        return self.volume

    def volumeDown(self, amount):
        """Decrease the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to decrease the volume relative to the current volume.

        """
        self._assertMediaPlayer()

        # get the current volume from the player
        self.volume = self.volume - amount

        return self.volume

    @property
    def volume(self):
        """Volume for the audio track for this movie (`int` or `float`).
        """
        self._assertMediaPlayer()

        return self._tStream.getVolume()

    @volume.setter
    def volume(self, value):
        self._assertMediaPlayer()
        self._tStream.setVolume(max(min(value, 1.0), 0.0))

    @property
    def loopCount(self):
        """Number of loops completed since playback started (`int`). This value
        is reset when either `stop` or `loadMovie` is called.
        """
        return self._loopCount

    # --------------------------------------------------------------------------
    # Timing related methods
    #
    # The methods here are used to handle timing, such as converting between
    # movie and experiment timestamps.
    #

    @property
    def pts(self):
        """Presentation timestamp for the current movie frame in seconds
        (`float`).

        The value for this either comes from the decoder or some other time
        source. This should be synchronized to the start of the audio track. A
        value of `-1.0` is invalid.

        """
        if self._tStream is None:
            return -1.0

        return self._lastFrame.absTime

    def getStartAbsTime(self):
        """Get the absolute experiment time in seconds the movie starts at
        (`float`).

        This value reflects the time which the movie would have started if
        played continuously from the start. Seeking and pausing the movie causes
        this value to change.

        Returns
        -------
        float
            Start time of the movie in absolute experiment time.

        """
        self._assertMediaPlayer()

        return getTime() - self._lastFrame.absTime

    def movieToAbsTime(self, movieTime):
        """Convert a movie timestamp to absolute experiment timestamp.

        Parameters
        ----------
        movieTime : float
            Movie timestamp to convert to absolute experiment time.

        Returns
        -------
        float
            Timestamp in experiment time which is coincident with the provided
            `movieTime` timestamp. The returned value should usually be precise
            down to about five decimal places.

        """
        self._assertMediaPlayer()

        # type checks on parameters
        if not isinstance(movieTime, float):
            raise TypeError(
                "Value for parameter `movieTime` must have type `float` or "
                "`int`.")

        return self.getStartAbsTime() + movieTime

    def absToMovieTime(self, absTime):
        """Convert absolute experiment timestamp to a movie timestamp.

        Parameters
        ----------
        absTime : float
            Absolute experiment time to convert to movie time.

        Returns
        -------
        float
            Movie time referenced to absolute experiment time. If the value is
            negative then provided `absTime` happens before the beginning of the
            movie from the current time stamp. The returned value should usually
            be precise down to about five decimal places.

        """
        self._assertMediaPlayer()

        # type checks on parameters
        if not isinstance(absTime, float):
            raise TypeError(
                "Value for parameter `absTime` must have type `float` or "
                "`int`.")

        return absTime - self.getStartAbsTime()

    def movieTimeFromFrameIndex(self, frameIdx):
        """Get the movie time a specific a frame with a given index is
        scheduled to be presented.

        This is used to handle logic for seeking through a video feed (if
        permitted by the player).

        Parameters
        ----------
        frameIdx : int
            Frame index. Negative values are accepted but they will return
            negative timestamps.

        """
        self._assertMediaPlayer()

        return frameIdx * self._metadata.frameInterval

    def frameIndexFromMovieTime(self, movieTime):
        """Get the frame index of a given movie time.

        Parameters
        ----------
        movieTime : float
            Timestamp in movie time to convert to a frame index.

        Returns
        -------
        int
            Frame index that should be presented at the specified movie time.

        """
        self._assertMediaPlayer()

        return math.floor(movieTime / self._metadata.frameInterval)

    @property
    def isSeekable(self):
        """Is seeking allowed for the video stream (`bool`)? If `False` then
        `frameIndex` will increase monotonically.
        """
        return False  # fixed for now

    @property
    def frameInterval(self):
        """Duration a single frame is to be presented in seconds (`float`). This
        is derived from the framerate information in the metadata. If not movie
        is loaded, the returned value will be invalid.
        """
        return self.metadata.frameInterval

    @property
    def frameIndex(self):
        """Current frame index (`int`).

        Index of the current frame in the stream. If playing from a file or any
        other seekable source, this value may not increase monotonically with
        time. A value of `-1` is invalid, meaning either the video is not
        started or there is some issue with the stream.

        """
        return self._lastFrame.frameIndex

    def getPercentageComplete(self):
        """Provides a value between 0.0 and 100.0, indicating the amount of the
        movie that has been already played (`float`).
        """
        duration = self.metadata.duration

        return (self.pts / duration) * 100.0

    # --------------------------------------------------------------------------
    # Methods for getting video frames from the encoder
    #
    
    def _enqueueFrame(self):
        """Grab the latest frame from the stream.

        Returns
        -------
        bool
            `True` if a frame has been enqueued. Returns `False` if the camera
            is not ready or if the stream was closed.

        """
        self._assertMediaPlayer()

        # If the queue is empty, the decoder thread has not yielded a new frame
        # since the last call.
        enqueuedFrame = self._tStream.getRecentFrame()
        if enqueuedFrame is None:
            return False

        # Unpack the data we got back ...
        # Note - Bit messy here, we should just hold onto the `enqueuedFrame`
        # instance and reference its fields from properties. Keeping like this
        # for now.
        frameImage = enqueuedFrame.frameImage
        streamStatus = enqueuedFrame.streamStatus
        self._metadata = enqueuedFrame.metadata
        self._frameIndex = streamStatus.frameIndex
        self._loopCount = streamStatus.loopCount

        # status information
        self._streamTime = streamStatus.streamTime  # stream time for the camera

        # if we have a new frame, update the frame information
        videoBuffer = frameImage.to_memoryview()[0].memview
        videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)

        # provide the last frame
        self._lastFrame = MovieFrame(
            frameIndex=self._frameIndex,
            absTime=self._streamTime,
            displayTime=self.metadata.frameInterval,
            size=frameImage.get_size(),
            colorData=videoFrameArray,
            audioChannels=0,  # not populated yet ...
            audioSamples=None,
            metadata=self.metadata,
            movieLib=u'ffpyplayer',
            userData=None,
            keepAlive=frameImage)

        return True

    def update(self):
        """Update this player.

        This get the latest data from the video stream and updates the player
        accordingly. This should be called at a higher frequency than the frame
        rate of the movie to avoid frame skips.

        """
        self._assertMediaPlayer()

        # check if the stream reader thread is present and alive, if not the
        # movie is finished
        self._enqueueFrame()

        if self._tStream.isFinished:  # are we done?
            self._status = FINISHED

    def getMovieFrame(self):
        """Get the movie frame scheduled to be displayed at the current time.

        Returns
        -------
        `~psychopy.visual.movies.frame.MovieFrame`
            Current movie frame.

        """
        self.update()

        return self._lastFrame

    def __del__(self):
        """Cleanup when unloading.
        """
        global _evtCleanUpMovieEvent
        if hasattr(self, '_tStream'):
            if self._tStream is not None:
                if not _evtCleanUpMovieEvent.is_set():
                    self._tStream.shutdown()
                    self._tStream.join()


if __name__ == "__main__":
    pass
