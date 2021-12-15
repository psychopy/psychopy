#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import visual, core, event, logging
import numpy as np

logging.console.setLevel(logging.EXP)
c = core.Clock()

from psychopy.visual.textbox2 import TextBox2, allFonts

win = visual.Window([800, 800], monitor='testMonitor')
logging.exp("{:.3f}: created window".format(c.getTime()))

psychopyInfo = u"<b>PsychoPy</b> is an <i>open-source</i> Python application allowing you to run a supercali-fragilisticexpeilidocious wide range of neuroscience, psychology and psychophysics experiments. It’s a free, powerful alternative to Presentation™ or e-Prime™, written in Python (a free alternative to Matlab™ g)."

# preload some chars into a font to see how long it takes
fontSize = 16
arial = allFonts.getFont("Arial", fontSize)
logging.exp("{:.3f}: created font".format(c.getTime()))
nChars = 256
arial.preload(nChars)  # or set to preload specific string of chars
logging.exp("{:.3f}: preloaded {} chars".format(c.getTime(), nChars))

txt1 = TextBox2(win, text="Type here, it's toptastic", font='Times',
                color='black', colorSpace='named', 
                pos=(0, 0.4), letterHeight=0.05, units='height',
                size=[0.8, 0.2],
                anchor='center-top',
                borderColor='lightgrey',
                fillColor='slategrey',
                editable=True)

txt2 = TextBox2(win, text=psychopyInfo, font='Arial',
            pos=(0, -5), anchor='middle', size=(20, None), units='cm',
            lineSpacing=1.1,
            letterHeight=1.,
            color='LightGrey', borderColor='Moccasin', fillColor=None,
            editable=True)

txt3 = TextBox2(win, text='Good for non-editable text (Esc to quit)',
            font='Arial',
            borderColor=None, fillColor=None,
            pos=(-0.5,-0.5), units='height', anchor='bottom-left',
            letterHeight=0.02,
            editable=False)

txt1.autoDraw=True
txt2.autoDraw=True
txt3.autoDraw=True

clock = core.Clock()
t=0
while t<30:
    t= clock.getTime()

    txt2.pos = (0.2*np.sin(t), 0.2*np.cos(t))
            
    if 'escape' in event.getKeys():
        core.quit()
    
    win.flip()

logging.flush()
