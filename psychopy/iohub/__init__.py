# -*- coding: utf-8 -*-
"""iohub provides an integrated framework to interact with input and output
devices (from keyboards and mice to eyetrackers and custom hardware) in a 
precise synchronised manner that will not interfere with stimulus presentation
"""

# ioHub Python Module
# .. file: psychopy/iohub/__init__.py
#
# fileauthor: Sol Simpson <sol@isolver-software.com>
#
# Copyright (C) 2012-2014 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License
# (GPL version 3 or any later version).

from __future__ import division

import sys
if sys.platform == 'darwin':
    import objc

from psychopy.clock import  MonotonicClock, monotonicClock

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

import constants
from constants import EventConstants, DeviceConstants
from constants import KeyboardConstants, MouseConstants, EyeTrackerConstants

from util import print2err, printExceptionDetailsToStdErr, ioHubError
from util import fix_encoding, OrderedDict, module_directory, updateDict
from util import isIterable, getCurrentDateTimeString, convertCamelToSnake
from util import ProgressBarDialog, MessageDialog, FileDialog, ioHubDialog
from util import win32MessagePump

fix_encoding.fix_encoding()

def _localFunc():
    return None

global IO_HUB_DIRECTORY
IO_HUB_DIRECTORY=module_directory(_localFunc)

import devices
from devices import Computer, import_device, DeviceEvent, Device

_DATA_STORE_AVAILABLE=False
try:
    import datastore
    _DATA_STORE_AVAILABLE=True
except Exception, e:
    print2err("WARNING: ioHub DataStore could not be loaded. DataStore functionality will be disabled. Error: ")
    printExceptionDetailsToStdErr()

import client
from client import ioHubConnection, launchHubServer, ioHubExperimentRuntime


from util import Trigger, TimeTrigger, DeviceEventTrigger
from util import ScreenState, ClearScreen, InstructionScreen, ImageScreen
from util import ExperimentVariableProvider, SinusoidalMotion, to_numeric
from util.targetpositionsequence import TargetStim, PositionGrid, TargetPosSequenceStim, ValidationProcedure

def _start(**kwargs):
    """
    Do not use this method. Incomplete. May go away.

    Starts an instance of the iohub server. An iohub_config.yaml is looked for
    in the the same directory as the script. If found, it is used to load
    devices for the experiment session.

    If no config files are found, the server is started with default device
    settings.

    :return:
    """
    import os

    # Check that a psychopy Window has been created so that we can get info
    # needed for the iohub Display device.
    from psychopy import visual
    openWindows = visual.window.openWindows
    if len(openWindows) == 0:
        print "The PsychoPy Window must be created prior to starting iohub. Exiting..."
        sys.exit(1)

    # TODO: Use info from win.monitor to set screen info and eye distance if possible.
    #win = openWindows[0]()

    #win_methods = [m for m in dir(win) if m[0] != '_']
    #pyglet_win_methods = [m for m in dir(win.winHandle) if m[0] != '_']

    #print "Window methods:"
    #for m in win_methods:
    #    print m

    #print "Pyglet Window methods:"
    #for m in pyglet_win_methods:
    #    print m

    '''
    Display:
        name: display
        reporting_unit_type: pix
        device_number: 0
        physical_dimensions:
            width: 500
            height: 281
            unit_type: mm
        default_eye_distance:
            surface_center: 550
            unit_type: mm
        psychopy_monitor_name: default
        override_using_psycho_settings: False
    '''

    if not kwargs.has_key('experiment_code'):
        kwargs['experiment_code'] = 'default_exp'

    if kwargs.has_key('iohub_config_name'):
        print "Starting iohub with iohub_config_name provided."
        return launchHubServer(**kwargs)

    iohub_config_name = './iohub_config.yaml'
    if os.path.isfile(os.path.normpath(os.path.abspath(iohub_config_name))):
        kwargs['iohub_config_name'] = os.path.normpath(os.path.abspath(iohub_config_name))
        print "Starting iohub with iohub_config_name:",kwargs['iohub_config_name']
        return launchHubServer(**kwargs)

    print "Starting iohub with default settings."
    return launchHubServer(**kwargs)