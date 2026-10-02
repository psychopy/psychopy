#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Class for storing movie file metadata.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'MovieMetadata',
    'NULL_MOVIE_METADATA',
]


class MovieMetadata:
    """Class for storing metadata about a movie file.

    This class is used to store metadata about a movie file. This includes
    information about the video and audio tracks in the movie. Metadata is
    extracted from the movie file when the movie reader is opened.

    This class is not intended to be used directly by users. It is used
    internally by the `MovieFileReader` class to store metadata about the movie
    file being read.

    Parameters
    ----------
    filename : str
        The name (or path) of the movie file to extract metadata from.
    size : tuple
        The size of the movie in pixels (width, height).
    frameRate : float
        The frame rate of the movie in frames per second.
    duration : float
        The duration of the movie in seconds.
    colorFormat : str
        The color format of the movie (e.g. 'rgba', etc.).
    audioTrack : AudioMetadata or None
        The audio track metadata.
    
    """
    __slots__ = (
        '_filename', '_size', '_frameRate', '_duration', '_frameInterval',
        '_colorFormat', '_audioTrack')
    
    def __init__(self, filename, size, frameRate, duration, colorFormat, 
                 audioTrack=None):
        self._filename = filename
        self._size = size
        self._frameRate = frameRate
        self._duration = duration
        self._frameInterval = 1.0 / self._frameRate

        if isinstance(colorFormat, bytes):
            colorFormat = colorFormat.decode('utf-8')
        self._colorFormat = colorFormat

        # audio track metadata
        self._audioTrack = audioTrack

    def __repr__(self):
        return (
            f"MovieMetadata(filename={self.filename}, "
            f"size={self.size}, "
            f"frameRate={self.frameRate}, "
            f"duration={self.duration})")
        
    def __str__(self):
        return (
            f"MovieMetadata(filename={self.filename}, "
            f"size={self.size}, "
            f"frameRate={self.frameRate}, "
            f"duration={self.duration})")

    @property
    def filename(self):
        """The name (path) of the movie file (`str`).

        """
        return self._filename

    @property
    def size(self):
        """The size of the movie in pixels (`tuple`).

        """
        return self._size

    @property
    def frameRate(self):
        """The frame rate of the movie in frames per second (`float`).

        """
        return self._frameRate
    
    @property
    def frameInterval(self):
        """The interval between frames in the movie in seconds (`float`).

        """
        return self._frameInterval
    
    @property
    def duration(self):
        """The duration of the movie in seconds (`float`).

        """
        return self._duration

    @property
    def colorFormat(self):
        """The color format of the movie (`str`).

        """
        return self._colorFormat
    
    @property
    def audioTrack(self):
        """The audio track metadata (`AudioMetadata` or `None`).

        """
        return self._audioTrack


# Null movie metadata object, return a reference to this object instead of
# `None` when no metadata is present.
NULL_MOVIE_METADATA = MovieMetadata(
    filename=u'', 
    size=(-1, -1),
    frameRate=-1,
    duration=-1.0, 
    colorFormat=u'unknown', 
    audioTrack=None
)
