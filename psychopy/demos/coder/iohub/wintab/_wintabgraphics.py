# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
"""iohub wintab util objects / functions for stylus, position traces,
and validation process psychopy graphics.
"""
from __future__ import division, absolute_import

import math
from collections import OrderedDict

import numpy as np

from psychopy import visual, core
from psychopy.visual.basevisual import MinimalStim

class PenPositionStim(MinimalStim):
    """Draws the current pen x,y position with graphics that represent the
    pressure, z axis, and tilt data for the wintab sample used."""
    def __init__(self, win, min_opacity=0.0, hover_color=(255,0,0), 
                 touching_color=(0,255,0), tiltline_color=(255,255, 0),
                 tiltline_width=2,
                 min_size=0.033, size_range=0.1666, tiltline_scalar=1.0,
                 name=None, autoLog=None, depth=-10000, colorSpace='rgb255'):
        self.win = win
        self.depth = depth
        super(PenPositionStim, self).__init__(name, autoLog)

        # Pen Hovering Related

        # Opaticy is changed based on pen's z axis if data for z axis
        # is available. Opacity of min_opacity is used when pen is at the
        # furthest hover distance (z value) supported by the device.
        # Opacity of 1.0 is used when z value == 0, meaning pen is touching
        # digitizer surface.
        self.min_opacity = min_opacity
        # If z axis is supported, hover_color specifies the color of the pen
        # position dot when z val > 0.
        self.hover_color = hover_color

        # Pen Pressure Related

        # Smallest radius (in norm units) that the pen position gaussian blob
        # will have, which occurs when pen pressure value is 0
        self.min_size = min_size
        # As pen pressure value increases, so does position gaussian blob
        # radius (in norm units). Max radius is reached when pressure is
        # at max device pressure value, and is equal to min_size+size_range
        self.size_range = size_range
        # Color of pen position blob when pressure > 0.
        self.touching_color = touching_color

        # Pen tilt Related

        # Color of line graphic used to represent the pens tilt relative to
        # the digitizer surface.
        self.tiltline_color = tiltline_color
        self.tiltline_width = tiltline_width
        self.tiltline_scalar = tiltline_scalar
        # Create a Gausian blob stim to use for pen position graphic
        self.pen_guass = visual.PatchStim(win, units='norm', tex='none',
                                          mask='gauss', pos=(0, 0), 
                                          colorSpace='rgb255',
                                          size=(self.min_size,self.min_size),
                                          color=self.hover_color,
                                          autoLog=False,
                                          opacity=0.0)

        # Create a line stim to use for pen position graphic
        self.pen_tilt_line = visual.Line(win, units='norm', start=[0, 0],
                                         lineWidth=self.tiltline_width,
                                         end=[0, 0],
                                         colorSpace='rgb255',
                                         lineColor=self.tiltline_color,
                                         opacity=0.0)
        #self.pen_tilt_line.opacity=0.0

    def updateFromEvent(self, evt):
        """Update the pen position and tilt graphics based on the data from
        a wintab sample event.

        :param evt: iohub wintab sample event
        :return:
        """
        # update the pen position stim based on
        # the last tablet event's data
        if evt.pressure > 0:
            # pen is touching tablet surface
            self.pen_guass.color = self.touching_color
        else:
            # pen is hovering just above tablet surface
            self.pen_guass.color = self.hover_color

        if evt.device.axis['pressure']['supported']:
            # change size of pen position blob based on samples pressure
            # value
            pnorm = evt.pressure / evt.device.axis['pressure']['range']
            self.pen_guass.size = self.min_size + pnorm * self.size_range

        # set the position of the gauss blob to be the pen x,y value converted
        # to norm screen coords.
        self.pen_guass.pos = evt.getNormPos()

        # if supported, update all graphics opacity based on the samples z value
        # otherwise opacity is always 1.0
        if evt.device.axis['z']['supported']:
            z = evt.device.axis['z']['range'] - evt.z
            znorm = z / evt.device.axis['z']['range']
            sopacity = self.min_opacity + znorm * (1.0 - self.min_opacity)
            self.pen_guass.opacity = self.pen_tilt_line.opacity = sopacity
        else:
            self.pen_guass.opacity = self.pen_tilt_line.opacity = 1.0

        # Change the tilt line start position to == pen position
        self.pen_tilt_line.start = self.pen_guass.pos

        # Change the tilt line end position based on samples tilt value
        # If tilt is not supported, it will always return 0,0
        # so no line is drawn.
        t1, t2 = evt.tilt
        pen_tilt_xy = 0, 0
        if t1 != t2 != 0:
            pen_tilt_xy = t1 * math.sin(t2), t1 * math.cos(t2)

        pen_pos = self.pen_guass.pos
        tiltend = (pen_pos[0] + pen_tilt_xy[0]*self.tiltline_scalar, 
                   pen_pos[1] + pen_tilt_xy[1]*self.tiltline_scalar)
        self.pen_tilt_line.end = tiltend

    def draw(self):
        """Draw the PenPositionStim to the opengl back buffer. This needs
        to be called prior to calling win.flip() for the stim is to be
        displayed.

        :return: None

        """
        self.pen_guass.draw()
        self.pen_tilt_line.draw()

    def clear(self):
        """Hide the graphics on the screen, even if they are drawn, by
        setting opacity to 0.

        :return: None

        """
        self.pen_guass.opacity = 0.0
        self.pen_tilt_line.opacity = 0.0

    def __del__(self):
        self.win = None

