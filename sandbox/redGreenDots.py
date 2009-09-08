from psychopy import visual, event, core
from copy import copy
from pyglet import gl

win = visual.Window((600,600), monitor='testMonitor', rgb=0, units='pix')
gl.glBlendFunc(gl.GL_SRC_COLOR,gl.GL_DST_COLOR)

red = visual.ElementArrayStim(win, fieldShape='circle',  fieldPos = [0,0], sfs=0, fieldSize=300,nElements=300,
        rgbs=[1.0,-1.0,-1.0], elementMask='none', sizes=4, depths=-0.01)        
green = visual.ElementArrayStim(win, fieldShape='circle',  fieldPos = [0,0], sfs=0, fieldSize=300,nElements=300,
        rgbs=[-1.0,0.6,-1.0], elementMask='none', sizes=4, xys=red.xys, depths=-0.001)
        
def setNewXYs(disp):    
    red.setXYs()
    green.setXYs(copy(red.xys))
#    now add/remove the disparity to the green
    upper = (red.xys[:,1]>0)
    lower = (red.xys[:,1]<=0)
    green.xys[upper,0] += disp/2.0
    red.xys[upper,0] -= disp/2.0
    green.xys[lower,0] -= disp/2.0
    red.xys[lower,:] += disp/2.0
mouse = event.Mouse()

rBalance=0.0
gBalance=0.0
setNewXYs(10)
while True:
    mouse_dX,mouse_dY = mouse.getRel()
    keys = event.getKeys()
    if 'q' in keys:
        break
    elif 'up' in keys:
        rBalance+= 0.1
        print rBalance
    elif 'down' in keys:
        rBalance-= 0.1
        print rBalance
    elif 'left' in keys:
        gBalance-= 0.1
        print gBalance
    elif 'right' in keys:
        gBalance+= 0.1    
        print gBalance  
    event.clearEvents()
    
    red.setRgbs([1, gBalance, -1])
    red.draw()
    green.setRgbs([rBalance, 0.6, -1])
    green.draw()    

    win.update()
    
print 'r,g:', rBalance, gBalance