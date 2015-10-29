from __future__ import division
#!/usr/bin/env python2
from psychopy import core, visual
from psychopy.gui import fileSaveDlg
from psychopy.iohub import launchHubServer, EventConstants
import math

draw_pen_traces = True

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


class PenTraces(object):
    def __init__(self):
        self.pentracestim = []
        self.current_pentrace = None
        self.current_points=[]

    @property
    def segments(self):
        return [pts.vertices for pts in self.pentracestim]

    def draw(self):
        for pts in self.pentracestim:
            pts.draw()

    def start(self, first_point):
        self.end()
        self.current_points.append(first_point)
        self.current_pentrace = visual.ShapeStim(myWin, units='norm', lineWidth=2,
                                 lineColor=(-1, -1, -1),
                                 lineColorSpace='rgb',
                                 vertices=self.current_points,
                                 closeShape=False, pos=(0, 0),
                                 size=1, ori=0.0, opacity=1.0,
                                 interpolate=True)
        self.pentracestim.append(self.current_pentrace)

    def end(self):
        self.current_pentrace = None
        self.current_points=[]

    def append(self, pos):
        if self.current_pentrace is None:
            self.start(pos)
        else:
            # TODO: This is VERY inefficient, look into a better way to add
            # points to a psychopy shape stim
            self.current_points.append(pos)
            self.current_pentrace.vertices = self.current_points

    def clear(self):
        self.end()
        for pts in self.pentracestim:
            pts.vertices=[(0,0)]

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

    pen_trace = PenTraces()

    pen_guass = visual.PatchStim(myWin, units='norm', tex="none",
                                   mask="gauss", pos=(0,0),
                                   size=(pen_size_min,pen_size_min),
                                   color='red', autoLog=False, opacity = 0.0)

    pen_tilt_line = visual.Line(myWin, units='norm', start=[0,0],
                                end=[0.5,0.5], lineColor=(1,1,0), opacity = 0.0)

    return myWin, (evt_text, instruct_text, pen_trace, pen_guass, pen_tilt_line)


def getPenPos(tablet_event):
    return (-1.0+(tablet_event.x/tablet_pos_range[0])*2.0,
            -1.0+(tablet_event.y/tablet_pos_range[1])*2.0)

def getPenSize(tablet_event):
    prange = tablet.axis['tip_pressure_axis']['axMax']-\
             tablet.axis['tip_pressure_axis']['axMin']
    pevt = tablet_event.pressure
    return pen_size_min + (pevt/prange)*pen_size_range

def getPenOpacity(tablet_event):
    zrange = tablet.axis['z_axis']['axMax']- tablet.axis['z_axis']['axMin']
    z = zrange-tablet_event.z
    sopacity = pen_opacity_min + (z/zrange)*(1.0-pen_opacity_min)
    return sopacity

def getPenTilt(tablet_event):
    '''
    Get the dx,dy screen position in norm units that should be used
    when drawing the pen titl line graphic end point.
    '''
    t1, t2 = tablet_event.tilt
    return t1*math.sin(t2), t1*math.cos(t2)

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
        evt_text, instruct_text, pen_trace, pen_guass, pen_tilt_line = vis_stim

        # Get the current reporting / recording state of the tablet
        is_reporting = tablet.reporting

        # Get x,y tablet evt pos ranges for future use
        tablet_pos_range = (float(tablet.axis['x_axis']['axMax'] -
                                  tablet.axis['x_axis']['axMin']),
                            float(tablet.axis['y_axis']['axMax'] -
                                  tablet.axis['y_axis']['axMin']))

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

            # check for any tablet enter region events,
            # ending current pen trace if any have occurred....
            wtab_enter_evts = tablet.getEnters()
            if draw_pen_traces and wtab_enter_evts:
                pen_trace.end()

            # check for any tablet sample events, processing as necessary
            wtab_evts = tablet.getSamples()
            last_evt_count=len(wtab_evts)
            if is_reporting:
                if last_evt_count:

                    if draw_pen_traces:
                        for pevt in wtab_evts:
                            if pevt.pressure>0:
                                pen_trace.append(getPenPos(pevt))
                            else:
                                pen_trace.end()

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
                    pen_trace.clear()
                    evt_text.text=''

            for stim in vis_stim:
                stim.draw()

            myWin.flip()#redraw the buffer

        if testTimeOutClock.getTime() >= test_timeout_sec:
            print "Test Time Out Occurred."
