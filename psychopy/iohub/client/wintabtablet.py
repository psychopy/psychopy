# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutionse
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division

from collections import deque, OrderedDict
import math
import numpy as np

from . import ioHubDeviceView, ioEvent, DeviceRPC
from ..devices import Computer
from ..devices.wintab import WintabTabletSampleEvent
from ..devices.wintab import WintabTabletEnterRegionEvent
from ..devices.wintab import WintabTabletLeaveRegionEvent
from ..constants import EventConstants

if Computer.system == 'win32':
    from win32api import LOWORD, HIWORD
    FRAC = LOWORD
    INT = HIWORD
else:
    FRAC = lambda x: x & 0x0000ffff
    INT = lambda x: x >> 16


def FIX_DOUBLE(x):
    return INT(x) + FRAC(x) / 65536.0

"""
TabletPen Device and Events Types

"""


class PenSampleEvent(ioEvent):
    """Represents a tablet pen position / pressure event."""
    STATES = dict()
    # A sample that is the first sample following a time gap in the sample
    # stream
    STATES[1] = 'FIRST_ENTER'
    # A sample that is the first sample with pressure == 0
    # following a sample with pressure > 0
    STATES[2] = 'FIRST_HOVER'
    # A sample that has pressure == 0, and previous sample also had pressure
    # == 0
    STATES[4] = 'HOVERING'
    # A sample that is the first sample with pressure > 0
    # following a sample with pressure == 0
    STATES[8] = 'FIRST_PRESS'
    #  A sample that has pressure > 0
    # following a sample with pressure > 0
    STATES[16] = 'PRESSED'

    _attrib_index = dict()
    _attrib_index[
        'x'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('x')
    _attrib_index[
        'y'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('y')
    _attrib_index[
        'z'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('z')
    _attrib_index[
        'buttons'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('buttons')
    _attrib_index['pressure'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index(
        'pressure')
    _attrib_index['altitude'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index(
        'orient_altitude')
    _attrib_index['azimuth'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index(
        'orient_azimuth')
    _attrib_index[
        'status'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('status')

    def __init__(self, ioe_array, device):
        super(PenSampleEvent, self).__init__(ioe_array, device)
        for efname, efvalue in PenSampleEvent._attrib_index.items():
            if efvalue >= 0:
                setattr(self, '_' + efname, ioe_array[efvalue])
        self._velocity = 0.0
        self._accelleration = 0.0

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def getPixPos(self, win):
        sw, sh = win.winHandle.width, win.winHandle.height
        nx, ny = self._x / \
            self.device.axis['x']['range'], self._y / \
            self.device.axis['y']['range']
        return int(nx * sw - sw / 2), int(ny * sh - sh / 2)

    def getNormPos(self):
        return (-1.0 + (self._x / self.device.axis['x']['range']) * 2.0,
                -1.0 + (self._y / self.device.axis['y']['range']) * 2.0)

    @property
    def z(self):
        return self._z

    @property
    def pressure(self):
        return self._pressure

    @property
    def altitude(self):
        return self._altitude

    @property
    def azimuth(self):
        return self._azimuth

    @property
    def buttons(self):
        return self._buttons

    @property
    def status(self):
        return [v for k, v in self.STATES.items() if self._status & k == k]

    @property
    def tilt(self):
        """Get the pen horizontal & vertical tilt for the sample.

        horizontal tilt (azimuth) is in radians,
        vertical tilt (altitude) is in ????.

        Note: wintab.h defines .orAltitude as a UINT but documents .orAltitude
        as positive for upward angles and negative for downward angles.
        WACOM uses negative altitude values to show that the pen is inverted;
        therefore we cast .orAltitude as an (int) and then use the absolute
        value.

        """
        axis = self.device.axis
        if axis['orient_altitude']['supported'] and axis[
                'orient_azimuth']['supported']:
            tilt1 = axis['orient_altitude']['adjust'] - \
                abs(self.altitude) / axis['orient_altitude']['factor']
            # below line would normalize the altitude to approx. between 0 and 1.0
            #
            #tilt1 = (1.0 -(self.altitude/axis['orient_altitude']['axMax']))

            #/* adjust azimuth */
            tilt2 = float(self.azimuth / axis['orient_azimuth']['factor'])

            return tilt1, tilt2
        return 0, 0

    @property
    def velocity(self):
        """Returns the calculated x, y, and xy velocity for the current sample.

        :return: (float, float, float)

        """
        return self._velocity

    @property
    def accelleration(self):
        """Returns the calculated x, y, and xy accelleration for the current
        sample.

        :return: (float, float, float)

        """
        return self._accelleration

    @velocity.setter
    def velocity(self, v):
        """Returns the calculated x, y, and xy velocity for the current sample.

        :return: (float, float, float)

        """
        self._velocity = v

    @accelleration.setter
    def accelleration(self, a):
        """Returns the calculated x, y, and xy accelleration for the current
        sample.

        :return: (float, float, float)

        """
        self._accelleration = a

    def __str__(self):
        return '{}, x,y,z: {}, {}, {} pressure: {}, tilt: {}'.format(
            ioEvent.__str__(self), self.x, self.y, self.z, self.tilt)


class PenEnterRegionEvent(ioEvent):
    """Occurs when Stylus enters the tablet region."""

    def __init__(self, ioe_array, device):
        super(PenEnterRegionEvent, self).__init__(ioe_array, device)


class PenLeaveRegionEvent(ioEvent):
    """Occurs when Stylus leaves the tablet region."""

    def __init__(self, ioe_array, device):
        super(PenLeaveRegionEvent, self).__init__(ioe_array, device)


class WintabTablet(ioHubDeviceView):
    """The WintabTablet device provides access to PenSampleEvent events."""
    SAMPLE = EventConstants.WINTAB_TABLET_SAMPLE
    ENTER = EventConstants.WINTAB_TABLET_ENTER_REGION
    LEAVE = EventConstants.WINTAB_TABLET_LEAVE_REGION
    _type2class = {SAMPLE: PenSampleEvent, ENTER: PenEnterRegionEvent,
                   LEAVE: PenLeaveRegionEvent}
    # TODO: name and class args should just be auto generated in init.

    def __init__(self, ioclient, device_class_name, device_config):
        super(WintabTablet, self).__init__(ioclient, device_class_name,
                                           device_config)

        self._prev_sample = None

        self._events = dict()
        self._reporting = False
        self._device_config = device_config
        self._event_buffer_length = self._device_config.get(
            'event_buffer_length')
        self._clearEventsRPC = DeviceRPC(
            self.hubClient._sendToHubServer,
            self.device_class,
            'clearEvents')
        self._context = {'Context': {'status': 'Device not Initialized'}}
        self._axis = {'Axis': {'status': 'Device not Initialized'}}
        self._hw_model = {'ModelInfo': {'status': 'Device not Initialized'}}

        if self.getInterfaceStatus() == 'HW_OK':
            wthw = self.getHardwareConfig()
            self._context = wthw['Context']
            self._axis = wthw['Axis']
            self._hw_model = wthw['ModelInfo']

            # Add extra axis info
            for axis in self._axis.values():
                axis['range'] = axis['max'] - axis['min']
                axis['supported'] = axis['range'] != 0

            # Add tilt related calc constants to orient_azimuth
            # and orient_altitude axis
            #
            if self._axis['orient_azimuth']['supported'] and self._axis[
                    'orient_altitude']['supported']:
                azimuth_axis = self._axis['orient_azimuth']
                azimuth_axis['factor'] = FIX_DOUBLE(
                    azimuth_axis['resolution']) / (2 * math.pi)

                altitude_axis = self._axis['orient_altitude']
                # convert altitude resolution to double
                altitude_axis['factor'] = FIX_DOUBLE(
                    altitude_axis['resolution'])
                # adjust for maximum value at vertical */
                altitude_axis['adjust'] = altitude_axis[
                    'max'] / altitude_axis['factor']

    def _calculateVelAccel(self, s):
        curr_samp = self._type2class[self.SAMPLE](s, self)
        if 'FIRST_ENTER' in curr_samp.status:
            self._prev_sample = None
        prev_samp = self._prev_sample
        if prev_samp:
            try:
                dx = curr_samp.x - prev_samp.x
                dy = curr_samp.y - prev_samp.y
                dt = (curr_samp.time - prev_samp.time)
                if dt <= 0:
                    print(
                        'Warning: dt == 0: {}, {}, {}'.format(
                            dt, curr_samp.time, prev_samp.time))
                    curr_samp.velocity = (0, 0, 0)
                    curr_samp.accelleration = (0, 0, 0)
                else:
                    cvx, cvy, cvxy = curr_samp.velocity = dx / \
                        dt, dy / dt, np.sqrt(dx * dx + dy * dy) / dt

                    pvx, pvy, pvxy = prev_samp.velocity
                    if prev_samp.velocity != (0, 0, 0):
                        curr_samp.accelleration = (cvx - pvx) / dt, (cvy - pvy) / dt, np.sqrt(
                            (cvx - pvx) * (cvx - pvx) + (cvy - pvy) * (cvy - pvy)) / dt
                    else:
                        curr_samp.accelleration = (0, 0, 0)
            except ZeroDivisionError as e:
                print(
                    'ERROR: wintab._calculateVelAccel ZeroDivisionError occurred. prevId: %d, currentId: %d' %
                    (curr_samp.id, prev_samp.id))
                curr_samp.velocity = (0, 0, 0)
                curr_samp.accelleration = (0, 0, 0)
            except Exception as e:
                print(
                    'ERROR: wintab._calculateVelAccel error [%s] occurred. prevId: %d, currentId: %d' %
                    (str(e), curr_samp.id, prev_samp.id))
                curr_samp.velocity = (0, 0, 0)
                curr_samp.accelleration = (0, 0, 0)
        else:
            curr_samp.velocity = (0, 0, 0)
            curr_samp.accelleration = (0, 0, 0)
        self._prev_sample = curr_samp
        return curr_samp

    def _syncDeviceState(self):
        """An optimized iohub server request that receives all device state and
        event information in one response.

        :return: None

        """
        kb_state = self.getCurrentDeviceState()
        self._reporting = kb_state.get('reporting_events')

        for etype, event_arrays in kb_state.get('events').items():
            et_queue = self._events.setdefault(
                etype, deque(maxlen=self._event_buffer_length))

            if etype == self.SAMPLE:
                for s in event_arrays:
                    et_queue.append(self._calculateVelAccel(s))
            else:
                et_queue.extend([self._type2class[etype](e, self)
                                 for e in event_arrays])

    @property
    def reporting(self):
        """Specifies if the the keyboard device is reporting / recording
        events.

          * True:  keyboard events are being reported.
          * False: keyboard events are not being reported.

        By default, the Keyboard starts reporting events automatically when the
        ioHub process is started and continues to do so until the process is
        stopped.

        This property can be used to read or set the device reporting state::

          # Read the reporting state of the keyboard.
          is_reporting_keyboard_event = keyboard.reporting

          # Stop the keyboard from reporting any new events.
          keyboard.reporting = False

        """
        return self._reporting

    @reporting.setter
    def reporting(self, r):
        """Sets the state of keyboard event reporting / recording."""
        if r is True:
            self._prev_sample = None
        self._reporting = self.enableEventReporting(r)
        return self._reporting

    @property
    def axis(self):
        return self._axis

    @property
    def context(self):
        return self._context

    @property
    def model(self):
        return self._hw_model

    def clearEvents(self, event_type=None, filter_id=None):
        result = self._clearEventsRPC(
            event_type=event_type, filter_id=filter_id)
        for etype, elist in self._events.items():
            if event_type is None or event_type == etype:
                elist.clear()
        return result

    def getSamples(self, clear=True):
        """
        Return a list of any Tablet sample events that have
        occurred since the last time either:

        * this method was called with the kwarg clear=True (default)
        * the tablet.clear() method was called.
        """
        self._syncDeviceState()
        return_events = [e for e in self._events.get(self.SAMPLE, [])]

        if return_events and clear is True:
            self._events.get(self.SAMPLE).clear()

        return sorted(return_events, key=lambda x: x.time)

    def getEnters(self, clear=True):
        """"""
        self._syncDeviceState()
        return_events = [e for e in self._events.get(self.ENTER, [])]

        if return_events and clear is True:
            self._events.get(self.ENTER).clear()

        return sorted(return_events, key=lambda x: x.time)

    def getLeaves(self, clear=True):
        """"""
        self._syncDeviceState()
        return_events = [e for e in self._events.get(self.LEAVE, [])]

        if return_events and clear is True:
            self._events.get(self.LEAVE).clear()

        return sorted(return_events, key=lambda x: x.time)

#
# iohub wintab util objects / functions for stylus,
# position traces, and validation process psychopy graphics.
#
try:
    from psychopy import visual, core
    from psychopy.visual.basevisual import MinimalStim

    class PenPositionStim(MinimalStim):
        """Draws the current pen x,y position with graphics that represent the
        pressure, z axis, and tilt data for the wintab sample used."""

        def __init__(self, win, name=None, autoLog=None, depth=-10000):
            self.win = win
            self.depth = depth
            super(PenPositionStim, self).__init__(name, autoLog)

            # Pen Hovering Related

            # opaticy is changed based on pen's z axis value, if z axis data
            # is available.
            # Opacity of min_opacity is used when pen is at the furthest hover
            # distance (z value) supported by the device.
            # Opacity of 1.0 is used when z value == 0, meaning pen is
            # touching digitizer surface.
            self.min_opacity = 0.0
            # If z axis is supported, hover_color specifies the color of the pen
            # position dot when z val > 0.
            self.hover_color = 'red'

            # Pen Pressure Related

            # Smallest radius (in norm units) that the pen position gaussian blob
            # will have, which occurs when pen pressure value is 0
            self.min_size = 0.033
            # As pen pressure value increases, so does position gaussian blob
            # radius (in norm units). Max radius is reached when pressure is
            # at max device pressure value, and is equal to min_size+size_range
            self.size_range = 0.1666
            # Color of pen position blob when pressure > 0.
            self.touching_color = 'green'

            # Pen tilt Related

            # Color of line graphic used to represent the pens tilt relative to the
            # digitizer surface.
            self.tiltline_color = (1, 1, 0)

            # Create a Gausian blob stim to use for pen position graphic
            self.pen_guass = visual.PatchStim(
                win,
                units='norm',
                tex='none',
                mask='gauss',
                pos=(
                    0,
                    0),
                size=(
                    self.min_size,
                    self.min_size),
                color=self.hover_color,
                autoLog=False,
                opacity=0.0)

            # Create a line stim to use for pen position graphic
            self.pen_tilt_line = visual.Line(win, units='norm', start=[0, 0],
                                             end=[0.5, 0.5],
                                             lineColor=self.tiltline_color,
                                             opacity=0.0)

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
                self.pen_guass.size = self.min_size + \
                    (evt.pressure / evt.device.axis['pressure']['range']) * \
                    self.size_range

            # set the position of the gauss blob to be the pen x,y value converted
            # to norm screen coords.
            self.pen_guass.pos = evt.getNormPos()

            # if supported, update all graphics opacity based on the samples z value
            # otherwise opacity is always 1.0
            if evt.device.axis['z']['supported']:
                z = evt.device.axis['z']['range'] - evt.z
                sopacity = self.min_opacity + \
                    (z / evt.device.axis['z']['range']) * \
                    (1.0 - self.min_opacity)
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

            self.pen_tilt_line.end = self.pen_guass.pos[0] + pen_tilt_xy[0],\
                self.pen_guass.pos[1] + pen_tilt_xy[1]

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

        def __init__(
                self,
                win,
                maxlen=256,
                name=None,
                autoLog=None,
                depth=-1000):
            self.depth = depth
            self.win = win
            super(PenTracesStim, self).__init__(name, autoLog)
            # A single pen trace can have at most max_trace_len points.
            self.max_trace_len = maxlen
            # The list of ShapeStim representing pen traces
            self.pentracestim = []
            # The ShapeStim state new / upcoming position points will be added
            # to.
            self.current_pentrace = None
            # A list representation of the current_pentrace.vertices
            self.current_points = []
            # The last pen position added to a pen trace.
            self.last_pos = [0, 0]

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
            self.current_pentrace = visual.ShapeStim(
                self.win,
                units='pix',
                lineWidth=2,
                lineColor=(-1, -1, -1),
                lineColorSpace='rgb',
                vertices=self.current_points,
                closeShape=False,
                pos=(0, 0),
                size=1,
                ori=0.0,
                opacity=1.0,
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
                # TODO: This is inefficient, look into a better way to add
                # points to a psychopy shape stim
                self.current_points.append(pos)
                self.current_pentrace.vertices = self.current_points

        def clear(self):
            """Remove all ShapStim being used. Next time this stim is drawn, no
            pen traces will exist.

            :return:

            """
            self.end()
            # for pts in self.pentracestim:
            #    pts.vertices = [(0,0)]
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

        def __init__(
                self,
                win,
                io,
                target_stim=None,
                pos_grid=None,
                display_pen_pos=True,
                force_quit=True,
                intro_title=None,
                intro_text1=None,
                intro_text2=None,
                intro_target_pos=None):
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

            from ..util.targetpositionsequence import TargetStim, PositionGrid

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
            if isinstance(intro_title, basestring):
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

            if isinstance(intro_text1, basestring):
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
            if isinstance(intro_text2, basestring):
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
                                              lineColorSpace='rgb255',
                                              fillColorSpace='rgb255',
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
                    return False

            pen.reporting = False
            return True

        def _enterValidationSequence(self):
            val_results = dict(target_data=dict(), avg_err=0, min_err=1000,
                               max_err=-1000, status='PASSED', point_count=0,
                               ok_point_count=0)

            self._lastPenSample = None

            kb = self.io.devices.keyboard
            pen = self.io.devices.tablet

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
except ImportError:
    # psychopy not available, skip defining PsychoPy stim stuff
    pass
