# -*- coding: utf-8 -*-
# ioHub Python Module
# .. file: iohub/__init__.py
#
# fileauthor: Sol Simpson <sol@isolver-software.com>
#
# Copyright (C) 2012-2014 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License
# (GPL version 3 or any later version).
from __future__ import absolute_import
import sys
from .errors import print2err, printExceptionDetailsToStdErr
from .util import module_directory

if sys.platform == 'darwin':
    import objc

try:
    import ujson as json
except Exception:
    import json

try:
    from yaml import load, dump
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# Only turn on converting all strings to unicode by the YAML loader
# if running Python 2.7 or higher. 2.6 does not seem to like unicode dict keys.
# ???
#
if sys.version_info[0] != 2 or sys.version_info[1] >= 7:
    def construct_yaml_unistr(self, node):
        return self.construct_scalar(node)
    Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_unistr)

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
    from .datastore import pandas as _dspandas
    _DATA_STORE_AVAILABLE = True
except Exception as e:
    print2err(
        'WARNING: ioHub DataStore could not be loaded. DataStore functionality will be disabled. Error: ')
    printExceptionDetailsToStdErr()

from .util.fix_encoding import fix_encoding
fix_encoding()
