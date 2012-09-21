"""demo for psychopy.visual.ShapeStim.contains() and .overlaps()
inherited by Polygon(), Circle(), and Rect()
"""
from psychopy import visual, event

win = visual.Window(size=(400,400), monitor='testMonitor', units='norm')
mouse = event.Mouse(win=win)
instr = visual.TextStim(win, text='click the shape to quit\nscroll to adjust circle', pos=(0,-.7), opacity=0.5)
msg = visual.TextStim(win, text=' ', pos=(0,-.4))

# a target polygon; concavities and self-overlapping are fine for contains() and overlaps()
shape = visual.ShapeStim(win, fillColor='darkblue', lineColor=None,
    vertices=[(-0.02, -0.0), (-.8,.2), (0,.6), (.1,0.06), (.8, .3), (.6,-.4)])

# define a buffer zone around the mouse for proximity detection:
bufzone = visual.Circle(win, radius=0.15, edges=13)

# loop until detect a click inside the shape:
inside = False
while not any(mouse.getPressed()) or not inside:
    instr.draw()
    # dynamic buffer zone around mouse pointer:
    bufzone.setPos(mouse.getPos())  # follow the mouse
    bufzone.setSize(mouse.getWheelRel()[1]/20., '+')  # vert scroll adjusts radius, can go negative
    # is the mouse inside the shape?
    inside = shape.contains(mouse)
    if inside:
        msg.setText('inside')
        shape.setOpacity(1)
        bufzone.setOpacity(1)
    elif shape.overlaps(bufzone):
        msg.setText('near')
        shape.setOpacity(.6)
        bufzone.setOpacity(.6)
    else:
        msg.setText('far away')
        shape.setOpacity(0.2)
        bufzone.setOpacity(0.2)
    bufzone.draw()  # drawing helps visualize the mechanics
    msg.draw()
    shape.draw()
    win.flip()
