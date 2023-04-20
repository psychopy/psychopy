# -*- coding: utf-8 -*-
"""
Created on Mon Dec 15 15:22:48 2014

@author: lpzjwp
"""
from psychopy import visual
from psychopy.tools import systemtools
from psychopy.tests import skip_under_vm
import numpy as np

try:
    from PIL import Image
except ImportError:
    import Image


array=np.array
#expectedVals = {'bits++':{}, 'mono++':{}, 'color++':{}}
expectedVals = {
    'color++': {1024: {'lowG': array([  0,  64,   0, 192,   1,  64,   1, 192,   2,  64]),
        'highR': array([ 62, 192,  63,  64,  63, 192]),
        'lowR': array([  0,  64,   0, 192,   1,  64,   1, 192,   2,  64]),
        'highG': array([ 62, 192,  63,  64,  63, 192])},
        65535: {'lowG': array([0, 1, 0, 3, 0, 5, 0, 7, 0, 9]),
        'highR': array([  0, 251,   0, 253,   0, 255]),
        'lowR': array([0, 1, 0, 3, 0, 5, 0, 7, 0, 9]),
        'highG': array([  0, 251,   0, 253,   0, 255])},
        255.0: {'lowG': array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
        'highR': array([250, 251, 252, 253, 254, 255]),
        'lowR': array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
        'highG': array([250, 251, 252, 253, 254, 255])}},
    'mono++':{1024: {'lowG': array([  0,  64, 128, 192,   0,  64, 128, 192,   0,  64]),
        'highR': array([62, 62, 62, 63, 63, 63]),
        'lowR': array([0, 0, 0, 0, 1, 1, 1, 1, 2, 2]),
        'highG': array([128, 192, 255,  64, 128, 192])},
        65535: {'lowG': array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
        'highR': array([0, 0, 0, 0, 0, 0]),
        'lowR': array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
        'highG': array([250, 251, 252, 253, 254, 255])},
        255.0: {'lowG': array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
        'highR': array([250, 251, 252, 253, 254, 255]),
        'lowR': array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
        'highG': array([250, 251, 252, 253, 254, 255])}},
    'bits++': {
        1024: {'lowG': array([106, 136,  19,  25, 115,  68,  41, 159,   0,   0]),
        'highR': array([119, 118, 120, 119, 121, 120]),
        'lowR': array([ 36,  63,   8, 211,   3, 112,  56,  34,   0,   0]),
        'highG': array([119, 118, 120, 119, 121, 120])},
        65535: {'lowG': array([106, 136,  19,  25, 115,  68,  41, 159,   0,   0]),
        'highR': array([119, 118, 120, 119, 121, 120]),
        'lowR': array([ 36,  63,   8, 211,   3, 112,  56,  34,   0,   0]),
        'highG': array([119, 118, 120, 119, 121, 120])},
        255.0: {'lowG': array([106, 136,  19,  25, 115,  68,  41, 159,   0,   0]),
        'highR': array([119, 118, 120, 119, 121, 120]),
        'lowR': array([ 36,  63,   8, 211,   3, 112,  56,  34,   0,   0]),
        'highG': array([119, 118, 120, 119, 121, 120])}}}

@skip_under_vm
def test_bitsShaders():
    try:
        from psychopy.hardware.crs.bits import BitsSharp
    except (ModuleNotFoundError, ImportError):
        return

    win = visual.Window([1024, 768], fullscr=0, screen=1, useFBO=True,
                        autoLog=True)

    bits = BitsSharp(win, mode='bits++', noComms=True)

    # draw a ramp across the screenexpectedVals = range(256)
    w, h = win.size
    intended = list(range(256))
    testArrLums = np.resize(intended,
                            [256, 256]) / 127.5 - 1  # NB psychopy uses -1:1
    stim = visual.ImageStim(win, image=testArrLums,
                            size=[256, h], pos=[128 - w / 2, 0], units='pix',
                            )
    expected = np.repeat(intended, 3).reshape([-1, 3])

    # stick something in the middle for fun!
    gabor = visual.GratingStim(win, mask='gauss', sf=3, ori=45, contrast=0.5)
    gabor.autoDraw = True

    #a dict of dicts for expected vals
    for mode in ['bits++', 'mono++', 'color++']:
        bits.mode=mode
        for finalVal in [255.0, 1024, 65535]:
            thisExpected = expectedVals[mode][finalVal]

            intended = np.linspace(0.0,1,256)*255.0/finalVal
            stim.image = np.resize(intended,[256,256])*2-1 #NB psychopy uses -1:1

            stim.draw()
            #fr = np.array(win._getFrame(buffer='back').transpose(Image.ROTATE_270))
            win.flip()
            fr = np.array(win._getFrame(buffer='front').transpose(Image.ROTATE_270))
            if not systemtools.isVM_CI():
                assert np.alltrue(thisExpected['lowR'] == fr[0:10, -1, 0])
                assert np.alltrue(thisExpected['lowG'] == fr[0:10, -1, 1])
                assert np.alltrue(thisExpected['highR'] == fr[250:256, -1, 0])
                assert np.alltrue(thisExpected['highG'] == fr[250:256, -1, 1])

                print('R', repr(fr[0:10,-1,0]), repr(fr[250:256,-1,0]))
                print('G', repr(fr[0:10,-1,1]), repr(fr[250:256,-1,0]))
            #event.waitKeys()


if __name__=='__main__':
    test_bitsShaders()
