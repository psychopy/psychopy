#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testing the iohub.launchHubServer function
illustrating the different ways it can be used.

No PsychoPy Window is created for this demo; results are
printed to stdout.

Initial Version: May 6th, 2013, Sol Simpson
"""

from psychopy.iohub import launchHubServer

def testWithNoKwargs():
    """
    testWithNoKwargs illustrates using the launchHubServer function with no
    parameters at all. Considerations:
        * A Keyboard, Mouse, Monitor, and Experiment device are created by default.
        * All devices use their default parameter settings. Therefore,
          not very useful in real studies.
        * ioHub DataStore is not enabled.
    """
    io = launchHubServer()

    # Get the default keyboard device created.
    keyboard = io.devices.keyboard

    print()
    print(" ** PRESS A KEY TO CONTINUE.....")

    # Check for new events every 1/4 second.
    # By using the io.wait() function, the ioHub Process is checked for
    # events every 50 msec or so, and they are cached in the PsychoPy process
    # until the next getEvents() call is made. On Windows, messagePump() is also
    # called periodically so that any Window you have created does not lock up.
    #
    while not keyboard.getEvents():
        io.wait(0.25)

    print("A Keyboard Event was Detected; exiting Test.")

    io.quit()

def testUsingPsychoPyMonitorConfig():
    """
    testUsingPsychoPyMonitorConfig illustrates using the launchHubServer function
    and providing a PsychoPy monitor configuration file name.
    Considerations:
        * A Keyboard, Mouse, Monitor, and Experiment device are created by default.
        * If the psychopy_monitor_name is valid, the ioHub Display is updated to
          use the display size and viewing distance specified in the psychopy monitor config.
        * ioHub DataStore is not enabled.
    """

    io = launchHubServer(psychopy_monitor_name='testMonitor')

    # Get the default display device created.
    display = io.devices.display

    # print(the display's physical characteristics, showing they have
    # been updated based on the settings in the PsychoPy monitor config.
    print('Display Psychopy Monitor Name: ', display.getPsychopyMonitorName())
    print('Display Default Eye Distance: ', display.getDefaultEyeDistance())
    print('Display Physical Dimensions: ', display.getPhysicalDimensions())

    # That's it, shut down the ioHub Process and exit. ;)
    io.quit()

def testEnabledDataStore():
        """
        testEnabledDataStore is the same as testUsingPsychoPyMonitorConfig above,
        but by adding an experiment_code parameter the ioHub DataStore will
        be enabled, using a auto generated session_code each time it is run.
        Experiment and session metadata is printed at the end of the demo.
        Considerations:
            * A Keyboard, Mouse, Monitor, and Experiment device are created by default.
            * If the psychopy_monitor_name is valid, the ioHub Display is updated to
              use the display size and viewing distance specified in the psychopy monitor config.
            * ioHub DataStore is enabled because experiment_code is provided.
              session_code will be auto generated using the current time.
        """
        psychopy_mon_name = 'testMonitor'
        exp_code = 'gap_endo_que'
        io = launchHubServer(psychopy_monitor_name=psychopy_mon_name,
                             experiment_code=exp_code)

        display = io.devices.display

        print('Display Psychopy Monitor Name: ', display.getPsychopyMonitorName())
        print('Display Default Eye Distance: ', display.getDefaultEyeDistance())
        print('Display Physical Dimensions: ', display.getPhysicalDimensions())

        from pprint import pprint

        print('Experiment Metadata: ')
        pprint(io.getExperimentMetaData())
        print('\nSession Metadata: ')
        pprint(io.getSessionMetaData())

        io.quit()

def testEnabledDataStoreAutoSessionCode():
        """
        testEnabledDataStoreAutoSessionCode is the same as testEnabledDataStore
        above, but session_code is provided by the script instead of being
        auto-generated. The ioHub DataStore will be enabled, using the
        experiment and session_code provided each time it is run. Experiment
        and session metadata is printed at the end of the demo.

        Considerations:
            * A Keyboard, Mouse, Monitor, and Experiment device are created by
              default.
            * If the psychopy_monitor_name is valid, the ioHub Display is
              updated to use the display size and viewing distance specified
              in the psychopy monitor config.
            * ioHub DataStore is enabled because experiment_code and
              session_code are provided.
        """
        import time
        from pprint import pprint

        psychopy_mon_name = 'testMonitor'
        exp_code = 'gap_endo_que'
        sess_code = 'S_{0}'.format(int(time.mktime(time.localtime())))
        print('Current Session Code will be: ', sess_code)

        io = launchHubServer(psychopy_monitor_name=psychopy_mon_name,
                             experiment_code=exp_code,
                             session_code=sess_code)

        display = io.devices.display

        print('Display Psychopy Monitor Name: ', display.getPsychopyMonitorName())
        print('Display Default Eye Distance: ', display.getDefaultEyeDistance())
        print('Display Physical Dimensions: ', display.getPhysicalDimensions())

        print('Experiment Metadata: ')
        pprint(io.getExperimentMetaData())
        print('\nSession Metadata: ')
        pprint(io.getSessionMetaData())

        io.quit()

test_list = ['testWithNoKwargs', 'testUsingPsychoPyMonitorConfig',
             'testEnabledDataStore', 'testEnabledDataStoreAutoSessionCode']

if __name__ == '__main__':
    for test in test_list:
        print('\n------------------------------------\n')
        print('Running %s Test:'%(test))

        for namespace in (locals(), globals()):
            if test in namespace:
               result = namespace[test]()
               print('Test Result: ', result)
               break

# The contents of this file are in the public domain.
