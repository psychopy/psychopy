from __future__ import division
#!/usr/bin/env python2
import psychopy
from psychopy import core, visual
from psychopy.gui import fileSaveDlg
from psychopy.iohub import launchHubServer, EventConstants
import math

draw_pen_traces = True

# if no keyboard or tablet data is received for test_timeout_sec,
# the test program will exit.
test_timeout_sec = 300 # 5 minutes

# Runtime global variables
tablet=None
last_evt=None
last_evt_count=0
tablet_pos_range=None

def start_iohub(sess_code=None):
    import time, os

    # Create initial default session code
    if sess_code is None:
        sess_code='S_{0}'.format(long(time.mktime(time.localtime())))

    # Ask for session name / hdf5 file name
    save_to = fileSaveDlg(initFilePath=os.path.dirname(__file__),initFileName=sess_code,
                          prompt="Set Session Output File",
                          allowed="ioHub Datastore Files (*.hdf5)|*.hdf5")
    if save_to:
        # session code should equal results file name
        fdir, sess_code = os.path.split(save_to)
        sess_code=sess_code[0:min(len(sess_code),24)]
        if sess_code.endswith('.hdf5'):
            sess_code = sess_code[:-5]
        if save_to.endswith('.hdf5'):
            save_to = save_to[:-5]
    else:
        save_to = sess_code

    exp_code='wintab_evts_test'

    kwargs={'experiment_code':exp_code,
            'session_code':sess_code,
            'datastore_name':save_to,
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

    pen_trace = psychopy.iohub.client.wintabtablet.PenTracesStim(myWin)
    pen_pos = psychopy.iohub.client.wintabtablet.PenPositionStim(myWin)
    return myWin, (evt_text, instruct_text, pen_trace, pen_pos)


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
        evt_text, instruct_text, pen_trace, pen_pos_gauss = vis_stim

        # Get the current reporting / recording state of the tablet
        is_reporting = tablet.reporting

        # Get x,y tablet evt pos ranges for future use
        tablet_pos_range = (tablet.axis['x']['range'],
                            tablet.axis['y']['range'])

        # remove any events iohub has already captured.
        io.clearEvents()

        # create a timer / clock that is used to determine if the test
        # should exit due to inactivity
        testTimeOutClock = core.Clock()
        pen_pos_list=[]

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


            # check for any tablet sample events, processing as necessary
            wtab_evts = tablet.getSamples()
            last_evt_count=len(wtab_evts)
            if is_reporting:
                if draw_pen_traces:
                    pen_trace.updateFromEvents(wtab_evts)

                if last_evt_count:
                    last_evt = wtab_evts[-1]
                    testTimeOutClock.reset()

                    pen_pos_gauss.updateFromEvent(last_evt)

                    # update the text that displays the event pos, pressure, etc...
                    evt_text.text=evt_text._txt_proto.format(**last_evt.dict)

            else:
                last_evt = None
                
            if last_evt is None:
                    last_evt_count = 0
                    pen_trace.clear()
                    evt_text.text=''

            for stim in vis_stim:
                stim.draw()

            myWin.flip()#redraw the buffer

        io.quit()
        if testTimeOutClock.getTime() >= test_timeout_sec:
            print "Test Time Out Occurred."