class PenTracesStim(MinimalStim):
    """Graphics representing where the pen has been moved on the digitizer
    surface. Positions where sample pressure > 0 are included.

    Implemented as a list of visual.ShapeStim, each representing a
    single pen trace/segment (series on pen samples with pressure >
    0). For improved performance, a single pen trace can have
    max_trace_len points before a new ShapeStim is created and made
    the 'current' pen trace'.
    """
    def __init__( self, win, lineWidth=2, lineColor=(0, 0, 0), opacity=1.0,
                 maxlen=256, name=None, autoLog=None, depth=-1000):
        self.depth = depth
        self.win = win
        super(PenTracesStim, self).__init__(name, autoLog)
        # A single pen trace can have at most max_trace_len points.
        self.max_trace_len = maxlen
        # The list of ShapeStim representing pen traces
        self.pentracestim = []
        # The ShapeStim state new / upcoming position points will be added to.
        self.current_pentrace = None
        # A list representation of the current_pentrace.vertices
        self.current_points = []
        # The last pen position added to a pen trace.
        self.last_pos = [0, 0]
        
        self.lineWidth=lineWidth
        self.lineColor=lineColor
        self.opacity=opacity


    @property
    def traces(self):
        """List of np arrays, each np array is the set of vertices for one
        pen trace.

        :return: list

        """
        return [pts.vertices for pts in self.pentracestim]

    def updateFromEvents(self, sample_events):
        """
        Update the stim graphics based on 0 - n pen sample events.
        :param sample_events:
        :return: None
        """
        for pevt in sample_events:
            if 'FIRST_ENTER' in pevt.status:
                self.end()
            if pevt.pressure > 0:
                lpx, lpy = self.last_pos
                px, py = pevt.getPixPos(self.win)
                if lpx != px or lpy != py:
                    if len(self.current_points) >= self.max_trace_len:
                        self.end()
                        self.append((lpx, lpy))
                    self.last_pos = (px, py)
                    self.append(self.last_pos)
            else:
                self.end()

    def draw(self):
        """Draws each pen trace ShapeStim to the opengl back buffer. This
        method must be called prior to calling win.flip() if it is to
        appear on the screen.

        :return: None
        """
        for pts in self.pentracestim:
            pts.draw()

    def start(self, first_point):
        """Start a new pen trace, by creating a new ShapeStim, adding it to
        the pentracestim list, and making it the current_pentrace.

        :param first_point: the first point in the ShapStim being craeted.
        :return: None
        """
        self.end()
        self.current_points.append(first_point)
        self.current_pentrace = visual.ShapeStim(self.win,
                                                 units='pix',
                                                 lineWidth=self.lineWidth,
                                                 color=self.lineColor,
                                                 lineColorSpace='rgb255',
                                                 vertices=self.current_points,
                                                 closeShape=False,
                                                 pos=(0, 0),
                                                 size=1,
                                                 ori=0.0,
                                                 opacity=self.opacity,
                                                 interpolate=True)
        self.pentracestim.append(self.current_pentrace)

    def end(self):
        """Stop using the current_pentrace ShapeStim. Next time a pen
        sample position is added to the PenTracesStim instance, a new
        ShapeStim will created and added to the pentracestim list.

        :return: None
        """
        self.current_pentrace = None
        self.current_points = []
        self.last_pos = [0, 0]

    def append(self, pos):
        """Add a pen position (in pix coords) to the current_pentrace
        ShapeStim vertices.

        :param pos: (x,y) tuple
        :return: None
        """
        if self.current_pentrace is None:
            self.start(pos)
        else:
            self.current_points.append(pos)
            self.current_pentrace.vertices = self.current_points

    def clear(self):
        """Remove all ShapStim being used. Next time this stim is drawn, no
        pen traces will exist.

        :return:
        """
        self.end()
        del self.pentracestim[:]

    def __del__(self):
        self.clear()
        self.win = None

