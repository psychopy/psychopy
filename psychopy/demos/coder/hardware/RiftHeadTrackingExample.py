# Oculus Rift head-mounted display example for rendering 3D with head tracking.
# Press the 'q' key or use the application GUI to exit. Press 'r' to recenter
# the HMD's view. Requires PsychXR 0.2+ to be installed.
#
# This file is public domain.
#
from psychopy import visual, event, core
from psychopy.tools import arraytools, rifttools
import pyglet.gl as GL

# Create a VR session, treat the returned object just like a regular window.
# Increase the number of samples for anti-aliasing, could be 2, 4, 6, 8, 16 or
# 32 depending on your hardware. The GLFW backend is preferred when using VR.
hmd = visual.Rift(samples=1, color=(0, 0, 0), colorSpace='rgb', winType='glfw')

# Create a LibOVRPose object to represent the rigid body pose of the triangle in
# the scene. The position of the triangle will be 2 meters away from the user at
# eye height which we obtain from the HMD's settings.
trianglePosition = (0., hmd.eyeHeight, -2.)
trianglePose = rifttools.LibOVRPose(trianglePosition)

# convert the pose to a view transformation matrix
translationMatrix = trianglePose.getModelMatrix()

# convert to format Pyglet's GL libraries accept
translationMatrix = arraytools.array2pointer(translationMatrix)

# uncomment the line below to show a performance HUD
# hmd.perfHudMode('PerfSummary')

# loop until the user quits the app through the GUI menu
stopApp = False
while not stopApp:
    # Get the current tracking state for the HMD which contains lots of
    # information about the current pose and dynamics of the user's head and
    # hands, however we are only interested in head pose for now.
    trackingState = hmd.getTrackingState()
    headPose = trackingState.headPose.thePose

    # Calculate the eye poses from the current head pose, must be done before
    # drawing anything or else the application hangs.
    hmd.calcEyePoses(headPose)

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
        # yaw, pitch, roll = [math.degrees(i) for i in headPose.getYawPitchRoll()]
        # print(yaw, pitch, roll)

        # You can get the position of the HMD in the scene as follows,
        # x, y, z = headPose.pos
        # print(x, y, z)

        # use OpenGL rendering commands here...
        GL.glPushMatrix()
        GL.glMultTransposeMatrixf(translationMatrix)
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

# turn off the hud
# hmd.perfHudMode('Off')

# cleanly end the session
hmd.close()
core.quit()
