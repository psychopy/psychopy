#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple demo for recording a video from a camera and saving the result to
disk.
"""

import psychopy
import psychopy.core as core
from psychopy.hardware.camera import Camera
from psychopy.sound.microphone import Microphone

# Create a microphone instance for recording audio samples. This will be passed
# off the camera object and controlled by it for recording the audio track of
# the video. Here we just get the first available microphone.
microphones = Microphone.getDevices()
if microphones:
    mic = Microphone(microphones[0])
else:
    mic = None  # no audio if ot mic was found

# Create a new camera instance. Values for `size` and `frameRate` must be
# appropriate for the device in use.
cam = Camera(0, mic=mic, size=(544, 288), frameRate=30)

# Open a camera stream. This will remain open until `close()` ia called.
cam.open()

# Start recording frames to file. This needs to be called after opening the
# stream if you wish to save video frames.
cam.record()

# record for (close to) 5 seconds
while cam.recordingTime < 5.0:
    frame = cam.getVideoFrame()  # get video frame data
    # print the current time in the recording
    print('t={}s'.format(round(frame.absTime, 6)))

# Stop the camera recording. This must be called prior to saving the video to
# file. The webcam stream is still open at this point and record can be called
# again.
cam.stop()  # stop the webcam recording

# Save the video to disk by calling this method. Video recordings are lost if
# this is not called prior to calling `record` again.
cam.save('myVideo.mp4')  # uncomment to save the file, just specify the path

# Print the path to where the clip was saved, this allows you to pass the clip
# to a `MovieStim` object to view it afterwards if desired.
print(cam.lastClip)

# Close the camera stream. You must call this before exiting or when you're
# done with the camera.
cam.close()

core.quit()
