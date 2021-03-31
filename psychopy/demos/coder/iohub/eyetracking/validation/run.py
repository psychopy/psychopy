#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Example of performing eye tracker validation using ioHub Common Eye Tracker interface
and the ValidationProcedure utility class.
"""
import time
from weakref import proxy

from psychopy import visual
from psychopy.iohub import launchHubServer
from psychopy.iohub.constants import EventConstants

from trigger import TimeTrigger, DeviceEventTrigger
from posgrid import PositionGrid
from validationroutine import ValidationProcedure

class TargetStim(object):
    def __init__(self,
                 win,
                 radius=None,       # The outer radius of the target.
                 fillcolor=None,    # The color used to fill the target body.
                 edgecolor=None,    # The color for the edge around the target.
                 edgewidth=None,    # The thickness of the target outer edge.
                 dotcolor=None,     # The color of the central target dot.
                 dotradius=None,    # The radius to use for the target dot.
                 units=None,        # The psychopy unit type of any size values.
                 colorspace=None,   # The psychopy color space of any colors.
                 opacity=1.0,       # The transparency of the target (0.0 - 1.0)
                 contrast=1.0       # The contrast of the target stim.
                 ):
        """
        TargetStim is a 'doughnut' style target graphic used during the validation procedure.

        :param win:
        :param radius:
        :param fillcolor:
        :param edgecolor:
        :param edgewidth:
        :param dotcolor:
        :param dotradius:
        :param units:
        :param colorspace:
        :param opacity:
        :param contrast:
        """
        self.win = proxy(win)
        self.stim = []
        self.radius = radius
        outer = visual.Circle(self.win, radius=radius, fillColor=fillcolor, lineColor=edgecolor, lineWidth=edgewidth,
                              edges=32, units=units, colorSpace=colorspace, opacity=opacity,
                              contrast=contrast, interpolate=True, autoLog=False)
        self.stim.append(outer)

        if dotcolor and dotcolor != fillcolor:
            centerdot = visual.Circle(self.win, radius=dotradius, fillColor=dotcolor, lineColor=dotcolor,
                                      lineWidth=0.0, edges=32, interpolate=True, units=units,
                                      colorSpace=colorspace, opacity=opacity, contrast=contrast, autoLog=False)
            self.stim.append(centerdot)

    def setRadius(self, r):
        """
        Update the radius of the target stim.
        """
        self.stim[0].radius = r

    def setPos(self, pos):
        """
        Set the center position of the target stim.
        """
        for s in self.stim:
            s.setPos(pos)

    def draw(self):
        """
        Draw the Target stim.
        """
        for s in self.stim:
            s.draw()

    def contains(self, p):
        """
        Is point p contained within the Target Stim?
        :param p: x, y position in stim units
        :return: bool
        """
        return self.stim[0].contains(p)


if __name__ == "__main__":
    # Create a default PsychoPy Window
    win = visual.Window((1920, 1080), fullscr=True, allowGUI=False, monitor='55w_60dist')


    exp_code = 'targetdisplay'
    sess_code = 'S_{0}'.format(int(time.mktime(time.localtime())))

    # Create ioHub Server config settings....
    iohub_config = dict()
    iohub_config['experiment_code'] = exp_code
    iohub_config['session_code'] = sess_code

    # Add an eye tracker device
    et_interface_name = 'eyetracker.hw.mouse.EyeTracker'
    iohub_config[et_interface_name] = dict(name='tracker')

    # Start ioHub event monitoring process....
    io = launchHubServer(window=win, **iohub_config)

    # Get the keyboard and mouse devices for future access.
    keyboard = io.devices.keyboard
    tracker = io.devices.tracker
    experiment = io.devices.experiment

    # run eyetracker calibration
    r = tracker.runSetupProcedure()


    # Create a TargetStim instance
    target = TargetStim(win,
                        radius=0.025,
                        fillcolor=[.5, .5, .5],
                        edgecolor=[-1, -1, -1],
                        edgewidth=2,
                        dotcolor=[1, -1, -1],
                        dotradius=0.005,
                        units='norm',
                        colorspace='rgb'
                        )

    # Create a PositionGrid instance that will hold the locations to display the
    # target at. The example lists all possible keyword arguments that are
    # supported. If bounds is None, the ioHub Display device is used
    # to get the bounding box to be used.
    #positions = PositionGrid(bounds=None,  # bounding rect of the window, in window unit coords.
    #                         shape=3,  # Create a grid with 3 cols * 3 rows.
    #                         posCount=None,
    #                         leftMargin=None,
    #                         rightMargin=None,
    #                         topMargin=None,
    #                         bottomMargin=None,
    #                         scale=0.85,  # Equally space the 3x3 grid across 85%
                             # of the window width and height.
    #                         posList=None,
    #                         noiseStd=None,
    #                         firstposindex=4,  # Use the center position grid
                             # location as the first point in
                             # the position order.
    #                         repeatFirstPos=True  # Redisplay first target position
                             # as the last target position.
    #                         )
    # randomize the grid position presentation order (not including
    # the first position).
    #positions.randomize()
    #print("positions: ", [(p[0], p[1]) for p in positions.getPositions()])

    positions = [(0.0, 0.0), (0.85, 0.85), (-0.85, 0.0), (0.85, 0.0), (0.85, -0.85), (-0.85, 0.85),
                 (-0.85, -0.85), (0.0, 0.85), (0.0, -0.85)]


    # Specifiy the Triggers to use to move from target point to point during
    # the validation sequence....

    # Use DeviceEventTrigger to create a keyboard event trigger
    # which will fire when the space key is pressed.
    kb_trigger = DeviceEventTrigger(io.getDevice('keyboard'),
                                    event_type=EventConstants.KEYBOARD_RELEASE,
                                    event_attribute_conditions={'key': ' '},
                                    repeat_count=0)

    # Creating a list of Trigger instances. The first one that
    #     fires will cause the start of the next target position
    #     presentation.
    multi_trigger = (TimeTrigger(start_time=None, delay=2.5), kb_trigger)


    # define a dict containing any animation params to be used,
    # None's to disable animation
    targ_anim_param = dict(velocity=1.0,  # 800.0,
                           expandedscale=3.0,  # 2.0,
                           expansionduration=0.2,  # 0.1,
                           contractionduration=0.4)  # 0.1
    print(win.units)
    print(target.stim[0].units)
    # Create a validation procedure
    vin_txt = 'Validation procedure is now going to be performed.'
    validation_proc = ValidationProcedure(win, target, positions,
                                          target_animation_params=targ_anim_param,
                                          background=None,
                                          triggers=multi_trigger, #kb_trigger,#multi_trigger,
                                          storeeventsfor=None,
                                          accuracy_period_start=0.550,
                                          accuracy_period_stop=.150,
                                          show_intro_screen=True,
                                          intro_text=vin_txt,
                                          show_results_screen=True,
                                          results_in_degrees=False,
                                          randomize_positions=False)

    # Run the validation procedure. The run() method does not return until
    # the validation is complete. The calculated validation results, and data
    # collected for the analysis, are returned.
    results = validation_proc.run()

    # The last run validation results can also be retrieved using:
    # results = validation_proc.getValidationResults()

    io.quit()
