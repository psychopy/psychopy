#!/usr/bin/env python2

"""Demo of psychopy.visual.TessStim: fillable shapes even if concave edges
"""

from psychopy import visual, event, core
from psychopy.visual import TessStim, ShapeStim

win = visual.Window(size=(800,400), units='height')
outline = [(-.2,-.05), (-.2,.05), (.2,.05), (.2,.15), (.35,0), (.2,-.15), (.2,-.05)]

# typically want lineWidth=0 (default); set lineWidth=1 to see the tesselation)
shape = TessStim(win, vertices=outline, fillColor='darkgreen')

#border = ShapeStim(win, vertices=shape.border)  # use as border only, no fill

c = core.Clock()
while not event.getKeys() and c.getTime() < 10:
    shape.setOri(1,'-')
    shape.draw()
    #border.setOri(1,'-')
    #border.draw()
    win.flip()
