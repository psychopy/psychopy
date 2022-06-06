#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple demo for recording a video from a camera.
"""

import psychopy
import psychopy.core as core
from psychopy.hardware.camera import Camera
from psychopy.sound.microphone import Microphone

mic = Microphone(Microphone.getDevices()[0])

# Open a camera
webcam = Camera(0, mic=mic)
webcam.open()

webcam.record()  # start recording frames

# record for (close to) 5 seconds
while webcam.recordingTime < 5.0:
    print(webcam.getVideoFrame())  # get video frame data, print it

webcam.stop()  # stop the webcam recording

# webcam.save('myVideo.mp4')  # uncomment to save the file, just specify the path

webcam.close()  # close the webcam stream
core.quit()
