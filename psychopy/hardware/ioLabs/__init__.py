"""import USBBox from IOLAB SYSTEMS ("ioLabs") button box, beta 3.1
"""
__author__ = 'IOLAB SYSTEMS INC'
__version__ = 'beta3.1'

from psychopy import log
import os 

try:
    import serial
except:
    serial=False
    raise ImportError('The module serial is needed to connect to the ioLab Systems button-box. ' +\
        "On most systems this can be installed with\n\t easy_install pyserial")

def USBBox(): # to be over-ridden if import is successful
    return False

if os.path.isfile('/System/Library/Extensions/BBoxArchiver.kext'):
    log.warning("ioLab Systems USBBox may not work properly:\n  /System/Library/Extensions/BBoxArchiver.kext exists")
        
try:
    from _ioLab_beta3p1 import USBBox
except RuntimeError, errMsg:
    raise RuntimeError, errMsg
    

