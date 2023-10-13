# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""
Eye Tracker Validation procedure using the ioHub common eye tracker interface.

To use the validation process from within a Coder script:
* Create a target stim
* Create a list of validation target positions. Use the `PositionGrid` class to help create a target position list.
* Create a ValidationProcedure class instance, providing the target stim and position list and other arguments
  to define details of the validation procedure.
* Use `ValidationProcedure.run()` to perform the validation routine.
* Use `ValidationProcedure.getValidationResults()` to access information about each target position displayed and
  the events collected during the each target validation period.

See demos/coder/iohub/eyetracking/validation.py for a complete example.
"""
from weakref import proxy
import numpy as np
from time import sleep
import os
import sys
from matplotlib import pyplot as pl

from psychopy import visual
from psychopy.iohub.util import win32MessagePump, normjoin
from psychopy.iohub.constants import EventConstants
from psychopy.iohub.client import ioHubConnection, Computer
from psychopy.tools.monitorunittools import convertToPix
from psychopy.tools.monitorunittools import pix2deg, deg2pix

from psychopy.iohub.client.eyetracker.validation import PositionGrid, Trigger, KeyboardTrigger, TimeTrigger

getTime = Computer.getTime


class TargetStim:
    def __init__(self, win, radius=None, fillcolor=None, edgecolor=None, edgewidth=None,
                 dotcolor=None, dotradius=None, units=None, colorspace=None, opacity=1.0, contrast=1.0):
        """
        TargetStim is a 'doughnut' style target graphic used during the validation procedure.

        :param win: Window being used for validation.
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
        self._radius = radius
        outer = visual.Circle(self.win, radius=radius, fillColor=fillcolor, lineColor=edgecolor, lineWidth=edgewidth,
                              edges=32, units=units, colorSpace=colorspace, opacity=opacity,
                              contrast=contrast, interpolate=True, autoLog=False)
        self.stim.append(outer)

        if dotcolor and dotcolor != fillcolor:
            centerdot = visual.Circle(self.win, radius=dotradius, fillColor=dotcolor, lineColor=dotcolor,
                                      lineWidth=0.0, edges=32, interpolate=True, units=units,
                                      colorSpace=colorspace, opacity=opacity, contrast=contrast, autoLog=False)
            self.stim.append(centerdot)

    def setPos(self, pos):
        """
        Set the center position of the target stim. Used during validation procedure to
        change target position.
        """
        for s in self.stim:
            s.setPos(pos)

    @property
    def pos(self):
        return self.stim[0].pos

    @pos.setter
    def pos(self, value):
        self.setPos(value)

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, r):
        self._radius = self.stim[0].radius = r

    def setSize(self, s):
        """
        Update the size of the target stim.
        """
        self.stim[0].radius = s/2

    def getSize(self):
        """
        Get the size of the target stim.
        """
        return self.stim[0].radius*2

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
        :return: bool: True: p is within the stim
        """
        return self.stim[0].contains(p)

    @property
    def innerRadius(self):
        try:
            return self.stim[1].radius
        except:
            return self.stim[0].radius

def create3PointGrid():
    io = ioHubConnection.getActiveConnection()
    if io is None:
        raise RuntimeError("iohub must be running.")
    l, t, r, b = io.devices.display.getCoordBounds()
    return [(0.0, (t-b)/4), (-(r-l)/4, -(t-b)/4), ((r-l)/4, -(t-b)/4)]


def create5PointGrid():
    io = ioHubConnection.getActiveConnection()
    if io is None:
        raise RuntimeError("iohub must be running.")
    four_point = PositionGrid(io.devices.display.getCoordBounds(), (2, 2), scale=0.85).getPositions()
    return [(0.0, 0.0),] + four_point


def create9PointGrid():
    io = ioHubConnection.getActiveConnection()
    if io is None:
        raise RuntimeError("iohub must be running.")
    return PositionGrid(io.devices.display.getCoordBounds(), (3, 3), scale=0.85, firstposindex=4)


def create13PointGrid():
    io = ioHubConnection.getActiveConnection()
    if io is None:
        raise RuntimeError("iohub must be running.")
    nine_point = create9PointGrid().getPositions()
    four_point = PositionGrid(io.devices.display.getCoordBounds(), (2, 2), scale=0.5).getPositions()
    thirteen_point = nine_point + four_point
    return thirteen_point


def create17PointGrid():
    io = ioHubConnection.getActiveConnection()
    if io is None:
        raise RuntimeError("iohub must be running.")
    sixteen_pos = PositionGrid(io.devices.display.getCoordBounds(), (4, 4), scale=0.85).getPositions()
    return [(0.0, 0.0), ] + sixteen_pos


class ValidationProcedure:
    def __init__(self,
                 win=None,  # psychopy window
                 target=None,  # target stim
                 positions=None,  # string constant or list of points
                 randomize_positions=True,  # boolean
                 expand_scale=None,  # float
                 target_duration=None,  # float
                 target_delay=None,  # float
                 enable_position_animation=True,
                 color_space=None,  # None == use window color space
                 unit_type=None,  # None == use window unit type (may need to enforce this for Validation)
                 progress_on_key=" ",  # str or None
                 gaze_cursor=None,  # None, color, or a stim object with setPos()
                 text_color=None,
                 show_results_screen=True,  # bool
                 save_results_screen=False,  # bool
                 # args not used by Builder at this time
                 contract_target=True,
                 accuracy_period_start=0.550,
                 accuracy_period_stop=.150,
                 show_intro_screen=False,
                 intro_text='Ready to Start Validation Procedure.',
                 results_in_degrees=False,
                 terminate_key="escape",
                 toggle_gaze_cursor_key="g"):
        """
        ValidationProcedure is used to test the gaze accuracy of a calibrated eye tracking system.

        Once a ValidationProcedure class instance has been created, call the `.run()` method
        to start the validation process, which consists of the following steps:

        1) (Optionally) Display an Introduction screen. A 'space' key press is used to start target presentation.
        2) Displaying the validation target at each position being validated. Target progression from one
           position to the next is controlled by the specified `triggers`, defaulting to a 'space' key press.
           The target graphics can simply jump from one position to the next, or optional target_animation settings
           can be used to have the target move across the screen from one point to the next and / or expand / contract
           at each target location.
        3) (Optionally) Display a Results screen. The Results screen shows each target position, the position of
           each sample used for the accuracy calculation, and some validation result statistics.

        Data collected during the validation target sequence is used to calculate accuracy information
        for each target position presented. The raw data as well as the computed accuracy stats is
        available via the `.getValidationResults()` method.

        To make the validation output consistent across iohub common eye tracker implementations, validation is
        performed on monocular eye data. If binocular eye samples are being recorded, the average of the
        left and right eye positions is used for each gaze sample.

        See the validation.py demo in demos.coder.iohub.eyetracking for a demo.

        TODO: Update param list docs
        :param win: PsychoPy window to use for validation. Must be full screen.
        :param target: Stimulus to use as validation target. If None, default `TargetStim` is used.
        :param positions: Positions to validate. Provide list of x,y pairs, or use a `PositionGrid` class.
        :param target_animation:
        :param randomize_positions: bool: Randomize target positions before presentation.
        :param show_intro_screen: bool: Display a validation procedure Introduction screen.
        :param intro_text: Introduction screen text.
        :param show_results_screen: bool: Display a validation procedure Results screen.
        :param results_in_degrees: bool: Convert results to visual degrees.
        :param save_results_screen: bool: Save results screen as image.
        :param terminate_key: Key that will end the validation procedure. Default is 'escape'.
        :param toggle_gaze_cursor_key: Key to toggle gaze cursor visibility (hidden to start). Default is key is 'g'.
        :param accuracy_period_start: Time prior to target trigger to use as start of period for valid samples.
        :param accuracy_period_stop: Time prior to target trigger to use as end of period for valid samples.
        :param triggers: Target progression triggers. Default is 'space' key press.
        :param storeeventsfor: iohub devices that events should be stored for.
        """
        self.terminate_key = terminate_key
        self.toggle_gaze_cursor_key = toggle_gaze_cursor_key

        self.io = ioHubConnection.getActiveConnection()

        if isinstance(positions, str):
            # position set constant, THREE_POINTS, FIVE_POINTS, NINE_POINTS, THIRTEEN_POINTS, SEVENTEEN_POINTS
            if positions == 'THREE_POINTS':
                positions = create3PointGrid()
            elif positions == 'FIVE_POINTS':
                positions = create5PointGrid()
            elif positions == 'NINE_POINTS':
                positions = create9PointGrid()
            elif positions == 'THIRTEEN_POINTS':
                positions = create13PointGrid()
            elif positions == 'SEVENTEEN_POINTS':
                positions = create17PointGrid()
            else:
                raise ValueError("Unsupported positions string constant: [{}]".format(positions))
        if isinstance(positions, (list, tuple)):
            positions = PositionGrid(posList=positions, firstposindex=0, repeatFirstPos=False)
        self.positions = positions

        self.randomize_positions = randomize_positions
        if self.randomize_positions:
            self.positions.randomize()

        self.win = proxy(win)

        target_animation = {}
        target_animation['enable'] = enable_position_animation
        target_animation['targetdelay'] = target_delay
        target_animation['targetduration'] = target_duration
        target_animation['expandedscale'] = expand_scale
        target_animation['contracttarget'] = contract_target

        self.animation_params = target_animation
        self.accuracy_period_start = accuracy_period_start

        self.accuracy_period_stop = accuracy_period_stop
        self.show_intro_screen = show_intro_screen
        self.intro_text = intro_text
        self.intro_text_stim = None
        self.show_results_screen = show_results_screen
        self.results_in_degrees = results_in_degrees
        self.save_results_screen = save_results_screen
        self._validation_results = None

        self.text_color = text_color
        self.text_color_space = color_space

        if text_color is None or text_color == 'auto':
            # If no calibration text color provided, base it on the window background color
            from psychopy.iohub.util import complement
            sbcolor = win.color
            from psychopy.colors import Color
            tcolor_obj = Color(sbcolor, win.colorSpace)
            self.text_color = complement(*tcolor_obj.rgb255)
            self.text_color_space = 'rgb255'

        storeeventsfor = [self.io.devices.keyboard,
                          self.io.devices.tracker,
                          self.io.devices.experiment]

        trig_list = []
        if progress_on_key:
            if isinstance(progress_on_key, (list, tuple)):
                for k in progress_on_key:
                    trig_list.append(KeyboardTrigger(k, on_press=True))
            else:
                trig_list.append(KeyboardTrigger(progress_on_key, on_press=True))
        elif target_duration:
            trig_list.append(TimeTrigger(start_time=None, delay=target_duration),)

        triggers = Trigger.getTriggersFrom(trig_list)

        # Create the ValidationTargetRenderer instance; used to control the sequential
        # presentation of the target at each of the grid positions.
        self.targetsequence = ValidationTargetRenderer(win, target=target, positions=self.positions,
                                                       triggers=triggers, storeeventsfor=storeeventsfor,
                                                       terminate_key=terminate_key,
                                                       gaze_cursor_key=toggle_gaze_cursor_key,
                                                       gaze_cursor=gaze_cursor,
                                                       color_space=color_space, unit_type=unit_type)

    def run(self):
        """
        Run the validation procedure, returning after the full validation process is complete, including:
            a) display of an instruction screen
            b) display of the target position sequence used for validation data collection.
            c) display of a validation accuracy results plot.
        """
        keyboard = self.io.devices.keyboard
        if self.show_intro_screen:
            # Display Validation Intro Screen
            self.showIntroScreen()
            if self.terminate_key and self.terminate_key in keyboard.waitForReleases(keys=[' ', 'space',self.terminate_key]):
                print("Escape key pressed. Exiting validation")
                self._validation_results = None
                return

        # Perform Validation.....
        terminate = not self.targetsequence.display(**self.animation_params)
        if terminate:
            print("Escape key pressed. Exiting validation")
            self._validation_results = None
            return

        self.io.clearEvents('all')

        self._createValidationResults()

        if self.show_results_screen:
            self.showResultsScreen()
            kb_presses = keyboard.waitForPresses(keys=['space',' ', self.terminate_key, self.targetsequence.gaze_cursor_key])
            while 'space' not in kb_presses and ' ' not in kb_presses:
                if self.targetsequence.gaze_cursor_key in kb_presses:
                    self.targetsequence.display_gaze = not self.targetsequence.display_gaze
                    self.showResultsScreen()
                if self.terminate_key in kb_presses:
                    print("Escape key pressed. Exiting validation")
                    break
                kb_presses = keyboard.waitForPresses(keys=['space', ' ',
                                                           self.terminate_key,
                                                           self.targetsequence.gaze_cursor_key])

        return self._validation_results

    def showResultsScreen(self):
        self.drawResultScreen()
        ftime = self.win.flip()
        if self.save_results_screen:
            self.win.getMovieFrame()
            self.win.saveMovieFrames(self._generateImageName())
        return ftime

    def showIntroScreen(self):
        text = self.intro_text + '\nPress SPACE to Start....'
        textpos = (0, 0)
        if self.intro_text_stim:
            self.intro_text_stim.setText(text)
            self.intro_text_stim.setPos(textpos)
        else:
            self.intro_text_stim = visual.TextStim(self.win, text=text, pos=textpos, height=30, color=self.text_color,
                                                   colorSpace=self.text_color_space, opacity=1.0, contrast=1.0, units='pix',
                                                   ori=0.0, antialias=True, bold=False, italic=False,
                                                   anchorHoriz='center', anchorVert='center',
                                                   wrapWidth=self.win.size[0] * .8)

        self.intro_text_stim.draw()
        self.win.flip()
        return self.win.flip()

    @property
    def results(self):
        """
        See getValidationResults().
        :return:
        """
        return self._validation_results

    def getValidationResults(self):
        """
        Return the validation results dict for the last validation run. If a validation as not yet been run(),
        None is returned. Validation results are provided separately for each target position and include:

        a) An array of the samples used for the accuracy calculation. The samples used are selected
           using the following criteria:
                i) Only samples where the target was stationary and not expanding or contracting are selected.
                ii) Samples are selected that fall between:

                              start_time_filter = last_sample_time - accuracy_period_start

                           and

                              end_time_filter = last_sample_time - accuracy_period_end

                           Therefore, the duration of the selected sample period is:

                              selection_period_dur = end_time_filter - start_time_filter

                iii) Sample that contain missing / invalid position data are removed, providing the
                     final set of samples used for accuracy calculations. The min, max, and mean values
                     from each set of selected samples is calculated.

        b) The x and y error of sampled gaze position relative to the current target position.
           This data is in the same units as is used by the validation window.

        c) The xy distance error from the from each eye's gaze position to the target position.
           This is also calculated as an average of both eyes when binocular data is available.
           The data is unsigned, providing the absolute distance from gaze to target positions

        Validation Results Dict Structure
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        {'display_bounds': [-1.0, 1.0, 1.0, -1.0],
         'display_pix': array([1920, 1080]),
         'display_units': 'norm',
         'max_error': 2.3668638421479,
         'mean_error': 0.9012516727129639,
         'min_error': 0.0,
         'passed': True,
         'position_count': 9,
         'positions_failed_processing': 0,
         'reporting_unit_type': 'degree',
         'target_positions': [array([0., 0.]), array([0.85, 0.85]), array([-0.85,  0.  ]),
                              array([0.85, 0.  ]), array([ 0.85, -0.85]), array([-0.85,  0.85]),
                              array([-0.85, -0.85]), array([0.  , 0.85]), array([ 0.  , -0.85])],
         'position_results': [{'index': 0,
                               'calculation_status': 'PASSED',
                               'target_position': array([0., 0.]),
                               'sample_time_range': [4.774341499977744, 6.8343414999777],
                               'filter_samples_time_range': [6.2843414999777005, 6.6843414999777],
                               'min_error': 0.0,
                               'max_error': 0.7484680652684592,
                               'mean_error': 0.39518431321527914,
                               'stdev_error': 0.24438398690651483,
                               'valid_filtered_sample_perc': 1.0,
                              },
                              # Validation results dict is given for each target position
                              # ....
                             ]
        }

        :return: validation results dict.
        """
        return self._validation_results

    def _createValidationResults(self):
        """
        Create validation results dict and save validation analysis info as experiment messages to
        the iohub .hdf5 file.

        :return: dict
        """
        self._validation_results = None
        sample_array = self.targetsequence.getSampleMessageData()
        target_positions_used = self.targetsequence.positions.getPositions()

        if self.results_in_degrees:
            for postdat in sample_array:
                postdat['targ_pos_x'], postdat['targ_pos_y'] = toDeg(self.win,
                                                                     *toPix(self.win, postdat['targ_pos_x'],
                                                                            postdat['targ_pos_y']))

                binoc_sample_types = [EventConstants.BINOCULAR_EYE_SAMPLE, EventConstants.GAZEPOINT_SAMPLE]
                if self.targetsequence.sample_type in binoc_sample_types:
                    postdat['left_eye_x'], postdat['left_eye_y'] = toDeg(self.win,
                                                                         *toPix(self.win, postdat['left_eye_x'],
                                                                                postdat['left_eye_y']))

                    postdat['right_eye_x'], postdat['right_eye_y'] = toDeg(self.win,
                                                                           *toPix(self.win, postdat['right_eye_x'],
                                                                                  postdat['right_eye_y']))
                else:
                    postdat['eye_x'], postdat['eye_y'] = toDeg(self.win,
                                                               *toPix(self.win, postdat['eye_x'], postdat['eye_y']))

        min_error = 100000.0
        max_error = 0.0
        summed_error = 0.0
        point_count = 0

        self.io.sendMessageEvent('Results', 'VALIDATION')
        results = dict(display_units=self.win.units, display_bounds=self.positions.bounds,
                       display_pix=self.win.size, position_count=len(sample_array),
                       target_positions=target_positions_used)

        for k, v in results.items():
            self.io.sendMessageEvent('{}: {}'.format(k, v), 'VALIDATION')

        results['position_results'] = []
        results['positions_failed_processing'] = 0

        for pindex, samplesforpos in enumerate(sample_array):
            self.io.sendMessageEvent('Target Position Results: {0}'.format(pindex), 'VALIDATION')

            stationary_samples = samplesforpos[samplesforpos['targ_state'] == self.targetsequence.TARGET_STATIONARY]

            if len(stationary_samples):
                last_stime = stationary_samples[-1]['eye_time']
                first_stime = stationary_samples[0]['eye_time']

                filter_stime = last_stime - self.accuracy_period_start
                filter_etime = last_stime - self.accuracy_period_stop

                all_samples_in_period = stationary_samples[stationary_samples['eye_time'] >= filter_stime]
                all_samples_in_period = all_samples_in_period[all_samples_in_period['eye_time'] < filter_etime]

                good_samples_in_period = all_samples_in_period[all_samples_in_period['eye_status'] == 0]

                all_samples_count = all_samples_in_period.shape[0]
                good_sample_count = good_samples_in_period.shape[0]
                try:
                    good_sample_ratio = good_sample_count / float(all_samples_count)
                except ZeroDivisionError:
                    good_sample_ratio = 0
            else:
                all_samples_in_period = []
                good_samples_in_period = []
                good_sample_ratio = 0

            # Dictionary of the different levels of samples selected during filtering
            # for valid samples to use in accuracy calculations.
            sample_msg_data_filtering = dict(all_samples=samplesforpos,  # All samples from target period.
                                                    # Sample during stationary period at end of target
                                                    # presentation display.
                                                    stationary_samples=stationary_samples,
                                                    # Samples that occurred within the
                                                    # defined time selection period.
                                                    time_filtered_samples=all_samples_in_period,
                                                    # Samples from the selection period that
                                                    # do not have missing data
                                                    used_samples=good_samples_in_period)

            position_results = dict(index=pindex,
                                    target_position=target_positions_used[pindex],
                                    sample_time_range=[first_stime, last_stime],
                                    filter_samples_time_range=[filter_stime, filter_etime],
                                    valid_filtered_sample_perc=good_sample_ratio)

            for k, v in position_results.items():
                self.io.sendMessageEvent('{}: {}'.format(k, v), 'VALIDATION')

            position_results['sample_from_filter_stages'] = sample_msg_data_filtering

            position_results2 = dict()
            if int(good_sample_ratio * 100) == 0:
                position_results2['calculation_status'] = 'FAILED'
                results['positions_failed_processing'] += 1
            else:
                target_x = good_samples_in_period[:]['targ_pos_x']
                target_y = good_samples_in_period[:]['targ_pos_y']

                binoc_sample_types = [EventConstants.BINOCULAR_EYE_SAMPLE, EventConstants.GAZEPOINT_SAMPLE]
                if self.targetsequence.sample_type in binoc_sample_types:
                    left_x = good_samples_in_period[:]['left_eye_x']
                    left_y = good_samples_in_period[:]['left_eye_y']
                    left_error_x = target_x - left_x
                    left_error_y = target_y - left_y
                    left_error_xy = np.hypot(left_error_x, left_error_y)

                    right_x = good_samples_in_period[:]['right_eye_x']
                    right_y = good_samples_in_period[:]['right_eye_y']
                    right_error_x = target_x - right_x
                    right_error_y = target_y - right_y
                    right_error_xy = np.hypot(right_error_x, right_error_y)

                    lr_error = (right_error_xy + left_error_xy) / 2.0
                    lr_error_max = lr_error.max()
                    lr_error_min = lr_error.min()
                    lr_error_mean = lr_error.mean()
                    lr_error_std = np.std(lr_error)
                    min_error = min(min_error, lr_error_min)
                    max_error = max(max_error, lr_error_max)
                    summed_error += lr_error_mean
                    point_count += 1.0
                else:
                    eye_x = good_samples_in_period[:]['eye_x']
                    eye_y = good_samples_in_period[:]['eye_y']
                    error_x = target_x - eye_x
                    error_y = target_y - eye_y
                    error_xy = np.hypot(error_x, error_y)
                    lr_error = error_xy
                    lr_error_max = lr_error.max()
                    lr_error_min = lr_error.min()
                    lr_error_mean = lr_error.mean()
                    lr_error_std = np.std(lr_error)
                    min_error = min(min_error, lr_error_min)
                    max_error = max(max_error, lr_error_max)
                    summed_error += lr_error_mean
                    point_count += 1.0

                position_results2['calculation_status'] = 'PASSED'
                position_results2['min_error'] = lr_error_min
                position_results2['max_error'] = lr_error_max
                position_results2['mean_error'] = lr_error_mean
                position_results2['stdev_error'] = lr_error_std
            for k, v in position_results2.items():
                self.io.sendMessageEvent('{}: {}'.format(k, v), 'VALIDATION')
                position_results[k] = v
            results['position_results'].append(position_results)
            self.io.sendMessageEvent('Done Target Position Results : {0}'.format(pindex), 'VALIDATION')

        unit_type = self.win.units
        if self.results_in_degrees:
            unit_type = 'degree'
        mean_error = summed_error / point_count
        err_results = dict(reporting_unit_type=unit_type, min_error=min_error, max_error=max_error,
                           mean_error=mean_error, passed=results['positions_failed_processing'] == 0,
                           positions_failed_processing=results['positions_failed_processing'])

        for k, v in err_results.items():
            self.io.sendMessageEvent('{}: {}'.format(k, v), 'VALIDATION')
            results[k] = v

        self.io.sendMessageEvent('Validation Report Complete', 'VALIDATION')

        self._validation_results = results
        return self._validation_results

    def _generateImageName(self):
        import datetime
        file_name = 'validation_' + datetime.datetime.now().strftime('%d_%m_%Y_%H_%M') + '.png'
        #if self.save_results_screen:
        #    return normjoin(self.save_results_screen, file_name)
        rootScriptPath = os.path.dirname(sys.argv[0])
        return normjoin(rootScriptPath, file_name)

    def drawResultScreen(self):
        """
        Draw validation results screen.
        :return:
        """

        results = self.getValidationResults()

        for tp in self.positions.getPositions():
            self.targetsequence.target.pos = tp
            self.targetsequence.target.draw()

        title_txt = 'Validation Results\nMin: %.4f, Max: %.4f,' \
                    ' Mean %.4f (%s units)' % (results['min_error'], results['max_error'],
                                               results['mean_error'], results['reporting_unit_type'])
        title_stim = visual.TextStim(self.win, text=title_txt, height=24, pos=(0.0, (self.win.size[1] / 2.0) * .95),
                                     color=self.text_color, colorSpace=self.text_color_space, units='pix', antialias=True,
                                     anchorVert='center', anchorHoriz='center', wrapWidth=self.win.size[0] * .8)
        title_stim.draw()

        exit_text = visual.TextStim(self.win, text='Press SPACE to continue.', opacity=1.0, units='pix', height=None,
                                    pos=(0.0, -(self.win.size[1] / 2.0) * .95), color=self.text_color, colorSpace=self.text_color_space,
                                    antialias=True, bold=True, anchorVert='center', anchorHoriz='center',
                                    wrapWidth=self.win.size[0] * .8)
        exit_text.draw()

        color_list = pl.cm.tab20b(np.linspace(0, 1, (len(results['position_results']))))
        # draw eye samples
        ci = 0
        for position_results in results['position_results']:
            color = color_list[ci] * 2.0 - 1.0
            utype = 'pix'
            target_x, target_y = position_results['target_position']

            sample_gfx_radius = deg2pix(0.33, self.win.monitor, correctFlat=False)
            if self.results_in_degrees:
                sample_gfx_radius = 0.33
                utype='deg'
            sample_gfx = visual.Circle(self.win, radius=sample_gfx_radius, fillColor=color, lineColor=[1, 1, 1],
                                       lineWidth=1, edges=64, units=utype, colorSpace='rgb', opacity=0.66,
                                       interpolate=True, autoLog=False)

            if position_results['calculation_status'] == 'FAILED':
                position_txt = "Failed"
                txt_bold = True
                position_txt_color = "red"
            else:
                samples = position_results['sample_from_filter_stages']['used_samples']
                binoc_sample_types = [EventConstants.BINOCULAR_EYE_SAMPLE, EventConstants.GAZEPOINT_SAMPLE]
                if self.targetsequence.sample_type in binoc_sample_types:
                    gaze_x = (samples[:]['left_eye_x'] + samples[:]['right_eye_x']) / 2.0
                    gaze_y = (samples[:]['left_eye_y'] + samples[:]['right_eye_y']) / 2.0
                else:
                    gaze_x = samples[:]['eye_x']
                    gaze_y = samples[:]['eye_y']

                for i in range(len(gaze_x)):
                    if self.results_in_degrees:
                        g_pos = gaze_x[i], gaze_y[i]
                    else:
                        g_pos = toPix(self.win, gaze_x[i], gaze_y[i])
                        g_pos = g_pos[0][0], g_pos[1][0]
                    sample_gfx.pos = g_pos
                    sample_gfx.draw()
                txt_bold = False
                position_txt = "Gaze Error:\nMin: %.4f\nMax: %.4f\n" \
                               "Avg: %.4f\nStdev: %.4f" % (position_results['min_error'],
                                                           position_results['max_error'],
                                                           position_results['mean_error'],
                                                           position_results['stdev_error'])
                position_txt_color = "green"

            if self.targetsequence.display_gaze:
                text_pix_pos = toPix(self.win, target_x, target_y)
                text_pix_pos = text_pix_pos[0][0], text_pix_pos[1][0]
                target_text_stim = visual.TextStim(self.win, text=position_txt, units='pix', pos=text_pix_pos,
                                                   height=21, color=position_txt_color, antialias=True,
                                                   bold=txt_bold, anchorVert='center', anchorHoriz='center')
                target_text_stim.draw()
            ci += 1


class ValidationTargetRenderer:
    TARGET_STATIONARY = 1
    TARGET_MOVING = 2
    TARGET_EXPANDING = 4
    TARGET_CONTRACTING = 8
    # Experiment Message text field types and tokens
    message_types = dict(BEGIN_SEQUENCE=('BEGIN_SEQUENCE', '', int),
                         DONE_SEQUENCE=('DONE_SEQUENCE', '', int),
                         NEXT_POS_TRIG=('NEXT_POS_TRIG', '', int, float),
                         START_DRAW=('START_DRAW', ',', int, float, float, float, float),
                         SYNCTIME=('SYNCTIME', ',', int, float, float, float, float),
                         EXPAND_SIZE=('EXPAND_SIZE', '', float, float),
                         CONTRACT_SIZE=('CONTRACT_SIZE', '', float, float),
                         POS_UPDATE=('POS_UPDATE', ',', float, float),
                         TARGET_POS=('TARGET_POS', ',', float, float))
    max_msg_type_length = max([len(s) for s in message_types.keys()])
    binocular_sample_message_element = [('targ_pos_ix', int),
                                        ('last_msg_time', np.float64),
                                        ('last_msg_type', str, max_msg_type_length),
                                        ('next_msg_time', np.float64),
                                        ('next_msg_type', str, max_msg_type_length),
                                        ('targ_pos_x', np.float64),
                                        ('targ_pos_y', np.float64),
                                        ('targ_state', int),
                                        ('eye_time', np.float64),
                                        ('eye_status', int),
                                        ('left_eye_x', np.float64),
                                        ('left_eye_y', np.float64),
                                        ('left_pupil_size', np.float64),
                                        ('right_eye_x', np.float64),
                                        ('right_eye_y', np.float64),
                                        ('right_pupil_size', np.float64)]
    monocular_sample_message_element = [('targ_pos_ix', int),
                                        ('last_msg_time', np.float64),
                                        ('last_msg_type', str, max_msg_type_length),
                                        ('next_msg_time', np.float64),
                                        ('next_msg_type', str, max_msg_type_length),
                                        ('targ_pos_x', np.float64),
                                        ('targ_pos_y', np.float64),
                                        ('targ_state', int),
                                        ('eye_time', np.float64),
                                        ('eye_status', int),
                                        ('eye_x', np.float64),
                                        ('eye_y', np.float64),
                                        ('pupil_size', np.float64)]

    def __init__(self, win, target, positions, storeeventsfor=[], triggers=None, msgcategory='',
                 io=None, terminate_key='escape', gaze_cursor_key='g', gaze_cursor=None,
                 color_space=None, unit_type=None):
        """
        ValidationTargetRenderer is an internal class used by `ValidationProcedure`.

        psychopy.iohub.client.eyetracker.validation.Trigger based classes are used
        to define the criteria used to start displaying the next target position graphics.
        By providing a set of DeviceEventTriggers, complex criteria for
        target position pacing can be defined.

        iohub devices can be provided in the storeeventsfor keyword argument.
        Events which occur during each target position presentation period are
        stored and are available at the end of the display() period, grouped by
        position index and device event types.

        :param win:
        :param target:
        :param positions:
        :param storeeventsfor:
        :param triggers:
        :param msgcategory:
        :param io:
        """
        self.terminate_key = terminate_key
        self.gaze_cursor_key = gaze_cursor_key
        self.display_gaze = False
        self.gaze_cursor = None
        if isinstance(gaze_cursor, (str, list, tuple)):
            gc_size = deg2pix(3.0, win.monitor, correctFlat=False)
            self.gaze_cursor = visual.GratingStim(win, tex=None, mask='gauss', pos=(0, 0), size=(gc_size, gc_size),
                                                  color=gaze_cursor, colorSpace=color_space, units='pix', opacity=0.8)
        elif gaze_cursor and hasattr(gaze_cursor, 'setPos'):
            self.gaze_cursor = gaze_cursor
        else:
            raise ValueError("Gaze Cursor must be a color value or visual stim type.")
        self._terminate_requested = False
        self.win = proxy(win)
        self.target = target
        self.positions = positions
        self.storeevents = storeeventsfor
        self.msgcategory = msgcategory

        if io is None:
            io = ioHubConnection.getActiveConnection()
        self.io = io
        self._keyboard = self.io.devices.keyboard

        # If storeevents is True, targetdata will be a list of dict's.
        # Each dict, among other things, contains all ioHub events that occurred
        # from when a target was first presented at a position, to when the
        # the wait period completed for that position.
        #
        self.targetdata = []
        self.triggers = triggers

    def _draw(self):
        """
        Draw the target stim.
        """
        self.target.draw()
        if self.gaze_cursor and self.display_gaze:
            gpos = self.io.devices.tracker.getLastGazePosition()
            valid_gaze_pos = isinstance(gpos, (tuple, list))
            if valid_gaze_pos:
                pix_pos = toPix(self.win, *gpos)
                pix_pos = pix_pos[0][0], pix_pos[1][0]
                self.gaze_cursor.setPos(pix_pos)
                self.gaze_cursor.draw()

    def _animateTarget(self, topos, frompos, **kwargs):
        """
        Any logic related to drawing the target at the new screen position,
        including any intermediate animation effects, is done here.

        Return the flip time when the target was first drawn at the newpos
        location.
        """
        io = self.io

        # Target position animation phase
        animate_position = kwargs.get('enable')
        targetdelay = kwargs.get('targetdelay')
        if frompos is not None:
            if animate_position:
                start_time = getTime()
                while (getTime() - start_time) <= targetdelay:
                    t = (getTime()-start_time) / targetdelay
                    v1 = frompos
                    v2 = topos
                    t = 60.0 * ((1.0 / 10.0) * t ** 5 - (1.0 / 4.0) * t ** 4 + (1.0 / 6.0) * t ** 3)
                    moveTo = ((1.0 - t) * v1[0] + t * v2[0], (1.0 - t) * v1[1] + t * v2[1])
                    self.target.pos = moveTo
                    self._draw()
                    fliptime = self.win.flip()
                    io.sendMessageEvent('POS_UPDATE %.4f,%.4f' % (moveTo[0], moveTo[1]), self.msgcategory,
                                        sec_time=fliptime)
                    self._addDeviceEvents()
                    if self._terminate_requested:
                        return 0
            else:
                # No target animation, so just show cleared screen
                # for targetdelay seconds
                fliptime = self.win.flip(clearBuffer=True)
                while getTime() < fliptime+targetdelay:
                    self._addDeviceEvents()
                    if self._terminate_requested:
                        return 0

        self.target.pos = topos
        self._draw()
        fliptime = self.win.flip()
        io.sendMessageEvent('TARGET_POS %.4f,%.4f' % (topos[0], topos[1]), self.msgcategory, sec_time=fliptime)
        self._addDeviceEvents()

        # Target expand / contract phase
        expandedscale = kwargs.get('expandedscale')
        targetduration = kwargs.get('targetduration')
        contract_target = kwargs.get('contracttarget')
        initialradius = self.target.radius

        expand_duration = None
        contract_duration = None
        if contract_target and expandedscale and expandedscale > 1.0:
            # both expand and contract
            expand_duration = contract_duration = targetduration / 2
        elif contract_target:
            # contract only
            expand_duration = None
            contract_duration = targetduration
        elif expandedscale and expandedscale > 1.0:
            # contract only
            expand_duration = targetduration
            contract_duration = None

        if expand_duration:
            expandedradius = self.target.radius * expandedscale
            starttime = getTime()
            expandedtime = fliptime + expand_duration
            while fliptime < expandedtime:
                mu = (fliptime - starttime) / expand_duration
                cradius = initialradius * (1.0 - mu) + expandedradius * mu
                self.target.radius = cradius
                self._draw()
                fliptime = self.win.flip()
                io.sendMessageEvent('EXPAND_SIZE %.4f %.4f' % (cradius, initialradius), self.msgcategory,
                                    sec_time=fliptime)
                self._addDeviceEvents()
                if self._terminate_requested:
                    return 0

        if contract_duration:
            starttime = getTime()
            contractedtime = fliptime + contract_duration
            start_radius = self.target.radius
            try:
                stop_radius = self.target.innerRadius
            except:
                stop_radius = start_radius/2
                print("Warning: validation target has no .innerRadius property.")
            while fliptime < contractedtime:
                mu = (fliptime - starttime) / contract_duration
                cradius = start_radius * (1.0 - mu) + stop_radius * mu
                self.target.radius = cradius
                self._draw()
                fliptime = self.win.flip()
                io.sendMessageEvent('CONTRACT_SIZE %.4f %.4f' % (cradius, initialradius), self.msgcategory,
                                    sec_time=fliptime)
                self._addDeviceEvents()
                if self._terminate_requested:
                    return 0
        return fliptime

    def moveTo(self, topos, frompos, **kwargs):
        """
        Indicates that the target should be moved frompos to topos.

        If a PositionGrid has been provided, moveTo should not be called
        directly. Instead, use the display() method to start the full
        target position presentation sequence.
        """
        io = self.io
        fpx, fpy = -1, -1
        if frompos is not None:
            fpx, fpy = frompos[0], frompos[1]
        io.sendMessageEvent('START_DRAW %d %.4f,%.4f %.4f,%.4f' % (self.positions.posIndex, fpx, fpy, topos[0],
                                                                   topos[1]), self.msgcategory)

        fliptime = self._animateTarget(topos, frompos, **kwargs)
        io.sendMessageEvent('SYNCTIME %d %.4f,%.4f %.4f,%.4f' % (self.positions.posIndex, fpx, fpy, topos[0], topos[1]),
                            self.msgcategory, sec_time=fliptime)

        # wait for trigger to fire
        last_pump_time = fliptime
        trig_fired = self._hasTriggerFired(start_time=fliptime)
        while not trig_fired:
            if getTime() - last_pump_time >= 0.250:
                win32MessagePump()
                last_pump_time = getTime()

            if self.display_gaze:
                self._draw()
                self.win.flip()
            else:
                sleep(0.001)

            if self._checkForTerminate():
                return
            self._checkForToggleGaze()
            trig_fired = self._hasTriggerFired(start_time=fliptime)

    def _hasTriggerFired(self, **kwargs):
        """
        Used internally to know when one of the triggers has occurred and
        the target should move to the next target position.
        """
        # wait for trigger to fire
        triggered = None
        for trig in self.triggers:
            if trig.triggered(**kwargs):
                triggered = trig
            self._addDeviceEvents(trig.clearEventHistory(True))
            if triggered:
                break

        if triggered:
            # by default, assume it was a timer trigger,so use 255 as 'event type'
            event_type_id = 255
            trig_evt = triggered.getTriggeringEvent()
            if hasattr(trig_evt, 'type'):
                # actually it was a device event trigger
                event_type_id = trig_evt.type
            # get time trigger of trigger event
            event_time = triggered.getTriggeringTime()
            self.io.sendMessageEvent('NEXT_POS_TRIG %d %.3f' % (event_type_id, event_time), self.msgcategory)
            for trig in self.triggers:
                trig.resetTrigger()
        return triggered

    def _initTargetData(self, frompos, topos):
        """
        Internally used to create the data structure used to store position
        information and events which occurred during each target position
        period.
        """
        if self.storeevents:
            deviceevents = {}
            for device in self.storeevents:
                deviceevents[device] = []
        self.targetdata.append(dict(frompos=frompos, topos=topos, events=deviceevents))

    def _addDeviceEvents(self, device_event_dict={}):
        if self._checkForTerminate():
            return
        self._checkForToggleGaze()
        dev_event_buffer = self.targetdata[-1]['events']
        for dev, dev_events in dev_event_buffer.items():
            if dev in device_event_dict:
                dev_events.extend(device_event_dict[dev])
            else:
                dev_events.extend(dev.getEvents())

    def _checkForTerminate(self):
        keys = self._keyboard.getEvents(EventConstants.KEYBOARD_PRESS, clearEvents=False)
        for k in keys:
            if k.key == self.terminate_key:
                self._terminate_requested = True
                break
        return self._terminate_requested

    def _checkForToggleGaze(self):
        keys = self._keyboard.getEvents(EventConstants.KEYBOARD_PRESS, clearEvents=False)
        for k in keys:
            if k.key == self.gaze_cursor_key:
                # get (clear) the event so it does not trigger multiple times.
                self._keyboard.getEvents(EventConstants.KEYBOARD_PRESS, clearEvents=True)
                self.display_gaze = not self.display_gaze
                self._draw()
                self.win.flip()
                return self.display_gaze
        return self.display_gaze

    def display(self, **kwargs):
        """
        Display the target at each point in the position grid, performing
        target animation if requested. The target then holds position until one
        of the specified triggers occurs, resulting in the target moving to the
        next position in the positiongrid.

        To setup target animation between grid positions, the following keyword
        arguments are supported. If an option is not specified, the animation
        related to it is not performed.



        Note that target expansion and contraction change the target stimulus
        outer diameter only. The edge thickness and central dot radius do not
        change.

        When this method returns, the target has been displayed at all
        positions. Data collected for each position period can be accessed via
        the targetdata attribute.
        """
        del self.targetdata[:]
        prevpos = None

        io = self.io
        io.clearEvents('all')
        io.sendMessageEvent('BEGIN_SEQUENCE {0}'.format(len(self.positions.positions)), self.msgcategory)
        turn_rec_off = []
        for d in self.storeevents:
            if not d.isReportingEvents():
                d.enableEventReporting(True)
                turn_rec_off.append(d)

        sleep(0.025)
        initialsize=self.target.radius
        for pos in self.positions:
            self._initTargetData(prevpos, pos)
            self._addDeviceEvents()
            if self._terminate_requested:
                break
            self.target.radius = initialsize
            self.moveTo(pos, prevpos, **kwargs)
            prevpos = pos
            self._addDeviceEvents()
            if self._terminate_requested:
                break
        self.target.radius = initialsize
        for d in turn_rec_off:
            d.enableEventReporting(False)

        if self._terminate_requested:
            io.sendMessageEvent('VALIDATION TERMINATED BY USER', self.msgcategory)
            return False

        io.sendMessageEvent('DONE_SEQUENCE {0}'.format(len(self.positions.positions)), self.msgcategory)
        sleep(0.025)
        self._addDeviceEvents()
        io.clearEvents('all')
        return True

    def _processMessageEvents(self):
        self.target_pos_msgs = []
        self.saved_pos_samples = []
        for pd in self.targetdata:
            events = pd.get('events')

            # create a dict of device labels as keys, device events as value
            devlabel_events = {}
            for k, v in events.items():
                devlabel_events[k.getName()] = v

            samples = devlabel_events.get('tracker', [])
            # remove any eyetracker events that are not samples
            samples = [s for s in samples if s.type in (EventConstants.BINOCULAR_EYE_SAMPLE,
                                                        EventConstants.MONOCULAR_EYE_SAMPLE,
                                                        EventConstants.GAZEPOINT_SAMPLE)]
            self.saved_pos_samples.append(samples)

            self.sample_type = self.saved_pos_samples[0][0].type
            if self.sample_type == EventConstants.MONOCULAR_EYE_SAMPLE:
                self.sample_msg_dtype = self.monocular_sample_message_element
            else:
                self.sample_msg_dtype = self.binocular_sample_message_element
            messages = devlabel_events.get('experiment', [])
            msg_lists = []
            for m in messages:
                temp = m.text.strip().split()
                msg_type = self.message_types.get(temp[0])
                if msg_type:
                    current_msg = [m.time, m.category]
                    if msg_type[1] == ',':
                        for t in temp:
                            current_msg.extend(t.split(','))
                    else:
                        current_msg.extend(temp)

                    for mi, dtype in enumerate(msg_type[2:]):
                        current_msg[mi + 3] = dtype(current_msg[mi + 3])

                    msg_lists.append(current_msg)

            if msg_lists[0][2] == 'NEXT_POS_TRIG':
                # handle case where the trigger msg from the previous target
                # message was not read until the start of the next pos.
                # In which case, move msg to end of previous targ pos msgs
                npm = msg_lists.pop(0)
                self.target_pos_msgs[-1].append(npm)

            self.target_pos_msgs.append(msg_lists)

        for i in range(len(self.target_pos_msgs)):
            self.target_pos_msgs[i] = np.asarray(self.target_pos_msgs[i], dtype=object)

        return self.target_pos_msgs

    def getSampleMessageData(self):
        """
        Return a list of numpy ndarrays, each containing joined eye sample
        and previous / next experiment message data for the sample's time.
        """
        # preprocess message events
        self._processMessageEvents()

        # inline func to return sample field array based on sample namedtup
        def getSampleData(s):
            sampledata = [s.time, s.status]
            binoc_sample_types = [EventConstants.BINOCULAR_EYE_SAMPLE, EventConstants.GAZEPOINT_SAMPLE]
            if s.type in binoc_sample_types:
                sampledata.extend((s.left_gaze_x, s.left_gaze_y, s.left_pupil_measure1,
                                   s.right_gaze_x, s.right_gaze_y, s.right_pupil_measure1))
                return sampledata

            sampledata.extend((s.gaze_x, s.gaze_y, s.pupil_measure1))
            return sampledata

        current_target_pos = -1.0, -1.0
        current_targ_state = 0
        target_pos_samples = []
        for pindex, samples in enumerate(self.saved_pos_samples):
            last_msg, messages = self.target_pos_msgs[pindex][0], self.target_pos_msgs[pindex][1:]
            samplesforposition = []
            pos_sample_count = len(samples)
            si = 0
            for current_msg in messages:
                last_msg_time = last_msg[0]
                last_msg_type = last_msg[2]
                if last_msg_type == 'START_DRAW':
                    if not current_targ_state & self.TARGET_STATIONARY:
                        current_targ_state += self.TARGET_STATIONARY
                    current_targ_state -= current_targ_state & self.TARGET_MOVING
                    current_targ_state -= current_targ_state & self.TARGET_EXPANDING
                    current_targ_state -= current_targ_state & self.TARGET_CONTRACTING
                elif last_msg_type == 'EXPAND_SIZE':
                    if not current_targ_state & self.TARGET_EXPANDING:
                        current_targ_state += self.TARGET_EXPANDING
                    current_targ_state -= current_targ_state & self.TARGET_CONTRACTING
                elif last_msg_type == 'CONTRACT_SIZE':
                    if not current_targ_state & self.TARGET_CONTRACTING:
                        current_targ_state += self.TARGET_CONTRACTING
                    current_targ_state -= current_targ_state & self.TARGET_EXPANDING
                elif last_msg_type == 'TARGET_POS':
                    current_target_pos = float(last_msg[3]), float(last_msg[4])
                    current_targ_state -= current_targ_state & self.TARGET_MOVING
                    if not current_targ_state & self.TARGET_STATIONARY:
                        current_targ_state += self.TARGET_STATIONARY
                elif last_msg_type == 'POS_UPDATE':
                    current_target_pos = float(last_msg[3]), float(last_msg[4])
                    if not current_targ_state & self.TARGET_MOVING:
                        current_targ_state += self.TARGET_MOVING
                    current_targ_state -= current_targ_state & self.TARGET_STATIONARY
                elif last_msg_type == 'SYNCTIME':
                    if not current_targ_state & self.TARGET_STATIONARY:
                        current_targ_state += self.TARGET_STATIONARY
                    current_targ_state -= current_targ_state & self.TARGET_MOVING
                    current_targ_state -= current_targ_state & self.TARGET_EXPANDING
                    current_targ_state -= current_targ_state & self.TARGET_CONTRACTING
                    current_target_pos = float(last_msg[6]), float(last_msg[7])

                while si < pos_sample_count:
                    sample = samples[si]
                    if last_msg_time <= sample.time < current_msg[0]:
                        sarray = [pindex, last_msg_time, last_msg_type,
                                  current_msg[0], current_msg[2],
                                  current_target_pos[0], current_target_pos[1],
                                  current_targ_state]
                        sarray.extend(getSampleData(sample))
                        sndarray = np.asarray(tuple(sarray), dtype=self.sample_msg_dtype)
                        samplesforposition.append(sndarray)
                        si += 1
                    elif sample.time >= current_msg[0]:
                        break
                    else:
                        si += 1
                last_msg = current_msg

            possamples = np.asanyarray(samplesforposition)
            target_pos_samples.append(possamples)

        # So we now have a list len == number target positions. Each element
        # of the list is a list of all eye sample / message data for a
        # target position. Each element of the data list for a single target
        # position is itself a list that that contains combined info about
        # an eye sample and message info valid for when the sample time was.
        return np.asanyarray(target_pos_samples, dtype=object)


def toPix(win, x, y):
    """Returns the stim's position in pixels,
    based on its pos, units, and win.
    """
    try:
        xy = np.zeros((len(x), 2))
    except TypeError:
        xy = np.zeros((1, 2))

    xy[:, 0] = x
    xy[:, 1] = y
    r = convertToPix(np.asarray((0, 0)), xy, win.units, win)
    return r[:, 0], r[:, 1]


def toDeg(win, x, y):
    try:
        xy = np.zeros((len(x), 2))
    except TypeError:
        xy = np.zeros((1, 2))
    xy[:, 0] = x
    xy[:, 1] = y
    r = pix2deg(xy, win.monitor, correctFlat=False)
    return r[:, 0], r[:, 1]
