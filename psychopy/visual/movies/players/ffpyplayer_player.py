#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for movie player interfaces.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from ._base import BaseMoviePlayer
from ffpyplayer.player import MediaPlayer
from ..metadata import MovieMetadata, NULL_MOVIE_METADATA
from ..frame import MovieFrame, NULL_MOVIE_FRAME_INFO
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED
from psychopy.tools.filetools import pathToString
import numpy as np

# constants for use with ffpyplayer
FFPYPLAYER_STATUS_EOF = 'eof'
FFPYPLAYER_STATUS_PAUSED = 'paused'


class FFPyPlayer(BaseMoviePlayer):
    """Interface class for the FFPyPlayer library for use with `MovieStim`.

    Parameters
    ----------
    win : `psychopy.visual.Window` or `None`
        Window the video is being rendered to, required for OpenGL.

    """
    _movieLib = 'ffpyplayer'

    def __init__(self):
        self._filename = u""

        # handle to `ffpyplayer`
        self._player = None
        self._lastFrameInfo = NULL_MOVIE_FRAME_INFO

        # status flags
        self._status = NOT_STARTED

    def start(self, log=True):
        """Initialize and start the decoder. This method will return when a
        valid frame is made available.

        """
        # open the media player
        self._player = MediaPlayer(self._filename)
        self._player.set_mute(True)

        # Block until a valid frame is returned from the stream, needed or else
        # we won't have the metadata needed to crete the pixel/texture buffers.
        #
        # NB - We should add a timeout here to prevent the application from
        # locking up if we can't get a valid frame within a reasonable time.
        #
        frame = None
        while frame is None:
            frame, _ = self._player.get_frame()

        # pause it once open since `ffpyplayer` plays the video automatically
        self._player.set_pause(True)
        self._player.seek(0.0)  # return to beginning
        self._player.set_mute(False)  # unmute for the user

    def load(self, pathToMovie):
        """Load a movie file from disk.

        Parameters
        ----------
        pathToMovie : str
            Path to movie file, stream (URI) or webcam. Must be a format that
            FFMPEG supports.

        """
        # set the file path
        self._filename = pathToString(pathToMovie)

        # Check if the player is already started. Close it and load a new
        # instance if so.
        if self._player is not None:  # player already started
            # make sure it's the correct type
            if not isinstance(self._player, MediaPlayer):
                raise TypeError(
                    'Incorrect type for `FFMovieStim._player`, expected '
                    '`ffpyplayer.player.MediaPlayer`. Got type `{}` '
                    'instead.'.format(type(self._player).__name__))

            # close the player and reset
            self.unload()

            # self._selectWindow(self.win)  # free buffers here !!!

        self.start()

        self._status = NOT_STARTED

    def unload(self):
        """Unload the video stream and reset.
        """
        self._player.close_player()
        self._filename = u""
        self._player = None  # reset

    @property
    def isLoaded(self):
        return self._player is not None

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

        metadata = self._player.get_metadata()

        # write metadata to the fields of a `MovieMetadata` object
        toReturn = MovieMetadata(
            mediaPath=self._filename,
            title=metadata['title'],
            duration=metadata['duration'],
            # frameRate=metadata['frame_rate'],
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
        if isinstance(self._player, MediaPlayer):
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

        return self._player.get_pause()

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

        # if not started, reset the clock
        # if self.status == NOT_STARTED:
        #     self._player.play()

        if self._player.get_pause():  # if paused, unpause to start playback
            self._player.set_pause(False)

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

        self._player.close_player()
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

        if not self.isPaused:
            self._player.set_pause(True)

        self._status = PAUSED

        return False

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
        self.stop()  # stop the movie
        lastMovieFile = self._filename

        self._autoStart = autoStart
        self.load(lastMovieFile)  # will play if auto start

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
        self._player.seek(timestamp)

        return self._player.get_pts()

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

        self._player.seek(-seconds, relative=True)
        self._videoClock.reset(self._player.get_pts())
        _ = self.updateVideoFrame(forceUpdate=True)

        # after seeking
        return self._player.get_pts()

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

        self._player.seek(seconds, relative=True)
        self._videoClock.reset(self._player.get_pts())
        _ = self.updateVideoFrame(forceUpdate=True)

        return self._player.get_pts()

    def volumeUp(self, amount):
        """Increase the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to increase the volume relative to the current volume.

        """
        pass

    def volumeDown(self, amount):
        """Decrease the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to decrease the volume relative to the current volume.

        """
        pass

    def volume(self):
        """Volume for the audio track for this movie (`int` or `float`).
        """
        pass

    @property
    def pts(self):
        """Current movie time in seconds (`float`). The value for this either
        comes from the decoder or some other time source. This should be
        synchronized to the start of the audio track. A value of `-1.0` is
        invalid.

        """
        if self._player is None:
            return -1.0

        return self._player.get_pts()

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
        frameRate = self.getMetadata().frameRate

        # could be in numerator+denominator format, else always a float
        if isinstance(frameRate, tuple):
            numer, denom = frameRate
            frameRate = numer / float(denom)

        return 1.0 / frameRate

    @property
    def frameIndex(self):
        """Current frame index (`int`).

        Index of the current frame in the stream. If playing from a file or any
        other seekable source, this value may not increase monotonically with
        time. A value of `-1` is invalid, meaning either the video is not
        started or there is some issue with the stream.

        """
        if self._player is None:
            return -1

    def getMovieFrame(self, absTime):
        """Get the movie frame scheduled to be displayed at the current movie
        time.

        Parameters
        ----------
        absTime : float
            Absolute movie time in seconds the frame is scheduled to appear. A
            new frame is returned only when movie time is beyond `absTime`,
            otherwise the previous frame is returned.

        Returns
        -------
        `~psychopy.visual.movies.frame.MovieFrame`
            Current movie frame.

        """
        self._assertMediaPlayer()

        # check if the frame needs to be presented
        if self._lastFrameInfo.absTime > absTime:
            return self._lastFrameInfo

        # get the frame and playback status
        frame, playbackStatus = self._player.get_frame(show=True)

        # NB - We could potentially buffer a bunch of frames in another thread
        # and pull them in here. Right now we're pulling one frame at a time.

        # set status flags accordingly
        if playbackStatus == FFPYPLAYER_STATUS_EOF:
            self._status = FINISHED
            return self._lastFrameInfo
        elif playbackStatus == FFPYPLAYER_STATUS_PAUSED:
            self._status = PAUSED
            return self._lastFrameInfo
        elif frame is None:
            return self._lastFrameInfo  # NOT_STARTED?
        else:
            self._status = PLAYING

        # process the new frame
        colorData, pts = frame

        # if we have a new frame, update the frame information
        videoBuffer = colorData.to_bytearray()[0]
        videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)

        # create data structure to hold frame information
        toReturn = MovieFrame(
            frameIndex=-1,
            absTime=pts,
            displayTime=self.frameInterval,
            size=self.getMetadata().size,
            colorData=videoFrameArray,
            audioChannels=0,
            audioSamples=None,
            movieLib=self._movieLib,
            userData=None)

        self._lastFrameInfo = toReturn

        return self._lastFrameInfo


if __name__ == "__main__":
    pass
