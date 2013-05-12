"""
ioHub Python Module
.. file: iohub/__init__.py

fileauthor: Sol Simpson <sol@isolver-software.com>

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
"""
from __future__ import division

try:
    from yaml import load, dump
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
    
def construct_yaml_unistr(self, node):
    return self.construct_scalar(node)
Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_unistr)
#SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)


import sys

from psychopy.clock import  MonotonicClock, monotonicClock
from util import fix_encoding,OrderedDict, module_directory, updateDict
from util import print2err, printExceptionDetailsToStdErr, ioHubError, createErrorResult, ioHubServerError, ioHubConnectionException
from util import isIterable,getCurrentDateTimeString,convertCamelToSnake
from util import ExperimentVariableProvider
from util import FullScreenWindow, win32MessagePump, SinusoidalMotion
from util import TimeTrigger, DeviceEventTrigger
from util import ScreenState, ClearScreen,InstructionScreen, ImageScreen
from util import ProgressBarDialog, MessageDialog, FileDialog, ioHubDialog

fix_encoding.fix_encoding()

def _localFunc():
    return None
    
global IO_HUB_DIRECTORY
IO_HUB_DIRECTORY=module_directory(construct_yaml_unistr)

#version info for ioHub
__version__='0.8.0'
__license__='GNU GPLv3 (or more recent equivalent)'
__author__='iSolver Software Solutions'
__author_email__='sol@isolver-software.com'
__maintainer_email__='sol@isolver-software.com'
__users_email__='sol@isolver-software.com'
__url__='https://www.github.com/isolver/ioHub/'


# check module is being loaded on a supported platform
SUPPORTED_SYS_NAMES=['linux2','win32','cygwin','darwin']  
if sys.platform not in SUPPORTED_SYS_NAMES:
    print ''
    print "ERROR: ioHub is not supported on the current OS platform. Supported options are: ", SUPPORTED_SYS_NAMES
    print "EXITING......"
    print ''
    sys.exit(1)

import constants
from constants import EventConstants, DeviceConstants, KeyboardConstants, MouseConstants,EyeTrackerConstants

import client
from client import ioHubConnection, launchHubServer, ioHubExperimentRuntime

import devices
from devices import Computer, import_device, DeviceEvent, Device

import datastore

import server
