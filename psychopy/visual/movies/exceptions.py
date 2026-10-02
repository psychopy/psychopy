#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Exceptions raised by movie readers and `MovieStim`.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'MoviePlaybackError',
    'MovieFileNotFoundError',
    'MovieFileFormatError',
    'MovieAudioError',
]

class MoviePlaybackError(Exception):
    """Exception raised when there is an error during movie playback."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"MoviePlaybackError: {self.message}"
    

class MovieFileNotFoundError(MoviePlaybackError):
    """Exception raised when a movie file is not found."""
    def __init__(self, filename):
        super().__init__(f"Movie file not found: {filename}")
        self.filename = filename

    def __str__(self):
        return f"MovieFileNotFoundError: {self.filename} does not exist."
    

class MovieFileFormatError(MoviePlaybackError):
    """Exception raised when a movie file format is not supported."""
    def __init__(self, filename):
        super().__init__(f"Movie file format not supported: {filename}")
        self.filename = filename

    def __str__(self):
        return f"MovieFileFormatError: {self.filename} is not a supported movie format."


class MovieAudioError(MoviePlaybackError):
    """Exception raised when there is an error with movie audio playback."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"MovieAudioError: {self.message}"
