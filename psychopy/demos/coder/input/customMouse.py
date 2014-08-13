#!/usr/bin/env python2

# demo of CustomMouse()
# author Jeremy Gray

from psychopy import visual, event

myWin = visual.Window()

# a virtual mouse, vm, with limits and click detected when release the left mouse button:
vm = visual.CustomMouse(myWin, leftLimit=-0.2, topLimit=0, rightLimit=0.2, bottomLimit=-0.4, 
            showLimitBox=True, clickOnUp=True)

instr = visual.TextStim(myWin,text="move the mouse around.\nclick to give the mouse more room to move.", pos=(0,.3))
new_pointer = visual.TextStim(myWin, text='o')
print "[getPos] [getWheelRel] click time"
while not event.getKeys():
    instr.draw()
    vm.draw()
    myWin.flip()
    if vm.getClicks():
        vm.resetClicks()
        #vm.setVisible(not vm.getVisible()) # can use get & set; here, a click toggles mouse visibility
        print "click at [%.2f, %.2f]" % (vm.getPos()[0],vm.getPos()[1]), 
        print vm.getWheelRel(),
        print "%.3f sec"%vm.mouseMoveTime()
        vm.setLimit(leftLimit = -0.7, rightLimit = 0.7, bottomLimit = -0.8) # can set some limits, others are unchanged
        instr.setText("any key to quit")
        vm.pointer = new_pointer # switch the pointer appearance to anything with a .draw() and setPos() method
        
