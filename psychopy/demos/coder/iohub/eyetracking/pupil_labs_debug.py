from psychopy import logging
from psychopy.core import getTime, wait, quit
from psychopy.iohub import launchHubServer
from psychopy.iohub.constants import EyeTrackerConstants

logging.console.setLevel(logging.DEBUG)

iohub_config = {
    "eyetracker.hw.pupil_labs.pupil_core.EyeTracker": {
        "name": "tracker",
        "runtime_settings": {
            "pupillometry_only": False,
            "surface_name": "psychopy_iohub_surface",
            "gaze_confidence_threshold": 0.6,
            "pupil_remote": {
                "ip_address": "127.0.0.1",
                "port": 50020,
                "timeout_ms": 1000.0,
            },
            "pupil_capture_recording": {"enabled": True},
        },
    }
}

io = launchHubServer(**iohub_config)

# Get the eye tracker device.
tracker = io.devices.tracker

# run eyetracker calibration
setup_result = tracker.runSetupProcedure()
if setup_result != EyeTrackerConstants.EYETRACKER_OK:
    logging.error(f"Calibration failed: {EyeTrackerConstants.getName(setup_result)}")
    io.quit()
    quit()


tracker.setConnectionState(True)

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
