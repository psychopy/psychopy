#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of CustomMouse(), showing movement limits, click detected upon release,
and ability to change the pointer.
"""

from __future__ import absolute_import, division, print_function

# author Jeremy Gray

from psychopy import visual, event

win = visual.Window()

# a virtual mouse, vm, :
vm = visual.CustomMouse(win,
    leftLimit=-0.2, topLimit=0, rightLimit=0.2, bottomLimit=-0.4,
    showLimitBox=True, clickOnUp=True)

instr = visual.TextStim(win, text="move the mouse around.\n"
    "click to give the mouse more room to move.", pos=(0, .3))
new_pointer = visual.TextStim(win, text='o')
print("[getPos] [getWheelRel] click time")
while not event.getKeys():
    instr.draw()
    vm.draw()
    win.flip()
    if vm.getClicks():
        vm.resetClicks()
        # vm.setVisible(not vm.getVisible())
        print("click at [%.2f, %.2f]" % (vm.getPos()[0], vm.getPos()[1]))
        print(vm.getWheelRel())
        print("%.3f sec"%vm.mouseMoveTime())

        # can set some limits, others are unchanged:
        vm.setLimit(leftLimit=-0.7, rightLimit=0.7, bottomLimit=-0.8)
        instr.setText("any key to quit")

        # can switch the pointer to anything with a .draw() and setPos() method
        vm.pointer = new_pointer

win.close()

# The contents of this file are in the public domain.
