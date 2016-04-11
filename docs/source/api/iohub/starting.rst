.. _starting_iohub:

.. module:: psychopy.iohub.client

Using ioHub 
===========

To use ioHub within a PsychoPy experiment script, the ioHub process must
be started. This is usually done near the begininning of the experiment script
by calling the :func:`psychopy.iohub.client.launchHubServer` function:

.. autofunction:: launchHubServer

ioHubConnection Class
--------------------------

The psychopy.iohub.ioHubConnection object returned from
:func:`psychopy.iohub.client.launchHubServer` provides 
methods for controlling the iohub process and accessing 
ioHub devices and events.

.. autoclass:: ioHubConnection
    :exclude-members: eventListToObject, eventListToDict, eventListToNamedTuple, addDeviceToMonitor, getHubServerConfig, getExperimentID, getExperimentMetaData, getSessionMetaData, initializeConditionVariableTable, addRowToConditionVariableTable, registerWindowHandles, unregisterWindowHandles, wait
    :members:
    :member-order: bysource

