# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).


from psychopy import visual
import gevent
import numpy as np
from collections import OrderedDict
from .....util import convertCamelToSnake, updateSettings
from .... import DeviceEvent, Computer
from .....constants import EventConstants
from psychopy.iohub.devices.keyboard import KeyboardInputEvent

from .....errors import print2err, printExceptionDetailsToStdErr

currentTime = Computer.getTime


class TobiiPsychopyCalibrationGraphics:
    IOHUB_HEARTBEAT_INTERVAL = 0.050  # seconds between forced run through of micro threads, since one is blocking on camera setup.
    CALIBRATION_POINT_LIST = [(0.5, 0.5), (0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9), (0.5, 0.5)]

    TEXT_POS = [0, 0]
    TEXT_HEIGHT = 36
    _keyboard_key_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key')

    def __init__(self, eyetrackerInterface, calibration_args={}):
        self._eyetrackerinterface = eyetrackerInterface
        self._tobii = eyetrackerInterface._tobii
        self.screenSize = eyetrackerInterface._display_device.getPixelResolution()
        self.width = self.screenSize[0]
        self.height = self.screenSize[1]
        self._ioKeyboard = None
        self._msg_queue = []
        self._lastCalibrationOK = False
        display = self._eyetrackerinterface._display_device

        self._device_config = self._eyetrackerinterface.getConfiguration()
        updateSettings(self._device_config.get('calibration'), calibration_args)
        self._calibration_args = self._device_config.get('calibration')
        #print2err("self._calibration_args:", self._calibration_args)
        
        unit_type = self.getCalibSetting('unit_type')
        if unit_type is None:
            unit_type = display.getCoordinateType()
            self._calibration_args['unit_type'] = unit_type
        color_type = self.getCalibSetting('color_type')
        if color_type is None:
            color_type = display.getColorSpace()
            self._calibration_args['color_type'] = color_type

        calibration_methods = dict(THREE_POINTS=3,
                                   FIVE_POINTS=5,
                                   NINE_POINTS=9,
                                   THIRTEEN_POINTS=13)

        cal_type = self.getCalibSetting('type')

        if cal_type in calibration_methods:
            num_points = calibration_methods[cal_type]

            if num_points == 3:
                TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_LIST = [
                    (0.5, 0.1), (0.1, 0.9), (0.9, 0.9)]
            elif num_points == 5:
                TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_LIST = [(0.5, 0.5),
                                                                           (0.1, 0.1),
                                                                           (0.9, 0.1),
                                                                           (0.9, 0.9),
                                                                           (0.1, 0.9)]
            elif num_points == 9:
                TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_LIST = [(0.5, 0.5),
                                                                           (0.1,
                                                                            0.5),
                                                                           (0.9,
                                                                            0.5),
                                                                           (0.1,
                                                                            0.1),
                                                                           (0.5,
                                                                            0.1),
                                                                           (0.9,
                                                                            0.1),
                                                                           (0.9,
                                                                            0.9),
                                                                           (0.5,
                                                                            0.9),
                                                                           (0.1,
                                                                            0.9)]
            elif num_points == 13:
                TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_LIST = [(0.5, 0.5),
                                                                               (0.1, 0.5),
                                                                               (0.9, 0.5),
                                                                               (0.1, 0.1),
                                                                               (0.5, 0.1),
                                                                               (0.9, 0.1),
                                                                               (0.9, 0.9),
                                                                               (0.5, 0.9),
                                                                               (0.1, 0.9),
                                                                               (0.25, 0.25),
                                                                               (0.25, 0.75),
                                                                               (0.75, 0.75),
                                                                               (0.75, 0.25)
                                                                               ]

        self.window = visual.Window(
            self.screenSize,
            monitor=display.getPsychopyMonitorName(),
            units=unit_type,
            fullscr=True,
            allowGUI=False,
            screen=display.getIndex(),
            color=self.getCalibSetting(['screen_background_color']),
            colorSpace=color_type)
        self.window.flip(clearBuffer=True)

        self._createStim()
        self._registerEventMonitors()
        self._lastMsgPumpTime = currentTime()

        self.clearAllEventBuffers()

    def getCalibSetting(self, setting):
        if isinstance(setting, str):
            setting = [setting, ]
        calibration_args = self._calibration_args
        if setting:
            for s in setting[:-1]:
                calibration_args = calibration_args.get(s)
            return calibration_args.get(setting[-1])

    def clearAllEventBuffers(self):
        self._eyetrackerinterface._iohub_server.eventBuffer.clear()
        for d in self._eyetrackerinterface._iohub_server.devices:
            d.clearEvents()

    def _registerEventMonitors(self):
        kbDevice = None
        if self._eyetrackerinterface._iohub_server:
            for dev in self._eyetrackerinterface._iohub_server.devices:
                if dev.__class__.__name__ == 'Keyboard':
                    kbDevice = dev

        if kbDevice:
            eventIDs = []
            for event_class_name in kbDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(
                    getattr(
                        EventConstants,
                        convertCamelToSnake(
                            event_class_name[
                            :-5],
                            False)))

            self._ioKeyboard = kbDevice
            self._ioKeyboard._addEventListener(self, eventIDs)
        else:
            print2err(
                'Warning: Tobii Cal GFX could not connect to Keyboard device for events.')

    def _unregisterEventMonitors(self):
        if self._ioKeyboard:
            self._ioKeyboard._removeEventListener(self)

    def _handleEvent(self, event):
        event_type_index = DeviceEvent.EVENT_TYPE_ID_INDEX
        if event[event_type_index] == EventConstants.KEYBOARD_PRESS:
            ek = event[self._keyboard_key_index]
            if isinstance(ek, bytes):
                ek = ek.decode('utf-8')
            if ek == ' ' or ek == 'space':
                self._msg_queue.append('SPACE_KEY_ACTION')
                self.clearAllEventBuffers()
            elif ek == 'escape':
                self._msg_queue.append('QUIT')
                self.clearAllEventBuffers()

    def MsgPump(self):
        # keep the psychopy window happy ;)
        if currentTime() - self._lastMsgPumpTime > self.IOHUB_HEARTBEAT_INTERVAL:
            # try to keep ioHub from being blocked. ;(
            if self._eyetrackerinterface._iohub_server:
                for dm in self._eyetrackerinterface._iohub_server.deviceMonitors:
                    dm.device._poll()
                self._eyetrackerinterface._iohub_server.processDeviceEvents()
            self._lastMsgPumpTime = currentTime()

    def getNextMsg(self):
        if len(self._msg_queue) > 0:
            msg = self._msg_queue[0]
            self._msg_queue = self._msg_queue[1:]
            return msg

    def _createStim(self):
        """
            outer_diameter: 35
            outer_stroke_width: 5
            outer_fill_color: [255,255,255]
            outer_line_color: [255,255,255]
            inner_diameter: 5
            inner_stroke_width: 0
            inner_color: [0,0,0]
            inner_fill_color: [0,0,0]
            inner_line_color: [0,0,0]
            calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']
        """
        color_type = self.getCalibSetting('color_type')
        unit_type = self.getCalibSetting('unit_type')

        self.calibrationPoint = visual.TargetStim(
            self.window, name="CP", style="circles",
            radius=self.getCalibSetting(['target_attributes', 'outer_diameter']) / 2.0,
            fillColor=self.getCalibSetting(['target_attributes', 'outer_fill_color']),
            borderColor=self.getCalibSetting(['target_attributes', 'outer_line_color']),
            lineWidth=self.getCalibSetting(['target_attributes', 'outer_stroke_width']),
            innerRadius=self.getCalibSetting(['target_attributes', 'inner_diameter']) / 2.0,
            innerFillColor=self.getCalibSetting(['target_attributes', 'inner_fill_color']),
            innerBorderColor=self.getCalibSetting(['target_attributes', 'inner_line_color']),
            innerLineWidth=self.getCalibSetting(['target_attributes', 'inner_stroke_width']),
            pos=(0, 0),
            units=unit_type,
            colorSpace=color_type,
            autoLog=False
        )
        self.calibrationPointINNER = self.calibrationPoint.inner
        self.calibrationPointOUTER = self.calibrationPoint.outer

        tctype = color_type
        tcolor = self.getCalibSetting(['text_color'])
        if tcolor is None:
            # If no calibration text color provided, base it on the window background color
            from psychopy.iohub.util import complement
            sbcolor = self.getCalibSetting(['screen_background_color'])
            if sbcolor is None:
                sbcolor = self.window.color
            from psychopy.colors import Color
            tcolor_obj = Color(sbcolor, color_type)
            tcolor = complement(*tcolor_obj.rgb255)
            tctype = 'rgb255'

        instuction_text = 'Press SPACE to Start Calibration; ESCAPE to Exit.'
        self.textLineStim = visual.TextStim(self.window,
                                            text=instuction_text,
                                            pos=self.TEXT_POS,
                                            height=self.TEXT_HEIGHT,
                                            color=tcolor,
                                            colorSpace=tctype,
                                            units='pix',
                                            wrapWidth=self.width * 0.9)

        # create Tobii eye position feedback graphics
        #
        sw, sh = self.screenSize
        self.hbox_bar_length = hbox_bar_length = sw / 4
        hbox_bar_height = 6
        marker_diameter = 7
        self.marker_heights = (-sh / 2.0 * .7, -sh / 2.0 * .75, -sh /
                               2.0 * .8, -sh / 2.0 * .7, -sh / 2.0 * .75, -sh / 2.0 * .8)

        bar_vertices = ([-hbox_bar_length / 2, -hbox_bar_height / 2], [hbox_bar_length / 2, -hbox_bar_height / 2],
                        [hbox_bar_length / 2, hbox_bar_height / 2], [-hbox_bar_length / 2, hbox_bar_height / 2])

        self.feedback_resources = OrderedDict()

        self.feedback_resources['hbox_bar_x'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='Firebrick',
            vertices=bar_vertices,
            units='pix',
            pos=(
                0,
                self.marker_heights[0]))
        self.feedback_resources['hbox_bar_y'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='DarkSlateGray',
            vertices=bar_vertices,
            units='pix',
            pos=(
                0,
                self.marker_heights[1]))
        self.feedback_resources['hbox_bar_z'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='GoldenRod',
            vertices=bar_vertices,
            units='pix',
            pos=(
                0,
                self.marker_heights[2]))

        marker_vertices = [-marker_diameter, 0], [0, marker_diameter], [marker_diameter, 0], [0, -marker_diameter]
        self.feedback_resources['left_hbox_marker_x'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='Black',
            vertices=marker_vertices,
            units='pix',
            pos=(
                0,
                self.marker_heights[0]))
        self.feedback_resources['left_hbox_marker_y'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='Black',
            units='pix',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[1]))
        self.feedback_resources['left_hbox_marker_z'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='Black',
            units='pix',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[2]))
        self.feedback_resources['right_hbox_marker_x'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='DimGray',
            units='pix',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[0]))
        self.feedback_resources['right_hbox_marker_y'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='DimGray',
            units='pix',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[1]))
        self.feedback_resources['right_hbox_marker_z'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='DimGray',
            units='pix',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[2]))

    def runCalibration(self):
        """
        Performs a Tobii calibration routine.
        """

        self._lastCalibrationOK = False
        calibration_sequence_completed = False

        instuction_text = 'Press SPACE to Start Calibration; ESCAPE to Exit.'
        continue_calibration = self.showSystemSetupMessageScreen(instuction_text, True)
        if not continue_calibration:
            return False
        auto_pace = self.getCalibSetting('auto_pace')
        pacing_speed = self.getCalibSetting('pacing_speed')
        randomize_points = self.getCalibSetting('randomize')

        movement_velocity = self.getCalibSetting(['target_attributes', 'animate', 'movement_velocity'])
        expansion_speed = self.getCalibSetting(['target_attributes', 'animate', 'expansion_speed'])
        use_deprecated_gfx = movement_velocity or expansion_speed
        if not use_deprecated_gfx:
            # If using calibration option as of 2021.2, set pacing_speed
            # to match target_delay
            pacing_speed = self.getCalibSetting('target_delay')

        cal_target_list = self.CALIBRATION_POINT_LIST[1:]
        if randomize_points is True:
            import random
            random.seed(None)
            random.shuffle(cal_target_list)
        cal_target_list.insert(0, self.CALIBRATION_POINT_LIST[0])

        calibration = self._tobii.newScreenCalibration()
        calibration.enter_calibration_mode()

        i = 0
        _quit = False
        left, top, right, bottom = self._eyetrackerinterface._display_device.getCoordBounds()
        w, h = right - left, top - bottom
        for pt in cal_target_list:
            self.clearAllEventBuffers()
            x, y = left + w * pt[0], bottom + h * (1.0 - pt[1])
            if use_deprecated_gfx:
                self.drawCalibrationTargetDeprecated(i, (x, y))
            else:
                start_time = currentTime()

                # Target animate / delay
                animate_enable = self.getCalibSetting(['target_attributes', 'animate', 'enable'])
                animate_expansion_ratio = self.getCalibSetting(['target_attributes', 'animate', 'expansion_ratio'])
                animate_contract_only = self.getCalibSetting(['target_attributes', 'animate', 'contract_only'])
                target_delay = self.getCalibSetting(['target_delay'])
                target_duration = self.getCalibSetting(['target_duration'])
                while currentTime()-start_time <= target_delay:
                    if animate_enable and i > 0:
                        t = (currentTime()-start_time) / target_delay
                        v1 = cal_target_list[i-1]
                        v2 = pt
                        t = 60.0 * ((1.0 / 10.0) * t ** 5 - (1.0 / 4.0) * t ** 4 + (1.0 / 6.0) * t ** 3)
                        mx, my = ((1.0 - t) * v1[0] + t * v2[0], (1.0 - t) * v1[1] + t * v2[1])
                        moveTo = left + w * mx, bottom + h * (1.0 - my)
                        self.drawCalibrationTarget(moveTo, reset=False)
                    else:
                        self.drawCalibrationTarget((x, y), False)

                    self.getNextMsg()
                    self.MsgPump()

                self.drawCalibrationTarget((x, y))
                start_time = currentTime()

                outer_diameter = self.getCalibSetting(['target_attributes', 'outer_diameter'])
                inner_diameter = self.getCalibSetting(['target_attributes', 'inner_diameter'])
                while currentTime()-start_time <= target_duration:
                    elapsed_time = currentTime()-start_time
                    d = t = None
                    if animate_contract_only:
                        # Change target size from outer diameter to inner diameter over target_duration seconds.
                        t = elapsed_time / target_duration
                        d = outer_diameter - t * (outer_diameter - inner_diameter)
                        self.calibrationPoint.outerRadius = d / 2
                        self.calibrationPoint.draw()
                        self.window.flip(clearBuffer=True)
                    elif animate_expansion_ratio not in [1, 1.0]:
                        if elapsed_time <= target_duration/2:
                            # In expand phase
                            t = elapsed_time / (target_duration/2)
                            d = outer_diameter + t * (outer_diameter*animate_expansion_ratio - outer_diameter)
                        else:
                            # In contract phase
                            t = (elapsed_time-target_duration/2) / (target_duration/2)
                            d = outer_diameter*animate_expansion_ratio - t * (outer_diameter*animate_expansion_ratio - inner_diameter)
                    if d:
                        self.calibrationPoint.outerRadius = d / 2
                        self.calibrationPoint.draw()
                        self.window.flip(clearBuffer=True)

                    self.getNextMsg()
                    self.MsgPump()
                    gevent.sleep(0.001)

            self.clearAllEventBuffers()

            stime = currentTime()
            def waitingForNextTargetTime():
                return True

            if auto_pace is True:
                def waitingForNextTargetTime():
                    if use_deprecated_gfx:
                        return currentTime() - stime < float(pacing_speed)
                    return False

            _quit = False
            while waitingForNextTargetTime():
                msg = self.getNextMsg()
                if msg == 'SPACE_KEY_ACTION':
                    break
                elif msg == 'QUIT':
                    _quit = True
                    break
                self.MsgPump()
                gevent.sleep(0.01)

            calibration.collect_data(pt[0], pt[1])

            if _quit:
                calibration.leave_calibration_mode()
                calibration = None
                break

            self.clearCalibrationWindow()
            self.clearAllEventBuffers()

            i += 1
            if i == len(cal_target_list):
                calibration_sequence_completed = True

        self.clearCalibrationWindow()
        self.clearAllEventBuffers()

        cal_result_dict = None
        if _quit:
            return cal_result_dict

        self._lastCalibrationOK = False
        if calibration:
            if calibration_sequence_completed:
                calibration_result = calibration.compute_and_apply()
                cal_result_dict = dict(status=calibration_result.status)
                cal_result_dict['points']=[]
                for cp in calibration_result.calibration_points:
                    csamples = []
                    for cs in cp.calibration_samples:
                        csamples.append((cs.left_eye.position_on_display_area, cs.left_eye.validity))
                    cal_result_dict['points'].append((cp.position_on_display_area, csamples))
                self._lastCalibrationOK = calibration_result.status == 'calibration_status_success'
            else:
                self._lastCalibrationOK = False
            calibration.leave_calibration_mode()
            calibration = None

        if self._lastCalibrationOK is False:
            instuction_text = 'Calibration Failed. Options: SPACE: Re-run Calibration; ESCAPE: Exit Setup'
            continue_method = self.showSystemSetupMessageScreen(
                instuction_text, True, msg_types=['SPACE_KEY_ACTION', 'QUIT'])
            if continue_method is False:
                return self.runCalibration()
            return cal_result_dict

        instuction_text = "Calibration Passed. PRESS 'SPACE' KEY TO CONTINUE."
        self.showSystemSetupMessageScreen(instuction_text, True, msg_types=['SPACE_KEY_ACTION'])

        return cal_result_dict   

    def clearCalibrationWindow(self):
        self.window.flip(clearBuffer=True)

    def showSystemSetupMessageScreen(self, text_msg='Press SPACE to Start Calibration; ESCAPE to Exit.',
                                     enable_recording=False, msg_types=('SPACE_KEY_ACTION', 'QUIT')):
        if enable_recording is True:
            self._eyetrackerinterface.setRecordingState(True)

        self.clearAllEventBuffers()

        while True:
            self.textLineStim.setText(text_msg)
            event_named_tuples = []
            for e in self._eyetrackerinterface.getEvents(EventConstants.BINOCULAR_EYE_SAMPLE):
                event_named_tuples.append(
                    EventConstants.getClass(EventConstants.BINOCULAR_EYE_SAMPLE).createEventAsNamedTuple(e))
            leye_box_pos, reye_box_pos = self.getHeadBoxPosition(event_named_tuples)
            lx, ly, lz = leye_box_pos
            rx, ry, rz = reye_box_pos
            eye_positions = (lx, ly, lz, rx, ry, rz)
            marker_names = (
                'left_hbox_marker_x',
                'left_hbox_marker_y',
                'left_hbox_marker_z',
                'right_hbox_marker_x',
                'right_hbox_marker_y',
                'right_hbox_marker_z')
            marker_heights = self.marker_heights
            hbox_bar_length = self.hbox_bar_length

            for i, p in enumerate(eye_positions):
                if p is not None:
                    mpoint = hbox_bar_length * p - hbox_bar_length / 2.0, marker_heights[i]
                    self.feedback_resources[marker_names[i]].setPos(mpoint)
                    self.feedback_resources[marker_names[i]].setOpacity(1.0)
                else:
                    self.feedback_resources[marker_names[i]].setOpacity(0.0)

            self.textLineStim.draw()
            [r.draw() for r in self.feedback_resources.values()]
            self.window.flip()

            msg = self.getNextMsg()
            if msg == 'SPACE_KEY_ACTION':
                if enable_recording is True:
                    self._eyetrackerinterface.setRecordingState(False)
                self.clearAllEventBuffers()
                return True
            elif msg == 'QUIT':
                if enable_recording is True:
                    self._eyetrackerinterface.setRecordingState(False)
                self.clearAllEventBuffers()
                return False
            self.MsgPump()
            gevent.sleep()

    def getHeadBoxPosition(self, events):
        # KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key_id')
        left_eye_cam_x = None
        left_eye_cam_y = None
        left_eye_cam_z = None
        right_eye_cam_x = None
        right_eye_cam_y = None
        right_eye_cam_z = None

        if len(events) == 0:
            return (left_eye_cam_x, left_eye_cam_y, left_eye_cam_z), (right_eye_cam_x, right_eye_cam_y, right_eye_cam_z)

        event = events[-1]
        if abs(event.left_eye_cam_x) != 1.0 and abs(event.left_eye_cam_y) != 1.0:
            left_eye_cam_x = 1.0 - event.left_eye_cam_x
            left_eye_cam_y = event.left_eye_cam_y
        if event.left_eye_cam_z != 0.0:
            left_eye_cam_z = event.left_eye_cam_z
        if abs(event.right_eye_cam_x) != 1.0 and abs(event.right_eye_cam_y) != 1.0:
            right_eye_cam_x = 1.0 - event.right_eye_cam_x
            right_eye_cam_y = event.right_eye_cam_y
        if event.right_eye_cam_z != 0.0:
            right_eye_cam_z = event.right_eye_cam_z
        return (left_eye_cam_x, left_eye_cam_y, left_eye_cam_z), (right_eye_cam_x, right_eye_cam_y, right_eye_cam_z)

    def setTargetDefaults(self):
        """
            outer_diameter: 35
            outer_stroke_width: 5
            outer_fill_color: [255,255,255]
            outer_line_color: [255,255,255]
            inner_diameter: 5
            inner_stroke_width: 0
            inner_color: [0,0,0]
            inner_fill_color: [0,0,0]
            inner_line_color: [0,0,0]
        """
        self.calibrationPointOUTER.radius = self.getCalibSetting(['target_attributes', 'outer_diameter']) / 2.0
        self.calibrationPointOUTER.setLineColor(self.getCalibSetting(['target_attributes', 'outer_line_color']))
        self.calibrationPointOUTER.setFillColor(self.getCalibSetting(['target_attributes', 'outer_fill_color']))
        self.calibrationPointOUTER.lineWidth = int(self.getCalibSetting(['target_attributes', 'outer_stroke_width']))
        self.calibrationPointINNER.radius = self.getCalibSetting(['target_attributes', 'inner_diameter']) / 2.0
        self.calibrationPointINNER.setLineColor(self.getCalibSetting(['target_attributes', 'inner_line_color']))
        self.calibrationPointINNER.setFillColor(self.getCalibSetting(['target_attributes', 'inner_fill_color']))
        self.calibrationPointINNER.lineWidth = int(self.getCalibSetting(['target_attributes', 'inner_stroke_width']))

        self.calibrationPointOUTER.draw()
        self.calibrationPointINNER.draw()
        return self.window.flip(clearBuffer=True)

    def moveTarget(self, start_pt, end_pt, TARG_VELOCITY):
        sx, sy = start_pt
        ex, ey = end_pt
        dist = np.linalg.norm(end_pt - start_pt)
        sec_dur = dist / TARG_VELOCITY
        num_retraces = sec_dur / self._eyetrackerinterface._display_device.getRetraceInterval()
        x_points = np.linspace(sx, ex, num=int(num_retraces))
        y_points = np.linspace(sy, ey, num=int(num_retraces))
        t_points = zip(x_points, y_points)
        for p in t_points:
            self.calibrationPointOUTER.setPos(p)
            self.calibrationPointINNER.setPos(p)
            self.calibrationPointOUTER.draw()
            self.calibrationPointINNER.draw()
            self.window.flip(clearBuffer=True)
        self.setTargetDefaults()

    def expandTarget(self, TARG_RAD_MULTIPLIER, EXPANSION_RATE):
        orad = self.getCalibSetting(['target_attributes', 'outer_diameter']) / 2.0
        self.calibrationPointOUTER.lineWidth = int(self.getCalibSetting(['target_attributes', 'outer_stroke_width']))
        if self.calibrationPointOUTER.lineWidth < 1:
            self.calibrationPointOUTER.lineWidth = 1

        max_osize = orad * TARG_RAD_MULTIPLIER
        if EXPANSION_RATE < 1:
            EXPANSION_RATE = 1.0

        stime = Computer.getTime()
        self.calibrationPoint.outerRadius = orad
        self.calibrationPoint.draw()
        ftime = self.window.flip(clearBuffer=True)
        current_size = self.calibrationPoint.outerRadius
        while current_size < max_osize:
            sec_dur = ftime - stime
            if sec_dur < 0.0:
                sec_dur = 0.0
            stime = ftime
            current_size += sec_dur * EXPANSION_RATE
            self.calibrationPoint.outerRadius = current_size
            self.calibrationPoint.draw()
            ftime = self.window.flip(clearBuffer=True)

    def contractTarget(self, TARG_RAD_MULTIPLIER, EXPANSION_RATE):
        orad = self.getCalibSetting(['target_attributes', 'outer_diameter']) / 2.0
        self.calibrationPointOUTER.lineWidth = int(self.getCalibSetting(['target_attributes', 'outer_stroke_width']))
        if self.calibrationPointOUTER.lineWidth < 1:
            self.calibrationPointOUTER.lineWidth = 1

        max_osize = orad * TARG_RAD_MULTIPLIER
        if EXPANSION_RATE < 1:
            EXPANSION_RATE = 1.0

        stime = Computer.getTime()
        self.calibrationPoint.outerRadius = max_osize
        self.calibrationPoint.draw()
        ftime = self.window.flip(clearBuffer=True)
        current_size = max_osize
        while current_size > orad:
            sec_dur = ftime - stime
            if sec_dur < 0.0:
                sec_dur = 0.0
            stime = ftime
            current_size -= sec_dur * EXPANSION_RATE
            self.calibrationPoint.outerRadius = current_size
            self.calibrationPoint.draw()
            ftime = self.window.flip(clearBuffer=True)

    def drawCalibrationTargetDeprecated(self, target_number, tp):
        """
            outer_diameter: 35
            outer_stroke_width: 5
            outer_fill_color: [255,255,255]
            outer_line_color: [255,255,255]
            inner_diameter: 5
            inner_stroke_width: 0
            inner_color: [0,0,0]
            inner_fill_color: [0,0,0]
            inner_line_color: [0,0,0]
            calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']
        """
        try:
            animate_prefs = self.getCalibSetting(['target_attributes', 'animate'])

            if animate_prefs:
                CONTRACT_ONLY = animate_prefs.get('contract_only', False)
                TARG_VELOCITY = animate_prefs.get('movement_velocity', 300.0)  # 200 pix / sec
                TARG_RAD_MULTIPLIER = animate_prefs.get('expansion_ratio', 3.0)
                EXPANSION_RATE = animate_prefs.get('expansion_speed', 30.0)

                if target_number == 0:
                    # Do first point animation
                    self.calibrationPointOUTER.setPos(tp)
                    self.calibrationPointINNER.setPos(tp)
                    self.setTargetDefaults()
                    if CONTRACT_ONLY is False:
                        self.expandTarget(TARG_RAD_MULTIPLIER, EXPANSION_RATE)
                    self.contractTarget(TARG_RAD_MULTIPLIER, EXPANSION_RATE)
                else:
                    # Move from current point to new point
                    # then do point animation
                    spos = self.calibrationPointOUTER.pos
                    # self.calibrationPointOUTER.setPos(tp)
                    # self.calibrationPointINNER.setPos(tp)
                    if TARG_VELOCITY > 0.0:
                        self.moveTarget(spos, tp, TARG_VELOCITY)
                    else:
                        self.calibrationPointOUTER.setPos(tp)
                        self.calibrationPointINNER.setPos(tp)
                    self.setTargetDefaults()
                    if CONTRACT_ONLY is False:
                        self.expandTarget(TARG_RAD_MULTIPLIER, EXPANSION_RATE)
                    self.contractTarget(TARG_RAD_MULTIPLIER, EXPANSION_RATE)
            else:
                self.calibrationPointOUTER.setPos(tp)
                self.calibrationPointINNER.setPos(tp)
                self.setTargetDefaults()

        except Exception:
            printExceptionDetailsToStdErr()

    def drawDefaultTarget(self):
        self.calibrationPointOUTER.radius = self.getCalibSetting(['target_attributes', 'outer_diameter']) / 2.0
        self.calibrationPointOUTER.setLineColor(self.getCalibSetting(['target_attributes', 'outer_line_color']))
        self.calibrationPointOUTER.setFillColor(self.getCalibSetting(['target_attributes', 'outer_fill_color']))
        self.calibrationPointOUTER.lineWidth = int(self.getCalibSetting(['target_attributes', 'outer_stroke_width']))
        self.calibrationPointINNER.radius = self.getCalibSetting(['target_attributes', 'inner_diameter']) / 2.0
        self.calibrationPointINNER.setLineColor(self.getCalibSetting(['target_attributes', 'inner_line_color']))
        self.calibrationPointINNER.setFillColor(self.getCalibSetting(['target_attributes', 'inner_fill_color']))
        self.calibrationPointINNER.lineWidth = int(self.getCalibSetting(['target_attributes', 'inner_stroke_width']))

        self.calibrationPoint.draw()
        return self.window.flip(clearBuffer=True)

    def drawCalibrationTarget(self, tp, reset=True):
        self.calibrationPoint.pos = tp
        if reset:
            return self.drawDefaultTarget()
        else:
            self.calibrationPoint.draw()
            return self.window.flip(clearBuffer=True)
