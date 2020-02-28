#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#
#  FreeType high-level python API - Copyright 2011-2015 Nicolas P. Rougier
#  Distributed under the terms of the new BSD license.
#
# -----------------------------------------------------------------------------


from psychopy import visual, core, event, logging

logging.console.setLevel(logging.WARNING)
c = core.Clock()

from psychopy.visual.textbox2 import TextBox2, allFonts

arial = "Arial Unicode MS"

win = visual.Window([800, 800], monitor='testMonitor', backend='glfw')
logging.exp("{:.3f}: created window".format(c.getTime()))

text = u"<i>The quick</i> brown <b>fox</b> jumped"
text2 = u"Some text in Times"
loremIpsum = u"PsychoPy is an open-source Python application allowing you to run a supercali-fragilisticexpeilidocious wide range of neuroscience, psychology and psychophysics experiments. It’s a free, powerful alternative to Presentation™ or e-Prime™, written in Python (a free alternative to Matlab™ g)."

fontSize = 16
# preload some chars into a font to see how long it takes
nChars = 256
arial = allFonts.getFont(arial, fontSize)
logging.exp("{:.3f}: created font".format(c.getTime()))
arial.preload(nChars)
logging.exp("{:.3f}: preloaded {} chars".format(c.getTime(), nChars))
# arial.saveToCache()  # can't yet retrieve the font but it's interesting to see!
logging.flush()

txt1 = TextBox2(win, color=[0.5, 0, 0, 0], text='Toptastic', font='Times',
                pos=(-1, 4), letterHeight=2, units='deg',
                anchor='left',
                borderColor='red',
                fillColor='lightgrey',
                editable=True)
txt1.draw()

x, y = 0, 0
#
center = visual.Rect(win, width=2, height=2, units='pix')
center.draw()

txt2 = TextBox2(win, color=[0, 0, 0, 0], text=loremIpsum, font=arial,
                pos=(x, y), anchor='center', size=(700, -1), units='pix',
                lineSpacing=1.1,
                letterHeight=20.,
                borderColor='white',
                fillColor=None,
                editable=True)
print ('line lens:', txt2._lineLenChars)

txt2.draw()

logging.exp("{:.3f}: drew altered Arial text".format(c.getTime()))

win.flip()
logging.exp("{:.3f}: drew TextBox Times (no preload)".format(c.getTime()))

logging.flush()

stims = [center, txt1, txt2, ]
win.flip()
while True:
    # txt2.pos += 0.001
    for stim in stims:
        stim.draw()
    keys = event.getKeys()
    if 'left' in keys:
        txt2._moveCaret(chars=-1)
    if 'right' in keys:
        txt2._moveCaret(chars=+1)
    if 'up' in keys:
        txt2._moveCaret(lines=-1)
    if 'down' in keys:
        txt2._moveCaret(lines=+1)
    if 'q' in keys:
        core.quit()

    win.flip()
logging.flush()
