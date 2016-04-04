# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, absolute_import

from .. import _DATA_STORE_AVAILABLE
from . import ioHubConnection
from ..util import yload, yLoader


def launchHubServer(**kwargs):
    """The launchHubServer function is used to start the ioHub Process by the
    main psychopy experiment script.

    To use ioHub for keyboard and mouse event reporting only, simply use
    the function in a way similar to the following::

        from psychopy.iohub.client import launchHubServer

        # Start the ioHub process. 'io' can now be used during the experiment
        # to access iohub devices and read iohub device events.
        io=launchHubServer()

        # By default, ioHub will create Keyboard and Mouse devices and
        # start monitoring for any events from these devices only.
        keyboard=io.devices.keyboard
        mouse=io.devices.mouse

        print "Press any Key to Exit Example....."

        keys = keyboard.waitForKeys()

        print "Key press detected, exiting experiment."

    launchHubServer() accepts several kwarg inputs, which can be used to
    define other devices to run and configure the iohub server in more detail.
    Supported kwargs are:

    - experiment_code: str with max length of 24 chars.
    - session_code: str with max length of 24 chars.
    - experiment_info: dict with following keys:
        - code = str with max length of 24 chars.
        - title = str with max length of 48 chars.
        - description  = str with max length of 256 chars.
        - version = str with max length of 6 chars.
    - session_info: dict with following keys:
        - code = str with max length of 24 chars.
        - name = str with max length of 48 chars.
        - comments  = str with max length of 256 chars.
        - user_variables = dict
    - psychopy_monitor_name: name of Monitor config file being used.
    - datastore_name: name of the hdf5 datastore file to create.
    - iohub_config_name: name of an iohub_config.yaml file. The
      'monitor_devices' field of the file is used to read the iohub device
       to be created along with each device configuration information.
    - any.iohub.device.class.path: value holds the device config dictionary.

    Please see the psychopy/demos/coder/iohub/launchHub.py demo for examples
    of different ways to use the launchHubServer function.
    """
    exp_code = kwargs.get('experiment_code', None)
    if exp_code:
        del kwargs['experiment_code']
    experiment_info = dict(code=exp_code)
    exp_info = kwargs.get('experiment_info', None)
    if exp_info:
        del kwargs['experiment_info']

        for k, v in exp_info.items():
            if k in ['code', 'title', 'description', 'version']:
                experiment_info[k] = u"{}".format(v)

    sess_code = kwargs.get('session_code', None)
    if sess_code:
        del kwargs['session_code']
    elif experiment_info.get('code'):
        # this means we should auto_generate a session code
        import datetime
        sess_code = u"S_{0}".format(
            datetime.datetime.now().strftime('%d_%m_%Y_%H_%M'))

    session_info = dict(code=sess_code)
    sess_info = kwargs.get('session_info', None)
    if sess_info:
        del kwargs['session_info']

        for k, v in sess_info.items():
            if k in ['code', 'name', 'comments']:
                session_info[k] = u"{}".format(v)
            elif k == 'user_variables':
                session_info[k] = v

    monitor_name = kwargs.get('psychopy_monitor_name', None)
    if monitor_name:
        del kwargs['psychopy_monitor_name']

    datastore_name = None
    if _DATA_STORE_AVAILABLE is True:
        datastore_name = kwargs.get('datastore_name', None)
        if datastore_name is not None:
            del kwargs['datastore_name']
        else:
            datastore_name = None

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
    if monitor_devices_config:
        iohub_config = dict(monitor_devices=monitor_devices_config)
    else:
        device_dict = kwargs
        device_list = []

        # >>>> TODO: WTF is this for .... ?????
        def isFunction(func):
            import types
            return isinstance(func, types.FunctionType)

        def func2str(func):
            return '%s.%s' % (func.__module__, func.__name__)

        def configfuncs2str(config):
            for k, v in config.items():
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

        # Add remaining defined devices to the device list.
        for class_name, device_config in device_dict.iteritems():
            #TODO: Check that class_name is valid before adding to list
            device_list.append({class_name: device_config})

        # Create an ioHub configuration dictionary.
        iohub_config = dict(monitor_devices=device_list)

    if _DATA_STORE_AVAILABLE is True and experiment_info.get(
            'code') and session_info.get('code'):
        # If datastore_name kwarg or experiment code has been provided,
        # then enable saving of device events to the iohub datastore hdf5 file.
        # If datastore_name kwarg was provided, it is used for the hdf5 file
        # name, otherwise the experiment code is used. This avoids different
        # experiments running in the same directory from using the same
        # hdf5 file name.
        if datastore_name is None:
            datastore_name = experiment_info.get('code')
        iohub_config['data_store'] = dict(enable=True,
                                          filename=datastore_name,
                                          experiment_info=experiment_info,
                                          session_info=session_info)

    return ioHubConnection(iohub_config)
