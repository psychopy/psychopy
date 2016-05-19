""" Test starting and stopping iohub server
"""
import pytest
from psychopy.tests.utils import skip_under_travis
from psychopy.tests.test_iohub.testutil import startHubProcess, stopHubProcess, getTime

@skip_under_travis
def testServerConnectionInstance():
    """
    """
    io = startHubProcess()

    # check that a kb and mouse have been created
    keyboard = io.devices.keyboard
    mouse = io.devices.mouse
    exp = io.devices.experiment
    assert keyboard is not None
    assert mouse is not None
    assert exp is not None

    assert io.getSessionID() is None
    assert io.getExperimentID() is None

    assert io.getExperimentMetaData() is None
    assert io.getSessionMetaData() is None

    assert isinstance(io.getHubServerConfig(), dict)
    stopHubProcess()


@skip_under_travis
def testKeyboardDeviceInstance():
    """
    """
    io = startHubProcess()

    # check that a kb 
    keyboard=io.devices.keyboard
    
    assert keyboard != None

    kb_name = keyboard.getName()
    assert kb_name == 'keyboard'
    
    kb_iohub_class = keyboard.getIOHubDeviceClass()
    assert kb_iohub_class == 'Keyboard', "keyboard.getIOHubDeviceClass() returned {} of type: {}".format(kb_iohub_class, type(kb_iohub_class))

    kb_iohub_methods = keyboard.getDeviceInterface()
    assert len(kb_iohub_methods) > 0
    assert 'getEvents' in kb_iohub_methods
    
    stopHubProcess()



