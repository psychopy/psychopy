#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This demo was created by Andrew Schofield to show how to use the advanced input/output 
functionality in the bits.py module. 

It also acts as a test routine to make sure your device is working and that the 
bits.py module is intact. 

The bits.py module mostly provides wrapper functions for getting control of the
CRS hardware family, Bits++, Bits#, Display++ and their variants. ViSaGe devices
are not supported unless you have one with a Bits# emulation mode. 

Most but not all of the bits.py commands are tested. Similarly
most but not all of the CRS functionality is tested often in combination. But there 
are two many combinations to test every thing.

There is some support for driving stereo goggles (CRS FE1) via the D25 feature connector 
output. Bits# has a stereo goggles port which works differently and is not tested. Nor is 
support for it currently provided in bits.py.

Stereo via frame interleaving is not recommended on a Display++ due to LCD pixel transition speeds.
CRS have a 3D version of Display++ which uses polarised galsses and line interleaving. This is not
specifically implemented in bits.py yet but you can still build an stereo image yourself.

Bits++ support is relatively minimal with, in particular, digital inputs not being supported.

To work effectively on a Bits++ box you will need an Oscilloscope and:
    Connect DOUT1 (pin2) to Oscilloscope channel A"
    Connect DOUT5 (pin6) to Oscilloscope channel B"
You will then observe changes in those outputs.

To work effectively on all other devices you will need to:

    Connect DOUT1 (pin 2) to DIN7 (pin 21)
    Connect DOUT5 (pin 6) to DIN8 (pin 24)
    Connect DOUT6 (pin 7) to DIN9 (pin 25)

and connect Analog OUT 1 to Analog IN 1 if you have a Bits# or a Display++
with the optional Analog factures. This will cunningly allow the CRS device to monitor
its own outputs. Testing both output and input features at once.

You can select the CRS hardware and options in a dialog box.
Note Screen is the screen number of your CRS connected monitor = 0 or 1.
(your working in coder after all).

Enter None to see what happens if there is 
no device and hence no serial comms.

Note that the monitor and LUT settings don't really matter much.

You will get warnings about stuff being found on the input buffer. This is because the command to
stop the CRS device from sending data expects a return message to say that data collection has stopped
but will always find the last chunk of data recorded instead.

See xxxxx for a description of the bits.py approach to CRS hardware and programmer guide.

