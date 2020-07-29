#!/usr/bin/env python
# -*- coding: utf-8 -*-


from psychopy import visual, core, event, logging

logging.console.setLevel(logging.DEBUG)
c = core.Clock()

from psychopy.visual.textbox2 import TextBox2, allFonts

win = visual.Window([800, 800], monitor='testMonitor', backend='glfw')
logging.exp("{:.3f}: created window".format(c.getTime()))

text = u"<i>The quick</i> brown <b>fox</b> jumped"
loremIpsum = u"PsychoPy is an open-source Python application allowing you to run a supercali-fragilisticexpeilidocious wide range of neuroscience, psychology and psychophysics experiments. It’s a free, powerful alternative to Presentation™ or e-Prime™, written in Python (a free alternative to Matlab™ g)."

fontSize = 16
# preload some chars into a font to see how long it takes
nChars = 256
arial = allFonts.getFont("Arial", fontSize)
logging.exp("{:.3f}: created font".format(c.getTime()))
arial.preload(nChars)
logging.exp("{:.3f}: preloaded {} chars".format(c.getTime(), nChars))
# arial.saveToCache()  # can't yet retrieve the font but it's interesting to see!


txt1 = TextBox2(win, color='black', colorSpace='named', text='Toptastic', font='Times',
                pos=(0, 0.0), letterHeight=0.1, units='height',
                size=[1, 1],
                anchor='right-bottom',
                borderColor='red',
                fillColor='slategrey',
                editable=True)
txt1.draw()

x, y = 0, -5

txt2 = TextBox2(win, color='blue', text=loremIpsum, font='Arial',
            pos=(x, y), anchor='bottom', size=(20, None), units='cm',
            lineSpacing=1.1,
            letterHeight=1.,
            borderColor='white',
            fillColor=None,
            editable=True)
txt2.draw()

logging.exp("{:.3f}: drew altered Arial text".format(c.getTime()))

win.flip()
logging.exp("{:.3f}: drew TextBox Times (no preload)".format(c.getTime()))

stims = [txt1, txt2]
win.flip()
for frame in range(1000):
    txt2.pos += 0.01
    for stim in stims:
        stim.draw()
    if 'escape' in event.getKeys():
        core.quit()

    win.flip()
logging.flush()

