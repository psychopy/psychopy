#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example using the iohub Wintab Pen device. Demo requires a properly
installed Wintab compatible device running on Windows.
(Wacom digital pen, MS Surface v1 or v2, ...)
"""
import os
import time

import _wintabgraphics as wintabgraphics
from psychopy import core, visual
from psychopy.gui import fileSaveDlg
from psychopy.iohub import launchHubServer

# Default session data file name
DEFAULT_SESSION_CODE = u's1234'

# RGB255 color to use for the experiment window background color. Must be a
# list or tuple of the form [r,g,b], where r,g, and b are values between 0
# (black) and 255 (white).
DEFAULT_SCREEN_COLOR = [128, 128, 128]

# The height of any text that is displayed during experiment trials. The value
# is in norm units, with a maximum value of 1.0.
DEFAULT_TEXT_STIM_HEIGHT = 0.05

# List of key values that will cause the experiment to end if detected by a
# keyboard key press event.
TERMINATE_EXP_KEYS = ['escape', ]

# Defaults for PenPositionStim
# Pen gaussian point color when hover is detected
PEN_POS_HOVER_COLOR = (0, 0, 255)

# Pen gaussian point color when pen press is detected
PEN_POS_TOUCHING_COLOR = (0, 255, 0)

# Color of the pen tilt line graphic 
PEN_POS_ANGLE_COLOR = (255, 255, 0)

# Pixel width of the pen tilt line graphic 
PEN_POS_ANGLE_WIDTH = 1

# Control the overall length of the pen tilt line graphic.
# 1.0 = default length. Set to < 1.0 to make line shorter, or > 1.0 to
# make line longer. 
PEN_POS_TILTLINE_SCALAR = 1.0

# Minimum opacity value allowed for pen position graphics.
# 0.0 = pen position disappears when pen is not detected.
PEN_POS_GFX_MIN_OPACITY = 0.0

# Minimum pen position graphic size, in normal coord space.
PEN_POS_GFX_MIN_SIZE = 0.033

# Maximum pen position graphic size, in normal coord space, is equal to
# PEN_POS_GFX_MIN_SIZE+PEN_POS_GFX_SIZE_RANGE 
PEN_POS_GFX_SIZE_RANGE = 0.033

# Defaults for PenTracesStim
# Width of pen trace line graphics (in pixels)
PEN_TRACE_LINE_WIDTH = 2

# Pen trace line color (in r,g,b 0-255)
PEN_TRACE_LINE_COLOR = (0, 0, 0)

# Pen trace line opacity. 0.0 = hidden / fully transparent, 1.0 = fully visible
PEN_TRACE_LINE_OPACITY = 1.0

draw_pen_traces = True

# if no keyboard or pen data is received for test_timeout_sec,
# the test program will exit.
test_timeout_sec = 300  # 5 minutes

# Runtime global variables
pen = None
last_evt = None
last_evt_count = 0
pen_pos_range = None


def start_iohub(myWin, sess_code=None, save_to=None):
    # Create initial default session code
    if sess_code is None:
        sess_code = 'S_{0}'.format(int(time.mktime(time.localtime())))

    # Ask for session name / hdf5 file name
    if save_to is None:
        save_to = fileSaveDlg(initFilePath=os.path.dirname(__file__), initFileName=sess_code,
                              prompt="Set Session Output File",
                              allowed="ioHub Data Files (*.hdf5)|*.hdf5")
    if save_to:
        # session code should equal results file name
        fdir, sess_code = os.path.split(save_to)
        sess_code = sess_code[0:min(len(sess_code), 24)]
        if sess_code.endswith('.hdf5'):
            sess_code = sess_code[:-5]
        if save_to.endswith('.hdf5'):
            save_to = save_to[:-5]
    else:
        save_to = sess_code

    exp_code = 'wintab_evts_test'

    kwargs = {'experiment_code': exp_code,
              'session_code': sess_code,
              'datastore_name': save_to,
              'wintab.Wintab': {'name': 'pen',
                                'mouse_simulation': {'enable': False,
                                                     'leave_region_timeout': 2.0
                                                     }
                                }
              }

    return launchHubServer(window=myWin, **kwargs)


def createPsychopyGraphics(myWin):
    #
    # Initialize Graphics
    #

    # hide the OS system mouse when on experiment window
    mouse.setPosition((0, 0))
    myWin.setMouseVisible(False)

    # INITIALISE SOME STIMULI
    evt_text = visual.TextStim(myWin, units='norm',
                               height=DEFAULT_TEXT_STIM_HEIGHT,
                               pos=(0, .9), text="")
    evt_text._txt_proto = 'pen: pos:\t{x},{y},{z}\t' \
                          'pressure: {pressure}\t' \
        # 'orientation: {orient_azimuth},{orient_altitude}'

    instruct_text = visual.TextStim(myWin, units='norm', pos=(0, -.9),
                                    height=DEFAULT_TEXT_STIM_HEIGHT,
                                    text="instruct_text")
    instruct_text._start_rec_txt = "Press 's' to start wintab reporting. " \
                                   "Press 'q' to exit."
    instruct_text._stop_rec_txt = "Press 's' to stop wintab reporting. " \
                                  "Press 'q' to exit."
    instruct_text.text = instruct_text._start_rec_txt

    pen_trace = wintabgraphics.PenTracesStim(myWin,
                                             PEN_TRACE_LINE_WIDTH,
                                             PEN_TRACE_LINE_COLOR,
                                             PEN_TRACE_LINE_OPACITY)
    pen_pos = wintabgraphics.PenPositionStim(myWin, PEN_POS_GFX_MIN_OPACITY,
                                             PEN_POS_HOVER_COLOR,
                                             PEN_POS_TOUCHING_COLOR,
                                             PEN_POS_ANGLE_COLOR,
                                             PEN_POS_ANGLE_WIDTH,
                                             PEN_POS_GFX_MIN_SIZE,
                                             PEN_POS_GFX_SIZE_RANGE,
                                             PEN_POS_TILTLINE_SCALAR)
    return evt_text, instruct_text, pen_trace, pen_pos


if __name__ == '__main__':
    # Ask for session name / hdf5 file name
    save_to = fileSaveDlg(initFilePath=os.path.dirname(__file__), initFileName=DEFAULT_SESSION_CODE,
                          prompt="Set Session Output File",
                          allowed="ioHub Data Files (*.hdf5)|*.hdf5")

    myWin = visual.Window((1920, 1080), units='pix', color=DEFAULT_SCREEN_COLOR,
                          colorSpace='rgb255', fullscr=True, allowGUI=False)

    # Start iohub process and create shortcut variables to the iohub devices
    # used during the experiment.
    io = start_iohub(myWin, DEFAULT_SESSION_CODE, save_to)

    keyboard = io.devices.keyboard
    mouse = io.devices.mouse
    pen = io.devices.pen

    # Check that the pen device was created without any errors
    if pen.getInterfaceStatus() != "HW_OK":
        print("Error creating Wintab device:", pen.getInterfaceStatus())
        print("TABLET INIT ERROR:", pen.getLastInterfaceErrorString())
    else:
        # Wintab device is a go, so setup and run test runtime....

        # Get Wintab device model specific hardware info and settings....
        # Create the PsychoPy Window and Graphics stim used during the test....
        vis_stim = createPsychopyGraphics(myWin)
        # break out graphics stim list into individual variables for later use
        evt_text, instruct_text, pen_trace, pen_pos_gauss = vis_stim

        # Get the current reporting / recording state of the pen
        is_reporting = pen.reporting

        # Get x,y pen evt pos ranges for future use
        pen_pos_range = (pen.axis['x']['range'],
                         pen.axis['y']['range'])

        # remove any events iohub has already captured.
        io.clearEvents()

        # create a timer / clock that is used to determine if the test
        # should exit due to inactivity
        testTimeOutClock = core.Clock()
        pen_pos_list = []

        # print "Axis: ", pen.axis
        # print "context: ", pen.context
        # print "model: ", pen.model

        while testTimeOutClock.getTime() < test_timeout_sec:
            # check for keyboard press events, process as necessary
            kb_events = keyboard.getPresses()
            if kb_events:
                testTimeOutClock.reset()
            if 'q' in kb_events:
                # End the text...
                break
            if 's' in kb_events:
                # Toggle the recording state of the pen....
                is_reporting = not is_reporting
                pen.reporting = is_reporting
                if is_reporting:
                    instruct_text.text = instruct_text._stop_rec_txt
                else:
                    instruct_text.text = instruct_text._start_rec_txt

            # check for any pen sample events, processing as necessary
            wtab_evts = pen.getSamples()
            last_evt_count = len(wtab_evts)
            if is_reporting:
                if draw_pen_traces:
                    pen_trace.updateFromEvents(wtab_evts)

                if last_evt_count:
                    # for e in wtab_evts:
                    #    print e
                    last_evt = wtab_evts[-1]
                    testTimeOutClock.reset()

                    pen_pos_gauss.updateFromEvent(last_evt)

                    # update the text that displays the event pos, pressure, etc...
                    evt_text.text = evt_text._txt_proto.format(**last_evt.dict)
            else:
                last_evt = None

            if last_evt is None:
                last_evt_count = 0
                pen_trace.clear()
                evt_text.text = ''

            for stim in vis_stim:
                stim.draw()

            myWin.flip()  # redraw the buffer

        if testTimeOutClock.getTime() >= test_timeout_sec:
            print("Test Time Out Occurred.")

        core.quit()
