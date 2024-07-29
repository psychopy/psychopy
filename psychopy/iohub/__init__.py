#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import sys
from .errors import print2err, printExceptionDetailsToStdErr
from .util import module_directory

if sys.platform == 'darwin':
    import objc  # pylint: disable=import-error

EXP_SCRIPT_DIRECTORY = ''


def _localFunc():
    return None


IOHUB_DIRECTORY = module_directory(_localFunc)

def _haveTables():
    if sys.platform == 'darwin':
        # on macos check if this is arm64
        import platform
        if platform.processor == 'arm64':
            # if we try to load the tables module on arm64 we get a seg fault
            # we don't want to even try until we can work out how to detect
            # in advance whether the library is arm64 or not
            print2err('WARNING: running on arm64 mac which may crash loading pytables. ',
                    'ioHub hdf5 datastore functionality will be disabled for now.')
            return False
    try:
        import tables
        return True
    except ImportError:
        print2err('WARNING: pytables package not found. ',
                'ioHub hdf5 datastore functionality will be disabled.')
        return False
    except Exception:
        printExceptionDetailsToStdErr()

_DATA_STORE_AVAILABLE = _haveTables()
if _DATA_STORE_AVAILABLE:
    import tables  # not sure if any part of iohub needed this in the namespace

from psychopy.iohub.constants import EventConstants, KeyboardConstants, MouseConstants

lazyImports = """
from psychopy.iohub.client.connect import launchHubServer
from psychopy.iohub.devices.computer import Computer
from psychopy.iohub.client.eyetracker.validation import ValidationProcedure
"""

try:
    from psychopy.contrib.lazy_import import lazy_import
    lazy_import(globals(), lazyImports)
except Exception:
    exec(lazyImports)
