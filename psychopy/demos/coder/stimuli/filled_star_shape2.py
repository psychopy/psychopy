#!/usr/bin/env python2

"""Demo of psychopy.visual.ShapeStim2: fillable shapes even if concave edges
"""

from psychopy import visual, event, core
from psychopy.visual import ShapeStim2, ShapeStim

win = visual.Window(size=(800, 400), units='height')

arrowVert = [ (-0.2,0.05), (-0.2,-0.05), (0.0,-0.05), (0.0,-0.1), (0.2,0), (0.0,0.1), (0.0,0.05) ]
starVert = [(0.0, 0.5), (0.09, 0.18), (0.39, 0.31), (0.19, 0.04), (0.49, -0.11), (0.16, -0.12), (0.22, -0.45), 
        (0.0, -0.2), (-0.22, -0.45), (-0.16, -0.12), (-0.49, -0.11), (-0.19, 0.04), (-0.39, 0.31), (-0.09, 0.18)]
thingVert = [(0,0),(0,.4),(.4,.4),(.4,0),(.1,0),(.2,.1),(.3,.1),(.3,.3),(.1,.3),(.1,0)]

# drawing a border line does not work yet; glitchy & static
arrow = ShapeStim2(win, vertices=arrowVert, fillColor='red', pos=(-.3,-.3))
star = ShapeStim2(win, vertices=starVert, fillColor='green',opacity=.3)  #,lineWidth=0.5,lineColor='white')
thing = ShapeStim2(win, vertices=thingVert, fillColor='blue',opacity=.3)  #,lineWidth=0.5,lineColor='white')

c = core.Clock()
while not event.getKeys() and c.getTime() < 10:
    star.setOri(1,'-')
    star.draw()
    thing.setPos(star.ori % 360 / 720.-.5)
    thing.draw()
    arrow.draw()
    win.flip()
