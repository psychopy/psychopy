#!/usr/bin/env python2

"""Demo of psychopy.visual.ShapeStim2: fillable shapes even if concave edges
"""

from psychopy import visual, event
from psychopy.visual import ShapeStim2

win = visual.Window(size=(800, 400), units='height')

arrowVert = [(-0.4,0.05), (-0.4,-0.05), (-.2,-0.05), (-.2,-0.1), (0,0), (-.2,0.1), (-.2,0.05)]
star7Vert = [(0.0, 0.5), (0.09, 0.18), (0.39, 0.31), (0.19, 0.04), (0.49, -0.11), (0.16, -0.12), (0.22, -0.45), 
        (0.0, -0.2), (-0.22, -0.45), (-0.16, -0.12), (-0.49, -0.11), (-0.19, 0.04), (-0.39, 0.31), (-0.09, 0.18)]
selfxVert = [(0,0),(0,.2),(.2,0),(.2,.2)]

# `thing` has a fake hole and discontinuity (as the border will reveal):
thingVert = [(0,0),(0,.4),(.4,.4),(.4,0),(.1,0),(.1,.1),(.3,.1),(.3,.3),(.1,.3),(.1,0),
    (0,0),(.1,-.1),(.3,-.1),(.3,-.3),(.1,-.3),(.1,-.1)]

arrow = ShapeStim2(win, vertices=arrowVert, fillColor='darkred',size=.5)#  , lineWidth=2, lineColor='red')
star7 = ShapeStim2(win, vertices=star7Vert, fillColor='green', lineWidth=2, lineColor='white')
selfx = ShapeStim2(win, vertices=selfxVert, fillColor='yellow', opacity=.6)
thing = ShapeStim2(win, vertices=thingVert, fillColor='blue', opacity=.3)  #,lineWidth=0.5,lineColor='white')
thing.flipVert = True

m = event.Mouse()
while not event.getKeys():
    star7.setOri(1,'-')  # rotate
    star7.setSize(-star7.ori%360 / 360)  # expand
    star7.draw()
    thing.setOri(-star7.ori/7)  # rotate slowly
    thing.draw()
    arrow.draw()
    selfx.draw()
    win.flip()
    if thing.contains(m): break
