#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for movie player interfaces.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import time
from pathlib import Path

from psychopy import prefs
from psychopy.core import getTime
from ._base import BaseMoviePlayer
from ffpyplayer.player import MediaPlayer
from ..metadata import MovieMetadata, NULL_MOVIE_METADATA
from ..frame import MovieFrame, NULL_MOVIE_FRAME_INFO
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED
from psychopy.tools.filetools import pathToString
import math
import numpy as np

# constants for use with ffpyplayer
FFPYPLAYER_STATUS_EOF = 'eof'
FFPYPLAYER_STATUS_PAUSED = 'paused'

# Options that PsychoPy devs picked to provide better performance, these can
# be overridden, but it might result in undefined behavior.
DEFAULT_FF_OPTS = {'sync': 'video'}


class FFPyPlayer(BaseMoviePlayer):
    """Interface class for the FFPyPlayer library for use with `MovieStim`.

    This class also serves as the reference implementation for classes which
    interface with movie codec libraries for use with `MovieStim`. Creating new
    player classes which closely replicate the behaviour of this one should
    allow them to smoothly plug into `MovieStim`.

    """
    _movieLib = 'ffpyplayer'

    def __init__(self):
        self._filename = u""

        # handle to `ffpyplayer`
        self._handle = None
        self._queuedFrame = NULL_MOVIE_FRAME_INFO
        self._frameIndex = -1

        # flag when random access has been invoked
        self._needsNewFrame = False

        # status flags
        self._status = NOT_STARTED

    def start(self, log=True):
        """Initialize and start the decoder. This method will return when a
        valid frame is made available.

        """
        # clear queued data from previous streams
        self._queuedFrame = NULL_MOVIE_FRAME_INFO
        self._frameIndex = -1

        # open the media player
        self._handle = MediaPlayer(self._filename, ff_opts=DEFAULT_FF_OPTS)

        # Pull the first frame to get metadata. NB - `_enqueueFrame` should be
        # able to do this but the logic in there depends on having access to
        # metadata first. That may be rewritten at some point to reduce all of
        # this to just a single `_enqeueFrame` call.
        #
        self._handle.set_mute(True)
        self._handle.set_pause(False)

        frame = None
        while frame is None:
            frame, _ = self._handle.get_frame(show=True)

        self._handle.set_pause(True)
        self._handle.seek(0.0, relative=False)  # advance to the desired frame
        self._handle.set_mute(False)

        # get the first frame
        self._enqueueFrame(0.0, blockUntilValidFrame=True)

        self._status = NOT_STARTED

    def load(self, pathToMovie):
        """Load a movie file from disk.

        Parameters
        ----------
        pathToMovie : str
            Path to movie file, stream (URI) or camera. Must be a format that
            FFMPEG supports.

        """
        # If given `untitled.mp4`, sub in full path
        if self._filename == "untitled.mp4":
            self._filename = str(Path(prefs.paths['resources']) / "untitled.mp4")
        # set the file path
        self._filename = pathToString(pathToMovie)

        # Check if the player is already started. Close it and load a new
        # instance if so.
        if self._handle is not None:  # player already started
            # make sure it's the correct type
            if not isinstance(self._handle, MediaPlayer):
                raise TypeError(
                    'Incorrect type for `FFMovieStim._player`, expected '
                    '`ffpyplayer.player.MediaPlayer`. Got type `{}` '
                    'instead.'.format(type(self._handle).__name__))

            # close the player and reset
            self.unload()

            # self._selectWindow(self.win)  # free buffers here !!!

        self.start()

        self._status = NOT_STARTED

    def unload(self):
        """Unload the video stream and reset.
        """
        self._handle.close_player()
        self._filename = u""
        self._frameIndex = -1
        self._handle = None  # reset

    @property
    def handle(self):
        """Handle to the `MediaPlayer` object exposed by FFPyPlayer. If `None`,
        no media player object has yet been initialized.
        """
        return self._handle

    @property
    def isLoaded(self):
        return self._handle is not None

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

        metadata = self._handle.get_metadata()

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
        if isinstance(self._handle, MediaPlayer):
            return  # nop if we're good

        raise RuntimeError(
            "Calling this class method requires a successful call to "
            "`load` first.")

    @property
    def status(self):
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

        return self._handle.get_pause()

    @property
    def isFinished(self):
        """`True` if the video is finished (`bool`).
        """
        # why is this the same as STOPPED?
        return self.status == FINISHED

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

        # if not started
        if self.status == NOT_STARTED:
            self._handle.seek(0.0, relative=False)

        if self._handle.get_pause():  # if paused, unpause to start playback
            self._handle.set_pause(False)

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
        self._assertMediaPlayer()

        self._status = STOPPED
        self.unload()

    def pause(self, log=False):
        """Pause the current point in the movie. The image of the last frame
        will persist on-screen until `play()` or `stop()` are called.

        Parameters
        ----------
        log : bool
            Log this event.

        """
        self._assertMediaPlayer()

        if not self.isPaused:
            self._handle.set_pause(True)

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
        self._handle.seek(timestamp, relative=False)
        self._queuedFrame = NULL_MOVIE_FRAME_INFO

        return self._handle.get_pts()

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

        timestamp = self.pts - seconds
        self.seek(timestamp)

        # after seeking
        return self._handle.get_pts()

    def fastForward(self, seconds=5, log=False):
        """Fast-forward the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to fast forward from the current position. Default
            is 5 seconds.
        log : bool
            Log this event.

        Returns
        -------
        float
            Timestamp at new position after fast forwarding the video.

        """
        self._assertMediaPlayer()

        timestamp = self.pts + seconds
        self.seek(timestamp)

        return self._handle.get_pts()

    def replay(self, autoStart=True, log=False):
        """Replay the movie from the beginning.

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
        self.stop()  # stop the movie
        # self._autoStart = autoStart
        self.load(lastMovieFile)  # will play if auto start

        self.start()

    # --------------------------------------------------------------------------
    # Audio stream control methods
    #

    @property
    def muted(self):
        """`True` if the stream audio is muted (`bool`).
        """
        return self._handle.get_mute()

    @muted.setter
    def muted(self, value):
        self._handle.set_mute(value)

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

        return self._handle.get_volume()

    @volume.setter
    def volume(self, value):
        self._assertMediaPlayer()

        self._handle.set_volume(max(min(value, 1.0), 0.0))

    # --------------------------------------------------------------------------
    # Timing related methods
    #
    # The methods here are used to handle timing, such as converting between
    # movie and experiment timestamps.
    #

    @property
    def pts(self):
        """Current movie time in seconds (`float`). The value for this either
        comes from the decoder or some other time source. This should be
        synchronized to the start of the audio track. A value of `-1.0` is
        invalid.

        """
        if self._handle is None:
            return -1.0

        return self._handle.get_pts()

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

        return getTime() - self._handle.get_pts()

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

        Examples
        --------
        Get the movie timestamp which is coincident with the next screen refresh
        (flip)::

            showNextFrameTime = self.absToMovieTime(win.getFutureFlipTime())
            self.getMovieFrame(showNextFrameTime)

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

        metadata = self.getMetadata()

        return frameIdx * metadata.frameInterval

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

        metadata = self.getMetadata()

        return math.floor(movieTime / metadata.frameInterval)

    @property
    def isSeekable(self):
        """Is seeking allowed for the video stream (`bool`)? If `False` then
        `frameIndex` will increase monotonically.
        """
        return True

    @property
    def frameInterval(self):
        """Duration a single frame is to be presented in seconds (`float`). This
        is derived from the framerate information in the metadata. If not movie
        is loaded, the returned value will be invalid.
        """
        metadata = self.getMetadata()

        return metadata.frameInterval

    @property
    def frameIndex(self):
        """Current frame index (`int`).

        Index of the current frame in the stream. If playing from a file or any
        other seekable source, this value may not increase monotonically with
        time. A value of `-1` is invalid, meaning either the video is not
        started or there is some issue with the stream.

        """
        return self._queuedFrame.frameIndex

    def getNextFrameAbsTime(self):
        """Get the absolute experiment time the next frame should be displayed
        at (`float`).
        """
        # move to main class, needs `win` attribute to work
        if self._handle is None:
            return -1.0

    def getPercentageComplete(self):
        """Provides a value between 0.0 and 100.0, indicating the amount of the
        movie that has been already played (`float`).
        """
        duration = self.getMetadata().duration

        return (self._handle.get_pts() / duration) * 100.0

    # --------------------------------------------------------------------------
    # Methods for getting video frames from the encoder
    #

    def _enqueueFrame(self, movieTime, blockUntilValidFrame=False):
        """Enqueue a frame from the decoder.

        This pulls the frame scheduled to be presented at the specified
        `movieTime` timestamp and queues it to be displayed or processed.

        Parameters
        ----------
        movieTime : float
            Timestamp of the frame to enqueue. If the timestamp is greater than
            the one of the next scheduled flip time, the movie will seek to the
            required timestamp automatically.
        blockUntilValidFrame : bool
            Block until the codec yields a valid frame. This function will block
            until a new frame comes in.

        """
        self._assertMediaPlayer()

        # check if we are in the range to pull a new frame
        frameIntervalStart = self._queuedFrame.absTime
        metadata = self.getMetadata()

        # do we show the frame we already decoded or do we need a new one?
        if frameIntervalStart >= movieTime:
            return self._queuedFrame

        # are we paused?
        # wasPaused = self._handle.get_pause()

        # Block until a valid frame is returned from the stream, needed or else
        # we won't have the metadata needed to crete the pixel/texture buffers.
        #
        # NB - We should add a timeout here to prevent the application from
        # locking up if we can't get a valid frame within a reasonable time.
        #
        frame = None
        status = ''
        if blockUntilValidFrame:
            while frame is None:
                frame, status = self._handle.get_frame(show=True)
                # break on other conditions
                if status != 'not ready':
                    break

                time.sleep(0.1)  # wait a bit for a new frame
        else:
            frame, status = self._handle.get_frame(show=True)

        # NB - We could potentially buffer a bunch of frames in another
        # thread and pull them in here. Right now we're pulling one frame at
        # a time.

        # set status flags accordingly
        if status == FFPYPLAYER_STATUS_EOF:
            self._status = FINISHED
        elif status == FFPYPLAYER_STATUS_PAUSED:
            self._status = PAUSED
        else:
            self._status = PLAYING  # could be not ready too, but still playing

        if frame is None:
            return self._queuedFrame

        # process the new frame
        colorData, pts = frame

        # if we have a new frame, update the frame information
        videoBuffer = colorData.to_bytearray()[0]
        videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)

        # create data structure to hold frame information
        self._queuedFrame = MovieFrame(
            frameIndex=self.frameIndexFromMovieTime(pts),
            absTime=pts,
            displayTime=metadata.frameInterval,
            size=metadata.size,
            colorData=videoFrameArray,
            audioChannels=0,
            audioSamples=None,
            movieLib=self._movieLib,
            userData=None)

        return self._queuedFrame

    def getMovieFrame(self, absTime):
        """Get the movie frame scheduled to be displayed at the current time.

        Parameters
        ----------
        absTime : float
            Current experiment time.

        Returns
        -------
        `~psychopy.visual.movies.frame.MovieFrame`
            Current movie frame.

        """
        self._assertMediaPlayer()

        return self._enqueueFrame(self.absToMovieTime(absTime))


if __name__ == "__main__":
    pass
