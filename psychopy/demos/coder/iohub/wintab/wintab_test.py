from __future__ import division
#!/usr/bin/env python2
from psychopy import core, visual
from psychopy.iohub import launchHubServer, EventConstants
from win32api import LOWORD, HIWORD
import math
FRAC = LOWORD
INT = HIWORD

# if no keyboard or tablet data is received for test_timeout_sec,
# the test program will exit.
test_timeout_sec = 300 # 5 minutes

# Pen graphics related settings
pen_size_min = 0.033
pen_size_range = 0.1666
pen_opacity_min = 0.0

# Runtime global variables
tablet=None
last_evt=None
last_evt_count=0

def start_iohub():
    import time

    exp_code='wintab_evts_test'
    sess_code='S_{0}'.format(long(time.mktime(time.localtime())))
    print('Current Session Code will be: ', sess_code)

    kwargs={'experiment_code':exp_code,
            'session_code':sess_code,
            'wintab.WintabTablet':{'name':'tablet'}}

    return launchHubServer(**kwargs)

def createPsychopyGraphics():
    #
    # Initialize Graphics
    #
    myWin = visual.Window(units='pix', color=[128, 128, 128],
                           colorSpace='rgb255', fullscr=True, allowGUI=False)

    # hide the OS system mouse when on experiment window
    mouse.setPosition((0,0))
    mouse.setSystemCursorVisibility(False)

    #INITIALISE SOME STIMULI
    evt_text = visual.TextStim(myWin, units='norm', height = 0.05,
                               pos=(0, .9), text="")
    evt_text._txt_proto='Tablet: pos:\t{x},{y},{z}\t' \
                        'pressure: {pressure}\t' \
                       # 'orientation: {orient_azimuth},{orient_altitude}'

    instruct_text = visual.TextStim(myWin, units='norm', pos=(0, -.9),
                              height = 0.05, text="instruct_text")
    instruct_text._start_rec_txt ="Press 's' to start wintab reporting. " \
                                  "Press 'q' to exit."
    instruct_text._stop_rec_txt ="Press 's' to stop wintab reporting. " \
                                   "Press 'q' to exit."
    instruct_text.text = instruct_text._start_rec_txt

    pen_guass = visual.PatchStim(myWin, units='norm', tex="none",
                                   mask="gauss", pos=(0,0),
                                   size=(pen_size_min,pen_size_min),
                                   color='red', autoLog=False, opacity = 0.0)

    pen_tilt_line = visual.Line(myWin, units='norm', start=[0,0],
                                end=[0.5,0.5], lineColor=(1,1,0), opacity = 0.0)
    return myWin, (evt_text, instruct_text, pen_guass, pen_tilt_line)

#TODO: Add support for x,y,z,pressure fields that have been normalized in clienmt.wintab class

def getPenPos(tablet_event):
    xrange=float(tablet.axis['x_axis']['axMax']- tablet.axis['x_axis']['axMin'])
    yrange=float(tablet.axis['y_axis']['axMax']- tablet.axis['y_axis']['axMin'])
    return (-1.0+(tablet_event.x/xrange)*2.0,-1.0+(tablet_event.y/yrange)*2.0)

def getPenSize(tablet_event):
    prange = float(tablet.axis['tip_pressure_axis']['axMax']-tablet.axis['tip_pressure_axis']['axMin'])
    pevt = tablet_event.pressure
    return pen_size_min + (pevt/prange)*pen_size_range

def getPenOpacity(tablet_event):

    zrange=float(tablet.axis['z_axis']['axMax']- tablet.axis['z_axis']['axMin'])
    z=zrange-tablet_event.z
    sopacity = pen_opacity_min + (z/zrange)*(1.0-pen_opacity_min)
    return sopacity

# TODO: Move tilt calc into client.wintab class

def getPenTilt(tablet_event):
    '''
    Get the dx,dy screen position in norm units that should be used
    when drawing the pen titl line graphic end point.
    '''
    palt, pangle = tablet_event.tilt
    return palt*math.sin(pangle), palt*math.cos(pangle)

if __name__ == '__main__':
    # Start iohub process and create shortcut variables to the iohub devices
    # used during the experiment.
    io = start_iohub()

    keyboard = io.devices.keyboard
    mouse = io.devices.mouse
    tablet = io.devices.tablet

    # Check that the tablet device was created without any errors
    if tablet.getInterfaceStatus() != "HW_OK":
        print "Error creating Wintab device:", tablet.getInterfaceStatus()
        print "TABLET INIT ERROR:", tablet.getLastInterfaceErrorString()

    else:
        # Wintab device is a go, so setup and run test runtime....

        # Get Wintab device model specific hardware info and settings....
        # Create the PsychoPy Window and Graphics stim used during the test....
        myWin, vis_stim = createPsychopyGraphics()
        # break out graphics stim list into individual variables for later use
        evt_text, instruct_text, pen_guass, pen_tilt_line = vis_stim

        # Get the current reporting / recording state of the tablet
        is_reporting = tablet.reporting
        # remove any events iohub has already captured.
        io.clearEvents()

        # create a timer / clock that is used to determine if the test
        # should exit due to inactivity
        testTimeOutClock = core.Clock()

        while testTimeOutClock.getTime() < test_timeout_sec:
            # check for keyboard press events, process as necessary
            kb_events = keyboard.getPresses()
            if kb_events:
                testTimeOutClock.reset()
            if 'q' in kb_events:
                # End the text...
                break
            if 's' in kb_events:
                # Toggle the recording state of the tablet....
                is_reporting = not is_reporting
                tablet.reporting = is_reporting
                if is_reporting:
                    instruct_text.text = instruct_text._stop_rec_txt
                else:
                    instruct_text.text = instruct_text._start_rec_txt

            # check for any tablet events, processing as necessary
            wtab_evts = tablet.getSamples()
            last_evt_count=len(wtab_evts)
            if is_reporting:
                if last_evt_count:
                    last_evt = wtab_evts[-1]

                    testTimeOutClock.reset()

                    # update the text that displays the event pos, pressure, etc...
                    evt_text.text=evt_text._txt_proto.format(**last_evt.dict)

                    # update the pen position stim based on
                    # the last tablet event's data
                    if last_evt.z == 0:
                        # pen is touching tablet surface
                        pen_guass.color='green'
                    else:
                        # pen is hovering just above tablet surface
                        pen_guass.color='red'

                    pen_guass.pos = getPenPos(last_evt)
                    pen_guass.size = getPenSize(last_evt)
                    pen_guass.opacity = pen_tilt_line.opacity = \
                        getPenOpacity(last_evt)

                    pen_tilt_line.start = pen_guass.pos

                    pen_tilt_xy = getPenTilt(last_evt)
                    pen_tilt_line.end = pen_guass.pos[0]+pen_tilt_xy[0],\
                                    pen_guass.pos[1]+pen_tilt_xy[1]
            else:
                last_evt = None
                
            if last_evt is None:
                    last_evt_count = 0
                    pen_guass.opacity = pen_tilt_line.opacity = 0
                    evt_text.text=''

            for stim in vis_stim:
                stim.draw()

            myWin.flip()#redraw the buffer

        if testTimeOutClock.getTime() >= test_timeout_sec:
            print "Test Time Out Occurred."
