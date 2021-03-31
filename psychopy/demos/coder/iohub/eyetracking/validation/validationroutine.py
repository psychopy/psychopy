# -*- coding: utf-8 -*-
"""
Eye Tracker Validation procedure using the ioHub common eye tracker interface.

To use the validation process from within a Coder script:
* Create an instance of TargetStim, specifying the fixation target appearance.
* Create an instance of PositionGrid, which defines target position information.
* Create a TargetPosSequenceStim instance, providing the TargetStim and
  PositionGrid objects created, as well as the Trigger's which should be used
  to transition from one target position to another during the sequence of
  target graphics presentation and the defined positions.
* Use TargetPosSequenceStim.display() to run the full presentation procedure.
* Use TargetPosSequenceStim.targetdata to access information about each target
  position displayed and the events collected during the display duration for
  each position.

See demos/coder/iohub/eyetracking/validation.py for a complete example.
"""
from weakref import proxy
import numpy as np
from time import sleep
import os
import sys
from PIL import Image
from collections import OrderedDict

from psychopy import visual, core
from psychopy.iohub.util import win32MessagePump, normjoin
from psychopy.iohub.constants import EventConstants
from psychopy.iohub.client import ioHubConnection
from psychopy.tools.monitorunittools import convertToPix
from psychopy.tools.monitorunittools import pix2deg, deg2pix

from posgrid import PositionGrid
from trigger import Trigger, KeyboardTrigger

getTime = core.getTime


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

