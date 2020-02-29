# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, absolute_import
from __future__ import print_function

import os
import sys
from collections import deque
from past.builtins import unicode

try:
    import psychopy.logging as psycho_logging
    from psychopy.gui.qtgui import warnDlg
except ImportError:
    psycho_logging = None

from . import ioHubConnection
from ..util import yload, ydump, yLoader, yDumper
from ..errors import printExceptionDetailsToStdErr
from ..devices import Computer


######################## ioHubExperimentRuntime ##########################
# pylint: disable=line-too-long
# pylint: disable=superfluous-parens
# pylint: disable=no-self-use
# pylint: disable=global-statement
# pylint: disable=pointless-string-statement
# pylint: disable=protected-access
# pylint: disable=broad-except
# pylint: disable=fixme
# pylink: disable=unused-variable
# pylink: disable=too-many-instance-attributes

class ioHubExperimentRuntime(object):
    # TODO: Deprecate. Standardize on using launchHubServer function.
    # Not going to correct this classes code format (pylint, pep8)
    # since it is on its way out..
    """The ioHubExperimentRuntime class brings together several aspects of the
    ioHub Event Monitoring Framework, making it simpler to define and manage
    experiments that use multiple ioHub Device types, particularly when using
    more complicated devices such as the Eye Tracker or Analog Input Device.

    Other benefits of using the ioHubExperimentRuntime class include:

    * Automatic creation of an ioHubConnection instance with configuration of devices based on the associated Device Configuration Files.
    * Access to the ioHubConnection instance, all created ioHub Devices, and the ioHub Computer Device interface via two class attributes of the ioHubExperimentRuntime.
    * Optional support for the presentation of an Experiment Information Dialog at the start of each experiment session, based on the experiment settings specified in one of the associated configuration files.
    * Optional support for the presentation of a Session Variable Input Dialog at the start of each experiment session, based on the session settings specified in one of the associated configuration files. This includes the ability to collect input for custom experimenter defined session level fields that is stored in the ioHub DataStore for later retrieval and association with the event data collected during the experiment session.
    * Runtime access to the experiment, session, and device level configuration settings being used by the experiment in the form of python dictionary objects.
    * Automatic closure of the ioHub Process and the PsychoPy Process at the end of the experiment session, even when an unhandled exception occurs within your experiment scripting.

    The ioHubExperimentRuntime class is used to define the main Python script that
    will be run during each session of the experiment being run. In addition
    to the Python file containing the ioHubExperimentRuntime class extension,
    two configuration files are created:

    #. experiment_config.yaml : This file contains configuration details about the experiment itself, the experiment sessions that will be run to collect data from each participant of the experiment, and allows for process affinities to be set for the Experiment Process, ioHub Process, as well as all other processing on the computer. For details on defining an experiment_config.yaml file for use with the ioHubExperimentRuntime class, please see the Configuration Files section of the documentation.
    #. iohub_config.yaml : This file contains configuration details about each device that is being used by the experiment, as well as the ioHub DataStore. For details on defining an iohub_config.yaml file for use with the ioHubExperimentRuntime class, please see the Configuration Files section of the documentation.

    By separating experiment and session meta data definitions, as well as device
    configuration details, from the experiment paradigm logic contained within the
    ioHubExperimentRuntime class extension created, the ioHub Event Framework
    makes it possible to modify or switch between different implementations of an
    ioHub Device Interface without having to modify the experiment program logic.
    This is currently most beneficial when using an Eye Tracker or Analog Input
    Device, as these Device Interfaces support more than one hardware implementation.

    Many of the example scripts provided with the ioHub distribution use the
    ioHubExperimentRuntime class and config.yaml configuration files. The second
    example used in the Quick Start section of the documentation also uses this
    approach. Please refer to these resources for examples of using the
    ioHubExperimentRuntime class when creating an ioHub enabled project.

    Finally, there is an example called *startingTemplate* in the top level ioHub
    examples folder that contains a Python file with the base ioHubExperimentRuntime
    class extension in it, along with the two necessary configuration files.
    This example project folder can be copied to a directory of your choosing and renamed.
    Simply add the experiment logic you need to the run() method in the run.py file
    of the project, modify the experiment_config.yaml file to reflect the details of
    your intended application or experiment paradigm, and modify the iohub_config.yaml
    ensuring the devices required by your program are defined as needed. Then run the
    project by launching the run.py script with a Python interpreter.

    """

    def __init__(self, configFilePath, configFile):

        #: The hub attribute is the ioHubConnection class instance
        #: created for the ioHubExperimentRuntime. When the custom script
        #: provided in ioHubExperimentRuntime.run() is called, .hub is already
        #: set to an active ioHubConnection instance.
        self.hub = None

        #: The devices attribute is a short cut to the ioHubConnection
        #: instance's .devices attribute. i.e. self.devices = self.hub.devices.
        #: A reference to the Computer class is also added to the devices
        #: attribute, so when using the ioHubConnection devices attribute,
        #: the ioHub Computer class can be accessed using self.devices.computer;
        #: It does not need to be imported by your script.
        self.devices = None

        self.configFilePath = configFilePath
        self.configFileName = configFile

        # load the experiment config settings from the experiment_config.yaml file.
        # The file must be in the same directory as the experiment script.
        self.configuration = yload(
            open(
                os.path.join(
                    self.configFilePath,
                    self.configFileName),
                u'r'),
            Loader=yLoader)

        import random
        random.seed(Computer.getTime() * 1000.123)
        randomInt = random.randint(1, 1000)
        self.experimentConfig = dict()
        self._experimentConfigKeys = [
            'title', 'code', 'version', 'description']
        self.experimentConfig.setdefault(
            'title', self.experimentConfig.get(
                'title', 'A Default Experiment Title'))
        self.experimentConfig.setdefault(
            'code', self.experimentConfig.get(
                'code', 'Def_Exp_Code'))
        self.experimentConfig.setdefault(
            'version', self.experimentConfig.get(
                'version', '0.0.0'))
        self.experimentConfig.setdefault(
            'description', self.experimentConfig.get(
                'description', 'A Default Experiment Description'))
