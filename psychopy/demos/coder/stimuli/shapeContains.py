"""demo for psychopy.visual.ShapeStim.contains(). 
inherited by Polygon(), Circle(), and Rect()
"""
from psychopy import visual, event

win = visual.Window(size=(400,400), monitor='testMonitor')
mouse = event.Mouse(win=win)
instr = visual.TextStim(win, text='click the shape to quit', wrapWidth=1.2)

# a target polygon:
shape = visual.ShapeStim(win, fillColor='blue', interpolate=False, lineColor=None,
    vertices=[(-0.02, -0.0), (-.8,.2), (0,.6), (.1,0.04), (.8, .3), (.6,-.4)])

# loop until detect a click inside the shape boundary
hovering = False
while not any(mouse.getPressed()) or not hovering:
    instr.draw()
    
    # is the mouse hovering over the shape (i.e., inside the shape boundary)?
    hovering = shape.contains(mouse.getPos())
    shape.setOpacity( (0.4, .7)[hovering] ) # could change color, lineWidth, etc
    shape.draw()
    win.flip()
