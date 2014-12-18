""" Test starting and stopping iohub server
"""
import pytest
from psychopy.tests.utils import skip_under_travis
from psychopy.tests.test_iohub.testutil import startHubProcess, stopHubProcess, getTime

@skip_under_travis
def testDefaultServerLaunch():
    """
    """
    io = startHubProcess()

    # check that a kb and mouse have been created
    keyboard=io.devices.keyboard
    mouse=io.devices.mouse
    exp = io.devices.experiment
    assert keyboard != None
    assert mouse != None
    assert exp != None

    stopHubProcess()

