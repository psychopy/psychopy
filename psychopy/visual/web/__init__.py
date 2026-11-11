#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Web pages as stimuli, see `WebBrowserStim`.

Pages are rendered by Chromium (Qt WebEngine) in a separate process, which
needs the `PyQt6-WebEngine` package (``pip install psychopy[web]``).
"""

import importlib.util

from .webbrowserstim import WebBrowserStim

__all__ = [
    'WebBrowserStim',
    'isAvailable',
    'preload',
    'shutdown',
    'getVersionInfo'
]


def isAvailable():
    """Whether web pages can be shown, i.e. Qt WebEngine is installed.

    Returns
    -------
    bool

    """
    try:
        return importlib.util.find_spec('PyQt6.QtWebEngineWidgets') is not None
    except (ImportError, ValueError):
        return False


def preload():
    """Start the web browser server, which otherwise starts when the first
    `WebBrowserStim` is made, taking a moment.

    Raises
    ------
    RuntimeError
        If it can't be started (e.g. Qt WebEngine isn't installed).

    """
    from ._host import BrowserHost
    BrowserHost.get()


def shutdown():
    """Stop the web browser server, closing all pages. It is stopped when
    Python exits anyway."""
    from ._host import BrowserHost
    host = BrowserHost.current()
    if host is not None:
        host.shutdown()


def getVersionInfo():
    """Get the versions of Qt, PyQt, Qt WebEngine and Chromium used to show
    pages, starting the web browser server if it isn't running.

    Returns
    -------
    dict

    """
    from ._host import BrowserHost
    return dict(BrowserHost.get().info.get('versions', {}))
