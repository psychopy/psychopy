ioHub Release Notes DRAFT
=========================

Enhancements
-------------

- Added wintab device (Windows only)
- ioSync Device now supports generating keyboard events using
  iosync.generateKeyboardEvent() device method. Limitations exist.....
- launchHubServer() should now be able to replace iohubExpRuntime class

Bugs Fixed
-----------

- mouse.setPosition was not correctly setting y position
- fixed bug in iohubdelaytest demo that was stopping it from running.
- Analog Input implementation for Measurement Computing works on python 64bit
- coder\iohub\network demo was referencing non-existant KeyboardChar event type.

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


- Created iohub.removed module that will hold any modules completely removed
  from psychopy.iohub. This allows user scripts that rely on this
  code to just change import for the short term. User scripts must switch to 
  using alternatives ASAP since iohub.removed will be deleted in a
  future release.

- Removed psychopy.iohub.util.dialogs module. ioHub demo's and internal code
  now use psychopy.gui equivelents instead.
  (psychopy.iohub.util.dialogs -> psychopy.iohub.removed.util.dialogs)


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


