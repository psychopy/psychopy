""" Test getting events (experiment events only) and clearing event logic
    for 'global' and 'device' level event buffers.
"""
import pytest
from psychopy.tests.utils import skip_under_travis
from psychopy.tests.test_iohub.testutil import startHubProcess, stopHubProcess, getTime

@skip_under_travis
def testGetEvents():
    """
    """
    io = startHubProcess()

    exp = io.devices.experiment
    assert exp != None

    io.sendMessageEvent("Test Message 1")
    io.sendMessageEvent("Category Test", category="TEST")
    ctime = getTime()
    io.sendMessageEvent("Time Test",sec_time=ctime)

    events = io.getEvents()

    event_count = len(events)
    assert event_count == 3

    m1, m2, m3 = events
    assert m1.text == "Test Message 1"
    assert m2.text == "Category Test" and m2.category == "TEST"
    assert m3.text == "Time Test" and m3.category == "" and m3.time == ctime

    assert len(io.getEvents()) == 0

    assert len(exp.getEvents()) == 3

    assert len(exp.getEvents()) == 0

    stopHubProcess()

@skip_under_travis
def testGlobalBufferOnlyClear():
    """
    """
    io = startHubProcess()

    exp = io.devices.experiment
    assert exp != None
    io.sendMessageEvent("Message Should Be Cleared Global Only")
    # clear only the global event buffer
    io.clearEvents(device_label=None)
    events = io.getEvents()
    assert len(events) == 0
    exp_events = exp.getEvents()
    assert len(exp_events) == 1
    assert exp_events[0].text == "Message Should Be Cleared Global Only"

    stopHubProcess()

@skip_under_travis
def testDeviceBufferOnlyClear():
    """
    """
    io = startHubProcess()

    exp = io.devices.experiment
    assert exp != None

    io.sendMessageEvent("Message Should Be Cleared Device Level Only")
    exp.clearEvents()
    events = io.getEvents()
    assert len(events) == 1
    assert events[0].text == "Message Should Be Cleared Device Level Only"
    exp_events = exp.getEvents()
    assert len(exp_events) == 0

    stopHubProcess()

@skip_under_travis
def testAllBuffersClear():
    """
    """
    io = startHubProcess()

    exp = io.devices.experiment
    assert exp != None

    io.sendMessageEvent("Message Should Be Cleared Everywhere")
    io.clearEvents('all')
    events = io.getEvents()
    assert len(events) == 0
    exp_events = exp.getEvents()
    assert len(exp_events) == 0

    stopHubProcess()
