#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Platform specific extensions (using ctypes)"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import platform

# dummy methods should be overridden by imports below if they exist


def rush(value=False, realtime=False):
    """
    """
    # dummy method.
    return False


def waitForVBL():
    """DEPRECATED: waiting for a VBL is handled by the screen flip
    """
    return False


def sendStayAwake():
    """Sends a signal to your system to indicate that the computer is
    in use and should not sleep. This should be sent periodically,
    but PsychoPy will send the signal by default on each screen refresh.

    Added: v1.79.00.

    Currently supported on: windows, macOS
    """
    return False

# NB includes vista and 7 (but not sure about vista64)
if sys.platform == 'win32':
    from .win32 import *  # pylint: disable=W0401
elif sys.platform == 'darwin':
    from .darwin import *  # pylint: disable=W0401
elif sys.platform.startswith('linux'):  # normally 'linux2'
    from .linux import *  # pylint: disable=W0401
