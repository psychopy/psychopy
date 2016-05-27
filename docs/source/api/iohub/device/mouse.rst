.. _iohub_mouse:

.. module:: psychopy.iohub.devices.mouse

Mouse Device
===============

Demo Script:
+++++++++++++

 * psychopy\\demos\\coder\\iohub\\mouse.py 

Support Platforms:
+++++++++++++++++++

 * Windows 7 +
 * OS X 10.7 +
 * Linux 2.6 +
 
.. autoclass:: Mouse
    :exclude-members: addFilter
    :inherited-members:
    :member-order: bysource

Mouse Events
---------------

The Mouse device supports several different event types, all of which extend MouseInputEvent:

.. autoclass:: psychopy.iohub.devices.mouse.MouseInputEvent
    :members:
    :inherited-members:
    :show-inheritance:
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

MouseMove Event
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: psychopy.iohub.devices.mouse.MouseMoveEvent
    :members:
    :show-inheritance:    
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource
    
MouseDrag Event
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: psychopy.iohub.devices.mouse.MouseDragEvent
    :members:
    :show-inheritance: 
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource
    
MouseButtonPress Event
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: psychopy.iohub.devices.mouse.MouseButtonPressEvent
    :show-inheritance: 
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource
    
MouseButtonRelease Event
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: psychopy.iohub.devices.mouse.MouseButtonReleaseEvent
    :show-inheritance: 
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource
    
MouseMultiClick Event
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: psychopy.iohub.devices.mouse.MouseMultiClickEvent
    :show-inheritance: 
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource
    
MouseScroll Event
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: psychopy.iohub.devices.mouse.MouseScrollEvent
    :show-inheritance: 
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource
