#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy using a
local installation of VLC media player (https://www.videolan.org/).

This class is kept for backwards compatibility. New code should use
:class:`~psychopy.visual.MovieStim` with `movieLib='vlc'` instead.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
#
# VlcMovieStim originally contributed by Dan Fitch, April 2019. The `MovieStim2`
# class was taken and rewritten to use only VLC.
#

import sys

from psychopy.tools.attributetools import logAttrib
from psychopy.visual.movies import MovieStim

try:
    # check if the lib can be loaded
    import vlc
    haveVLC = True
except Exception as err:
    haveVLC = False
    # store the error but only raise it if the class is used
    if "wrong architecture" in str(err):
        msg = ("Failed to import `vlc` module required by `vlcmoviestim`.\n"
               "You're using %i-bit python. Is your VLC install the same?"
               % (64 if sys.maxsize > 2 ** 32 else 32))
        _vlcImportErr = OSError(msg)
    else:
        _vlcImportErr = err

# flip time, and time since last movie frame flip will be printed
reportNDroppedFrames = 10


def _toUnitVolume(volume):
    """Convert a volume level in the legacy `VlcMovieStim` format to the
    `0.0` to `1.0` range used by `MovieStim`.

    A `float` between 0 and 1 is taken as is, anything else is taken as a
    percentage where 100 is the nominal level.

    """
    if isinstance(volume, float) and 0.0 <= volume <= 1.0:
        v = volume
    else:
        v = volume / 100.0

    return min(max(float(v), 0.0), 1.0)


class VlcMovieStim(MovieStim):
    """A stimulus class for playing movies in various formats (mpeg, avi,
    etc...) in PsychoPy using the VLC media player as a decoder. This is
    a lazy-imported class, therefore import using full path
    `from psychopy.visual.vlcmoviestim import VlcMovieStim` when inheriting
    from it.

    This class is a thin wrapper around :class:`~psychopy.visual.MovieStim`
    using `movieLib='vlc'`, kept so that existing code using `VlcMovieStim`
    continues to work. New code should use `MovieStim` directly.

    Audio is played by VLC on the default output device. This may be adequate
    for most applications where the user is not concerned about precision
    audio onset times.

    The VLC media player (https://www.videolan.org/) must be installed on the
    machine running PsychoPy to use this class. Make certain that the version
    of VLC installed matches the architecture of the Python interpreter hosting
    PsychoPy.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window the video is being drawn to.
    filename : str
        Name of the file or stream URL to play. If an empty string, no file will
        be loaded on initialization but can be set later.
    units : str
        Units to use when sizing the video frame on the window, affects how
        `size` is interpreted.
    size : ArrayLike or None
        Size of the video frame on the window in `units`. If `None`, the native
        size of the video will be used.
    flipVert : bool
        If `True` then the movie will be top-bottom flipped.
    flipHoriz : bool
        If `True` then the movie will be right-left flipped.
    volume : int or float
        If specifying an `int` the nominal level is 100, and 0 is silence. If a
        `float`, values between 0 and 1 may be used.
    loop : bool
        Whether to start the movie over from the beginning if draw is called and
        the movie is done. Default is `False.
    autoStart : bool
        Automatically begin playback of the video when `flip()` is called.
    **kwargs
        Other arguments accepted by :class:`~psychopy.visual.MovieStim`.

    Notes
    -----
    * You may see error messages in your log output from VLC (e.g.,
      `get_buffer() failed`, `no frame!`, etc.) after shutting down. These
      errors originate from the decoder and can be safely ignored.

    """
    def __init__(self, win,
                 filename="",
                 units='pix',
                 size=None,
                 pos=(0.0, 0.0),
                 ori=0.0,
                 flipVert=False,
                 flipHoriz=False,
                 color=(1.0, 1.0, 1.0),  # remove?
                 colorSpace='rgb',
                 opacity=1.0,
                 volume=1.0,
                 name='',
                 loop=False,
                 autoLog=True,
                 depth=0.0,
                 noAudio=False,
                 interpolate=True,
                 autoStart=True,
                 **kwargs):
        # check if we have the VLC lib
        if not haveVLC:
            raise _vlcImportErr

        # the decoder is always VLC for this class
        kwargs.pop('movieLib', None)
        kwargs.pop('audioLib', None)

        super(VlcMovieStim, self).__init__(
            win,
            filename=filename,
            movieLib='vlc',
            audioLib='vlc',
            units=units,
            size=size,
            pos=pos,
            ori=ori,
            flipVert=flipVert,
            flipHoriz=flipHoriz,
            color=color,
            colorSpace=colorSpace,
            opacity=opacity,
            volume=_toUnitVolume(volume),
            name=name,
            loop=loop,
            autoLog=autoLog,
            depth=depth,
            noAudio=noAudio,
            interpolate=interpolate,
            autoStart=autoStart,
            **kwargs)

        self.nDroppedFrames = 0

    # --------------------------------------------------------------------------
    # Movie file handlers
    #
    def setMovie(self, filename, log=True):
        """See `~VlcMovieStim.loadMovie` (the functions are identical).

        This form is provided for syntactic consistency with other visual
        stimuli.
        """
        if self._isLoaded:
            self.unload()
        self.loadMovie(filename, log=log)

    def loadMovie(self, filename, log=True):
        """Load a movie from file

        Parameters
        ----------
        filename : str
            The name of the file or URL, including path if necessary.
        log : bool
            Log this event.

        """
        super(VlcMovieStim, self).loadMovie(filename)
        logAttrib(self, log, 'movie', filename)

    def updateTexture(self):
        """Update the video texture buffer to the most recent video frame.
        """
        if self.updateVideoFrame():
            self._pixelTransfer()

    # --------------------------------------------------------------------------
    # Video playback controls
    #
    def pause(self, log=True):
        """Pause the current point in the movie.

        Parameters
        ----------
        log : bool
            Log the pause event.

        Returns
        -------
        bool
            `True` if the movie was playing and is now paused.

        """
        if not self.isPlaying:
            return False

        super(VlcMovieStim, self).pause(log=log)

        return True

    def rewind(self, seconds=5, blocking=True, log=True):
        """Rewind the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to rewind from the current position. Default is 5
            seconds.
        blocking : bool
            Whether to wait for the frame at the new position before returning.
            See `seek()`.
        log : bool
            Log this event.

        Returns
        -------
        float
            Timestamp after rewinding the video.

        """
        super(VlcMovieStim, self).rewind(seconds, blocking=blocking, log=log)

        return self.getCurrentFrameTime()

    def fastForward(self, seconds=5, blocking=True, log=True):
        """Fast-forward the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to fast forward from the current position. Default
            is 5 seconds.
        blocking : bool
            Whether to wait for the frame at the new position before returning.
            See `seek()`.
        log : bool
            Log this event.

        Returns
        -------
        float
            Timestamp at new position after fast forwarding the video.

        """
        super(VlcMovieStim, self).fastForward(
            seconds, blocking=blocking, log=log)

        return self.getCurrentFrameTime()

    def replay(self, autoPlay=True, blocking=True, log=True):
        """Replay the movie from the beginning.

        Parameters
        ----------
        autoPlay : bool
            Start playback immediately. If `False`, you must call `play()`
            afterwards to initiate playback.
        blocking : bool
            Whether to wait for the first frame before returning. See `seek()`.
        log : bool
            Log this event.

        """
        if autoPlay:
            super(VlcMovieStim, self).replay(blocking=blocking, log=log)
        else:
            self.reset(blocking=blocking)

    # --------------------------------------------------------------------------
    # Volume controls
    #
    # These use the legacy `VlcMovieStim` volume scale where 100 is the nominal
    # level, rather than the `0.0` to `1.0` range used by `MovieStim`.
    #
    @property
    def volume(self):
        """Audio track volume (`int` or `float`). See `setVolume` for more
        information about valid values.

        """
        return self.getVolume()

    @volume.setter
    def volume(self, value):
        self.setVolume(value)

    def setVolume(self, volume):
        """Set the audio track volume.

        Parameters
        ----------
        volume : int or float
            Volume level to set. 0 = mute, 100 = 0 dB. float values between 0.0
            and 1.0 are also accepted, and scaled to an int between 0 and 100.

        """
        self._volume = _toUnitVolume(volume)

        if self._hasPlayer:
            MovieStim.volume.fset(self, self._volume)

    def getVolume(self):
        """Returns the current movie audio volume.

        Returns
        -------
        int
            Volume level, 0 is no audio, 100 is max audio volume.

        """
        # VLC can't report the volume until playback starts, so return the
        # level last requested instead of asking the player
        return int(round(self._volume * 100))

    def volumeUp(self, amount=0.05):
        """Increase the volume by a fixed amount.

        Parameters
        ----------
        amount : float
            Amount to increase the volume relative to the current volume, where
            `1.0` is the nominal level.

        """
        self.setVolume(min(max(self._volume + amount, 0.0), 1.0))

    def volumeDown(self, amount=0.05):
        """Decrease the volume by a fixed amount.

        Parameters
        ----------
        amount : float
            Amount to decrease the volume relative to the current volume, where
            `1.0` is the nominal level.

        """
        self.setVolume(min(max(self._volume - amount, 0.0), 1.0))

    def increaseVolume(self, amount=10):
        """Increase the volume.

        Parameters
        ----------
        amount : int
            Increase the volume by this amount (percent). This gets added to the
            present volume level. If the value of `amount` and the current
            volume is outside the valid range of 0 to 100, the value will be
            clipped. The default value is 10 (or 10% increase).

        Returns
        -------
        int
            Volume after changed.

        See also
        --------
        getVolume
        setVolume
        decreaseVolume

        Examples
        --------
        Adjust the volume of the current video using key presses::

            # assume `mov` is an instance of this class defined previously
            for key in event.getKeys():
                if key == 'minus':
                    mov.decreaseVolume()
                elif key == 'equals':
                    mov.increaseVolume()

        """
        if not self._hasPlayer:
            return 0

        self.setVolume(min(max(self.getVolume() + int(amount), 0), 100))

        return self.getVolume()

    def decreaseVolume(self, amount=10):
        """Decrease the volume.

        Parameters
        ----------
        amount : int
            Decrease the volume by this amount (percent). This gets subtracted
            from the present volume level. If the value of `amount` and the
            current volume is outside the valid range of 0 to 100, the value
            will be clipped. The default value is 10 (or 10% decrease).

        Returns
        -------
        int
            Volume after changed.

        See also
        --------
        getVolume
        setVolume
        increaseVolume

        """
        if not self._hasPlayer:
            return 0

        self.setVolume(min(max(self.getVolume() - int(amount), 0), 100))

        return self.getVolume()

    # --------------------------------------------------------------------------
    # Video and playback information
    #
    @property
    def percentageComplete(self):
        """Percentage of the video completed (`float`)."""
        return self.getPercentageComplete()

    @property
    def frameTime(self):
        """Current frame time in seconds (`float`)."""
        return self.getCurrentFrameTime()

    def getCurrentFrameTime(self):
        """Get the time that the movie file specified the current video frame as
        having.

        Returns
        -------
        float
            Current video time in seconds.

        """
        if not self._hasPlayer:
            return 0.0

        return self.pts

    # --------------------------------------------------------------------------
    # Drawing methods
    #
    def setFlipHoriz(self, newVal=True, log=True):
        """If set to True then the movie will be flipped horizontally
        (left-to-right). Note that this is relative to the original, not
        relative to the current state.
        """
        self.flipHoriz = newVal
        logAttrib(self, log, 'flipHoriz')

    def setFlipVert(self, newVal=True, log=True):
        """If set to True then the movie will be flipped vertically
        (top-to-bottom). Note that this is relative to the original, not
        relative to the current state.
        """
        self.flipVert = newVal
        logAttrib(self, log, 'flipVert')


if __name__ == "__main__":
    pass