class TargetPosSequenceStim(object):
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
    binocular_sample_message_element = [('targ_pos_ix', np.int),
                                        ('last_msg_time', np.float64),
                                        ('last_msg_type', np.str, max_msg_type_length),
                                        ('next_msg_time', np.float64),
                                        ('next_msg_type', np.str, max_msg_type_length),
                                        ('targ_pos_x', np.float64),
                                        ('targ_pos_y', np.float64),
                                        ('targ_state', np.int),
                                        ('eye_time', np.float64),
                                        ('eye_status', np.int),
                                        ('left_eye_x', np.float64),
                                        ('left_eye_y', np.float64),
                                        ('left_pupil_size', np.float64),
                                        ('right_eye_x', np.float64),
                                        ('right_eye_y', np.float64),
                                        ('right_pupil_size', np.float64)]
    monocular_sample_message_element = [('targ_pos_ix', np.int),
                                        ('last_msg_time', np.float64),
                                        ('last_msg_type', np.str, max_msg_type_length),
                                        ('next_msg_time', np.float64),
                                        ('next_msg_type', np.str, max_msg_type_length),
                                        ('targ_pos_x', np.float64),
                                        ('targ_pos_y', np.float64),
                                        ('targ_state', np.int),
                                        ('eye_time', np.float64),
                                        ('eye_status', np.int),
                                        ('eye_x', np.float64),
                                        ('eye_y', np.float64),
                                        ('pupil_size', np.float64)]

    def __init__(self, win, target, positions, background=None, storeeventsfor=[], triggers=None, msgcategory='',
                 config=None, io=None, terminate_key='escape', gaze_cursor_key='g'):
        """
        TargetPosSequenceStim combines an instance of a Target stim and an
        instance of a PositionGrid to create everything needed to present the
        target at each position returned by the PositionGrid instance within the
        psychopy window used to create the Target stim. The target is presented at
        each position sequentially.

        By providing keyword arguments to the TargetPosSequenceStim.display(...)
        method, position animation between target positions, and target stim
        expansion and / or contraction transitions are possible.

        psychopy.iohub.Trigger based classes are used to define the criteria used to
        start displaying the next target position graphics. By providing a list
        of a TimerTrigger and a set of DeviceEventTriggers, complex criteria
        for target position pacing can be easily defined for use during the display
        period.

        iohub devices can be provided in the storeeventsfor keyword argument.
        Events which occur during each target position presentation period are
        stored and are available at the end of the display() period, grouped by
        position index and device event types.

        :param win:
        :param target:
        :param positions:
        :param background:
        :param storeeventsfor:
        :param triggers:
        :param msgcategory:
        :param config:
        :param io:
        """
        self.terminate_key = terminate_key
        self.gaze_cursor_key = gaze_cursor_key
        self.display_gaze = False
        gc_size = deg2pix(3.0, win.monitor, correctFlat=False)
        self.gaze_cursor = visual.GratingStim(win, tex=None, mask='gauss', pos=(0, 0), size=(gc_size, gc_size),
                                              color='green', units='pix', opacity=0.8)
        self._terminate_requested = False
        self.win = proxy(win)
        self.target = target
        self.background = background
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



    def getIO(self):
        """
        Get the active ioHubConnection instance.
        """
        return self.io

    def _draw(self):
        """
        Fill the window with the specified background color and draw the
        target stim.
        """
        if self.background:
            self.background.draw()
        self.target.draw()
        if self.display_gaze:
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
        io = self.getIO()
        if frompos is not None:
            velocity = kwargs.get('velocity')
            if velocity:
                starttime = getTime()
                a, b = np.abs(topos - frompos) ** 2
                duration = np.sqrt(a + b) / velocity
                arrivetime = duration + starttime
                fliptime = starttime
                while fliptime < arrivetime:
                    mu = (fliptime - starttime) / duration
                    tpos = frompos * (1.0 - mu) + topos * mu
                    self.target.setPos(frompos * (1.0 - mu) + topos * mu)
                    self._draw()
                    fliptime = self.win.flip()
                    io.sendMessageEvent('POS_UPDATE %.4f,%.4f' % (tpos[0], tpos[1]), self.msgcategory,
                                        sec_time=fliptime)
                    self._addDeviceEvents()
                    if self._terminate_requested:
                        return 0

        self.target.setPos(topos)
        self._draw()
        fliptime = self.win.flip()
        io.sendMessageEvent('TARGET_POS %.4f,%.4f' % (topos[0], topos[1]), self.msgcategory, sec_time=fliptime)
        self._addDeviceEvents()

        expandedscale = kwargs.get('expandedscale')
        expansionduration = kwargs.get('expansionduration')
        contractionduration = kwargs.get('contractionduration')

        initialradius = self.target.radius
        if expandedscale:
            expandedradius = self.target.radius * expandedscale

            if expansionduration:
                starttime = fliptime
                expandedtime = fliptime + expansionduration
                while fliptime < expandedtime:
                    mu = (fliptime - starttime) / expansionduration
                    cradius = initialradius * (1.0 - mu) + expandedradius * mu
                    self.target.setRadius(cradius)
                    self._draw()
                    fliptime = self.win.flip()
                    io.sendMessageEvent('EXPAND_SIZE %.4f %.4f' % (cradius, initialradius), self.msgcategory,
                                        sec_time=fliptime)
                    self._addDeviceEvents()
                    if self._terminate_requested:
                        return 0
            if contractionduration:
                starttime = fliptime
                contractedtime = fliptime + contractionduration
                while fliptime < contractedtime:
                    mu = (fliptime - starttime) / contractionduration
                    cradius = expandedradius * (1.0 - mu) + initialradius * mu
                    self.target.setRadius(cradius)
                    self._draw()
                    fliptime = self.win.flip()
                    io.sendMessageEvent('CONTRACT_SIZE %.4f %.4f' % (cradius, initialradius), self.msgcategory,
                                        sec_time=fliptime)
                    self._addDeviceEvents()
                    if self._terminate_requested:
                        return 0

        self.target.setRadius(initialradius)
        return fliptime

    def moveTo(self, topos, frompos, **kwargs):
        """
        Indicates that the target should be moved frompos to topos.

        If a PositionGrid has been provided, moveTo should not be called
        directly. Instead, use the display() method to start the full
        target position presentation sequence.
        """
        io = self.getIO()
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
                break
        self._addDeviceEvents(trig.clearEventHistory(True))
        if triggered:
            # by default, assume it was a timer trigger,so use 255 as 'event type'
            event_type_id = 255
            trig_evt = triggered.getTriggeringEvent()
            if hasattr(trig_evt, 'type'):
                # actually it was a device event trigger
                event_type_id = trig_evt.type
            # get time trigger of trigger event
            event_time = triggered.getTriggeringTime()
            self.getIO().sendMessageEvent('NEXT_POS_TRIG %d %.3f' % (event_type_id, event_time), self.msgcategory)
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
        related to it is not preformed.

        velocity: The rate (units / second) at which the target should move
                  from a current target position to the next target position.
                  The value should be in the unit type the target stimulus
                  is using.

        expandedscale: When a target stimulus is at the current grid position,
                       the target graphic can expand to a size equal to the
                       original target radius * expandedscale.

        expansionduration: If expandedscale has been specified, this option is
                           used to set how long it should take for the target to
                           reach the full expanded target size. Time is in sec.

        contractionduration: If a target has been expanded, this option is used
                             to specify how many seconds it should take for the
                             target to contract back to the original target
                             radius.

        Note that target expansion and contraction change the target stimulus
        outer diameter only. The edge thickness and central dot radius do not
        change.

        All movement and size changes are linear in fashion.

        For example, to display a static target at each grid position::

        targetsequence.display()

        To have the target stim move between each grid position
        at 400 pixels / sec and not expand or contract::

        targetsequence.display(velocity=400.0)

        If the target should jump from one grid position to the next, and then
        expand to twice the radius over a 0.5 second period::

        targetsequence.display(
                                expandedscale=2.0,
                                expansionduration=0.50
                              )

        To do a similar animation as the pervious example, but also have the
        target contract back to it's original size over 0.75 seconds::

        targetsequence.display(
                                expandedscale=2.0,
                                expansionduration=0.50,
                                contractionduration=0.75
                              )

        When this method returns, the target has been displayed at all
        positions. Data collected for each position period can be accessed via
        the targetdata attribute.
        """
        del self.targetdata[:]
        prevpos = None

        io = self.getIO()
        io.clearEvents('all')
        io.sendMessageEvent('BEGIN_SEQUENCE {0}'.format(len(self.positions.positions)), self.msgcategory)
        turn_rec_off = []
        for d in self.storeevents:
            if not d.isReportingEvents():
                d.enableEventReporting(True)
                turn_rec_off.append(d)

        sleep(0.025)
        for pos in self.positions:
            self._initTargetData(prevpos, pos)
            self._addDeviceEvents()
            if self._terminate_requested:
                break
            self.moveTo(pos, prevpos, **kwargs)
            prevpos = pos
            self._addDeviceEvents()
            if self._terminate_requested:
                break

        for d in turn_rec_off:
            d.enableEventReporting(False)

        if self._terminate_requested:
            io.sendMessageEvent('VALIDATION TERMINATED BY USER', self.msgcategory)
            return False

        io.sendMessageEvent('DONE_SEQUENCE {0}'.format( len(self.positions.positions)), self.msgcategory)
        sleep(0.025)
        self._addDeviceEvents()
        io.clearEvents('all')
        return True

    def _processMessageEvents(self):
        self.target_pos_msgs = []
        self.saved_pos_samples = []
        for pd in self.targetdata:
            frompos = pd.get('frompos')
            topos = pd.get('topos')
            events = pd.get('events')

            # create a dict of device labels as keys, device events as value
            devlabel_events = {}
            for k, v in events.items():
                devlabel_events[k.getName()] = v

            samples = devlabel_events.get('tracker', [])
            # remove any eyetracker events that are not samples
            samples = [s for s in samples if s.type in (EventConstants.BINOCULAR_EYE_SAMPLE,
                                                        EventConstants.MONOCULAR_EYE_SAMPLE)]
            self.saved_pos_samples.append(samples)

            self.sample_type = self.saved_pos_samples[0][0].type
            if self.sample_type == EventConstants.BINOCULAR_EYE_SAMPLE:
                self.sample_msg_dtype = self.binocular_sample_message_element
            else:
                self.sample_msg_dtype = self.monocular_sample_message_element

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
            if self.sample_type == EventConstants.BINOCULAR_EYE_SAMPLE:
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
                    if sample.time >= last_msg_time and sample.time < current_msg[0]:
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


class ValidationProcedure(object):
    def __init__(self, win=None, target=None, positions=None, target_animation_params={}, randomize_positions=True,
                 background=None, triggers=None, storeeventsfor=None, accuracy_period_start=0.350,
                 accuracy_period_stop=.050, show_intro_screen=True, intro_text='Ready to Start Validation Procedure.',
                 show_results_screen=True, results_in_degrees=False, save_figure_path=None,
                 terminate_key="escape", toggle_gaze_cursor_key="g"):
        """
        ValidationProcedure can be used to check the accuracy of a calibrated
        eye tracking system.

        Once a ValidationProcedure class instance has been created, the display(**kwargs) method
        can be called to run the validation process.

        The validation process consists of the following stages:

        1) Display an Introduction / Instruction screen. A key press is used to
           start target presentation.
        2) The validation target presentation sequence. Based on the Target and
           PositionGrid objects provided when the ValidationProcedure was created,
           a series of target positions are displayed. The progression from one
           target position to the next is controlled by the triggers specified.
           The target can simply jump from one position to the next, or optional
           linear motion settings can be used to have the target move across the
           screen from one point to the next. The Target graphic itself can also
           be configured to expand or contract once it has reached a location
           defined in the position grid.
        3) During stage 2), data is collected from the devices being monitored by
           iohub. Specifically eye tracker samples and experiment messages are
           collected.
        4) The data collected during the validation target sequence is used to
           calculate accuracy information for each target position presented.
           The raw data as well as the computed accuracy data is available via the
           ValidationProcedure class. Calculated measures are provided seperately
           for each target position and include:

               a) An array of the samples used for the accuracy calculation. The
                  samples used are selected using the following criteria:
                       i) Only samples where the target was stationary and
                          not expanding or contracting are selected.

                       ii) Samples are selected that fall between:

                              start_time_filter = last_sample_time - accuracy_period_start

                           and

                              end_time_filter = last_sample_time - accuracy_period_end

                           Therefore, the duration of the selected sample period is:

                              selection_period_dur = end_time_filter - start_time_filter

                       iii) Sample that contain missing / invalid position data
                            are then removed, providing the final set of samples
                            used for accuracy calculations. The min, max, and mean
                            values from each set of selected samples is calculated.

               b) The x and y error of each samples gaze position relative to the
                  current target position. This data is in the same units as is
                  used by the Target instance. Computations are done for each eye
                  being recorded. The values are signed floats.

               c) The xy distance error from the from each eye's gaze position to
                  the target position. This is also calculated as an average of
                  both eyes when binocular data is available. The data is unsigned,
                  providing the absolute distance from gaze to target positions

        5) A 2D plot is created displaying each target position and the position of
           each sample used for the accuracy calculation. The minimum, maximum, and
           average error is displayed for all target positions. A key press is used
           to remove the validation results plot, and control is returned to the
           script that started the validation display. Note that the plot is also
           saved as a png file in the same directory as the calling stript.

        See the validation.py demo in demos.coder.iohub.eyetracker for example usage.

        :param win:
        :param target:
        :param positions:
        :param target_animation_params:
        :param randomize_positions:
        :param background:
        :param triggers:
        :param storeeventsfor:
        :param accuracy_period_start:
        :param accuracy_period_stop:
        :param show_intro_screen:
        :param intro_text:
        :param show_results_screen:
        :param results_in_degrees:
        :param save_figure_path:
        :param terminate_key:
        :param toggle_gaze_cursor_key:
        """
        self.terminate_key = terminate_key
        self.toggle_gaze_cursor_key = toggle_gaze_cursor_key

        self.io = ioHubConnection.getActiveConnection()

        if isinstance(positions, (list, tuple)):
            positions = PositionGrid(posList=positions, firstposindex=0, repeatFirstPos=False)
        self.positions = positions

        self.randomize_positions = randomize_positions
        if self.randomize_positions:
            self.positions.randomize()
        self.win = proxy(win)
        if target_animation_params is None:
            target_animation_params = {}
        self.animation_params = target_animation_params
        self.accuracy_period_start = accuracy_period_start
        self.accuracy_period_stop = accuracy_period_stop
        self.show_intro_screen = show_intro_screen
        self.intro_text = intro_text
        self.show_results_screen = show_results_screen
        self.results_in_degrees = results_in_degrees
        self.save_figure_path = save_figure_path
        self.validation_results = None
        if storeeventsfor is None:
            storeeventsfor = [self.io.devices.keyboard,
                              self.io.devices.mouse,
                              self.io.devices.tracker,
                              self.io.devices.experiment
                              ]

        if triggers is None:
            # Use space key press as default target trigger
            triggers = KeyboardTrigger(' ', on_press=True)
        triggers = Trigger.getTriggersFrom(triggers)

        # Create the TargetPosSequenceStim instance; used to control the sequential
        # presentation of the target at each of the grid positions.
        self.targetsequence = TargetPosSequenceStim(win, target=target, positions=self.positions, background=background,
                                                    triggers=triggers, storeeventsfor=storeeventsfor,
                                                    terminate_key=terminate_key, gaze_cursor_key=toggle_gaze_cursor_key)
        # Stim for results screen
        self.imagestim = None
        self.textstim = None
        self.use_dpi = 90

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
            if self.terminate_key and self.terminate_key in keyboard.waitForReleases(keys=[' ', self.terminate_key]):
                print("Escape key pressed. Exiting validation")
                self.validation_results = None
                return

        # Perform Validation.....
        terminate = not self.targetsequence.display(**self.animation_params)
        if terminate:
            print("Escape key pressed. Exiting validation")
            self.validation_results = None
            return

        self.io.clearEvents('all')

        self._createValidationResults()

        if self.show_results_screen:
            if self.showResultsScreen() is not None:
                if self.terminate_key and self.terminate_key in keyboard.waitForPresses(keys=[' ', self.terminate_key]):
                    print("Escape key pressed. Exiting validation")
                    self.validation_results = None
                    return
        return self.validation_results

    def showResultsScreen(self):
        self._buildResultScreen()
        if self.imagestim:
            self.imagestim.draw()
        self.textstim.draw()
        return self.win.flip()

    def showIntroScreen(self):
        text = self.intro_text + '\nPress SPACE to Start....'
        textpos = (0, 0)
        if self.textstim:
            self.textstim.setText(text)
            self.textstim.setPos(textpos)
        else:
            self.textstim = visual.TextStim(self.win, text=text, pos=textpos, height=30, color=(0, 0, 0),
                                            colorSpace='rgb255', opacity=1.0, contrast=1.0, units='pix',
                                            ori=0.0, antialias=True, bold=False, italic=False, anchorHoriz='center',
                                            anchorVert='center', wrapWidth=self.win.size[0] * .8)

        self.textstim.draw()
        return self.win.flip()

    def getValidationResults(self):
        return self.validation_results

    def _createValidationResults(self):
        """
        Create validation results dict and save validation analysis info as experiment messages to
        the iohub .hdf5 file.

        :return: dict
        """
        self.validation_results = None
        sample_array = self.targetsequence.getSampleMessageData()

        if self.results_in_degrees:
            for postdat in sample_array:
                postdat['targ_pos_x'], postdat['targ_pos_y'] = toDeg(self.win, *toPix(self.win, postdat['targ_pos_x'], postdat['targ_pos_y']))

                if self.targetsequence.sample_type == EventConstants.BINOCULAR_EYE_SAMPLE:
                    postdat['left_eye_x'], postdat['left_eye_y'] = toDeg(self.win, *toPix(self.win, postdat['left_eye_x'],
                                                                                postdat['left_eye_y']))

                    postdat['right_eye_x'], postdat['right_eye_y'] = toDeg(self.win, *toPix(self.win, postdat['right_eye_x'],
                                                                                  postdat['right_eye_y']))
                else:
                    postdat['eye_x'], postdat['eye_y'] = toDeg(self.win, *toPix(self.win, postdat['eye_x'], postdat['eye_y']))

        min_error = 100000.0
        max_error = 0.0
        summed_error = 0.0
        point_count = 0

        self.io.sendMessageEvent('Results', 'VALIDATION')
        results = dict(display_units=self.win.units, display_bounds=self.positions.bounds,
                       display_pix=self.win.size, position_count=len(sample_array),
                       target_positions=self.targetsequence.positions.getPositions())

        for k, v in results.items():
            self.io.sendMessageEvent('{}: {}'.format(k, v), 'VALIDATION')

        results['position_results'] = []
        results['positions_failed_processing'] = 0

        for pindex, samplesforpos in enumerate(sample_array):
            self.io.sendMessageEvent('Target Position Results: {0}'.format(pindex), 'VALIDATION')

            stationary_samples = samplesforpos[samplesforpos['targ_state'] == self.targetsequence.TARGET_STATIONARY]

            last_stime = stationary_samples[-1]['eye_time']
            first_stime = stationary_samples[0]['eye_time']

            filter_stime = last_stime - self.accuracy_period_start
            filter_etime = last_stime - self.accuracy_period_stop

            all_samples_for_accuracy_calc = stationary_samples[stationary_samples['eye_time'] >= filter_stime]
            all_samples_for_accuracy_calc = all_samples_for_accuracy_calc[all_samples_for_accuracy_calc['eye_time'] < filter_etime]

            good_samples_for_accuracy_calc = all_samples_for_accuracy_calc[all_samples_for_accuracy_calc['eye_status'] <= 1]

            all_samples_for_accuracy_count = all_samples_for_accuracy_calc.shape[0]
            good_accuracy_sample_count = good_samples_for_accuracy_calc.shape[0]
            accuracy_calc_good_sample_perc = good_accuracy_sample_count / float(all_samples_for_accuracy_count)

            # Ordered dictionary of the different levels of samples selected during filtering
            # for valid samples to use in accuracy calculations.
            sample_msg_data_filtering = OrderedDict(all_samples=samplesforpos,  # All samples from target period.
                                                    # Sample during stationary period at end of target
                                                    # presentation display.
                                                    stationary_samples=stationary_samples,
                                                    # Samples that occurred within the
                                                    # defined time selection period.
                                                    time_filtered_samples=all_samples_for_accuracy_calc,
                                                    # Samples from the selection period that
                                                    # do not have missing data
                                                    used_samples=good_samples_for_accuracy_calc)

            position_results = dict(pos_index=pindex,
                                    sample_time_range=[first_stime, last_stime],
                                    filter_samples_time_range=[filter_stime, filter_etime],
                                    valid_filtered_sample_perc=accuracy_calc_good_sample_perc)

            for k, v in position_results.items():
                self.io.sendMessageEvent('{}: {}'.format(k, v), 'VALIDATION')

            position_results['sample_from_filter_stages'] = sample_msg_data_filtering

            if accuracy_calc_good_sample_perc == 0.0:
                position_results['calculation_status'] = 'FAILED'
                results['positions_failed_processing'] += 1
            else:
                target_x = good_samples_for_accuracy_calc[:]['targ_pos_x']
                target_y = good_samples_for_accuracy_calc[:]['targ_pos_y']

                if self.targetsequence.sample_type == EventConstants.BINOCULAR_EYE_SAMPLE:
                    left_x = good_samples_for_accuracy_calc[:]['left_eye_x']
                    left_y = good_samples_for_accuracy_calc[:]['left_eye_y']
                    left_error_x = target_x - left_x
                    left_error_y = target_y - left_y
                    left_error_xy = np.hypot(left_error_x, left_error_y)

                    right_x = good_samples_for_accuracy_calc[:]['right_eye_x']
                    right_y = good_samples_for_accuracy_calc[:]['right_eye_y']
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
                    eye_x = good_samples_for_accuracy_calc[:]['eye_x']
                    eye_y = good_samples_for_accuracy_calc[:]['eye_y']
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

                position_results2 = dict()
                position_results2['calculation_status'] = 'PASSED'
                position_results2['target_position'] = (target_x[0], target_y[0])
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
            unit_type = 'degrees'
        mean_error = summed_error / point_count
        err_results = dict(reporting_unit_type=unit_type, min_error=min_error, max_error=max_error,
                           mean_error=mean_error)

        for k, v in err_results.items():
            self.io.sendMessageEvent('{}: {}'.format(k, v), 'VALIDATION')
            results[k] = v

        self.io.sendMessageEvent('Validation Report Complete', 'VALIDATION')

        self.validation_results = results
        return self.validation_results

    def createPlot(self):
        """
        Creates a matplotlib figure of validation results.
        :return:
        """
        from matplotlib import pyplot as pl

        results = self.getValidationResults()
        if results is None:
            raise RuntimeError("Validation must be run before creating results plot.")

        pixw, pixh = results['display_pix']

        pl.clf()
        fig = pl.gcf()
        fig.set_size_inches((pixw * .9) / self.use_dpi, (pixh * .8) / self.use_dpi)
        cm = pl.cm.get_cmap('RdYlBu')

        for position_results in results['position_results']:
            pindex = position_results['pos_index']
            if position_results['calculation_status'] == 'FAILED':
                # Draw nothing for failed position
                # TODO: Draw something. ;)
                pass
            else:
                samples = position_results['sample_from_filter_stages']['used_samples']
                time = samples[:]['eye_time']
                target_x = samples[:]['targ_pos_x']
                target_y = samples[:]['targ_pos_y']
                if self.targetsequence.sample_type == EventConstants.BINOCULAR_EYE_SAMPLE:
                    gaze_x = (samples[:]['left_eye_x'] + samples[:]['right_eye_x']) / 2.0
                    gaze_y = (samples[:]['left_eye_y'] + samples[:]['right_eye_y']) / 2.0
                else:
                    gaze_x = samples[:]['eye_x']
                    gaze_y = samples[:]['eye_y']

                normed_time = (time - time.min()) / (time.max() - time.min())
                pl.scatter(target_x[0], target_y[0], s=400, color=[0.75, 0.75, 0.75], alpha=0.5)
                pl.text(target_x[0], target_y[0], str(pindex), size=11, horizontalalignment='center',
                        verticalalignment='center')
                pl.scatter(gaze_x, gaze_y, s=40, c=normed_time, cmap=cm, alpha=0.75)

        if self.results_in_degrees:
            l, b = toDeg(self.win, (-pixw / 2,), (-pixh / 2, ))
            r, t = toDeg(self.win, (pixw / 2, ), (pixh / 2, ))
        else:
            l, t, r, b = results['display_bounds']

        pl.xlim(l, r)
        pl.ylim(b, t)
        pl.xlabel('Horizontal Position (%s)' % (results['reporting_unit_type']))
        pl.ylabel('Vertical Position (%s)' % (results['reporting_unit_type']))
        pl.title('Validation Accuracy (%s)\nMin: %.4f, Max: %.4f, Mean %.4f' % (results['reporting_unit_type'],
                                                                                results['min_error'],
                                                                                results['max_error'],
                                                                                results['mean_error']))

        # pl.colorbar()
        fig.tight_layout()
        return fig

    def _generateImageName(self):
        import datetime
        file_name = 'validation_' + datetime.datetime.now().strftime('%d_%m_%Y_%H_%M') + '.png'
        if self.save_figure_path:
            return normjoin(self.save_figure_path, file_name)
        rootScriptPath = os.path.dirname(sys.argv[0])
        return normjoin(rootScriptPath, file_name)

    def _buildResultScreen(self, replot=False):
        """
        Build validation results screen.
        Currently saves the plot from .createPlot() to disk and the loads that as an image.
        :param replot:
        :return:
        """
        if replot or self.imagestim is None:
            iname = self._generateImageName()
            self.createPlot().savefig(iname, dpi=self.use_dpi)

            text_pos = (0, 0)
            text = 'Accuracy Calculation not Possible do to Analysis Error. Press SPACE to continue.'

            if iname:
                fig_image = Image.open(iname)

                if self.imagestim:
                    self.imagestim.setImage(fig_image)
                else:
                    self.imagestim = visual.ImageStim(self.win, image=fig_image, units='pix', pos=(0.0, 0.0))

                text = 'Press SPACE to continue.'
                text_pos = (0.0, -(self.win.size[1] / 2.0) * .9)
            else:
                self.imagestim = None

            if self.textstim is None:
                self.textstim = visual.TextStim(self.win, text=text, pos=text_pos, color=(0, 0, 0), colorSpace='rgb255',
                                                opacity=1.0, contrast=1.0, units='pix', ori=0.0, height=None,
                                                antialias=True, bold=False, italic=False, anchorVert='center',
                                                anchorHoriz='center', wrapWidth=self.win.size[0] * .8)
            else:
                self.textstim.setText(text)
                self.textstim.setPos(text_pos)

        elif self.imagestim:
            return True
        return False

from psychopy.iohub.util.visualangle import VisualAngleCalc
