#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Demonstrate sending flip-synchronized events to EGI NetStation.

Install ``psychopy-egi-pynetstation`` from PsychoPy's Plugin/packages manager
before running this example. Change the network addresses below to match the
NetStation host and amplifier NTP server used by your lab.
"""

from psychopy import core, visual
from psychopy_egi_pynetstation import EGINetStation


NETSTATION_IP = "10.10.10.42"
AMPLIFIER_NTP_IP = "10.10.10.51"
ECI_PORT = 55513


win = visual.Window(fullscr=True, screen=0, color="black", units="height")
fixation = visual.TextStim(win, text="+", color="white", height=0.08)

ns = EGINetStation(
    ip=NETSTATION_IP,
    ntpIP=AMPLIFIER_NTP_IP,
    port=ECI_PORT,
)

try:
    ns.connect()
    ns.beginRecording()

    for trial in range(10):
        fixation.draw()

        # Timestamp the event on the flip which presents the stimulus. Sending
        # is asynchronous, so this callback does not block the display refresh.
        win.callOnFlip(
            ns.sendEvent,
            eventType="stim",  # NetStation event types are exactly 4 characters
            label="fixation",
            duration=0.1,
            data={"trl_": trial},  # data keys are also exactly 4 characters
        )
        win.flip()
        core.wait(0.5)

        win.flip()
        core.wait(1.0)
finally:
    # Stops an active recording, flushes queued events, and disconnects.
    ns.close()
    win.close()


# The contents of this file are in the public domain.
