#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo and utility for finding out the key-code for specific keys
"""

from __future__ import absolute_import, division, print_function

from psychopy import visual, event, core

win = visual.Window([400, 400])
msg = visual.TextStim(win, text='press a key\n < esc > to quit')
msg.draw()
win.flip()

k = ['']
count = 0
while k[0] not in ['escape', 'esc'] and count < 5:
    k = event.waitKeys()
    print(k)
    count += 1

win.close()
core.quit()

# The contents of this file are in the public domain.
