#!/usr/bin/env python
#  -*- coding: utf-8 -*-

# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, absolute_import, print_function

import sys

from .errors import print2err, printExceptionDetailsToStdErr
from .util import module_directory, fix_encoding

fix_encoding.fix_encoding()

if sys.platform == 'darwin':
    import objc  # pylint: disable=import-error

EXP_SCRIPT_DIRECTORY = ''

def _localFunc():
    return None
IOHUB_DIRECTORY = module_directory(_localFunc)

_ispkg = True
_pkgroot = 'iohub'
if IOHUB_DIRECTORY.find('psychopy') >= 0:
    _ispkg = False
    _pkgroot = 'psychopy.iohub'

_DATA_STORE_AVAILABLE = False
try:
    import tables # pylint: disable=wrong-import-position, wrong-import-order
    _DATA_STORE_AVAILABLE = True
except ImportError:
    print2err('WARNING: pytables package not found. ',
              'ioHub functionality will be disabled.')
except Exception: # pylint: disable=broad-except
    printExceptionDetailsToStdErr()

from .client.expruntime import ioHubExperimentRuntime

lazyImports = """
from {pkgroot}.client.connect import launchHubServer
from {pkgroot}.devices.computer import Computer
""".format(pkgroot=_pkgroot)

try:
    from psychopy.contrib.lazy_import import lazy_import
    lazy_import(globals(), lazyImports)
except Exception:
    exec(lazyImports)