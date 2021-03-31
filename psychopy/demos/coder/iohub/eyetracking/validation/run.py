#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Example of performing eye tracker validation using ioHub Common Eye Tracker interface
and the ValidationProcedure utility class.
"""
import time
from psychopy import visual
from psychopy.iohub import launchHubServer

from trigger import TimeTrigger, KeyboardTrigger
from validationroutine import ValidationProcedure

class TargetStim(object):
    def __init__(self, win, radius=None, fillcolor=None, edgecolor=None, edgewidth=None,
                 dotcolor=None, dotradius=None, units=None, colorspace=None, opacity=1.0, contrast=1.0):
        """
        TargetStim is a 'doughnut' style target graphic used during the validation procedure.

        :param win: Window being sued for validation.
        :param radius: The outer radius of the target.
        :param fillcolor: The color used to fill the target body.
        :param edgecolor: The color for the edge around the target.
        :param edgewidth: The thickness of the target outer edge (always in pixels).
        :param dotcolor: The color of the central target dot.
        :param dotradius: The radius to use for the target dot.
        :param units: The psychopy unit type of any size values.
        :param colorspace: The psychopy color space of any colors.
        :param opacity: The transparency of the target (0.0 - 1.0).
        :param contrast: The contrast of the target stim.
        """
        from weakref import proxy
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


def runValidation(win):
    """
    Runs the eye tracker validation procedure using PsychoPy Window win.
    This function performs a ValidationProcedure using a validation target
    stimulus, a validation position list, and the triggers used to determine
    target position progression during the validation procedure.

    :param win: PsychoPy window being used for validation.
    :return:
    """
    # Create a TargetStim instance
    target = TargetStim(win, radius=0.025, fillcolor=[.5, .5, .5], edgecolor=[-1, -1, -1], edgewidth=2,
                        dotcolor=[1, -1, -1], dotradius=0.005, units='norm', colorspace='rgb')

    positions = [(0.0, 0.0), (0.85, 0.85), (-0.85, 0.0), (0.85, 0.0), (0.85, -0.85), (-0.85, 0.85),
                 (-0.85, -0.85), (0.0, 0.85), (0.0, -0.85)]

    # Specifiy the Triggers to use to move from target point to point during
    # the validation sequence....
    target_triggers = KeyboardTrigger(' ', on_press=True) #TimeTrigger(start_time=None, delay=2.5),

    # Create a validation procedure
    validation_proc = ValidationProcedure(win, target, positions,
                                          target_animation_params=dict(velocity=1.0,
                                                                       expandedscale=3.0,
                                                                       expansionduration=0.2,
                                                                       contractionduration=0.4),
                                          background=None,
                                          triggers=target_triggers,
                                          storeeventsfor=None,
                                          accuracy_period_start=0.550,
                                          accuracy_period_stop=.150,
                                          show_intro_screen=True,
                                          intro_text='Validation procedure is now going to be performed.',
                                          show_results_screen=True,
                                          results_in_degrees=False,
                                          randomize_positions=False,
                                          toggle_gaze_cursor_key='g'
                                          )

    # Run the validation procedure. The run() method does not return until
    # the validation is complete.
    return validation_proc.run()


if __name__ == "__main__":
    # Create a default PsychoPy Window
    win = visual.Window((1920, 1080), fullscr=True, allowGUI=False, monitor='55w_60dist')


    exp_code = 'validation_demo'
    sess_code = 'S_{0}'.format(int(time.mktime(time.localtime())))

    # Create ioHub Server config settings....
    iohub_config = dict()
    iohub_config['experiment_code'] = exp_code
    iohub_config['session_code'] = sess_code
    # Add an eye tracker device
    et_interface_name = 'eyetracker.hw.mouse.EyeTracker'
    iohub_config[et_interface_name] = dict(name='tracker')

    # Start the ioHub process.
    io = launchHubServer(window=win, **iohub_config)

    # Get the keyboard and mouse devices for future access.
    keyboard = io.devices.keyboard
    tracker = io.devices.tracker
    experiment = io.devices.experiment

    # Run eyetracker calibration
    r = tracker.runSetupProcedure()

    # Run eye tracker validation
    validation_results = runValidation(win)

    io.quit()
