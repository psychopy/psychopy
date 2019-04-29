.. _starting_iohub:

.. module:: psychopy.iohub.client

Starting the psychopy.iohub Process
=====================================

To use ioHub within your PsychoPy Coder experiment script, ioHub needs to
be started at the start of the experiment script. The easiest way to do this
is by calling the launchHubServer function.

launchHubServer function
--------------------------

.. autofunction:: launchHubServer

ioHubConnection Class
--------------------------

The psychopy.iohub.ioHubConnection object returned from the launchHubServer
function provides methods for controlling the iohub process and
accessing iohub devices and events.

.. autoclass:: ioHubConnection(object)
    :exclude-members: eventListToObject, eventListToDict, eventListToNamedTuple, _isErrorReply, _startServer, _createDeviceList, _addDeviceView, _sendToHubServer, _sendExperimentInfo, _sendSessionInfo, addDeviceToMonitor, getHubServerConfig, getExperimentID, getExperimentMetaData, getSessionMetaData, initializeConditionVariableTable, addRowToConditionVariableTable, registerWindowHandles, unregisterWindowHandles, wait
    :members:
    :member-order: bysource

