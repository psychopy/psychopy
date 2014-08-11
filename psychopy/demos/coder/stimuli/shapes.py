from psychopy import visual, event, core
from math import sin, cos
"""ShapeStim can be used to make geometric shapes where you specify the locations of each vertex
relative to some anchor point. 

NB for now the fill of objects is performed using glBegin(GL_POLYGON) and that is limited to convex 
shapes. With concavities you get unpredictable results (e.g. add a fill colour to the arrow stim below). 
To create concavities, you can combine multiple shapes, or stick to just outlines. (If anyone wants
to rewrite ShapeStim to use glu tesselators that would be great!)
"""
win = visual.Window([600,600], monitor='testMonitor', units='norm')

arrowVertices=[ [-0.2,0.05], [-0.2,-0.05], [0.0,-0.05], [0.0,-0.1], [0.2,0], [0.0,0.1],  [0.0,0.05] ]
sqrVertices = [ [0.2,-0.2], [-0.2,-0.2], [-0.2,0.2], [0.2,0.2] ]

stim1 = visual.ShapeStim(win, 
                 lineColor='red',
                 lineWidth=2.0, #in pixels
                 fillColor=None, #beware, with convex shapes fill colors don't work
                 vertices=arrowVertices,#choose something from the above or make your own
                 closeShape=True,#do you want the final vertex to complete a loop with 1st?
                 pos= [0,0], #the anchor (rotaion and vertices are position with respect to this)
                 interpolate=True,
                 opacity=0.9,
                 autoLog=False)#this stim changes too much for autologging to be useful

stim2 = visual.ShapeStim(win, 
                 lineColor='green',
                 lineWidth=2.0, #in pixels
                 fillColor=[-0.5,0.5,-0.5], #beware, with convex shapes this won't work
                 fillColorSpace='rgb',
                 vertices=sqrVertices,#choose something from the above or make your own
                 closeShape=True,#do you want the final vertex to complete a loop with 1st?
                 pos= [0.5,0.5], #the anchor (rotaion and vertices are position with respect to this)
                 interpolate=True,
                 opacity=0.9,
                 autoLog=False)#this stim changes too much for autologging to be useful
                 
clock = core.Clock()
while True:
    stim1.setOri(2,'+')
    stim1.draw()
    
    sqrVertices[1] = [ -0.2-sin(clock.getTime())/6.0, -0.2-cos(clock.getTime())/6.0 ]#change one of the vertices
    stim2.setVertices(sqrVertices)
    stim2.draw()
 
    win.flip()
    if len(event.getKeys()):
        core.quit()
