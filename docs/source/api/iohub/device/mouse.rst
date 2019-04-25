.. _iohub_mouse:

########################
The ioHub Mouse Device
########################

**Platforms:** Windows, macOS, Linux

.. currentmodule:  psychopy.iohub.devices.mouse
.. autoclass:: psychopy.iohub.devices.mouse.Mouse
    :members: getPosition, setPosition, getEvents, clearEvents, getPositionAndDelta, getScroll, setScroll
    :member-order: bysource

Mouse Event Types
#####################

.. currentmodule:  psychopy.iohub.devices.mouse
.. autoclass:: psychopy.iohub.devices.mouse.MouseInputEvent
    :members:
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

.. currentmodule:  psychopy.iohub.devices.mouse
.. autoclass:: psychopy.iohub.devices.mouse.MouseMoveEvent
    
    .. autoattribute:: display_id
    
.. currentmodule:  psychopy.iohub.devices.mouse
.. autoclass:: psychopy.iohub.devices.mouse.MouseDragEvent
    :members:
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

.. autoclass:: psychopy.iohub.devices.mouse.MouseButtonPressEvent
    :members:
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

.. autoclass:: psychopy.iohub.devices.mouse.MouseButtonReleaseEvent
    :members:
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

.. autoclass:: psychopy.iohub.devices.mouse.MouseMultiClickEvent
    :members:
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

.. autoclass:: psychopy.iohub.devices.mouse.MouseScrollEvent
    :members:
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource