#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Class for video frames.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ["MovieFrame", "NULL_MOVIE_FRAME_INFO", "MOVIE_FRAME_NOT_READY"]


MOVIE_FRAME_NOT_READY = object()


class MovieFrame:
    """Class containing data of a single movie frame.

    Parameters
    ----------
    frameIndex : int
        The index for this frame in the movie.
    absTime : float
        Absolute time in seconds in movie time which the frame is to appear
        on-screen.
    displayTime : float
        Time in seconds the frame is intended to remain on screen after
        `absTime`. Usually equal to the frame period.
    size : ArrayLike
        Width and height of the source video frame in pixels. This is needed to
        correctly interpret `colorData`.
    colorFormat : str
        Color format identifier. This is used to ensure the correct format for
        the destination texture buffer that will contain `colorData`. Default is
        `'rgb8'` for 8-bit RGB.
    colorData : ArrayLike or None
        Movie frame color pixel data as an array. Set as `None` if no image data
        is available.
    audioChannels : int
        Number of audio channels present in `audioSamples` (`int`). Use `1` for
        mono and `2` for stereo. This is used to correctly format the data
        contained in `audioSamples` to pass to the desired audio sink.
    audioSamples : ArrayLike or None
        Audio samples as an array. Set as `None` if audio data is unavailable.
    metadata : MovieMetadata
        Metadata of the stream at the time this movie frame was obtained.
    movieLib : str or None
        Movie library used to obtain this frame (e.g., `'ffpyplayer'`).
    userData : dict or None
        Optional mapping for storing user defined data.

    """
    __slots__ = [
        "_metadata",
        "_frameIndex",
        "_absTime",
        "_displayTime",
        "_size",
        "_colorFormat",
        "_colorData",
        "_audioSamples",
        "_audioChannels",
        "_movieLib",
        "_userData",
        '_keepAlive'
    ]

    def __init__(self,
                 frameIndex=-1,
                 absTime=-1.0,
                 displayTime=0.0,
                 size=(-1, -1),
                 colorFormat='rgb8',
                 colorData=None,
                 audioChannels=2,
                 audioSamples=None,
                 metadata=None,
                 movieLib=u"",
                 userData=None,
                 keepAlive=None):

        self.frameIndex = frameIndex
        self.absTime = absTime
        self.displayTime = displayTime
        self.size = size
        self.colorFormat = colorFormat
        self.colorData = colorData
        self.audioSamples = audioSamples
        self.audioChannels = audioChannels
        self._metadata = metadata
        self.movieLib = movieLib
        self.userData = userData
        self._keepAlive = keepAlive

    def __repr__(self):
        return (f"MovieFrame(frameIndex={self.frameIndex}, "
                f"absTime={self.absTime}, "
                f"displayTime={self.displayTime}, "
                f"size={self.size}, "
                f"colorData={repr(self.colorData)}, "
                f"colorFormat={repr(self.colorFormat)}, "
                f"audioChannels={self.audioChannels}, "
                f"audioSamples={repr(self.audioSamples)}, "
                f"metadata={repr(self._metadata)}, "
                f"movieLib={repr(self.movieLib)}, "
                f"userData={repr(self.userData)})")

    @property
    def frameIndex(self):
        """The index for this frame in the movie (`int`). A value of `-1`
        indicates that this value is uninitialized.
        """
        return self._frameIndex

    @frameIndex.setter
    def frameIndex(self, val):
        self._frameIndex = int(val)

    @property
    def absTime(self):
        """Absolute time in seconds in movie time which the frame is to appear
        on-screen (`float`). A value of -1.0 indicates that this value is not
        valid.
        """
        return self._absTime

    @absTime.setter
    def absTime(self, val):
        self._absTime = float(val)

    @property
    def displayTime(self):
        """Time in seconds the frame is intended to remain on screen after
        `absTime` (`float`). Usually equal to the frame period.
        """
        return self._displayTime

    @displayTime.setter
    def displayTime(self, val):
        self._displayTime = float(val)

    @property
    def size(self):
        """Source video size (frame size) (w, h) in pixels (`tuple`). This value
        is uninitialized if `(-1, -1)` is returned.
        """
        return self._size

    @size.setter
    def size(self, value):
        # format checking
        if not hasattr(value, '__len__'):
            raise TypeError('Value for `size` must be iterable.')

        if not len(value) == 2:
            raise ValueError(
                'Invalid length for value `size`, must have length of 2.')

        if not all([isinstance(i, int) for i in value]):
            raise TypeError('Elements of `size` must all have type `int`.')

        self._size = tuple(value)

    @property
    def colorFormat(self):
        """Color format of the frame color data (`str`). Default is `'rgb8'`.
        """
        return self._colorFormat

    @colorFormat.setter
    def colorFormat(self, value):
        self._colorFormat = str(value)

    @property
    def colorData(self):
        """Movie frame color data as an array (`ArrayLike` or `None`). The
        format of this array is contingent on the `movieLib` in use.
        """
        return self._colorData

    @colorData.setter
    def colorData(self, val):
        self._colorData = val

    @property
    def audioSamples(self):
        """Audio data as an array (`ArrayLike` or `None`). The format of this
        array is contingent on the `movieLib` in use.
        """
        return self._audioSamples

    @audioSamples.setter
    def audioSamples(self, val):
        self._audioSamples = val

    @property
    def audioChannels(self):
        """Number of audio channels present in `audioSamples` (`int`). Use
        `1` for mono and `2` for stereo. This is used to correctly format the
        data contained in `audioSamples` to get past to the desired audio
        sink.
        """
        return self._audioChannels

    @audioChannels.setter
    def audioChannels(self, val):
        self._audioChannels = int(val)

    @property
    def metadata(self):
        """Movie library used to get this metadata (`str`). An empty string
        indicates this field is not initialized.
        """
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    @property
    def movieLib(self):
        """Movie library used to get this metadata (`str`). An empty string
        indicates this field is not initialized.
        """
        return self._movieLib

    @movieLib.setter
    def movieLib(self, value):
        self._movieLib = str(value)

    @property
    def userData(self):
        """Optional mapping for storing user defined data (`dict` or `None`). If
        set to `None`, an empty dictionary will be initialized and set as this
        value.
        """
        return self._userData

    @userData.setter
    def userData(self, value):
        if value is None:
            self._userData = {}
            return

        if not isinstance(value, dict):
            raise TypeError(
                'Value for `userData` must be type `dict` or `None`.')

        self._userData = value


# used to represent an empty frame
NULL_MOVIE_FRAME_INFO = MovieFrame()


if __name__ == "__main__":
    pass