#
# Pen position validation process code
#

class ScreenPositionValidation(object):
    NUM_VALID_SAMPLES_PER_TARG = 100
    TARGET_TIMEOUT = 10.0

    def __init__(self, win, io, target_stim=None, pos_grid=None,
                 display_pen_pos=True, force_quit=True, intro_title=None,
                 intro_text1=None, intro_text2=None, intro_target_pos=None):
        """ScreenPositionValidation is used to perform a pen position
        accuracy test for an iohub wintab device.

        :param win: psychopy Window instance to ude for the validation graphics
        :param io: iohub connection instance
        :param target_stim: None to use default, or  psychopy.iohub.util.targetpositionsequence.TargetStim instance
        :param pos_grid: None to use default, or  psychopy.iohub.util.targetpositionsequence.PositionGrid instance
        :param display_pen_pos: True to add calculated pen position graphic
        :param force_quit: Not Used
        :param intro_title: None to use default, str or unicode to set the text used for the introduction screen title, or an instance of psychopy.visual.TextStim
        :param intro_text1: None to use default, str or unicode to set the text used for the introduction text part 1, or an instance of psychopy.visual.TextStim
        :param intro_text2: None to use default, str or unicode to set the text used for the introduction text part 2, or an instance of psychopy.visual.TextStim
        :param intro_target_pos: None to use default, or (x,y) position to place the target graphic on the introduction screen. (x,y) position must be specified in 'norm' coordinate space.
        :return:
        """

        from psychopy.iohub.util.targetpositionsequence import TargetStim, PositionGrid

        self.win = win
        self.io = io
        self._lastPenSample = None
        self._targetStim = target_stim
        self._positionGrid = pos_grid
        self._forceQuit = force_quit
        self._displayPenPosition = display_pen_pos

        # IntroScreen Graphics
        intro_graphics = self._introScreenGraphics = OrderedDict()

        # Title Text
        title_stim = visual.TextStim(self.win, units='norm',
                                     pos=(0, .9),
                                     height=0.1,
                                     text='Pen Position Validation')
        if isinstance(intro_title, str):
            title_stim.setText(intro_title)
        elif isinstance(intro_title, visual.TextStim):
            title_stim = intro_title
        intro_graphics['title'] = title_stim

        # Intro Text part 1
        text1_stim = visual.TextStim(self.win, units='norm',
                                     pos=(0, .65),
                                     height=0.05,
                                     text='On the following screen, '
                                     'press the pen on the target '
                                     'graphic when it appears, '
                                     'as accurately as '
                                     'possible, until the target '
                                     'moves to a different '
                                     'location. Then press at the '
                                     'next target location. '
                                     'Hold the stylus in exactly '
                                     'the same way as you would '
                                     'hold a pen for normal '
                                     'handwriting.',
                                     wrapWidth=1.25
                                     )

        if isinstance(intro_text1, str):
            text1_stim.setText(intro_text1)
        elif isinstance(intro_text1, visual.TextStim):
            text1_stim = intro_text1
        intro_graphics['text1'] = text1_stim

        # Intro Text part 2
        text2_stim = visual.TextStim(self.win, units='norm',
                                     pos=(0, -0.2),
                                     height=0.066,
                                     color='green',
                                     text='Press the pen on the above '
                                     'target to start the '
                                     'validation, or the ESC key '
                                     'to skip the procedure.')
        if isinstance(intro_text2, str):
            text2_stim.setText(intro_text2)
        elif isinstance(intro_text2, visual.TextStim):
            text2_stim = intro_text2
        intro_graphics['text2'] = text2_stim

        self._penStim = None
        if self._displayPenPosition:
            # Validation Screen Graphics
            self._penStim = visual.Circle(self.win,
                                          radius=4,
                                          fillColor=[255, 0, 0],
                                          lineColor=[255, 0, 0],
                                          lineWidth=0,
                                          edges=8,  # int(np.pi*radius),
                                          units='pix',
                                          colorSpace='rgb255',
                                          opacity=0.9,
                                          contrast=1,
                                          interpolate=True,
                                          autoLog=False)

        if self._targetStim is None:
            self._targetStim = TargetStim(win,
                                          radius=16,
                                          fillcolor=[64, 64, 64],
                                          edgecolor=[192, 192, 192],
                                          edgewidth=1,
                                          dotcolor=[255, 255, 255],
                                          dotradius=3,
                                          units='pix',
                                          colorspace='rgb255',
                                          opacity=1.0,
                                          contrast=1.0
                                          )
        if intro_target_pos:
            self._targetStim.setPos(intro_target_pos)

        intro_graphics['target'] = self._targetStim

        if self._positionGrid is None:
            self._positionGrid = PositionGrid(
                winSize=win.monitor.getSizePix(),
                shape=[
                    3,
                    3],
                scale=0.9,
                posList=None,
                noiseStd=None,
                firstposindex=0,
                repeatfirstpos=True)

        # IntroScreen Graphics
        finished_graphics = self._finsihedScreenGraphics = OrderedDict()

        finished_graphics['title'] = visual.TextStim(
            self.win, units='norm', pos=(
                0, .9), height=0.1, text='Validation Complete')
        finished_graphics['result_status'] = visual.TextStim(
            self.win, units='norm', pos=(
                0, .7), height=0.07, color='blue', text='Result: {}')
        finished_graphics['result_stats'] = visual.TextStim(self.win, units='norm', pos=(
            0, .6), height=0.05, text='{}/{} Points Validated. Min, Max, Mean Errors: {}, {}, {}')
        finished_graphics['exit_text'] = visual.TextStim(
            self.win, units='norm', pos=(
                0, .5), height=0.05, text='Press any key to continue...')

    @property
    def targetStim(self):
        return self._targetStim

    @targetStim.setter
    def targetStim(self, ts):
        self._targetStim = ts

    @property
    def positionGrid(self):
        return self._positionGrid

    @positionGrid.setter
    def positionGrid(self, ts):
        self._positionGrid = ts

    def _enterIntroScreen(self):
        kb = self.io.devices.keyboard
        pen = self.io.devices.tablet

        exit_screen = False
        hitcount = 0
        pen.reporting = True
        kb.getPresses()

        while exit_screen is False:
            for ig in self._introScreenGraphics.values():
                ig.draw()
            samples = pen.getSamples()
            if samples:
                self._drawPenStim(samples[-1])
                spos = samples[-1].getPixPos(self.win)
                if samples[-1].pressure > 0 and \
                        self._introScreenGraphics['target'].contains(spos):
                    if hitcount > 10:
                        exit_screen = True
                    hitcount = hitcount + 1
                else:
                    hitcount = 0
            self.win.flip()
            if 'escape' in kb.getPresses():
                exit_screen = True
                pen.reporting = False
                break

        pen.reporting = False
        return True

    def _enterValidationSequence(self):
        val_results = dict(target_data=dict(), avg_err=0, min_err=1000,
                           max_err=-1000, status='PASSED', point_count=0,
                           ok_point_count=0)

        self._lastPenSample = None

        #kb = self.io.devices.keyboard
        pen = self.io.devices.pen

        self._positionGrid.randomize()

        pen.reporting = True
        for tp in self._positionGrid:
            self._targetStim.setPos(tp)
            self._targetStim.draw()
            targ_onset_time = self.win.flip()

            pen.clearEvents()

            val_sample_list = []

            while len(val_sample_list) < self.NUM_VALID_SAMPLES_PER_TARG:
                if core.getTime() - targ_onset_time > self.TARGET_TIMEOUT:
                    break
                self._targetStim.draw()

                samples = pen.getSamples()
                for s in samples:
                    spos = s.getPixPos(self.win)
                    if s.pressure > 0 and self.targetStim.contains(spos):
                        dx = math.fabs(tp[0] - spos[0])
                        dy = math.fabs(tp[1] - spos[1])
                        perr = math.sqrt(dx * dx + dy * dy)
                        val_sample_list.append((spos[0], spos[1], perr))
                    else:
                        val_sample_list = []

                if samples:
                    self._drawPenStim(samples[-1])
                    self._lastPenSample = samples[-1]
                elif self._lastPenSample:
                    self._drawPenStim(self._lastPenSample)
                self.win.flip()

            tp = int(tp[0]), int(tp[1])
            val_results['target_data'][tp] = None
            val_results['point_count'] = val_results['point_count'] + 1

            if val_sample_list:
                pos_acc_array = np.asarray(val_sample_list)
                serr_array = pos_acc_array[:, 2]

                targ_err_stats = val_results['target_data'][tp] = dict()
                targ_err_stats['samples'] = pos_acc_array
                targ_err_stats['count'] = len(val_sample_list)
                targ_err_stats['min'] = serr_array.min()
                targ_err_stats['max'] = serr_array.max()
                targ_err_stats['mean'] = serr_array.mean()
                targ_err_stats['median'] = np.median(serr_array)
                targ_err_stats['stdev'] = serr_array.std()

                val_results['min_err'] = min(
                    val_results['min_err'], targ_err_stats['min'])
                val_results['max_err'] = max(
                    val_results['max_err'], targ_err_stats['max'])

                val_results['avg_err'] = val_results[
                    'avg_err'] + targ_err_stats['mean']
                val_results['ok_point_count'] = val_results[
                    'ok_point_count'] + 1
            else:
                val_results['status'] = 'FAILED'

            self._lastPenSample = None

        if val_results['ok_point_count'] > 0:
            val_results['avg_err'] = val_results[
                'avg_err'] / val_results['ok_point_count']

        pen.reporting = False

        return val_results

    def _enterFinishedScreen(self, results):
        kb = self.io.devices.keyboard

        status = results['status']
        ok_point_count = results['ok_point_count']
        min_err = results['min_err']
        max_err = results['max_err']
        avg_err = results['avg_err']
        point_count = results['point_count']
        self._finsihedScreenGraphics['result_status'].setText(
            'Result: {}'.format(status))

        self._finsihedScreenGraphics['result_stats'].setText(
            '%d/%d '
            'Points Validated.'
            'Min, Max, Mean '
            'Errors: '
            '%.3f, %.3f, %.3f'
            '' %
            (ok_point_count, point_count, min_err, max_err, avg_err))
        for ig in self._finsihedScreenGraphics.values():
            ig.draw()
        self.win.flip()
        kb.clearEvents()

        while not kb.getPresses():
            for ig in self._finsihedScreenGraphics.values():
                ig.draw()
            self.win.flip()

    def _drawPenStim(self, s):
        if self._displayPenPosition:
            spos = s.getPixPos(self.win)
            if spos:
                self._penStim.setPos(spos)
                if s.pressure == 0:
                    self._penStim.setFillColor([255, 0, 0])
                    self._penStim.setLineColor([255, 0, 0])
                else:
                    self._penStim.setFillColor([0, 0, 255])
                    self._penStim.setLineColor([0, 0, 255])

                self._penStim.draw()

    def run(self):
        """Starts the validation process. This function will not return
        until the validation is complete. The validation results are
        returned in dict format.

        :return: dist containing validation results.

        """

        continue_val = self._enterIntroScreen()

        if continue_val is False:
            return None

        # delay about 0.5 sec before staring validation
        ftime = self.win.flip()
        while core.getTime() - ftime < 0.5:
            self.win.flip()
            self.io.clearEvents()

        val_results = self._enterValidationSequence()

        # delay about 0.5 sec before showing validation end screen
        ftime = self.win.flip()
        while core.getTime() - ftime < 0.5:
            self.win.flip()
            self.io.clearEvents()

        self._enterFinishedScreen(val_results)
        self.io.clearEvents()
        self.win.flip()

        return val_results

        # returning None indicates to experiment that the vaidation process
        # was terminated by the user
        # return None

    def free(self):
        self.win = None
        self.io = None
        self._finsihedScreenGraphics.clear()
        self._introScreenGraphics.clear()
        self._targetStim = None
        self._penStim = None

    def __del__(self):
        self.free()
