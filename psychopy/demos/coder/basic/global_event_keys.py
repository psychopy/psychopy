#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo shows how to use "global event keys" to interact with a running
experiment. The keys do not have to be checked manually, but
rather get handled automatically by PsychoPy.

This works when calling win.flip() repeatedly (as in this example)
and when using core.wait() (not demonstrated here). If using core.wait(),
be sure to set the `hogCPUperiod` parameter equal to the entire
waiting duration, e.g. `core.wait(10, hogCPUperiod=10)`.

"""

from psychopy import core, event, visual


win = visual.Window(units="height")
# Create rectangle
rect = visual.Rect(win, 
    fillColor='blue', 
    pos=(0, -0.25), size=(0.2, 0.2))
# Create textbox for instructions
text = visual.TextBox2(win,
    text="Press B for blue rectangle, \nCTRL + R for red rectangle, \nQ or ESC to quit.",
    font="Open Sans", letterHeight=0.07,
    pos=(0, 0.25), size=(1, 0.3))

# Add an event key.
event.globalKeys.add(key='b', func=setattr,
                     func_args=(rect, 'fillColor', 'blue'),
                     name='blue rect')

# Add an event key with a "modifier" (CTRL).
event.globalKeys.add(key='r', modifiers=['ctrl'], func=setattr,
                     func_args=(rect, 'fillColor', 'red'),
                     name='red rect')

# Add multiple shutdown keys "at once".
for key in ['q', 'escape']:
    event.globalKeys.add(key, func=core.quit)

# Print all currently defined global event keys.
print(event.globalKeys)
print(repr(event.globalKeys))

while True:
    text.draw()
    rect.draw()
    win.flip()
