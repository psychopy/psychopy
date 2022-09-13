#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for interfacing with movie player libraries.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ["getMoviePlayer"]

import psychopy.logging as logging
from ._base import BaseMoviePlayer

# Players available, you must update this list to make players discoverable by
# the `MovieStim` class when the user specifies `movieLib`.
_players = {'Null': None}
PREFERRED_VIDEO_LIB = 'ffpyplayer'


def getMoviePlayer(movieLib):
    """Get a movie player interface.

    Calling this returns a reference to the unbound class for the requested
    movie player interface.

    Parameters
    ----------
    movieLib : str
        Name of the player interface to get.

    Returns
    -------
    Subclass of BaseMoviePlayer

    """
    if not isinstance(movieLib, str):  # type check
        raise TypeError(
            "Invalid type for parameter `movieLib`. Must have type `str`.")

    global _players
    try:
        from .ffpyplayer_player import FFPyPlayer
        _players['ffpyplayer'] = FFPyPlayer
    except ImportError:
        logging.warn("Cannot import library `ffpyplayer`, backend is "
                     "unavailable.")

    # get a reference to the player object
    reqPlayer = _players.get(movieLib, None)
    if reqPlayer is not None:
        return reqPlayer

    # error if the key is not in `reqPlayer`
    raise ValueError(
        "Cannot find matching video player interface for '{}'.".format(
            movieLib))


if __name__ == "__main__":
    pass
