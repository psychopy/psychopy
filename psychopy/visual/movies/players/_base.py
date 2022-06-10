#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Base class for player interfaces.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ["BaseMoviePlayer"]

from abc import ABC, abstractmethod


class BaseMoviePlayer(ABC):
    """Base class for all movie players.

    This class specifies a standardized interface for movie player APIs. All
    movie player interface classes must be subclasses of `BaseMoviePlayer` and
    implement (override) the abstract attributes associated with it.
    Furthermore, methods of the subclass must be conformant to the behaviors
    outlined in documentation strings of each.

    """
    _movieLib = u''

    # --------------------------------------------------------------------------
    # Movie loading and information
    #

    @abstractmethod
    def load(self, pathToMovie):
        """Load the movie stream.

        This must be called prior to using any playback control method. The
        property `isLoaded` should return `True` afterwards.

        Parameters
        ----------
        pathToMovie : str
            Path to movie file. Must be a format that FFMPEG supports.

        """
        pass

    @abstractmethod
    def unload(self):
        """Unload the movie stream.

        Similar to `stop()` but can contain additional cleanup routines. The
        value of `isLoaded` should be set to `False` after calling this.

        """
        pass

    @property
    @abstractmethod
    def isLoaded(self):
        """`True` if a movie is loaded and playback controls are available."""
        pass

    @abstractmethod
    def getMetadata(self):
        """Get metadata from the movie stream.

        This is only valid after `load()` has been called. Do not make any calls
        to `_setupBuffers()` until after the video stream has been loaded since
        the metadata is invalid until so for most streaming movie player APIs.

        Returns
        -------
        MovieMetadata
            Movie metadata object. If no movie is loaded, return a
            `NULL_MOVIE_METADATA` object instead of `None`. At a minimum,
            ensure that fields `duration`, `size`, and `frameRate` are
            populated if a valid movie is loaded.

        """
        pass

    @abstractmethod
    def _assertMediaPlayer(self):
        """Assert that a video is loaded and playback controls are available.

        This method must raise an error if the media player is not yet ready.
        Usually a `RuntimeError` will suffice. Any method which relies on the
        media player being open should make a call to this method prior to doing
        anything::

            def play(self):
                self._assertMediaPlayer()  # requires a stream to be opened
                # playback logic here ...

        """
        pass

    # --------------------------------------------------------------------------
    # Playback controls
    #

    @property
    @abstractmethod
    def status(self):
        """Playback status (`int`).

        Possible values are symbolic constants  `PLAYING`, `FINISHED`,
        `NOT_STARTED`, `PAUSED`, `PLAYING` or `STOPPED`.
        """
        pass

    @property
    @abstractmethod
    def isPlaying(self):
        """`True` if the video is presently playing (`bool`)."""
        pass

    @property
    @abstractmethod
    def isNotStarted(self):
        """`True` if the video has not be started yet (`bool`). This status is
        given after a video is loaded and play has yet to be called."""
        pass

    @property
    @abstractmethod
    def isStopped(self):
        """`True` if the video is stopped (`bool`)."""
        pass

    @property
    @abstractmethod
    def isPaused(self):
        """`True` if the video is presently paused (`bool`)."""
        pass

    @property
    @abstractmethod
    def isFinished(self):
        """`True` if the video is finished (`bool`)."""
        pass

    @property
    @abstractmethod
    def frameIndex(self):
        """Index of the current movie frame (`int`)."""
        pass

    @abstractmethod
    def start(self, log=True):
        """Start decoding.

        Calling this method should begin decoding frames for the stream, making
        them available when requested. This is similar to `play()` but doesn't
        necessarily mean that the video is to be displayed, just that the
        decoder should start queuing frames up.

        """
        pass

    @abstractmethod
    def play(self, log=True):
        """Begin playback.

        If playback is already started, this method should do nothing. If
        `pause()` was called previously, calling this method should resume
        playback. This should cause the decoder to start processing frames and
        making them available when `getMovieFrame` is called.

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
        pass

    @abstractmethod
    def stop(self, log=True):
        """Stop playback.

        This should also unload the video (i.e. close the player stream). The
        return value of `getMetadata()` should be `NULL_MOVIE_METADATA`.
        Successive calls to this method should do nothing. The value returned
        by `isLoaded` should be `False`.

        """
        pass

    @abstractmethod
    def pause(self, log=True):
        """Pause the video.

        Calling this should result in the video freezing on the current frame.
        The stream should not be closed during pause. Calling `play()` is the
        only way to unpause/resume the video.

        Parameters
        ----------
        log : bool
            Log the pause event.

        """
        pass

    @abstractmethod
    def replay(self, autoStart=True, log=True):
        """Replay the video.

        This is a convenience method to restart the stream. This is equivalent
        to calling `stop()`, reloading the current video, and calling `play()`.

        Parameters
        ----------
        autoStart : bool
            Start playback immediately. If `False`, you must call `play()`
            afterwards to initiate playback.
        log : bool
            Log this event.

        """
        pass

    @abstractmethod
    def seek(self, timestamp, log=True):
        """Skip to some position in the video.

        If playing, the video should advance to the new frame and continue
        playing. If paused, the video should advance to the required frame and
        the frame should appear static.

        Parameters
        ----------
        timestamp : float
            Time in seconds.
        log : bool
            Log this event.

        """
        pass

    @abstractmethod
    def rewind(self, seconds=5, log=True):
        """Rewind the movie.

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
        pass

    @abstractmethod
    def fastForward(self, seconds=5, log=True):
        """Fast forward.

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
        pass

    @abstractmethod
    def volumeUp(self, amount):
        """Increase the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to increase the volume relative to the current volume.

        """
        pass

    @abstractmethod
    def volumeDown(self, amount):
        """Decrease the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to decrease the volume relative to the current volume.

        """
        pass

    @property
    @abstractmethod
    def volume(self):
        """Volume for the audio track for this movie (`int` or `float`).
        """
        pass

    @property
    @abstractmethod
    def isSeekable(self):
        """Is seeking allowed for the video stream (`bool`)? If `False` then
        `frameIndex` will increase monotonically.
        """
        pass

    # --------------------------------------------------------------------------
    # Video display and timing
    #

    @property
    @abstractmethod
    def pts(self):
        """Current movie time in seconds (`float`). The value for this either
        comes from the decoder or some other time source. This should be
        synchronized to the audio track.

        """
        pass

    @property
    @abstractmethod
    def frameInterval(self):
        """Duration a single frame is to be presented in seconds (`float`). This
        is derived from the framerate information in the metadata.
        """
        pass

    @abstractmethod
    def getMovieFrame(self):
        """Get the most recent movie frame from the player.

        Returns
        -------
        `~psychopy.visual.movies.frame.MovieFrame`
            Current movie frame.

        """
        pass


if __name__ == "__main__":
    pass