"""
from psychopy import locale_setup, sound, gui, visual, core, data, event, logging
from psychopy import monitors, filters, gamma 
from psychopy.hardware import crs
from scipy import misc

from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from time import sleep, clock, time
import os  # handy system and path functions
import sys  # to get file system encoding


# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))#.decode(sys.getfilesystemencoding())
os.chdir(_thisDir)

# Store info about the experiment session
expName = 'crsTest'  # from the Builder filename that created this script
expInfo = {'Device': 'Display++',
           'Analog': 'No',
           'Touch screen': 'Yes',
           'Button box': 'CB6',
           'Monitor': 'Display++160',
           'LUTfile': 'invGammaLUT.txt',
           'Screen': '1'}
dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)
if dlg.OK == False:
    core.quit()  # user pressed cancel


#===================================================================#
# Setup the Window
print("Open window")
win = visual.Window(
    size=(800, 600), fullscr=True, screen=int(expInfo['Screen']),
    allowGUI=False, allowStencil=False,
    monitor=expInfo['Monitor'], color=[0,0,0], colorSpace='rgb',
    blendMode='avg', useFBO=True,
    units='deg')
# store frame rate of monitor if we can measure it
expInfo['frameRate'] = win.getActualFrameRate()
if expInfo['frameRate'] != None:
    frameDur = 1.0 / round(expInfo['frameRate'])
else:
    frameDur = 1.0 / 60.0  # could not measure, so guess

# Initialize components for Routine "preflight"
#preflightClock = core.Clock()


#frameRate=win.getActualFrameRate()
#print(expInfo['frameRate'])

mon=monitors.Monitor(expInfo['Monitor'],distance=56)

#=======================================================================================#
#Opening the appropriate a CRS class of the desired / necessary type
print("open CRS")
if expInfo['Device']=='Bits++':
    bits = crs.BitsPlusPlus(win, mode='bits++',rampType=1) 
if expInfo['Device']=='Bits#':
    bits = crs.BitsSharp(win, mode='bits++',checkConfigLevel=1) 
if expInfo['Device']=='Display++' or expInfo['Device']=='None':
    if expInfo['Touch screen']=="Yes":
        if expInfo['Device']=='Display++':
            bits = crs.DisplayPlusPlusTouch(win, mode='bits++',checkConfigLevel=1) 
        else:
            bits = crs.DisplayPlusPlusTouch(win, mode='bits++',checkConfigLevel=1,noComms=True) 
    else:
        if expInfo['Device']=='Display++':
            bits = crs.DisplayPlusPlus(win, mode='bits++',checkConfigLevel=1) 
        else:
            bits = crs.DisplayPlusPlus(win, mode='bits++',checkConfigLevel=1,noComms=True) 

#=======================================================================================#
# If Bits# or Display++ initialise the device.                                          #
# This can also be done via parameter setters but this illustrates the low level send   #
# commands.                                                                              #
if  expInfo['Device'] != 'Bits++':
    #bits = crs.BitsSharp(win, mode='bits++') 
    #gamma.setGamma(win.winHandle._dc, 1.0, 1)
    bits.sendMessage('$TemporalDithering=[ON]\r')
    bits.read(timeout=0.1)
    bits.sendMessage('$VideoFrameRate\r')
    bits.read(timeout=0.1)
    lutfile = expInfo['LUTfile']
    msg='$enableGammaCorrection=['+lutfile+']\r'
    bits.sendMessage(msg)
    bits.read(timeout=0.1)
    bits.sendMessage(r'$EnableTouchScreen=[OFF]\e')
    bits.read(timeout=0.1)
    bits.sendMessage('$Stop\r')
    # Clear the buffer
    bits.flush()
    bits.RTBoxDisable()
    bits.flush()
    print("OK I seem to have cleared the buffer now")

#=======================================================================================#
# House keeping
    print("Connect DOUT1 (pin 2) to DIN7 (pin 21)")
    print("Connect DOUT5 (pin 6) to DIN8 (pin 24)")
    print("Connect DOUT6 (pin 7) to DIN9 (pin 25)")
    if expInfo['Device'] == 'Bits#' or expInfo['Analog'] == 'Yes':
        print("Connect Analog OUT 1 TO Analog IN 1")
else:
    print("Connect DOUT1 (pin2) to Oscilloscope A")
    print("Connect DOUT5 (pin6) to Oscilloscope B")

sleep(10)

# Make a grating
grating = visual.GratingStim(
    win=win, name='grating',units='norm', 
    tex='sin', mask=None,
    ori=0, pos=(0,0), size=(1, 1), sf=5, phase=1.0,
    color=[1,1,1], colorSpace='rgb', opacity=1,blendmode='avg',
    texRes=128, interpolate=True, depth=-2.0)

bits.resetClock()
bits.win.flip()
sleep(1)

#=============================================================================#
#LUT test
# Varies the contrast of a grating by setting the software LUT in bits++ mode
# via a Tlock command.
print("1: LUT test")
print("Should see pulsating grating")
frameN=-1
while frameN < bits.frameRate*5:
    # get current time
    frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
    # update/draw components on each frame
    #bits.setAnalog(AOUT1 = 5*sin(t*50), AOUT2 = 5*cos(t*50))
    # *thanksMsg* updates
    if frameN == 0:
        grating.setAutoDraw(True)
    bits.setContrast((sin(np.pi*frameN/bits.frameRate)))
    win.flip()
grating.setAutoDraw(False)
bits.setContrast(1.0)
win.flip()



#=============================================================================#
# Trigger and goggle tests
print("2a: Triggers test")
# Sets up a 2ms trigger pulse and issues via TLock 
# Recoding Digital inputs via the status logging commands
bits.setTrigger(0b0000000010,0.002,0.002)
bits.startTrigger()
bits.win.flip()
T=clock()
if expInfo['Device'] != 'Bits++': #Bist# / Display++ version
    # Recording Digital inputs via the status logging commands

    # Example of starting and stopping status log
    bits.startStatusLog()
    while clock()-T<5:
        bits.win.flip()
    bits.stopStatusLog()
    
    #Example of reading status values
    vals = bits.getAllStatusValues()
    if vals:
        if len(vals) > 20:
            print("All status values")
            for i in range(-20,0):
                print(vals[i])
            print("DIN7 should change lots")
    
    #Example of reading status events
    vals = bits.getAllStatusEvents()
    if vals:
        if len(vals) > 20:
            print("All status events")
            for i in range(-20,0):
                print(vals[i])
            print("Input 7 should have 2ms high every frame.")
else: # Bits++ version
    print("Should observe 2ms pulses on Ch A")
    while clock()-T<5:
        bits.win.flip()
bits.stopTrigger()
bits.win.flip()
sleep(5)
if expInfo['Device'] != 'Bits++':
    bits.flush()

#=============================================================================#
print("2b: Goggles test")
# Sets up alternating left / right goggle control via D25 output and the TLock
bits.startGoggles(left=0,right=1)
bits.win.flip()
T=clock()
if expInfo['Device'] != 'Bits++': # Bits# and Display++ version
    # Recording Digital inputs via the status logging commands
    
    # Example of starting and stopping status log
    bits.startStatusLog()
    while clock()-T<5:
        bits.win.flip()
    bits.stopStatusLog()
    bits.flush()
    
    #Example of reading status values
    vals = bits.getAllStatusValues()
    if vals:
        if len(vals) > 20:
            print("All status values")
            for i in range(-20,0):
                print(vals[i])
            print("DIN8 should change lots")
    
    #Example of reading status events
    vals = bits.getAllStatusEvents()
    if vals:
        if len(vals) > 20:
            print("All status events")
            for i in range(-20,0):
                print(vals[i])
            print("Input 8 should change state every frame.")
else: # Bits++ version
    print("Should observe square wave on Ch B")
    while clock()-T<5:
        bits.win.flip()

bits.stopGoggles()
bits.win.flip()
sleep(5)
if expInfo['Device'] != 'Bits++':
    bits.flush()

#=============================================================================#
print("2c: Goggles with  triggers")
# Drive the goggles and a trigger at the same time.
# Note uses trigger from 2a as this will have been kept
# even when the goggles were used ioin 2b.
bits.startTrigger()
bits.startGoggles()
bits.win.flip()
T=clock()
if expInfo['Device'] != 'Bits++':# Bits# and Display++ version
    # Recording Digital inputs via the status logging commands
    
    # Example of starting and stopping status log
    bits.startStatusLog()
    while clock()-T<5:
        bits.win.flip()
    bits.stopStatusLog()
    bits.flush()
    
    #Example of reading status values
    vals = bits.getAllStatusValues()
    if vals:
        if len(vals) > 20:
            print("All status values")
            for i in range(-20,0):
                print(vals[i])
            print("DIN7 and DIN8 should change lots")
            
    #Example of reading status events
    vals = bits.getAllStatusEvents()
    if vals:
        if len(vals) > 20:
            print("All status events")
            for i in range(-20,0):
                print(vals[i])
            print("Input 7 should have 2ms high every frame.")
            print("Input 8 should change state every frame.")
else: # Bits++ version
    print("Should observe 2ms pulses on Ch A")
    print("Should observe square wave on Ch B")
    while clock()-T<5:
        #sleep(0.002)
        bits.win.flip()

bits.stopGoggles()
bits.stopTrigger()
bits.win.flip()
sleep(5)

if expInfo['Device'] != 'Bits++':
    bits.flush()

#=============================================================================#
# If using a bits++ all available tests are now done
if expInfo['Device'] == 'Bits++':
    print("All tests done")
else: # otherwise carry on
    bits.flush() # Flush the com port often
    
    print("2d: Poll status")
    #=============================================================================#
    # Status polling
    # Example of using the pollStatus command
    bits.pollStatus()
    # Get the digital word form of DIN states
    valD = bits.getDigitalWord()
    # Example of how to print it
    if valD:
        print(bin(valD['DWORD']))
    
    #=============================================================================#
    #RTBox operation
    # Example of RTBox Enable, here using a bespoke mapping to route DIN9 to btn1
    print("2e: Single shot trigger detected by RTBox  via DIN")
    bits.RTBoxEnable(mode=['down'], map=[('btn1','Din9')])
    
    # Example of using send trigger to issue a trigger that will pulse Dout6 which would be connected to DIN
    bits.sendTrigger(0b1111111,0,0.004)
    bits.win.flip()  # win.flip needed to finish off the trigger

    #Example of using RTBoxKeysPressed to detect button box events.
    if not bits.noComms: # noComms safe
        # Wait for a key - its probably already been recvied anyway.
        while not bits.RTBoxKeysPressed(1):
            continue
    # Get the response
    btn=bits.getRTBoxResponse()
    # Example button response
    if btn:
        print(btn)
    else:
        print("No button")
    bits.flush()
    btn = None
    # Disable the RTBox for now
    bits.RTBoxDisable()
    sleep(5)

    #=============================================================================#
    # Example for making the CRS device beep
    print("3a: Beep test")
    bits.beep(400,0.5)
    sleep(0.5)
    
    #=============================================================================#
    # Using Tlock to reset the CRS device clock
    print("3b: Clock Reset test")
    bits.resetClock()
    bits.win.flip()
    sleep(1)
    T=clock()
    
    #=============================================================================#
    # Example for using PollStatus to read the device time
    bits.pollStatus()
    print("Time taken to poll status = ",clock()-T)
    val = bits.getStatus()
    if val:
        print("Time recorded by device should be about 1s. Actually = ", val.time)
    sleep(5)
    # Just to make sure the status log has been stopped
    bits.sendMessage('$Stop\r')
    bits.flush()

    #=============================================================================#
    # Example Using statusBox to record key presses
    
    print("4a: Using statusBox and Din")
    bits.statusBoxEnable(mode = ['up','IO10'])
    bits.sendTrigger(0b1111111,0,0.004)
    bits.win.flip()  # win.flip needed to finish off the trigger

    if not bits.noComms: # noComms safe
        # Wait for a key - its probably already been recvied anyway.
        while not bits.statusBoxKeysPressed(1):
            continue
    # Disable the status box as soon as you don't need it.
    bits.statusBoxDisable()
    bits.stopTrigger()
    bits.win.flip() # win.flip to make sure triggers are off.
    # Get the response
    btn = bits.getStatusBoxResponse() # just get first response and ditch others.
    # Example button response
    if btn:
        print(btn)
    else:
        print("No button")

    btn = None
    
    bits.flush()
    sleep(5)
    
    #=============================================================================#
    #   Example using the statusBox with different button boxes
    print("4b: Using statusBox with a button box")
    
    # Enables different statusBox defaults depending on users input
    if expInfo['Button box'] == 'CB6': #IR box
        bits.statusBoxEnable(mode=['CB6','Down'])
        print("Press a button on the Box")
        
        #Example statusBoxWait command - waits for a button press
        button = bits.statusBoxWait()
        if button:
            print(button)
    elif expInfo['Button box'] == 'IO6': # A wired box
        bits.statusBoxEnable(mode=['IO6','Down'])
        print("Press one of first 3 buttons on the Box")
        
        #Example statusBoxWait command - waits for a button press
        button = bits.statusBoxWait()
        if button:
            print(button)
    elif expInfo['Button box'] == 'IO': # A wired box with only 3 buttons
        bits.statusBoxEnable(mode=['IO','Down'])
        print("Press of first 3 buttons on the Box")
        
        #Example statusBoxWait command - waits for a button press
        button = bits.statusBoxWait()
        if button:
            print(button)
    
    #=============================================================================#
    #   Example using the statusBox to get multiple responses
    #   We've left the statusBix running for this
    print("4c: Multiple buttons")
    print("Now press some buttons")
    T = clock()
    while clock()-T<10:
        bits.win.flip()
    bits.statusBoxDisable()
    print('Some buttons presses ',bits.statusBoxKeysPressed())
    res = bits.getAllStatusBoxResponses()
    if res:
        print(len(res))
        print(res)
    bits.flush()

    #=============================================================================#
    # More RTBox usage examples
    print("4d: RTBox test")
    bits.flush()
    
    # Enables different RTBox defaults depending on users input
    if expInfo['Button box'] == 'CB6': #IR box
        bits.RTBoxEnable(mode=['CB6','Down'])
        print("Press a button on the Box")
        
        #Example RTBoxWait command - waits for a button press
        button = bits.RTBoxWait()
        if button:
            print(button)
    elif expInfo['Button box'] == 'IO6': # A wired box
        bits.RTBoxEnable(mode=['IO6','Down'])
        print("Press one of first 3 buttons on the Box")
        
        #Example RTBoxWait command - waits for a button press
        button = bits.RTBoxWait()
        if button:
            print(button)
    elif expInfo['Button box'] == 'IO': # A wired box
        bits.RTBoxEnable(mode=['IO','Down'])
        print("Press of first 3 buttons on the Box")
        
        #Example RTBoxWait command - waits for a button press
        button = bits.RTBoxWait()
        if button:
            print(button)
    
    #=============================================================================#
    # Example of how to calibrate or charaterise the RTBox timer
    # relative to the host clock
    print("4e: RTBox calibration test")
    res=bits.RTBoxCalibrate(5)
    bits.RTBoxDisable()
    bits.flush()
    print('Average clock difference =', res)
    
    #=============================================================================#
    # Commands for analog outputs, used if we have a Bits# or a 
    # display++ with analog feature
    if (expInfo['Device'] == 'Bits#' 
        or expInfo['Device'] == 'None' 
        or expInfo['Analog'] == 'Yes'):
        print("5: Analog tests")
        
        
        #=============================================================================#
        # Example of sending an analog out - will continue while we poll the status
        print("5a: Analog only using pollStatus")
        bits.sendAnalog(2,2)
        sleep(1) # let the output it settle
        bits.pollStatus()
        
        # Example for getting analog values and displaying them
        val = bits.getAnalog()
        bits.win.flip()
        #bits.stopAnalog
        print("Analog 1 should be = 2v")
        if val:
            print(val['ADC'])
        sleep(5)
        bits.flush()
        
        #=============================================================================#
        # Example using triggers and analog outputs at the same time.
        print("5b: Analog and triggers")
        # Example using set analog
        bits.setAnalog(3,3)
        # Set a long trigger
        bits.setTrigger(0b1111111101,0.0,0.0084)
        
        #Start both outputs
        bits.startTrigger()
        bits.startAnalog()
        bits.win.flip()
        sleep(1)
        bits.pollStatus()
        valA = bits.getAnalog()
        valD = bits.getDigitalWord()
        bits.stopAnalog
        bits.stopTrigger()
        print("Analog 1 should be = 3v")
        if valA:
            print(valA['ADC'])
        print("Digital word should have bit 8 low")
        if valD:
            print(bin(valD['DWORD']))
        sleep(5)
        bits.flush()
        
        #=============================================================================#
        # Example using triggers, goggles and analog all at once
        # Also test the ability of triggers to service people messing with
        # Goggles and Analog outs as these all use the same communication channel.
        print("5c: Goggles, analog and triggers")
        bits.setAnalog(3,3)
        bits.setTrigger(0b0000000010,0.002,0.002)
        
        # Test to see if triggers can service lots of toing a froing
        # of the analog and goggles outputs.
        bits.startAnalog()
        bits.win.flip()
        bits.startGoggles()
        bits.win.flip()
        bits.stopAnalog()
        bits.win.flip()
        bits.stopGoggles()
        bits.win.flip()
        
        # Now set them all going
        bits.startGoggles()
        bits.startAnalog()
        bits.startTrigger()
        bits.win.flip()
        T=time()
        
        #Setting the status event parameters to determine which events
        #are recorded. Now only 'up' events will be registered
        bits.setStatusEventParams(DINBase=0b1111111111, 
                                      IRBase=0b111111, 
                                      TrigInBase=0,
                                      ADCBase=0,
                                      threshold=1.0,
                                      mode=['up'])
        bits.startStatusLog()
        while time()-T<5:
            bits.setAnalog(5*sin((time()-T)), 0)
            bits.win.flip()
        bits.stopStatusLog()
        sleep(1)
        bits.flush()
        
        # Analog should show up on the status log
        vals = bits.getAllStatusValues()
        if vals:
            if len(vals) > 1:
                print("All status values")
                for i in range(1,len(vals),700):# only read every 700'th status report as 
                    # analog inputs update slowly relative to everything else
                    print(vals[i])
                print("Should see analog 1 changing")
                
        #The Goggles and triggers are best detected as events
        vals = bits.getAllStatusEvents()
        if vals:
            if len(vals) > 20:
                print("All status events")
                for i in range(-20,0):
                    print(vals[i])
            print("Input 7 should go up once every frame.")
            print("Input 8 should go up every other frame.")
        bits.stopTrigger()
        bits.stopGoggles()
        bits.stopAnalog()
        bits.win.flip()
        
        #=============================================================================#
        # Example for detecting changes on the analog inputs via status events
        # Not the analog threshold was set to 0.5 volts above
        print("5d: Detecting analog events via status")
        bits.setStatusEventParams(DINBase=0b1111111111, 
                                      IRBase=0b111111, 
                                      TrigInBase=0,
                                      ADCBase=0,
                                      threshold=1.0,
                                      mode=['Up'])
        bits.startStatusLog()
        bits.startAnalog()
        T = time()
        while time()-T<10:
            bits.setAnalog(5*sin((time()-T)), 0)
            bits.win.flip()
        bits.stopStatusLog()
        sleep(1)
        bits.stopAnalog()
        bits.flush()
        
        # Analog should show up on the status log
        vals = bits.getAllStatusValues()
        if vals:
            if len(vals) > 1:
                print("Status values")
                for i in range(1,len(vals),700):# only read every 700'th status report as 
                    # analog inputs update slowly relative to everything else
                    print(vals[i])
                print("Should see analog 1 changing")
                
        #Analog changes as events
        vals = bits.getAllStatusEvents()
        if vals:
            if len(vals) > 5:
                print("Status events")
                for i in range(len(vals)):
                    print(vals[i])
            print("Should see some events on Analog 1.")
            print("May get spurious events on some Bits# boxes.")
        bits.stopAnalog()
        bits.win.flip()
       
        #=============================================================================#
        # Example for usinf the statusBox to detect analog events
        print("5e: Using status box to detect analog events")
        bits.sendAnalog(0.5,0.5)
        bits.win.flip
        bits.win.flip
        bits.statusBoxEnable(mode=['Analog','Up','down'], threshold = 3.25)
        bits.sendAnalog(4.0,4.0)
        bits.win.flip
        sleep(2)
        # need to set analog low again by more than
        # threshold in order to record new event
        bits.sendAnalog(0.5,0.5)
        bits.win.flip
        sleep(2)
        bits.sendAnalog(4.0,4.0)
        bits.win.flip
        sleep(2)
        if not bits.noComms: # noComms safe
        # Wait for a key - its probably already been recvied anyway.
            while not bits.statusBoxKeysPressed():
                continue
        # Get the response
        bits.statusBoxDisable()
        btn = bits.getAllStatusBoxResponses()
        
        # Example button response
        if btn:
            print(btn)
        else:
            print("No button")
    
    #=============================================================================#
    # Touch screen tests
    if ((expInfo['Device'] == 'Display++' and expInfo['Touch screen'] == 'Yes')
          or expInfo['Device'] == 'None'):
        print("6: Touch Screen test")
        
        #=============================================================================#
        #Example of a touch enable, wait, disable cycle
        print("6a: Touch the screen")
        bits.touchEnable()
        val=bits.touchWait() # pause while waiting for touch
        bits.touchDisable()
        if val:
            print(val)
        sleep(5)
        
        #=============================================================================#
        # Example of a touch enable, touchPressed, disable cycle
        print("6b: Touch the screen again")
        bits.touchEnable()
        if not bits.noComms:
            while not bits.touchPressed(): # idle while waiting for touch
                # But you could do stuff here
                continue
        # Example of getAllTouchResponses()
        vals=bits.getAllTouchResponses()
        bits.touchDisable()
        if vals:
            for i in range(len(vals)):
                print(vals[i])
            
        sleep(5)
        
        #=============================================================================#
        # Exampe of using a touch log cycle to get lots of touch responses
        bits.startTouchLog()
        print("6c: Touch the screen lots")
        sleep(10)
        bits.stopTouchLog()
        
        #=============================================================================#
        # Example of getting the full touch log and then extracting events
        bits.getTouchLog()
        vals=bits.getTouchEvents()
        if vals:
            for i in range(len(vals)):
                print(vals[i])
    print("All tests done")
del bits
win.close()
core.quit()
