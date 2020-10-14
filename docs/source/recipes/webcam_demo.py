from __future__ import print_function

from psychopy import visual, event, core
import Image, time, pylab, cv, numpy

mywin = visual.Window(allowGUI=False, monitor='testMonitor', units='norm',colorSpace='rgb',color=[-1,-1,-1], fullscr=True)
mywin.setMouseVisible(False)

capture = cv.CaptureFromCAM(0)
img = cv.QueryFrame(capture)
pi = Image.fromstring("RGB", cv.GetSize(img), img.tostring(), "raw", "BGR", 0, 1)
print(pi.size)
myStim = visual.GratingStim(win=mywin, tex=pi, pos=[0,0.5], size = [0.6,0.6], opacity = 1.0, units = 'norm')
myStim.setAutoDraw(True)

while True:
    img = cv.QueryFrame(capture)
    pi = Image.fromstring("RGB", cv.GetSize(img), img.tostring(), "raw", "BGR", 0, 1)
    myStim.setTex(pi)
    mywin.flip()
    theKey = event.getKeys()
    if len(theKey) != 0:
        break
