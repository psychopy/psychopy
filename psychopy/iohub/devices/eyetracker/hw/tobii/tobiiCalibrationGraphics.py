"""
ioHub Common Eye Tracker Interface for Tobii (C) Eye Tracking System.
Calibration graphics implemented using PsychoPy.
"""
# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy
from psychopy import visual
import gevent
import time
import copy
import numpy as np
from collections import OrderedDict
from .....util import convertCamelToSnake
from .... import DeviceEvent, Computer
from .....constants import EventConstants
from .....errors import print2err, printExceptionDetailsToStdErr
currentTime = Computer.getTime


class TobiiPsychopyCalibrationGraphics(object):
    IOHUB_HEARTBEAT_INTERVAL = 0.050   # seconds between forced run through of
    # micro threads, since one is blocking
    # on camera setup.
    WINDOW_BACKGROUND_COLOR = (128, 128, 128)
    CALIBRATION_POINT_LIST = [
        (0.5, 0.5), (0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9), (0.5, 0.5)]

    TEXT_POS = [0, 0]
    TEXT_COLOR = [0, 0, 0]
    TEXT_HEIGHT = 36
    _keyboard_key_index = EventConstants.getClass(
        EventConstants.KEYBOARD_RELEASE).CLASS_ATTRIBUTE_NAMES.index('key')

    def __init__(self, eyetrackerInterface, screenColor=None,
                 calibrationPointList=None):
        self._eyetrackerinterface = eyetrackerInterface
        # The EyeX interface has to fake the other API's calibration stuff
        self._tobii = eyetrackerInterface._tobii
        self.screenSize = eyetrackerInterface._display_device.getPixelResolution()

        self.width = self.screenSize[0]
        self.height = self.screenSize[1]
        self._ioKeyboard = None

        self._msg_queue = []
        self._lastCalibrationOK = False

        TobiiPsychopyCalibrationGraphics.WINDOW_BACKGROUND_COLOR = screenColor

        if calibrationPointList is not None:
            TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_LIST = calibrationPointList

        calibration_methods = dict(THREE_POINTS=3,
                                   FIVE_POINTS=5,
                                   NINE_POINTS=9,
                                   THIRTEEN_POINTS=13)

        cal_type = self._eyetrackerinterface.getConfiguration()['calibration'][
            'type']

        if cal_type in calibration_methods:
            num_points = calibration_methods[cal_type]

            if num_points == 3:
                TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_LIST = [
                    (0.5, 0.1), (0.1, 0.9), (0.9, 0.9), (0.5, 0.1)]
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
                                                                            0.9),
                                                                           (0.5, 0.5)]
        display = self._eyetrackerinterface._display_device
        self.window = visual.Window(
            self.screenSize,
            monitor=display.getPsychopyMonitorName(),
            units=display.getCoordinateType(),
            fullscr=True,
            allowGUI=False,
            screen=display.getIndex(),
            color=self.WINDOW_BACKGROUND_COLOR[
                0:3],
            colorSpace='rgb255')
        self.window.flip(clearBuffer=True)

        self._createStim()
        self._registerEventMonitors()
        self._lastMsgPumpTime = currentTime()

        self.clearAllEventBuffers()

    def clearAllEventBuffers(self):
        self._eyetrackerinterface._iohub_server.eventBuffer.clear()
        for d in self._eyetrackerinterface._iohub_server.devices:
            d.clearEvents()

    def _registerEventMonitors(self):
        if self._eyetrackerinterface._iohub_server:
            for dev in self._eyetrackerinterface._iohub_server.devices:
                #ioHub.print2err("dev: ",dev.__class__.__name__)
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
            if ek == ' ':
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
        if len(self._msg_queue)>0:
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
        coord_type = self._eyetrackerinterface._display_device.getCoordinateType()
        calibration_prefs = self._eyetrackerinterface.getConfiguration()['calibration'][
            'target_attributes']
        self.calibrationPointOUTER = visual.Circle(
            self.window,
            pos=(
                0,
                0),
            lineWidth=calibration_prefs['outer_stroke_width'],
            radius=calibration_prefs['outer_diameter'] / 2.0,
            name='CP_OUTER',
            fillColor=calibration_prefs['outer_fill_color'],
            lineColor=calibration_prefs['outer_line_color'],
            fillColorSpace='rgb255',
            lineColorSpace='rgb255',
            opacity=1.0,
            interpolate=False,
            edges=64,
            units=coord_type)

        self.calibrationPointINNER = visual.Circle(
            self.window,
            pos=(
                0,
                0),
            lineWidth=calibration_prefs['inner_stroke_width'],
            radius=calibration_prefs['inner_diameter'] / 2.0,
            name='CP_INNER',
            fillColor=calibration_prefs['inner_fill_color'],
            lineColor=calibration_prefs['inner_line_color'],
            fillColorSpace='rgb255',
            lineColorSpace='rgb255',
            opacity=1.0,
            interpolate=False,
            edges=64,
            units=coord_type)

        instuction_text = 'Press SPACE to Start Calibration; ESCAPE to Exit.'
        self.textLineStim = visual.TextStim(self.window,
                                            text=instuction_text,
                                            pos=self.TEXT_POS,
                                            height=self.TEXT_HEIGHT,
                                            color=self.TEXT_COLOR,
                                            colorSpace='rgb255',
                                            alignHoriz='center',
                                            alignVert='center',
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

        bar_vertices = [-hbox_bar_length / 2, -hbox_bar_height / 2], [hbox_bar_length / 2, -hbox_bar_height /
                                                                      2], [hbox_bar_length / 2, hbox_bar_height / 2], [-hbox_bar_length / 2, hbox_bar_height / 2]

        self.feedback_resources = OrderedDict()

        self.feedback_resources['hbox_bar_x'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='Firebrick',
            vertices=bar_vertices,
            pos=(
                0,
                self.marker_heights[0]))
        self.feedback_resources['hbox_bar_y'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='DarkSlateGray',
            vertices=bar_vertices,
            pos=(
                0,
                self.marker_heights[1]))
        self.feedback_resources['hbox_bar_z'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='GoldenRod',
            vertices=bar_vertices,
            pos=(
                0,
                self.marker_heights[2]))

        marker_vertices = [-marker_diameter, 0], [0,
                                                  marker_diameter], [marker_diameter, 0], [0, -marker_diameter]
        self.feedback_resources['left_hbox_marker_x'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='Black',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[0]))
        self.feedback_resources['left_hbox_marker_y'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='Black',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[1]))
        self.feedback_resources['left_hbox_marker_z'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='Black',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[2]))
        self.feedback_resources['right_hbox_marker_x'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='DimGray',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[0]))
        self.feedback_resources['right_hbox_marker_y'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='DimGray',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[1]))
        self.feedback_resources['right_hbox_marker_z'] = visual.ShapeStim(
            win=self.window,
            lineColor='White',
            fillColor='DimGray',
            vertices=marker_vertices,
            pos=(
                0,
                self.marker_heights[2]))

    def runCalibration(self):
        """Performs a simple Tobii - like (@2010) calibration routine.

        Args:
            None

        Result:
            bool: True if calibration was successful. False if not.

        """

        self._lastCalibrationOK = False
        calibration_sequence_completed = False

        instuction_text = 'Press SPACE to Start Calibration; ESCAPE to Exit.'
        continue_calibration = self.showSystemSetupMessageScreen(
            instuction_text, True)
        if not continue_calibration:
            return False

        auto_pace = self._eyetrackerinterface.getConfiguration()['calibration'][
            'auto_pace']
        pacing_speed = self._eyetrackerinterface.getConfiguration()['calibration'][
            'pacing_speed']
        randomize_points = self._eyetrackerinterface.getConfiguration()['calibration'][
            'randomize']

        cal_target_list = self.CALIBRATION_POINT_LIST[1:-1]
        if randomize_points is True:
            import random
            random.seed(None)
            random.shuffle(cal_target_list)

        cal_target_list.insert(0, self.CALIBRATION_POINT_LIST[0])
        cal_target_list.append(self.CALIBRATION_POINT_LIST[-1])

        calibration = self._tobii.newScreenCalibration()

        calibration.enter_calibration_mode()

        i = 0
        for pt in cal_target_list:
            self.clearAllEventBuffers()
            left, top, right, bottom = self._eyetrackerinterface._display_device.getCoordBounds()
            w, h = right - left, top - bottom
            x, y = left + w * pt[0], bottom + h * (1.0 - pt[1])
            self.drawCalibrationTarget(i, (x, y))
            self.clearAllEventBuffers()
            stime = currentTime()
            def waitingForNextTargetTime():
                return True

            if auto_pace is True:
                def waitingForNextTargetTime():
                    return currentTime() - stime < float(pacing_speed)

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

            # TODO: Switch to support per target status check available
            # in tobii_research.
            #if calibration.collect_data(pt[0], pt[1]) != self._tobii.CALIBRATION_STATUS_SUCCESS:
                # Try again if it didn't go well the first time.
                # Not all eye tracker models will fail at this point, but instead fail on ComputeAndApply.
            #    print2err("Calibration failed for target {}. Recollecting data.... TODO: Give visual feedback.")
            #    calibration.collect_data(pt[0], pt[1])

            self.clearCalibrationWindow()
            self.clearAllEventBuffers()

            i += 1
            if i == len(cal_target_list):
                calibration_sequence_completed = True

        self.clearCalibrationWindow()
        self.clearAllEventBuffers()

        if _quit:
            return False
        
        self._lastCalibrationOK = False
        if calibration:
            if calibration_sequence_completed:
                calibration_result = calibration.compute_and_apply()
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
            return False
        
        instuction_text = "Calibration Passed. PRESS 'SPACE' KEY TO CONTINUE."
        self.showSystemSetupMessageScreen(instuction_text, True, msg_types=['SPACE_KEY_ACTION'])
        return True
    
    def clearCalibrationWindow(self):
        self.window.flip(clearBuffer=True)

    def showSystemSetupMessageScreen(
        self,
        text_msg='Press SPACE to Start Calibration; ESCAPE to Exit.',
        enable_recording=False,
        msg_types=[
            'SPACE_KEY_ACTION',
            'QUIT']):
        if enable_recording is True:
            self._eyetrackerinterface.setRecordingState(True)

        self.clearAllEventBuffers()

        while True:
            self.textLineStim.setText(text_msg)
            event_named_tuples = []
            for e in self._eyetrackerinterface.getEvents(
                    EventConstants.BINOCULAR_EYE_SAMPLE):
                event_named_tuples.append(EventConstants.getClass(
                    EventConstants.BINOCULAR_EYE_SAMPLE).createEventAsNamedTuple(e))
            leye_box_pos, reye_box_pos = self.getHeadBoxPosition(
                event_named_tuples)
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
                    mpoint = hbox_bar_length * p - \
                        hbox_bar_length / 2.0, marker_heights[i]
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
            return (left_eye_cam_x, left_eye_cam_y,
                    left_eye_cam_z), (right_eye_cam_x, right_eye_cam_y, right_eye_cam_z)

        event = events[-1]
        if abs(
                event.left_eye_cam_x) != 1.0 and abs(
                event.left_eye_cam_y) != 1.0:
            left_eye_cam_x = 1.0 - event.left_eye_cam_x
            left_eye_cam_y = event.left_eye_cam_y
        if event.left_eye_cam_z != 0.0:
            left_eye_cam_z = event.left_eye_cam_z
        if abs(
                event.right_eye_cam_x) != 1.0 and abs(
                event.right_eye_cam_y) != 1.0:
            right_eye_cam_x = 1.0 - event.right_eye_cam_x
            right_eye_cam_y = event.right_eye_cam_y
        if event.right_eye_cam_z != 0.0:
            right_eye_cam_z = event.right_eye_cam_z
        return (left_eye_cam_x, left_eye_cam_y,
                left_eye_cam_z), (right_eye_cam_x, right_eye_cam_y, right_eye_cam_z)

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
            calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']
        """
        calibration_prefs = self._eyetrackerinterface.getConfiguration()['calibration'][
            'target_attributes']

        self.calibrationPointOUTER.radius = calibration_prefs[
            'outer_diameter'] / 2.0
        self.calibrationPointOUTER.setLineColor(
            calibration_prefs['outer_line_color'])
        self.calibrationPointOUTER.setFillColor(
            calibration_prefs['outer_fill_color'])
        self.calibrationPointOUTER.lineWidth = int(
            calibration_prefs['outer_stroke_width'])

        self.calibrationPointINNER.radius = calibration_prefs[
            'inner_diameter'] / 2.0
        self.calibrationPointINNER.setLineColor(
            calibration_prefs['inner_line_color'])
        self.calibrationPointINNER.setFillColor(
            calibration_prefs['inner_fill_color'])
        self.calibrationPointINNER.lineWidth = int(
            calibration_prefs['inner_stroke_width'])

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
        calibration_prefs = self._eyetrackerinterface.getConfiguration()['calibration'][
            'target_attributes']
        orad = calibration_prefs['outer_diameter'] / 2.0
        self.calibrationPointOUTER.lineWidth = int(
            calibration_prefs['outer_stroke_width'])
        if self.calibrationPointOUTER.lineWidth < 1:
            self.calibrationPointOUTER.lineWidth = 1

        max_osize = orad * TARG_RAD_MULTIPLIER
        if EXPANSION_RATE < 1:
            EXPANSION_RATE = 1.0

        stime = Computer.getTime()
        self.calibrationPointOUTER.radius = orad
        self.calibrationPointOUTER.draw()
        self.calibrationPointINNER.draw()
        ftime = self.window.flip(clearBuffer=True)
        current_size = self.calibrationPointOUTER.radius
        while current_size < max_osize:
            sec_dur = ftime - stime
            if sec_dur < 0.0:
                sec_dur = 0.0
            stime = ftime
            current_size += sec_dur * EXPANSION_RATE
            self.calibrationPointOUTER.radius = current_size
            self.calibrationPointOUTER.draw()
            self.calibrationPointINNER.draw()
            ftime = self.window.flip(clearBuffer=True)

    def contractTarget(self, TARG_RAD_MULTIPLIER, EXPANSION_RATE):
        calibration_prefs = self._eyetrackerinterface.getConfiguration()['calibration'][
            'target_attributes']
        orad = calibration_prefs['outer_diameter'] / 2.0
        self.calibrationPointOUTER.lineWidth = int(
            calibration_prefs['outer_stroke_width'])
        if self.calibrationPointOUTER.lineWidth < 1:
            self.calibrationPointOUTER.lineWidth = 1

        max_osize = orad * TARG_RAD_MULTIPLIER
        if EXPANSION_RATE < 1:
            EXPANSION_RATE = 1.0

        stime = Computer.getTime()
        self.calibrationPointOUTER.radius = max_osize
        self.calibrationPointOUTER.draw()
        self.calibrationPointINNER.draw()
        ftime = self.window.flip(clearBuffer=True)
        current_size = max_osize
        while current_size > orad:
            sec_dur = ftime - stime
            if sec_dur < 0.0:
                sec_dur = 0.0
            stime = ftime
            current_size -= sec_dur * EXPANSION_RATE
            self.calibrationPointOUTER.radius = current_size
            self.calibrationPointOUTER.draw()
            self.calibrationPointINNER.draw()
            ftime = self.window.flip(clearBuffer=True)

    def drawCalibrationTarget(self, target_number, tp):
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
            calibration_prefs = self._eyetrackerinterface.getConfiguration()['calibration'][
                'target_attributes']
            animate_prefs = calibration_prefs.get('animate', None)

            if animate_prefs:
                CONTRACT_ONLY = animate_prefs.get('contract_only', False)
                TARG_VELOCITY = animate_prefs.get(
                    'movement_velocity', 300.0)  # 200 pix / sec
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