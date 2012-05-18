"""demo ShapeStim.contains()
"""
from psychopy import visual, core, event
import time

win = visual.Window(size=(400,400))

# these are the target shapes, will see if points are inside or not:
cir = visual.Circle(win, radius=.6, edges=64)
irreg = visual.ShapeStim(win, vertices=[(0,0), (-.8,.2), (0,.6), (.1,0), (.8, .3), (.6,-.4)])

dot = visual.Circle(win, radius=.03, fillColor=1, lineColor=0)  # display dot
points = [(.4,0), (.1,0.5), (0,.5), (0.73, 0), (0.62, 0), (.6, 0), (.56,0.3)]

for shape in [cir, irreg]:
    for p in points:
        shape.draw()
        dot.setPos(p)
        t0 = time.time()
        inside = shape.contains(p) # == shape.contains(dot.pos)
        t1 = time.time() - t0
        dot.setFillColor(('red','green')[inside])
        dot.draw()
        win.flip()
        print p, inside, ('out', 'in')[inside], "%.2fms" % (t1 * 1000)
        core.wait(1)
