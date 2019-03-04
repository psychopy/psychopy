# Minimal Oculus Rift head-mounted display example. Press the 'q' key or use
# the application GUI to exit. Requires PsychXR to be installed.
#
# This file is public domain.
#
from psychopy import visual, event, core  # visual imported, even if not used!

# Create a VR session, treat the returned object just like a regular window.
#
hmd = visual.Rift()

# loop until the user quits the app through the GUI menu
stopApp = False
while not stopApp:
    for i in ('left', 'right'):
        hmd.setBuffer(i)  # select the eye buffer to draw to

        # Setup the viewing parameters for the current buffer, this needs to be
        # called every time the buffer changes.
        #
        # For standard PsychoPy stimuli (e.g. GratingStim, ImageStim, etc.) you
        # should use 'setDefaultView' with 'mono=True' when creating a
        # visual.Rift instance. This configures the headset to properly render
        # 2D stimuli, treating the HMD as a monitor.
        #
        hmd.setDefaultView()

    # send the rendered buffer to the HMD
    hmd.flip()

    # check if the application should exit
    if event.getKeys('q') or hmd.shouldQuit:
        stopApp = True

# cleanly end the session
core.quit()
