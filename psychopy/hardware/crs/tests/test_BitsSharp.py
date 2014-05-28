"""Some classes to support import of data files
"""

from psychopy.hardware import crs
from psychopy import visual
import sys, os, time
from psychopy import logging
logging.console.setLevel(logging.DEBUG)

thisDir = os.path.split(__file__)[0]
win = visual.Window()

def test_BitsSharp():
    if sys.platform=='win32':
        portName='COM7'
    else:
        portName=None
    bitsBox = crs.BitsSharp(win=win, portName=portName, mode='mono++')
    assert bitsBox.OK == True #make sure we were successful
    print bitsBox.info

    ##status screen is slow
    bitsBox.mode = 'bits++'
    bitsBox.mode = 'status'
    ##get video line implicitly uses status screen
    print bitsBox.getVideoLine(lineN=1, nPixels=5)
    time.sleep(0.1)
    #bitsBox.mode = 'massStorage' #if you test this you have to repower the box after

    #check that we can switch to the different modes
    bitsBox.mode = 'color++'
    time.sleep(5) #give time to get back out of status screen
    bitsBox.mode = 'mono++'
    time.sleep(1)
    bitsBox.mode = 'bits++'
    time.sleep(1)
    bitsBox.beep(freq=800, dur=1) #at one point dur was rounded down to 0 if les than 1

if __name__ == '__main__':
    test_BitsSharp()