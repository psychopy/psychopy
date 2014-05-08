"""Some classes to support import of data files
"""

from pycrsltd import bits
import sys, os, time
from psychopy import logging
#logging.console.setLevel(logging.DEBUG)

thisDir = os.path.split(__file__)[0]

def test_BitsSharp():
    if sys.platform=='win32':
        portname='COM7'
    else:
        portname=None
    bitsBox = bits.BitsSharp(portname)
    assert bitsBox.OK == True
    print bitsBox.getInfo()

    ##status screen is slow
    bitsBox.mode = 'status'
    time.sleep(2)#time to switch
    ##get video line implicitly uses status screen
    print bitsBox.getVideoLine(lineN=50, nPixels=5)
    time.sleep(1)
    #bitsBox.mode = 'massStorage' #if you test this you have to repower the box after

    bitsBox.mode = 'color++'
    time.sleep(5)
    bitsBox.mode = 'mono++'
    time.sleep(1)
    bitsBox.mode = 'bits++'
    time.sleep(1)
    bitsBox.beep(freq=800, dur=1) #at one point dur was rounded down to 0 if les than 1

if __name__ == '__main__':
    test_BitsSharp()