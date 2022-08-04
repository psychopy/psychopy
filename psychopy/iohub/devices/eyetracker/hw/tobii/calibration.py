# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy.iohub.devices.eyetracker.calibration import BaseCalibrationProcedure
from collections import OrderedDict
from psychopy import visual
from .....constants import EventConstants
import gevent


class TobiiCalibrationProcedure(BaseCalibrationProcedure):
    def __init__(self, eyetrackerInterface, calibration_args):
        self.feedback_resources = OrderedDict()
        self.tobii_calibration = None
        self.cal_result_dict = dict(status="Calibration Not Started")
        BaseCalibrationProcedure.__init__(self, eyetrackerInterface, calibration_args, allow_escape_in_progress=True)

    def createGraphics(self):
        """
        """
        BaseCalibrationProcedure.createGraphics(self)

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

    def showIntroScreen(self, text_msg='Press SPACE to Start Calibration; ESCAPE to Exit.'):
        self.clearAllEventBuffers()
        self._eyetracker.setRecordingState(True)

        while True:
            self.textLineStim.setText(text_msg)
            event_named_tuples = []
            for e in self._eyetracker.getEvents(EventConstants.BINOCULAR_EYE_SAMPLE):
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
                self._eyetracker.setRecordingState(False)
                self.clearAllEventBuffers()
                return True
            elif msg == 'QUIT':
                self._eyetracker.setRecordingState(False)
                self.clearAllEventBuffers()
                return False
            self.MsgPump()
            gevent.sleep()

    def startCalibrationHook(self):
        self.tobii_calibration = self._eyetracker._tobii.newScreenCalibration()
        self.tobii_calibration.enter_calibration_mode()

    def registerCalibrationPointHook(self, pt):
        self.tobii_calibration.collect_data(pt[0], pt[1])

    def finishCalibrationHook(self, aborted=False):
        cal_result_dict = dict(status="Calibration Aborted")
        if not aborted:
            calibration_result = self.tobii_calibration.compute_and_apply()
            cal_result_dict = dict(status=calibration_result.status)
            cal_result_dict['points'] = []
            for cp in calibration_result.calibration_points:
                csamples = []
                for cs in cp.calibration_samples:
                    csamples.append((cs.left_eye.position_on_display_area, cs.left_eye.validity))
                cal_result_dict['points'].append((cp.position_on_display_area, csamples))

        self.tobii_calibration.leave_calibration_mode()
        self.tobii_calibration = None
        self.cal_result_dict = cal_result_dict
