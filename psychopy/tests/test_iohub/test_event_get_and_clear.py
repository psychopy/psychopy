""" Test getting events (experiment events only) and clearing event logic
    for 'global' and 'device' level event buffers.
"""
import pytest
from psychopy.tests.utils import skip_under_travis
from psychopy.tests.test_iohub.testutil import startHubProcess, stopHubProcess, getTime

from psychopy.iohub.client import ioHubConnection

def setup():
    startHubProcess()

def teardown():
    stopHubProcess()
        
@skip_under_travis
def testGetEvents():
    """
    """
    io = ioHubConnection.getActiveConnection()

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
    
    # Test with device_label kwarg, which should function the same as if
    # device.getEvents() was called at the device level.
    
    io.sendMessageEvent("Test Message 2")

    kb_events = io.getEvents(device_label='keyboard')
    exp_events = io.getEvents(device_label='experiment')

    assert len(kb_events) == 0
    assert len(exp_events) == 1
    
    evts = io.getEvents()
    assert len(evts) == 1
    evt = evts[0]
    assert hasattr(evt, 'text') and evt.text == "Test Message 2"

    # Test with as_type kwarg at both global and device levels
    io.sendMessageEvent("Test Message 3")
    evts = io.getEvents(as_type='dict')
    assert len(evts) == 1
    evt = evts[0]
    assert isinstance(evt, dict)
    assert evt['text'] == "Test Message 3"
    evts = exp.getEvents(as_type='dict')
    assert len(evts) == 1
    evt = evts[0]
    assert isinstance(evt, dict)
    assert evt['text'] == "Test Message 3"

    io.sendMessageEvent("Test Message 4")
    evts = io.getEvents(as_type='list')
    assert len(evts) == 1
    evt = evts[0]
    assert isinstance(evt, (list, tuple))
    evts = exp.getEvents(as_type='list')
    assert len(evts) == 1
    evt = evts[0]
    assert isinstance(evt, (list, tuple))
    
    io.sendMessageEvent("Test Message 5")
    evts = io.getEvents(as_type='object')
    assert len(evts) == 1
    evt = evts[0]
    assert 'MessageEvent' == evt.__class__.__name__, "Event class is: {}".format(evt.__class__.__name__)
    evts = exp.getEvents(as_type='object')
    assert len(evts) == 1
    evt = evts[0]
    assert 'MessageEvent' == evt.__class__.__name__, "Event class is: {}".format(evt.__class__.__name__)
      
@skip_under_travis
def testGlobalBufferOnlyClear():
    """
    """
    io = ioHubConnection.getActiveConnection()

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


@skip_under_travis
def testDeviceBufferOnlyClear():
    """
    """
    io = ioHubConnection.getActiveConnection()

    exp = io.devices.experiment
    assert exp != None

    io.sendMessageEvent("Message Should Be Cleared Device Level Only")
    exp.clearEvents()
    events = io.getEvents()
    assert len(events) == 1
    assert events[0].text == "Message Should Be Cleared Device Level Only"
    exp_events = exp.getEvents()
    assert len(exp_events) == 0

@skip_under_travis
def testAllBuffersClear():
    """
    """
    io = ioHubConnection.getActiveConnection()

    exp = io.devices.experiment
    assert exp != None

    io.sendMessageEvent("Message Should Be Cleared Everywhere")
    io.clearEvents('all')
    events = io.getEvents()
    assert len(events) == 0
    exp_events = exp.getEvents()
    assert len(exp_events) == 0
