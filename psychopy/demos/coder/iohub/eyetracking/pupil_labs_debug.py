from psychopy import logging
from psychopy.core import getTime, wait
from psychopy.iohub import launchHubServer

logging.console.setLevel(logging.DEBUG)

iohub_config = {
    "eyetracker.hw.pupil_labs.pupil_core.EyeTracker": {
        "name": "tracker",
        "runtime_settings": {"pupil_capture_recording": {"enabled": False}},
    }
}

io = launchHubServer(**iohub_config)

# Get the eye tracker device.
tracker = io.devices.tracker

# run eyetracker calibration
# r = tracker.runSetupProcedure()

tracker.setConnectionState(True)
tracker.enableEventReporting(True)

# Check for and print any eye tracker events received...
tracker.setRecordingState(True)

# B. Print all eye tracker events received for 2 seconds

stime = getTime()
while getTime() - stime < 10.0:
    events = tracker.getEvents()
    print("b", sum(1 for e in events))
    wait(0.5)

# # C. Print current eye position for 5 seconds

# # Check for and print current eye position every 100 msec.
# stime = getTime()
# while getTime() - stime < 5.0:
#     position = tracker.getPosition()
#     print("c", position)
#     wait(0.1)

tracker.setRecordingState(False)

# Stop the ioHub Server
io.quit()
