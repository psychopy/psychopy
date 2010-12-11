#test boot

from psychopy import data, core
import scipy

xx= scipy.array([[0, 0, 0, 0], [0.0,0.0,1.0,1.0],[1,1,1,1]])
timer=core.Clock()
boots = data.bootrsp(xx,1000)
print timer.getTime()