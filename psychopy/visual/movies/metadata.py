#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Class for storing and working with movie file metadata.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ["MovieMetadata", "NULL_MOVIE_METADATA"]


class MovieMetadata:
    """Class for storing metadata and other information associated with a movie.

    Some fields may not be populated if the video format or decoder cannot
    determine them from the stream.

    Parameters
    ----------
    mediaPath : str
        Path to the file that has been loaded or is presently being played.
        This may be a file path or URI to the location of the media.
    title : str
        Title of the clip stored in the metadata.
    duration : float
        Total length of the loaded movie clip in seconds.
    size : tuple
        Width and height of the source video frame in pixels.
    frameRate : float or tuple
        Frame rate of the movie in Hertz (Hz). If a tuple is specified, the
        format should be `(numerator, denominator)`.
    movieLib : str or None
        Library used to obtain this metadata. Almost always will be the same
        value as `MovieStim.movieLib` if this metadata has been retrieved using
        that class.
    userData : dict or None
        Optional mapping for storing user defined data.

    Examples
    --------
    Accessing metadata via the `MovieStim` class::

        myMovie = MovieStim(win, '/path/to/my/movie.mpeg')
        clipDuration = myMovie.metadata.duration

    Check if metadata is valid::

        metadataValid = myMovie.metadata is not NULL_MOVIE_METADATA

    """
    __slots__ = [
        '_mediaPath',
        '_title',
        '_duration',
        '_size',
        '_frameRate',
        '_frameInterval',
        '_pixelFormat',
        '_movieLib',
        '_userData'
    ]

    def __init__(self,
                 mediaPath=u"",
                 title=u"",
                 duration=-1,
                 size=(-1, -1),
                 frameRate=-1,
                 pixelFormat='unknown',
                 movieLib=u"",
                 userData=None):

        self.mediaPath = mediaPath
        self.title = title
        self.duration = duration
        self.frameRate = frameRate
        self.size = size
        self.pixelFormat = pixelFormat
        self.movieLib = movieLib
        self.userData = userData

    def __repr__(self):
        return (f"MovieMetadata(mediaPath={repr(self.mediaPath)}, "
                f"title={repr(self.title)}, "
                f"duration={self.duration}, "
                f"size={self.size}, "
                f"frameRate={self.frameRate}, "
                f"pixelFormat={self.pixelFormat}, "
                f"movieLib={repr(self.movieLib)}, "
                f"userData={repr(self.userData)})")

    def compare(self, metadata):
        """Get a list of attribute names that differ between this and another
        metadata object.

        Returns
        -------
        list of str

        """
        if not isinstance(metadata, MovieMetadata):
            raise TypeError(
                'Value for `metadata` must have type `MovieMetadata`.')

        return []

    @property
    def mediaPath(self):
        """Path to the video (`str`). May be either a path to a file on the
        local machine, URI, or camera enumeration. An empty string indicates
        this field is uninitialized.
        """
        return self._mediaPath

    @mediaPath.setter
    def mediaPath(self, value):
        self._mediaPath = str(value)

    @property
    def title(self):
        """Title of the video (`str`). An empty string indicates this field is
        not initialized.
        """
        return self._title

    @title.setter
    def title(self, value):
        self._title = str(value)

    @property
    def duration(self):
        """Total length of the loaded movie clip in seconds (`float`). A value
        of `-1` indicates that this value is uninitialized.
        """
        return self._duration

    @duration.setter
    def duration(self, value):
        if value is None:
            value = 0.0

        self._duration = float(value)

    @property
    def frameRate(self):
        """Framerate of the video (`float` or `tuple`). A value of `-1`
        indicates that this field is not initialized.
        """
        return self._frameRate

    @frameRate.setter
    def frameRate(self, value):
        if isinstance(value, (tuple, list,)):
            self._frameRate = value[0] / float(value[1])
        else:
            self._frameRate = float(value)

        # compute the frame interval from the frame rate
        self._frameInterval = 1.0 / self._frameRate

    @property
    def frameInterval(self):
        """Frame interval in seconds (`float`). This is the amount of time the
        frame is to remain onscreen given the framerate. This value is computed
        after the `frameRate` attribute is set.
        """
        return self._frameInterval

    @property
    def size(self):
        """Source video size (w, h) in pixels (`tuple`). This value is
        uninitialized if `(-1, -1)` is returned.
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
    def movieLib(self):
        """Movie library used to get this metadata (`str`). An empty string
        indicates this field is not initialized.
        """
        return self._movieLib

    @movieLib.setter
    def movieLib(self, value):
        self._movieLib = str(value)

    @property
    def pixelFormat(self):
        """Video pixel format (`str`). An empty string indicates this field is
        not initialized.
        """
        return self._pixelFormat

    @pixelFormat.setter
    def pixelFormat(self, value):
        self._pixelFormat = str(value)

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


# Null movie metadata object, return a reference to this object instead of
# `None` when no metadata is present.
NULL_MOVIE_METADATA = MovieMetadata()


if __name__ == "__main__":
    pass
