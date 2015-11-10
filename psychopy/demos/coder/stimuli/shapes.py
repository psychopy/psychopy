#!/usr/bin/env python2

"""Demo of psychopy.visual.ShapeStim: fillable shapes even if concave edges, holes, etc
"""

from psychopy import visual, event
from psychopy.visual import ShapeStim

win = visual.Window(size=(800, 400), units='height')

arrowVert = [(-0.4,0.05), (-0.4,-0.05), (-.2,-0.05), (-.2,-0.1), (0,0), (-.2,0.1), (-.2,0.05)]
star7Vert = [(0.0, 0.5), (0.09, 0.18), (0.39, 0.31), (0.19, 0.04), (0.49, -0.11), (0.16, -0.12), (0.22, -0.45), 
        (0.0, -0.2), (-0.22, -0.45), (-0.16, -0.12), (-0.49, -0.11), (-0.19, 0.04), (-0.39, 0.31), (-0.09, 0.18)]
selfxVert = [(0,0),(0,.2),(.2,0),(.2,.2)]

# `thing` has a fake hole and discontinuity (as the border will reveal):
thingVert = [(0,0),(0,.4),(.4,.4),(.4,0),(.1,0),(.1,.1),(.3,.1),(.3,.3),(.1,.3),(.1,0),
    (0,0),(.1,-.1),(.3,-.1),(.3,-.3),(.1,-.3),(.1,-.1)]

# a true hole, using two loops of vertices:
donutVert = [[(-.2,-.2),(-.2,.2),(.2,.2),(.2,-.2)], [(-.15,-.15),(-.15,.15),(.15,.15),(.15,-.15)]]

# lines are ok; use closeShape=False
lineAVert = [(0,0),(.1,.1),(.1,.2),(.1,.1),(.1,-.1),(0,.1)]

arrow = ShapeStim(win, vertices=arrowVert, fillColor='darkred', size=.5, lineColor='red')
star7 = ShapeStim(win, vertices=star7Vert, fillColor='green', lineWidth=2, lineColor='white')
selfx = ShapeStim(win, vertices=selfxVert, fillColor='yellow', opacity=.6, pos=(.2,-.3), size=1.6)
thing = ShapeStim(win, vertices=thingVert, fillColor='blue', lineWidth=0, opacity=.3, size=.7)
donut = ShapeStim(win, vertices=donutVert, fillColor='orange', lineWidth=0, size=.75, pos=(-.2,-.25))
lineA = ShapeStim(win, vertices=lineAVert, closeShape=False, lineWidth=2, pos=(-.5,0), ori=180)

#m = event.Mouse()
while not event.getKeys():
    star7.setOri(1,'-')  # rotate
    star7.setSize(star7.ori % 360 / 360)  # shrink
    star7.draw()
    thing.setOri(-star7.ori/7)  # rotate slowly
    thing.draw()
    arrow.draw()
    selfx.draw()
    donut.draw()
    lineA.draw()
    # illustration of dynamic vertices:
    selfxVert[0] = star7.size/5
    selfxVert[3] = star7.size/5 * (0,.9)
    selfx.vertices = selfxVert  # can be slow with many vertices
    win.flip()
    #if thing.contains(m): break
