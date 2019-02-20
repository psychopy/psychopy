#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

import threading
import time
from collections import OrderedDict

import wx

from psychopy import prefs, logging
from psychopy.constants import NOT_STARTED, STARTED, SKIP, FINISHED
from . import connections
from psychopy.tools import versionchooser as vc

_t0 = time.time()


tasks = OrderedDict()
if prefs.connections['allowUsageStats']:
    tasks['sendUsageStats'] = {
        'status': NOT_STARTED,
        'func': connections.sendUsageStats,
        'tstart': None, 'tEnd': None,
        'thread': True,
    }
else:
    tasks['sendUsageStats'] = {
        'status': SKIP,
        'func': connections.sendUsageStats,
        'tstart': None, 'tEnd': None,
        'thread': True,
    }
if prefs.connections['checkForUpdates']:
    tasks['checkForUpdates'] = {
        'status': NOT_STARTED,
        'func': connections.getLatestVersionInfo,
        'tstart': None, 'tEnd': None,
        'thread': True,
    }
else:
    tasks['checkForUpdates'] = {
        'status': SKIP,
        'func': connections.getLatestVersionInfo,
        'tstart': None, 'tEnd': None,
        'thread': True,
    }

tasks['checkNews'] = {
    'status': NOT_STARTED,
    'func': connections.getNewsItems,
    'tstart': None, 'tEnd': None,
    'thread': True,
}
tasks['showTips'] = {
    'status': NOT_STARTED,
    'func': None,
    'tstart': None, 'tEnd': None,
    'thread': True,
}
tasks['updateVersionChooser'] = {
    'status': NOT_STARTED,
    'func': vc._remoteVersions,
    'tstart': None, 'tEnd': None,
    'thread': True,
}
tasks['showNews'] = {
    'status': NOT_STARTED,
    'func': connections.showNews,
    'tstart': None, 'tEnd': None,
    'thread': False,
}

currentTask = None


def doIdleTasks(app=None):
    global currentTask

    if currentTask and currentTask['thread'] and \
            currentTask['thread'].is_alive():
        # is currently tunning in a thread
        return 0

    for taskName in tasks:
        thisTask = tasks[taskName]
        thisStatus = tasks[taskName]['status']
        if thisStatus == NOT_STARTED:
            currentTask = thisTask
            currentTask['tStart'] = time.time() - _t0
            currentTask['status'] = STARTED
            logging.debug('Started {} at {}'.format(taskName,
                                                    currentTask['tStart']))
            _doTask(taskName, app)
            return 0  # something is in motion
        elif thisStatus == STARTED:
            if not currentTask['thread'] \
                    or not currentTask['thread'].is_alive():
                # task finished so take note and pick another
                currentTask['status'] = FINISHED
                currentTask['thread'] = None
                currentTask['tEnd'] = time.time() - _t0
                logging.debug('Finished {} at {}'.format(taskName,
                                                         currentTask['tEnd']))
                currentTask = None
                continue
            else:
                return 0
    logging.flush()

    return 1


def _doTask(taskName, app):
    currentTask = tasks[taskName]

    # what args are needed
    if taskName == 'updateVersionChooser':
        args = (True,)
    else:
        args = (app,)

    # if we need a thread then create one and keep track of it
    if currentTask['thread'] == True:
        currentTask['thread'] = threading.Thread(
                target=currentTask['func'], args=args)
        # currentTask['thread'].daemon = True  # kill if the app quits
        currentTask['thread'].start()

    else:  # otherwise run immediately
        currentTask['func'](*args)
        currentTask['status'] = FINISHED
        currentTask['tEnd'] = time.time() - _t0
        logging.debug('Finished {} at {}'.format(taskName,
                                                 currentTask['tEnd']))
