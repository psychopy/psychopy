# Oculus Rift head-mounted display example for rendering 3D with head tracking.
# Press the 'q' key or use the application GUI to exit. Press 'r' to recenter
# the HMD's view. Requires PsychXR to be installed.
#
# This file is public domain.
#
from psychopy import visual, event, core
from psychopy.tools.rifttools import *  # math types are accessed from here
import pyglet.gl as GL
import math

# Create a VR session, treat the returned object just like a regular window.
# Change headLocked to True to disable head tracking, increase the number of
# samples for anti-aliasing, could be 2, 4, 6, 8, 16 or 32 depending on your
# hardware.
hmd = visual.Rift(headLocked=False, samples=1)

# loop until the user quits the app through the GUI menu
stopApp = False
while not stopApp:
    for i in ('left', 'right'):
        hmd.setBuffer(i)  # select the eye buffer to draw to

        # Setup the viewing parameters for the current buffer, this needs to be
        # called every time the buffer changes.
        #
        # Use setRiftView to setup the projection and view matrices
        # automatically from data provided by the API. Take note of which eye
        # buffer is active when rendering.
        #
        hmd.setRiftView()

        # Get the yaw, pitch and roll angles of the HMD in radians, convert them
        # to degrees. This is just to demonstrate how to do so using PsychXR's
        # 3D types interface. For instance, hmd.headPose.rotation is a
        # Quaternion type with method "getYawPitchRoll".
        #
        yaw, pitch, roll = [math.degrees(i) for i in
                            hmd.headPose.rotation.getYawPitchRoll()]
        # print(yaw, pitch, roll)

        # You can get the position of the HMD in the scene as follows,
        x = hmd.headPose.translation.x
        y = hmd.headPose.translation.y
        z = hmd.headPose.translation.z
        # print(x, y, z)

        # use OpenGL rendering commands here...

        # Just draw a triangle 2 meters away. Let's use the ovrMatrix4f type to
        # handle the translation. You can do whatever you like to the position
        # every frame.
        #
        triangle_origin = ovrVector3f(0.0, 0.0, -2.0)
        M = ovrMatrix4f.translation(triangle_origin)

        GL.glPushMatrix()
        GL.glMultMatrixf(M.ctypes)  # multiply the scene by the matrix
        GL.glBegin(GL.GL_TRIANGLES)
        GL.glColor3f(1, 0, 0)
        GL.glVertex3f(-1.0, -1.0, 0.0)
        GL.glColor3f(0, 1, 0)
        GL.glVertex3f(1.0, -1.0, 0.0)
        GL.glColor3f(0, 0, 1)
        GL.glVertex3f(0.0, 1.0, 0.0)
        GL.glEnd()
        GL.glPopMatrix()

    # send the rendered buffer to the HMD
    hmd.flip()

    # check if the application should exit
    if event.getKeys('q') or hmd.shouldQuit:
        stopApp = True
    elif event.getKeys('r') or hmd.shouldRecenter:
        hmd.recenterTrackingOrigin()

# cleanly end the session
core.quit()
