#!/usr/bin/env python

"""Demo program to illustrate using ioLabs button box

To run this demo the ioLab library needs to be installed (it is included with
the Standalone distributions of PsychoPy).

"""

__author__ = 'Jonathan Roberts'

from psychopy import logging
#log.console.setLevel(log.CRITICAL)

from psychopy import core, visual, event
try:
   import ioLabs
except RuntimeError, errMsg:
    logging.error('Is an ioLabs button-box connected and turned on? (import failed: "'+str(errMsg)+'")')
    core.quit()

import random

def setup_bbox():
    '''Initialize the button box object and disable all buttons and lights.'''

    global usbbox # button box object declared global so the other routines can use it
    usbbox=ioLabs.USBBox()
    usbbox.buttons.enabled = 0x00 #8 bit pattern 0=disabled 1=enabled
    usbbox.port2.state = 0xFF #port2 is the lights on the bbox - 8 bit pattern 0=on 1=off
    
def enableButtons(buttonList=(0,1,2,3,4,5,6,7)):
    '''enable the specified buttons
    the argument should beone of the following:
    None - disable all buttons
    an integer - enable a single buttonList
    a list of integers - enable all buttons in the list'''

    global usbbox
    if buttonList == None:
        usbbox.buttons.enabled = 0
    elif type(buttonList) == int:
        usbbox.buttons.enabled = 2**(buttonList)
    elif type(buttonList) == list:
        bits = 0
        for btn in buttonList:
            bits = bits + 2**(btn)
        usbbox.buttons.enabled = bits
    else:
        print 'invalid button list - must be None, an integer or a list of integers'

def lights(lightList=None):
    global usbbox
    if lightList == None:
        usbbox.leds.state = 0xFF
    elif type(lightList) == int:
        usbbox.leds.state = ~(2**(lightList))
    elif type(lightList) == list:
        bits = 0
        for btn in lightList:
            bits = bits + 2**(btn)
        usbbox.leds.state = ~bits
    else:
        print 'invalid light list - must be None, an integer or a list of integers'

def reset_bbox_clock():
    '''Reset the internal clock of the button box.'''
    global usbbox
    usbbox.reset_clock()

def waitForVoice():
    '''Wait for the button box to report that the voice key was triggered.'''
    global usbbox
    usbbox.buttons.enabled = myButtons(1)
    usbbox.port2.state = myLights(1)
    detected = False
    while not detected:
        report = usbbox.wait_for_keydown()
        if report != None:
            if (report.key_code == 64) or (report.key_code == 0):
                detected = True
    return report.rtc

def waitForButton():
    '''Wait for the button box to report that an enabled button was pressed.'''
    global usbbox
    detected = False
    while not detected:
        report = usbbox.wait_for_keydown()
        if report != None:
            if report.key_code in range(8):
                detected = True
    return report.key_code,report.rtc

#create a window
myWin = visual.Window((1024,768), allowGUI=False, color=(-1,-1,-1), colorSpace='rgb', monitor='testMonitor', winType='pyglet')

# create a trial clock and display instructions
trialClock = core.Clock()
textStim = visual.TextStim(myWin,text='press each lighted button as fast as you can', font='Arial', height=.1,
                           color=(1,1,1), colorSpace='rgb', pos=(0,0))
textStim.draw()
myWin.flip()

# set up the button box
setup_bbox()

# create a list of buttons to test and randomize it
buttons = [0,1,2,3,4,5,6,7]
random.shuffle(buttons)

# loop through the button list 
for i in buttons:
    enableButtons(i) #enable only the given button
    reset_bbox_clock() # reset the bbox clock
    trialClock.reset() # and the psychopy trial clock
    lights(i) # turn on the light for the give buttonList
    btn,bboxTime = waitForButton() # wait for the button to be pressed and get the button number and bbox time
    trialTime = trialClock.getTime() # mark the time on the psycopy trial clock
    #print out the button pressed, and the RT measured both by psychopy and the button box
    print 'button: %d   bbox time: %7d        psychoPy time: %7d' % (btn,bboxTime,round(trialTime*1000))
    
lights(None) # turn out all the lights


