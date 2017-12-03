ioHub vx.x Release Notes
========================

Enhancements
-------------

- Added wintab device (Windows only)
- ioSync Device now supports generating keyboard events using
  iosync.generateKeyboardEvent() device method. Limitations exist.....
- launchHubServer() should now be able to replace iohubExpRuntime class
- other than 'data_store', launchHubServer supports updating
  psychopy/iohub/default_config.yaml settings by adding kwargs that match the
  files keys. For example, to set the iohub Server UDP port to a custom value:
     io = launchHubServer(udp_port=1234)
- launchHubServer builds the monitor_devices list by combining
  devices found using the 'iohub_config_name' kwarg with any devices defined
  in the function's kwarg dict itself.

DataStore Changes
-----------------

- Added 'multiple_sessions' config param to datastore section of iohub_config.
  * If True (Default), > 1 sessions / participants data can be saved to a
    single hdf5 file.
  * If False, current session data overwrites any existing data in the hdf5
    file.

Bugs Fixed
-----------

- mouse.setPosition was not correctly setting y position
- fixed bug in iohubdelaytest demo that was stopping it from running.
- Analog Input implementation for Measurement Computing works on python 64bit
- coder\iohub\network demo was referencing non-existent KeyboardChar event type.
- io.clearEvents() was not clearing any locally cached events in
  psychopy.io.client.Keyboard class.
  
User API Backwards Incompatibles
--------------------------------

iohub Package
~~~~~~~~~~~~~~

- Importing iohub submodules and classes is no longer all in the root iohub
    module. For example:

        from psychopy.iohub import launchHubServer, EventConstants

    becomes:

        from psychopy.iohub.client import launchHubServer
        from psychopy.iohub.constants import EventConstants

    TODO: Full list of new import paths


- Created iohub.removed module that holds any modules completely removed
  from psychopy.iohub. This allows user scripts that rely on this
  code to just change import for the short term. User scripts must switch to
  using alternatives ASAP since iohub.removed will be deleted in a
  future release.

- Added to psychopy.iohub.util:
    - saveConfig(...): Save python dict / list to a YAML file.
    - readConfig(...): Load a config dict from a YAML file path.

- Removed following modules from psychopy.iohub.util. All have been
  temporarily moved to psychopy.iohub.removed.xxxxxx:
    - dialogs module. ioHub demo's and internal code now use psychopy.gui
      equivalents instead.
    - images module. Was only used by util.dialogs.
    - visualUtil module. While useful functionality, out of scope for
      psychopy.iohub. If needed, file can be copied to same folder as user
      script and used.
    - targetpositionsequence module. While useful functionality, out of scope
      for psychopy.iohub. If needed, file can be copied to same folder as user
      script and used.

- ioHubExperimentRuntime class is no longer supported. Use
  psychopy.iohub.client.launchHubServer() instead.

- Removed psychopy.iohub.client.expruntime module.
 (psychopy.iohub.client.expruntime -> psychopy.iohub.removed.client.expruntime)

ioHubConnection Class
~~~~~~~~~~~~~~~~~~~~~~

Removed:
    - enableHighPriority(). Use setPriority('high') instead.
    - disableHighPriority().  Use setPriority('normal') instead.
    - enableRealTimePriority(). Use setPriority('realtime') instead.
    - disableRealTimePriority(). Use setPriority('normal') instead.
    - removed initializeConditionVariableTable(). Use
      createTrialHandlerRecordTable() instead.
    - removed addRowToConditionVariableTable(). Use addTrialHandlerRecord()
      instead.
    - removed .deviceByLabel[dev_name] dict. Use .getDevice(dev_name).

ioHubDevices Class
~~~~~~~~~~~~~~~~~~~

Added:
    - getAll(): returns a list of all enabled iohub devices
    - getNames(): returns a list with the name of each enabled iohub device
    - getDevice(name): returns the iohub device identified by 'name'. If no
      device with that name exists, None is returned.

ioHubDeviceView Class
~~~~~~~~~~~~~~~~~~~~~~

Removed:
    - setPreRemoteMethodCallFunction(). No replacement.
    - setPostRemoteMethodCallFunction(). No replacement.


Mouse Device
~~~~~~~~~~~~

Following methods have been removed. Use equivalent psychopy or pyglet
functionality instead:

    - lockMouseToDisplayID
    - getLockMouseToDisplayID
    - getSystemCursorVisibility
    - setSystemCursorVisibility

Computer Device
~~~~~~~~~~~~~~~~

- renamed .sysbits to .pybits
- renamed .system to .platform
- removed getProcessPriority and setProcessPriority, use get/setPriority().
- removed enableHighPriority(), use setPriority('high')
- removed enableRealTimePriority, use setPriority('realtime')
- removed disableRealTimePriority, use setPriority('normal')
- removed disableHighPriority, use setPriority('normal')
- removed currentTime(). Use getTime()
- removed currentSec(). Use getTime()

Internal API Changes
--------------------

- _getNextEventID() moved from iohub.devices.Computer to iohub.devices.Device
- When adding new Device and/or Event types, iohub.datastore module does not
  need to be changed. Adding new Device or Event types to iohub.constants.py
  is still required.

demos.coder.iohub Changes
-------------------------

- Moved eyetracker/validation.py to eyetracker/validation/run.py


