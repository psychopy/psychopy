#!/usr/bin/env python

"""Demo program to illustrate using ioLabs button box

To run this test the ioLab library needs to be installed (it is included with
the Standalone distributions of PsychoPy).

"""

__author__ = 'Jonathan Roberts'

import random
from numpy import ubyte
from psychopy import core, visual, event
try:
   import ioLabs
except RuntimeError, errMsg:
    print('Is an ioLabs button-box connected and turned on? (import failed: "'+str(errMsg)+'")')
    core.quit()

class BBox(ioLabs.USBBox):
    def __init__(self):
        ioLabs.USBBox.__init__(self)
        #disable all buttons and lights 
        self.buttons.enabled = 0x00 #8 bit pattern 0=disabled 1=enabled
        self.port2.state = 0xFF #port2 is the lights on the bbox - 8 bit pattern 0=on 1=off
        self.keyevents = []
        # set up callbacks for button and voice key events.
        # when the button box detects a button press or voice key, it will call this function with a report describing the event
        # this routine simply appends the report to the keyevents attribute of our BBox object
        # so when waiting for a button we simply watch self.keyevents to see if it is not empty
        def key_press(report):
            self.keyevents.append(report)
        self.commands.add_callback(ioLabs.REPORT.KEYDN,key_press)

    def makeBitPattern(self,buttonList):
        if buttonList == None:
            return(0)
        elif type(buttonList) == int:
            return(2**buttonList)
        elif type(buttonList) in (list,tuple):
            bits = 0
            for btn in buttonList:
                bits = bits + 2**(btn)
            return(ubyte(bits))
        else:
            print 'invalid button list - must be None, an integer or a list of integers'
        
    def enableButtons(self,buttonList=[0,1,2,3,4,5,6,7],voice=False):
        '''enable the specified buttons
        the argument should be one of the following:
        None - disable all buttons
        an integer - enable a single buttonList
        a list of integers - enable all buttons in the list
        
        set voice to True to enable the voiceKey - gets reported as button 64'''
    
        self.int0.enabled = int(voice)
        self.buttons.enabled = self.makeBitPattern(buttonList)    
    
    def lights(self,lightList=[0,1,2,3,4,5,6,7]):
        '''turn on only the specified LEDs - 
        the argument should be one of the following:
        None - turn off all LEDs
        an integer - turn on a single LED
        a list of integers - turn on all LEDs in the list'''
        self.leds.state = ~self.makeBitPattern(lightList) # in the bit pattern for lights, 1 is on and 0 is off
        
    def waitForButton(self):
        '''Wait for the button box to report that an enabled button or voice key was pressed/triggered.
        voice key gets reported as button 64'''
        while not self.keyevents:
            self.process_received_reports()
        return self.keyevents[0].key_code
    
    def clearEvents(self):
        '''clear out any button or voice key events that have happened up to now'''
        self.keyevents[:] = []
        self.clear_received_reports()

#create a window
myWin = visual.Window((1024,768), fullscr=False, winType='pyglet')

# create a trial clock and instructions and fixation stimulus
trialClock = core.Clock()
instructions = visual.TextStim(myWin,
                                                text = '6 trials:\nhit the left lighted button when you see the word "left".\nhit the right lighted button when you see the word "right".\nhit space to start...',
                                                wrapWidth = 1.8, height =.08)
fixation = visual.TextStim(myWin,text = '+')
target = visual.TextStim(myWin,text = 'to be filled it during trial loop')

# set up the button box
myBBox = BBox()

#
buttons = [1,6]
labeledResponse = {1:'left', 6:'right'}
stims = ['left']*3+['right']*3 # make a list of stims with 3 'lefts' and 3 'rights'
random.shuffle(stims) # shuffle the list

# turn on the lights above the buttons we will be using and enable them
myBBox.lights(buttons)
myBBox.enableButtons(buttons)

# show instructions, wait for spacebar
instructions.draw()
myWin.flip()
event.waitKeys(['space'])
myWin.flip()

# trial loop
for stim in stims:
    core.wait(0.5) #ITI

    # brief fixation point
    fixation.draw()
    myWin.flip()
    core.wait(0.5)

    target.setText(stim)
    target.draw()
    myBBox.clearEvents() # clear any events that have already happened
    myWin.flip()
    trialClock.reset() #reset the trial clock immediately after the screen flip
    btn = myBBox.waitForButton()
    rt = trialClock.getTime() # get the time as soon as we detect a keyevent
    rt = round(rt*1000,2) #convert to msec with 2 digits to right of decimal pt.
    if  labeledResponse[btn] == stim:
        print 'correct', btn, rt
    else:
        print 'wrong', btn, rt
    myWin.flip()

myBBox.lights(None) # turn out all the lights


