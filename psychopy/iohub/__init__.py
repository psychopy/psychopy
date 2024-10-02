#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import platform
from .errors import print2err, printExceptionDetailsToStdErr
from .util import module_directory

if sys.platform == 'darwin':
    import objc  # pylint: disable=import-error

EXP_SCRIPT_DIRECTORY = ''


def _localFunc():
    return None


IOHUB_DIRECTORY = module_directory(_localFunc)

try:
    import tables
    _DATA_STORE_AVAILABLE = True
except ModuleNotFoundError:
    print2err('WARNING: pytables package not found. ',
            'ioHub hdf5 datastore functionality will be disabled.')
    _DATA_STORE_AVAILABLE = False
except ImportError:
    print2err('WARNING: pytables package failed to load. ',
            'ioHub hdf5 datastore functionality will be disabled.')
    _DATA_STORE_AVAILABLE = False
except Exception:
    printExceptionDetailsToStdErr()

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
