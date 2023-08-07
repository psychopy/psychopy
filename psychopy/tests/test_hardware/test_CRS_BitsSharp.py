# -*- coding: utf-8 -*-
"""
Created on Thu May  8 10:46:41 2014

@author: jon.peirce
"""
import pytest
from psychopy import visual, core


def test_bitsSharp():
    try:
        from psychopy.hardware.crs import BitsSharp
    except (ModuleNotFoundError, ImportError):
        return

    win = visual.Window(screen=0, fullscr=True, useFBO=True, autoLog=True)
    win.setGamma(1.0) #make sure gfx card LUT is identity
    #initialise BitsSharp
    try:
        bits = BitsSharp(win=win, mode='color++')
    except ImportError:
        pytest.skip("crs.BitsSharp: could not initialize. possible:\nfrom serial.tools import list_ports\n"
           "ImportError: No module named tools")

    if not bits.OK:
        win.close()
        pytest.skip("No BitsSharp connected")
        
    print(bits.info)

    #switch to status screen (while keeping in mono 'mode')
    bits.getVideoLine(lineN=1, nPixels=1)
    core.wait(5) #wait for status mode to take effect

    #create a stimulus to check luminance values
    screenSqr = visual.GratingStim(win,tex=None, mask=None,
               size=2)

    print('\n  up from zero:')
    bit16 = (2.0 ** 16) - 1
    for frameN in range(5):
        intensity = frameN / bit16
        screenSqr.color = intensity * 2 - 1  # psychopy is -1:1
        screenSqr.draw()
        win.flip()
        pixels = bits.getVideoLine(lineN=1, nPixels=2)
        print(pixels[0], pixels[1], intensity)

    print('\n  down from 1:')
    for frameN in range(5):
        intensity = 1 - (frameN / bit16)
        screenSqr.color = intensity * 2 - 1  # psychopy is -1:1
        screenSqr.draw()
        win.flip()
        pixels = bits.getVideoLine(lineN=1, nPixels=2)
        print(pixels[0], pixels[1], intensity)

    print('\n  check the middle::')
    for intensity in [0.5, 0.5 + (1 / bit16)]:
        screenSqr.color = intensity * 2 - 1  # psychopy is -1:1
        screenSqr.draw()
        win.flip()
        pixels = bits.getVideoLine(lineN=1, nPixels=2)
        print(pixels[0], pixels[1], intensity)

    bits.mode = "color++" #get out of status screen
