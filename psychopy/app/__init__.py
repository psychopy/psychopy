#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Module for the PsychoPy GUI application.
"""

__all__ = [
    'startApp',
    'quitApp',
    'restartApp',
    'setRestartRequired',
    'isRestartRequired',
    'getAppInstance',
    'getAppFrame',
    'isAppStarted']

try:
    from psychopy_app import *
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "The code for PsychoPy's GUI application now lives in the 'psychopy_app' package. " \
        "Either install that module with `pip install psychopy_app` or download the new PsychoPy Studio " \
        "which has the same functionality rewritten in Electron. See https://www.psychopy.org/download.html for more details."
    )

if __name__ == "__main__":
    pass
