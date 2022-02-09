#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of CustomMouse(), showing movement limits, click detected upon release,
and ability to change the pointer.
"""
# authors Jeremy Gray & Todd Parsons

from psychopy import visual, event

# Create window
win = visual.Window(units="height")

# Create a virtual mouse
vm = visual.CustomMouse(win,
    leftLimit=-0.2, topLimit=0, rightLimit=0.2, bottomLimit=-0.4,
    showLimitBox=True, clickOnUp=True)
# Textbox for instructions
instr = visual.TextBox2(win, 
    text="Move the mouse around. Click to give the mouse more room to move.",
    font="Open Sans", letterHeight=0.08,
    pos=(0, .3))
# Create a character to use as mouse
new_pointer = visual.TextStim(win, 
    text=u'\u265e', 
    font="Gothic A1")
print("[getPos] [getWheelRel] click time")
# Listen for clicks
while not event.getKeys():
    # Draw components
    instr.draw()
    vm.draw()
    win.flip()
    # Check for clicks
    if vm.getClicks():
        vm.resetClicks()
        # Print click details
        print("click at [%.2f, %.2f]" % (vm.getPos()[0], vm.getPos()[1]))
        print(vm.getWheelRel())
        print("%.3f sec"%vm.mouseMoveTime())
        # can set some limits, others are unchanged:
        vm.setLimit(leftLimit=-0.5, topLimit=0.1, rightLimit=0.5, bottomLimit=-0.4,)
        instr.text = "Room to gallop! Press any key to quit."

        # can switch the pointer to anything with a .draw() and setPos() method
        vm.pointer = new_pointer

win.close()

# The contents of this file are in the public domain.
