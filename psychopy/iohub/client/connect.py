# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, absolute_import, print_function

import os
 
from .. import _DATA_STORE_AVAILABLE, IOHUB_DIRECTORY
from . import ioHubConnection
from ..util import yload, yLoader, readConfig


def launchHubServer(**kwargs):
    """
    Starts the ioHub Server subprocess, and return a
    :class:`psychopy.iohub.client.ioHubConnection` object that is used to
    access enabled iohub device's events, get events, and control the
    ioHub process during the experiment.

    By default (no kwargs specified), the ioHub server does not create an
    ioHub HDF5 file, events are available to the experiment program at runtime.
    The following Devices are enabled by default:

    - Keyboard: named 'keyboard', with runtime event reporting enabled.
    - Mouse: named 'mouse', with runtime event reporting enabled.
    - Monitor: named 'monitor'.
    - Experiment: named 'experiment'.

    To customize how the ioHub Server is initialized when started, use
    one or more of the following keyword arguments when calling the function:

    +---------------------+-----------------+---------------+-----------------+
    | kwarg Name          | Value Type      | Description                     |
    +=====================+=================+===============+=================+
    | experiment_code     | str, <= 24 char | If experiment_code is provided, |
    |                     |                 | an ioHub HDF5 file will be      |
    |                     |                 | created for the session.        |
    +---------------------+-----------------+---------------+-----------------+
    | session_code        | str, <= 24 char | When specified, used as the name|
    |                     |                 | of the ioHub HDF5 file created  |
    |                     |                 | for the session.                |
    +---------------------+-----------------+---------------+-----------------+
    | experiment_info     | dict            | Can be used to save the         |
    |                     |                 | following experiment metadata   |
    |                     |                 | fields:                         |
    +---------------------+-----------------+---------------+-----------------+
    |                                       | - code:         str, <= 24 char |
    |                                       | - title:        str, <= 48 char |
    |                                       | - description:  str, < 256 char |
    |                                       | - version:      str, <= 6 char  |
    +---------------------+-----------------+---------------+-----------------+
    | session_info        | dict            | Can be used to save the         |
    |                     |                 | following session metadata      |
    |                     |                 | fields:                         |
    +---------------------+-----------------+---------------+-----------------+
    |                                       | - code:         str, <= 24 char |
    |                                       | - name:         str, <= 48 char |
    |                                       | - comments:     str, < 256 char |
    |                                       | - user_variables:          dict |
    +---------------------+-----------------+---------------+-----------------+
    | datastore_name      | str             | Used to provide an ioHub HDF5   |
    |                     |                 | file name different than the    |
    |                     |                 | session_code.                   |
    +---------------------+-----------------+---------------+-----------------+
    |psychopy_monitor_name| str             | Provides the path of a          |
    |                     |                 | PsychoPy Monitor Center config  |
    |                     |                 | file. Information like display  |
    |                     |                 | size is read and used to update |
    |                     |                 | the ioHub Display Device config.|
    +---------------------+-----------------+---------------+-----------------+
    | iohub_config_name   | str             | Specifies the name of the       |
    |                     |                 | iohub_config.yaml file that     |
    |                     |                 | contains the ioHub Device       |
    |                     |                 | list to be used by the ioHub    |
    |                     |                 | Server. i.e. the 'device_list'  |
    |                     |                 | section of the yaml file.       |
    +---------------------+-----------------+---------------+-----------------+
    | iohub.device.path   | dict            | Add an ioHub Device by using the|
    |                     |                 | device class path as the key,   |
    | Multiple Device's   |                 | and the device's configuration  |
    | can be specified    |                 | in a dict value.                |
    | using separate      |                 |                                 |
    | kwarg entries.      |                 |                                 |
    +---------------------+-----------------+---------------+-----------------+

    Examples:

        A. Wait for the 'q' key to be pressed::

            from psychopy.iohub.client import launchHubServer

            # Start the ioHub process. 'io' can now be used during the
            # experiment to access iohub devices and read iohub device events.
            io=launchHubServer()

            print "Press any Key to Exit Example....."

            # Wait until a keyboard event occurs
            keys = io.devices.keyboard.waitForKeys(['q',])

            print("Key press detected: {}".format(keys))
            print("Exiting experiment....")

            # Stop the ioHub Server
            io.quit()

        B. Use a XInput compliant game pad (e.g. Xbox 360 controller)::

            from psychopy.iohub.client import launchHubServer

            # Create an iohub_config kwargs dict and indicate that ioHub
            # should connect to a XInput compliant game pad using the
            # default devices settings.
            iohub_config = dict()
            iohub_config['xinput.Gamepad'] = dict()

            # Start the ioHub Server Process and access the gamepad and
            # keyboard devices.
            io = launchHubServer(**iohub_config)
            gamepad = io.getDevice('gamepad')
            keyboard = io.devices.keyboard

            if gamepad:
                print("Press 'A' button on controller to make it rumble.")
                print("To Exit the Demo, press any Keyboard key.....")

                while not keyboard.getPresses():
                    # Get any new events from the game pad
                    for gp_evt in gamepad.getEvents():
                        # Check if the gamepad button 'A' was pressed....
                        if 'A' in gp_evt.buttons:
                            # Rumble the game pad for 1 second:
                            #   - low frequency motor @ 50%
                            #   - high frequency motor @ 25%
                            # setRumble() returns as soon as the
                            # ioHub Server has started the requested action.
                            rt, rd = gamepad.setRumble(50.0, 25.0, 1.0)
                            print("Started Rumbling....")
                            io.wait(0.01)
            else:
                print("XInput device connection failed.")
            print("Exiting demo....")
            # Stop the ioHub Server
            io.quit()

    Please see the psychopy/demos/coder/iohub/launchHub.py demo for examples
    of different ways to use the launchHubServer function.
    """
    experiment_code = kwargs.get('experiment_code', None)
    if experiment_code:
        del kwargs['experiment_code']
    experiment_info = kwargs.get('experiment_info')
    if experiment_info:
        del kwargs['experiment_info']
        for k, v in list(experiment_info.items()):
            if k in ['code', 'title', 'description', 'version']:
                experiment_info[k] = u"{}".format(v)
        if experiment_info.get('code'):
            experiment_code = experiment_info['code']
        elif experiment_code:
            experiment_info['code'] = experiment_code
    elif experiment_code:
        experiment_info = dict(code=experiment_code)

    session_code = kwargs.get('session_code', None)
    if session_code:
        del kwargs['session_code']
    session_info = kwargs.get('session_info')
    if session_info:
        del kwargs['session_info']
        for k, v in list(session_info.items()):
            if k in ['code', 'name', 'comments']:
                session_info[k] = u"{}".format(v)
            elif k == 'user_variables':
                session_info[k] = v
        if session_info.get('code'):
            session_code = session_info['code']
        elif session_code:
            session_info['code'] = session_code
    elif session_code:
        session_info = dict(code=session_code)
    else:        
        session_info = {}

    if experiment_code and not session_code:
        # this means we should auto_generate a session code
        import datetime
        dtstr = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M')
        session_info['code'] = session_code = u"S_{0}".format(dtstr)

    datastore_name = None
    if _DATA_STORE_AVAILABLE is True:
        datastore_name = kwargs.get('datastore_name')
        if datastore_name:
            del kwargs['datastore_name']
        elif session_code:
            datastore_name = session_code

    monitor_name = kwargs.get('psychopy_monitor_name')
    if monitor_name:
        del kwargs['psychopy_monitor_name']

    monitor_devices_config = None
    iohub_conf_file_name = kwargs.get('iohub_config_name')
    if iohub_conf_file_name:
        # Load the specified iohub configuration file,
        # converting it to apython dict.
        with file(iohub_conf_file_name, 'r') as iohub_conf_file:
            _temp_conf_read = yload(iohub_conf_file, Loader=yLoader)
            monitor_devices_config = _temp_conf_read.get('monitor_devices')
            del kwargs['iohub_config_name']

    iohub_config = None
    device_dict = {}
    if monitor_devices_config:
        device_dict = monitor_devices_config
    #    iohub_config = dict(monitor_devices=monitor_devices_config)
    
    if isinstance(device_dict,(list,tuple)):
        tempdict_ = {}
        for ddict in device_dict:
            tempdict_[list(ddict.keys())[0]] = list(ddict.values())[0]
        device_dict = tempdict_
        
    device_dict.update(kwargs)
    device_list = []

    def isFunction(func):
        import types
        return isinstance(func, types.FunctionType)

    def func2str(func):
        return '%s.%s' % (func.__module__, func.__name__)

    def configfuncs2str(config):
        for k, v in list(config.items()):
            if isinstance(v, dict):
                configfuncs2str(v)
            if isFunction(v):
                config[k] = func2str(v)

    configfuncs2str(device_dict)
    # <<< WTF is this for .... ?????

    # Ensure a Display Device has been defined. If not, create one.
    # Insert Display device as first device in dev. list.
    if 'Display' not in device_dict:
        if monitor_name:
            display_config = {'psychopy_monitor_name': monitor_name,
                              'override_using_psycho_settings': True}
        else:
            display_config = {'override_using_psycho_settings': False}
        device_list.append(dict(Display=display_config))
    else:
        device_list.append(dict(Display=device_dict['Display']))
        del device_dict['Display']

    # Ensure a Experiment, Keyboard, and Mouse Devices have been defined.
    # If not, create them.
    check_for_devs = ['Experiment', 'Keyboard', 'Mouse']
    for adev_name in check_for_devs:
        if adev_name not in device_dict:
            device_list.append({adev_name : {}})
        else:
            device_list.append({adev_name : device_dict[adev_name]})
            del device_dict[adev_name]
    
    iohub_config = dict()
    def_ioconf = readConfig(os.path.join(IOHUB_DIRECTORY,u'default_config.yaml'))
    # Add remaining defined devices to the device list.
    for class_name, device_config in device_dict.items():
        if class_name in def_ioconf:
            # not a device, a top level iohub config param
            iohub_config[class_name] = device_config
        else:
            #TODO: Check that class_name is valid before adding to list
            device_list.append({class_name: device_config})
            
    # Create an ioHub configuration dictionary.
    iohub_config['monitor_devices'] = device_list

    if _DATA_STORE_AVAILABLE and experiment_code and session_code:
        # If datastore_name kwarg or experiment code has been provided,
        # then enable saving of device events to the iohub datastore hdf5 file.
        # If datastore_name kwarg was provided, it is used for the hdf5 file
        # name, otherwise the session code is used. This avoids different
        # experiments / sessions running in the same directory from using
        # the same hdf5 file name.
        if datastore_name is None:
            datastore_name = session_code
        iohub_config['data_store'] = dict(enable=True,
                                          filename=datastore_name,
                                          experiment_info=experiment_info,
                                          session_info=session_info)

    #import pprint
    #print()
    #print('ioHubConnection(iohub_config):')
    #pprint.pprint(iohub_config)
    return ioHubConnection(iohub_config)
