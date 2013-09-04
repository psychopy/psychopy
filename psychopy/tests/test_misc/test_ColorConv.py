from psychopy.tools.colorspacetools import hsv2rgb
import numpy

#We need more tests of these conversion routines. Feel free to jump in and help! ;-)


def test_HSV_RGB():
    HSV=numpy.array([
       [  0,   1,   1],
       [  0,   1, 0.5],#reducing Value reduces intensity of primary gun
       [  0,   0.5, 0.5],#reducing Saturation increases intensity of other guns
       [ 30,   1,   1],
       [ 60,   1,   1],
       [ 90,   1,   1],
       [120,   1,   1],
       [150,   1,   1],
       [180,   1,   1],
       [210,   1,   1],
       [240,   1,   1],
       [270,   1,   1],
       [300,   1,   1],
       [330,   1,   1],
       [360,   1,   1]])
    expectedRGB=numpy.array([
       [ 1. ,  -1. ,  -1. ],
       [ 0.,  -1. ,  -1. ],
       [ 0., -0.5,  -0.5],
       [ 1. ,  0.,  -1. ],
       [ 1. ,  1. ,  -1. ],
       [ 0.,  1. ,  -1. ],
       [ -1. ,  1. ,  -1. ],
       [ -1. ,  1. ,  0.],
       [ -1. ,  1. ,  1. ],
       [ -1. ,  0.,  1. ],
       [ -1. ,  -1. ,  1. ],
       [ 0.,  -1. ,  1. ],
       [ 1. ,  -1. ,  1. ],
       [ 1. ,  -1. ,  0.],
       [ 1. ,  -1. ,  -1. ]])
    RGB = hsv2rgb(HSV)
    assert numpy.allclose(RGB,expectedRGB,0.0001)

if __name__=='__main__':
    test_HSV_RGB()
