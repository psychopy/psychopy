.. _iohub_keyboard:

.. module:: psychopy.iohub.client.keyboard

Keyboard Device
===============

The iohub Keyboard device provides methods to:
  * Check for any new keyboard events that have occurred since the last time
    keyboard events were checked or cleared.
  * Wait until a keyboard event occurs.
  * Clear the device of any unread events.
  * Get a list of all currently pressed keys.

.. autoclass:: Keyboard
    :exclude-members: getDeviceInterface, getIOHubDeviceClass, getName, _syncDeviceState
    :members:
    :inherited-members:

Keyboard Events
---------------

The Keyboard device can return two types of events, which represent key press
and key release actions on the keyboard.

KeyboardPress Event
~~~~~~~~~~~~~~~~~~~

.. autoclass:: KeyboardPress
    :exclude-members: id
    :members:
    :inherited-members:
    :member-order: bysource

KeyboardRelease Event
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: KeyboardRelease
    :exclude-members: id
    :members:
    :inherited-members:
    :member-order: bysource

