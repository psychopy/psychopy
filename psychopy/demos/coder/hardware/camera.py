#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple demo for recording a video from a camera.
"""

import psychopy
import psychopy.core as core
from psychopy.hardware.camera import Camera
import time

# Open a camera
webcam = Camera(0)
webcam.open()

webcam.record()  # start recording frames

# record for 5 seconds
while webcam.recordingTime < 5.0:
    time.sleep(0.05)  # sleep a bit

webcam.stop()  # stop the webcam recording
# webcam.save('myVideo.mp4')  # save the file
webcam.close()  # close the webcam stream
core.quit()