#        self.experimentConfig.setdefault('total_sessions_to_run',self.experimentConfig.get('total_sessions_to_run',0))

        for key in self._experimentConfigKeys:
            if key in self.configuration:
                self.experimentConfig[key] = self.configuration[key]

        self.experimentSessionDefaults = self.configuration.get(
            'session_defaults', {})
        self.sessionUserVariables = self.experimentSessionDefaults.get(
            'user_variables', None)
        if self.sessionUserVariables is not None:
            del self.experimentSessionDefaults['user_variables']
        else:
            self.sessionUserVariables = {}

        # initialize the experiment object based on the configuration settings.
        self.hub = self._initalizeConfiguration()

        self.devices = self.hub.devices
        self.devices.computer = Computer

    def run(self, *sys_argv):
        """The run method must be overwritten by your subclass of
        ioHubExperimentRuntime, and would include the equivalent logic to what
        would be added to the main starting script in a procedural PsychoPy
        script.

        When the run method starts, the ioHub Server is online and any devices
        specified for the experiment are ready for use. When the contents of the run method
        allow the method to return or end, the experiment session is complete.

        Any sys_argv are equal to the sys.argv received by the script when it was started.

        Args:
            sys_argv (list): The list of arguments passed to the script when it was started with Python.

        Returns:
            User defined.

        """
        pass

    def getConfiguration(self):
        """Returns the full parsing of experiment_config.yaml as a python
        dictionary.

        Args:
            None

        Returns:
            dict: The python object representation of the contents of the experiment_config.yaml file loaded for the experiment.

        """
        return self.configuration

    def getExperimentMetaData(self):
        """
        Returns the experiment parameters saved to the ioHub DataStore experiment_metadata table.
        The values are actually only saved the first time the experiment is run.
        The variable names and values contained within the returned dict are also what
        would be presented at the experiment start in the read-only Experiment Information Dialog.

        Args:
            None

        Returns:
            dict: The python object representation of the experiment meta data, namely the experiment_code, title, version, and description fields.
        """
        if self.hub is not None:
            return self.hub.getExperimentMetaData()
        return self.experimentConfig

    def getSessionMetaData(self):
        """Returns the experiment session parameters saved to the ioHub
        DataStore for the current experiment session. These are the parameters
        defined in the session_defaults section of the experiment_config.yaml
        and are also optionally displayed in the Session Input Dialog at the
        start of each experiment session.

        Args:
            None

        Returns:
            dict: The python object representation of the session meta data saved to the ioHub DataStore for the current experiment run.

        """
        if self.hub is not None:
            return self.hub.getSessionMetaData()
        return self.experimentSessionDefaults

    def getUserDefinedParameters(self):
        """Return only the user defined session parameters defined in the
        experiment_config.yaml. These parameters are displayed in the Session
        Input Dialog (if enabled) and the value entered for each parameter is
        provide in the state of the returned dict. These parameters and values
        are also saved in the session meta data table of the ioHub DataStore.

        Args:
            None

        Returns:
            dict: The python object representation of the user defined session parameters saved to the ioHub DataStore for the current experiment run.

        """
        return self.sessionUserVariables

    def isSessionCodeInUse(self, current_sess_code):
        """Session codes must be unique within an experiment. This method will
        return True if the provided session code is already used in one of the
        existing experiment sessions saved to the ioHub DataStore. False is
        returned if the session code is not used, and would therefore make a
        valid session code for the current run.

        Args:
            current_sess_code (str): The string being requested to be used as the
            current experiment session code. maximum length is 24 characters.

        Returns:
            bool: True if the code given is already in use. False if it is not in use.

        """
        r = self.hub._sendToHubServer(
            ('RPC', 'checkIfSessionCodeExists', (current_sess_code,)))
        return r[2]

    def prePostExperimentVariableCallback(self, experiment_meta_data):
        """This method is called prior to the experiment meta data being sent
        to the ioHub DataStore to be saved as the details regarding the current
        experiment being run. Any changes made to the experiment_meta_data dict
        passed into the method will be reflected in the data values saved to
        the ioHub DataStore.

        Note that the same dict object that is passed into the method as an argument
        must be returned by the method as the result.

        Args:
            experiment_meta_data (dict): The state of the experiment meta data prior to being sent to the ioHub DataStore for storage.

        Returns:
            dict: The experiment_meta_data arg passed to the method.

        """
        return experiment_meta_data

    def prePostSessionVariableCallback(self, session_meta_data):
        """This method is called prior to the session meta data being sent to
        the ioHub DataStore to be saved as the details regarding the current
        session being run. Any changes made to the session_meta_data dict
        passed into the method will be reflected in the data values saved to
        the ioHub DataStore for the session.

        Note that the same dict object that is passed into the method as an argument
        must be returned by the method as the result.

        Args:
            session_meta_data (dict): The state of the session meta data prior to being sent to the ioHub DataStore for storage.

        Returns:
            dict: The session_meta_data arg passed to the method.

        """
        org_sess_code = session_meta_data.setdefault('code', 'default_sess')
        scount = 1
        sess_code = org_sess_code
        while self.isSessionCodeInUse(sess_code) is True:
            sess_code = '%s-%d' % (org_sess_code, scount)
            scount += 1
        session_meta_data['code'] = sess_code
        return session_meta_data

    @staticmethod
    def printExceptionDetails():
        """Prints out stack trace information for the last exception raised by
        the PsychoPy Process.

        Currently a lot of redundant data is printed regarding the exception and stack trace.

        TO DO: clean this up so there is not so much redundant info printed.

        Args:
            None

        Returns:
            None

        """
        import traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print('*** print_tb:')
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        print('*** print_exception:')
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                                  limit=2, file=sys.stdout)
        print('*** print_exc:')
        traceback.print_exc()
        print('*** format_exc, first and last line:')
        formatted_lines = traceback.format_exc().splitlines()
        print(formatted_lines[0])
        print(formatted_lines[-1])
        print('*** format_exception:')
        print(repr(traceback.format_exception(exc_type, exc_value,
                                              exc_traceback)))
        print('*** extract_tb:')
        print(repr(traceback.extract_tb(exc_traceback)))
        print('*** format_tb:')
        print(repr(traceback.format_tb(exc_traceback)))
        print(('*** tb_lineno:', exc_traceback.tb_lineno))

    @staticmethod
    def mergeConfigurationFiles(
            base_config_file_path,
            update_from_config_file_path,
            merged_save_to_path):
        """Merges two iohub configuration files into one and saves it to a file
        using the path/file name in merged_save_to_path."""
        base_config = yload(open(base_config_file_path, 'r'), Loader=yLoader)
        update_from_config = yload(
            open(
                update_from_config_file_path,
                'r'),
            Loader=yLoader)

        def merge(update, base):
            if isinstance(update, dict) and isinstance(base, dict):
                for k, v in base.items():
                    if k not in update:
                        update[k] = v
                    else:
                        if isinstance(update[k], list):
                            if isinstance(v, list):
                                v.extend(update[k])
                                update[k] = v
                            else:
                                update[k].insert(0, v)
                        else:
                            update[k] = merge(update[k], v)
            return update

        import copy
        merged = merge(copy.deepcopy(update_from_config), base_config)
        ydump(merged, open(merged_save_to_path, 'w'), Dumper=yDumper)

        return merged

    def _initalizeConfiguration(self):
        global _currentSessionInfo
        """
        Based on the configuration data in the experiment_config.yaml and iohub_config.yaml,
        configure the experiment environment and ioHub process environments. This mehtod is called by the class init
        and should not be called directly.
        """
        display_experiment_dialog = self.configuration.get(
            'display_experiment_dialog', False)
        display_session_dialog = self.configuration.get(
            'display_session_dialog', False)

        if display_experiment_dialog is True:
            # display a read only dialog verifying the experiment parameters
            # (based on the experiment .yaml file) to be run. User can hit OK to continue,
            # or Cancel to end the experiment session if the wrong experiment
            # was started.
            exitExperiment = self._displayExperimentSettingsDialog()
            if exitExperiment:
                print('User Cancelled Experiment Launch.')
                self._close()
                sys.exit(1)

        self.experimentConfig = self.prePostExperimentVariableCallback(
            self.experimentConfig)

        ioHubInfo = self.configuration.get('ioHub', {})

        if ioHubInfo is None:
            print('ioHub section of configuration file could not be found. Exiting.....')
            self._close()
            sys.exit(1)
        else:
            ioHubConfigFileName = unicode(
                ioHubInfo.get('config', 'iohub_config.yaml'))
            ioHubConfigAbsPath = os.path.join(
                self.configFilePath, unicode(ioHubConfigFileName))
            self.hub = ioHubConnection(None, ioHubConfigAbsPath)

            # print 'ioHubExperimentRuntime.hub: {0}'.format(self.hub)
            # A circular buffer used to hold events retrieved from self.getEvents() during
            # self.delay() calls. self.getEvents() appends any events in the allEvents
            # buffer to the result of the hub.getEvents() call that is made.
            self.hub.allEvents = deque(
                maxlen=self.configuration.get(
                    'event_buffer_length', 256))

            # print 'ioHubExperimentRuntime sending experiment config.....'
            # send experiment info and set exp. id
            self.hub._sendExperimentInfo(self.experimentConfig)

            # print 'ioHubExperimentRuntime SENT experiment config.'

            allSessionDialogVariables = dict(
                self.experimentSessionDefaults,
                **self.sessionUserVariables)
            sessionVariableOrder = self.configuration.get(
                'session_variable_order', [])
            if 'user_variables' in allSessionDialogVariables:
                del allSessionDialogVariables['user_variables']

            if display_session_dialog is True:
                # display session dialog
                r = True
                while r is True:
                    # display editable session variable dialog displaying the ioHub required session variables
                    # and any user defined session variables (as specified in the experiment config .yaml file)
                    # User can enter correct values and hit OK to continue, or
                    # Cancel to end the experiment session.

                    allSessionDialogVariables = dict(
                        self.experimentSessionDefaults, **self.sessionUserVariables)
                    sessionVariableOrder = self.configuration.get(
                        'session_variable_order', [])
                    if 'user_variables' in allSessionDialogVariables:
                        del allSessionDialogVariables['user_variables']

                    tempdict = self._displayExperimentSessionSettingsDialog(
                        allSessionDialogVariables, sessionVariableOrder)
                    if tempdict is None:
                        print('User Cancelled Experiment Launch.')
                        self._close()
                        sys.exit(1)

                    tempdict['user_variables'] = self.sessionUserVariables

                    r = self.isSessionCodeInUse(tempdict['code'])

                    if r is True:
                        display_device = self.hub.getDevice('display')
                        display_id = 0
                        if display_device:
                            display_id = display_device.getIndex()
                        msg_dialog = warnDlg('Session Code In Use',
                                             'Session Code {0} is already in '
                                             'use by the experiment.\nPlease '
                                             'enter a new Session '
                                             'Code'.format(tempdict['code']))
                        msg_dialog.show()
            else:
                tempdict = allSessionDialogVariables
                tempdict['user_variables'] = self.sessionUserVariables

            for key, value in allSessionDialogVariables.items():
                if key in self.experimentSessionDefaults:
                    # (u''+value).encode('utf-8')
                    self.experimentSessionDefaults[key] = value
                elif key in self.sessionUserVariables:
                    # (u''+value).encode('utf-8')
                    self.sessionUserVariables[key] = value

            tempdict = self.prePostSessionVariableCallback(tempdict)
            tempdict['user_variables'] = self.sessionUserVariables

            _currentSessionInfo = self.experimentSessionDefaults

            self.hub._sendSessionInfo(tempdict)

            self._setInitialProcessAffinities(ioHubInfo)

            return self.hub

    def _setInitialProcessAffinities(self, ioHubInfo):
            # set process affinities based on config file settings
        cpus = range(Computer.processing_unit_count)
        experiment_process_affinity = cpus
        other_process_affinity = cpus
        iohub_process_affinity = cpus

        experiment_process_affinity = self.configuration.get(
            'process_affinity', [])
        if len(experiment_process_affinity) == 0:
            experiment_process_affinity = cpus

        other_process_affinity = self.configuration.get(
            'remaining_processes_affinity', [])
        if len(other_process_affinity) == 0:
            other_process_affinity = cpus

        iohub_process_affinity = ioHubInfo.get('process_affinity', [])
        if len(iohub_process_affinity) == 0:
            iohub_process_affinity = cpus

        if len(experiment_process_affinity) < len(
                cpus) and len(iohub_process_affinity) < len(cpus):
            Computer.setProcessAffinities(
                experiment_process_affinity,
                iohub_process_affinity)

        if len(other_process_affinity) < len(cpus):
            ignore = [Computer.currentProcessID, Computer.iohub_process_id]
            Computer.setAllOtherProcessesAffinity(
                other_process_affinity, ignore)

    def start(self, *sys_argv):
        """This method should be called from within a user script which as
        extended this class to start the ioHub Server. The run() method of the
        class, containing the user experiment logic, is then called. When the
        run() method completes, the ioHub Server is stopped and the program
        exits.

        Args: None
        Return: None

        """
        try:
            result = self.run(*sys_argv)
            self._close()
            return result
        except Exception:
            printExceptionDetailsToStdErr()
            self._close()

    def _displayExperimentSettingsDialog(self):
        """
        Display a read-only dialog showing the experiment setting retrieved from the configuration file. This gives the
        experiment operator a chance to ensure the correct configuration file was loaded for the script being run. If OK
        is selected in the dialog, the experiment logic continues, otherwise the experiment session is terminated.
        """
        # print 'self.experimentConfig:', self.experimentConfig
        # print 'self._experimentConfigKeys:',self._experimentConfigKeys
        result = True
        try:
            from psychopy import gui
            experimentDlg = gui.DlgFromDict(
                self.experimentConfig,
                'Experiment Launcher',
                self._experimentConfigKeys,
                self._experimentConfigKeys,
                {})
            if experimentDlg.OK:
                result = False
            else:
                result = True
        except ImportError:
            result = False
        return result

    def _displayExperimentSessionSettingsDialog(
            self, allSessionDialogVariables, sessionVariableOrder):
        """Display an editable dialog showing the experiment session setting
        retrieved from the configuration file.

        This includes the few mandatory ioHub experiment session
        attributes, as well as any user defined experiment session
        attributes that have been defined in the experiment
        configuration file. If OK is selected in the dialog, the
        experiment logic continues, otherwise the experiment session is
        terminated.

        """
        result = None
        try:
            from psychopy import gui
            sessionDlg = gui.DlgFromDict(
                allSessionDialogVariables,
                'Experiment Session Settings',
                [],
                sessionVariableOrder)
            if sessionDlg.OK:
                result = allSessionDialogVariables
        except ImportError:
            result = None
        return result

    def _close(self):
        """Close the experiment runtime and the ioHub server process."""
        # terminate the ioServer
        if self.hub:
            self.hub._shutDownServer()
        # terminate psychopy
        # core.quit()

    def __del__(self):
        try:
            if self.hub:
                self.hub._shutDownServer()
        except Exception:
            pass
        self.hub = None
        self.devices = None

# pylint: enable=line-too-long
# pylint: enable=superfluous-parens
# pylint: enable=no-self-use
# pylint: enable=global-statement
# pylint: enable=pointless-string-statement
# pylint: enable=protected-access
# pylint: enable=broad-except
# pylint: enable=fixme
# pylink: enable=unused-variable
# pylink: enable=too-many-instance-attributes
