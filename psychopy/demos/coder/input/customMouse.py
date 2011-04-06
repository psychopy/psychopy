#!/usr/bin/env python

# demo of CustomMouse()
# author Jeremy Gray

from psychopy import visual, event

myWin = visual.Window()

# a virtual mouse, vm:
vm = event.CustomMouse(myWin, leftLimit=0, topLimit=0, rightLimit=0.3, bottomLimit=-0.3)

instr = visual.TextStim(myWin,text="move the mouse around.\nclick to free the mouse.", pos=(0,.3))
new_pointer = visual.TextStim(myWin,text='o')

clicks = 0
mouseDown = False
print "[getPos] [getRel] [getWheelRel] mouseMoveTime (press,released)"
while clicks < 3:
    instr.draw()
    vm.draw()
    myWin.flip()
    if vm.getPressed()[0]:
        #vm.setVisible(not vm.getVisible()) # note both get & set -> click toggles mouse visibility
        if not mouseDown:
            clicks += 1
            print "[%.2f, %.2f]" % (vm.getPos()[0],vm.getPos()[1]), 
            print vm.getRel(), vm.getWheelRel(),
            print "%.3f down, "%vm.mouseMoveTime(),
        
        vm.setLimit(rightLimit = .7, bottomLimit = -.8)
        vm.showLimits=True
        instr.setText("click twice to quit")
        vm.pointer = new_pointer # can change the pointer
        mouseDown=True
    else:
        if mouseDown:
            print '%.3f up'%vm.mouseMoveTime()
        mouseDown = False
