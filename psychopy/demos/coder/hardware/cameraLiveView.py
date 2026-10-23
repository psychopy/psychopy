"""Show a live camera feed in an ImageStim.

Press escape to exit. This file is public domain.

"""
from psychopy import visual, core, event
from psychopy.hardware.camera import Camera

# open a window
win = visual.Window(size=(800, 600), units='pix', color='black',
                    fullscr=False, allowGUI=True, title='Camera feed')

# open a camera
cam = Camera(device=0,  # change this value to change the camera
             win=win, 
             usageMode='cv')  # use 'cv' mode if not recording to disk
cam.open()
print("camera open: %s @ %s fps" % (cam.frameSize, cam.frameRate))

# create an ImageStim to display the camera feed
camView = visual.ImageStim(win, image=cam, size=cam.frameSize, units='pix')

# instruction text
instr = visual.TextStim(win, text="Press escape to exit.", pos=(0, -280), color='white')

# enter the main loop to display the camera feed
shots = []
while event.getKeys(keyList=['escape']) == []:
    camView.draw()
    instr.draw()
    win.flip()

# clean up and close the camera and window
cam.close()
win.close()
core.quit()
