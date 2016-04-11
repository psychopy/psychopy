.. _iohub_keyboard:

.. module:: psychopy.iohub.client.keyboard

Keyboard Device
===============

Demo Script:
+++++++++++++

 * psychopy\\demos\\coder\\iohub\\keyboard.py 

Support Platforms:
+++++++++++++++++++

 * Windows 7 +
 * OS X 10.7 +
 * Linux 2.6 +
 
.. autoclass:: Keyboard
    :exclude-members: getDeviceInterface, getIOHubDeviceClass, getName
	:members:
    :inherited-members:
    :member-order: bysource

Keyboard Events
---------------

The Keyboard device can return two types of events, which represent key press
and key release actions on the keyboard.

KeyboardPress Event
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: KeyboardPress
    :exclude-members: id, device, pressEventID
    :members:
    :inherited-members:
    :member-order: bysource

KeyboardRelease Event
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: KeyboardRelease
    :exclude-members: id, device
	:members:
    :inherited-members:
    :member-order: bysource

