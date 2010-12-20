from psychopy import *
import numpy as num

ori = 45

step=2*num.pi/128
cycle= num.arange(0,4*num.pi, step)
[xx,yy] = num.meshgrid(cycle,cycle)

grating = num.sin(xx*num.cos(ori*num.pi/180)+yy*num.cos(ori*num.pi/180))

win = visual.Window([800,800])
spiral = visual.RadialStim(win, tex=grating, pos=[-0.5, 0])
patch = visual.PatchStim(win, tex=grating, pos=[0.5, 0], sf=2)


spiral.draw()
patch.draw()
win.update()

event.waitKeys()
