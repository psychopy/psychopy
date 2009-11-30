from psychopy import event, visual, core
import numpy

win = visual.Window([1680,1050], winType='pyglet',monitor='testMonitor', units='pix', allowGUI=True)

myMouse = event.Mouse(win=win)

while True:
    if myMouse.getPressed()[0]:
#        if numpy.any(myMouse.lastPos!=myMouse.getPos()):
#            print myMouse.getPos()
        print myMouse.getRel()
    win.flip()
    if myMouse.getPressed()[2]:
        break