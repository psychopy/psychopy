# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import absolute_import

import sys

from .errors import print2err, printExceptionDetailsToStdErr
from .util import module_directory

if sys.platform == 'darwin':
    import objc

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
    import tables
    _DATA_STORE_AVAILABLE = True
except Exception as e:
    print2err(
        'WARNING: ioHub DataStore could not be loaded. DataStore functionality will be disabled. Error: ')
    printExceptionDetailsToStdErr()

from .util.fix_encoding import fix_encoding
fix_encoding()
