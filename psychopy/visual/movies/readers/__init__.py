#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Readers which decode frames from movie files.

Each decoder library has a reader of its own, a subclass of `MovieFileReader`.
Creating a `MovieFileReader` gives the reader of the library asked for.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'MovieFileReader',
    'FFPyPlayerMovieFileReader',
    'PyAVMovieFileReader',
    'OpenCVMovieFileReader',
    'VLCMovieFileReader',
    'PREFERRED_VIDEO_LIB',
    'SUPPORTED_VIDEO_LIBS']

from ._base import MovieFileReader, PREFERRED_VIDEO_LIB, SUPPORTED_VIDEO_LIBS
# each of these registers its reader with `_MOVIE_READER_CLASSES`
from .ffpyplayer_reader import FFPyPlayerMovieFileReader
from .pyav_reader import PyAVMovieFileReader
from .opencv_reader import OpenCVMovieFileReader
from .vlc_reader import VLCMovieFileReader
