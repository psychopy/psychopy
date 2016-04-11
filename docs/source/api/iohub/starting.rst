.. _starting_iohub:

.. module:: psychopy.iohub.client

Starting the psychopy.iohub Process
=====================================

To use ioHub within a PsychoPy experiment script, the ioHub process must
be started. This is usually done near the begininning of the experiment script
by calling the :func:`psychopy.iohub.client.launchHubServer` function:

.. autofunction:: launchHubServer

ioHubConnection Class
--------------------------

The psychopy.iohub.ioHubConnection object returned from the launchHubServer
function provides methods for controlling the iohub process and
accessing iohub devices and events.

.. autoclass:: ioHubConnection
    :exclude-members: addDeviceToMonitor, getHubServerConfig, getExperimentID, getExperimentMetaData, getSessionMetaData, initializeConditionVariableTable, addRowToConditionVariableTable, registerWindowHandles, unregisterWindowHandles, wait
    :members:
    :member-order: bysource

