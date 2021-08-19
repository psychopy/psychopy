# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from psychopy.iohub.constants import EventConstants, EyeTrackerConstants
from psychopy.iohub.devices import Computer, Device

from psychopy.iohub.devices.eyetracker.hw.pupil_labs.pupil_core.constants import EYE_ID_LEFT, EYE_ID_RIGHT


def gaze_position_from_gaze_3d(gaze_datum):

    gaze_x, gaze_y, _ = gaze_datum['gaze_point_3d']

    return gaze_x, gaze_y


def eye_sample_from_gaze_3d(surface_datum, gaze_datum, metadata):
    pupil_datum_right, pupil_datum_left = None, None

    for p in gaze_datum['base_data']:
        if p['id'] == EYE_ID_RIGHT:
            pupil_datum_right = p
        if p['id'] == EYE_ID_LEFT:
            pupil_datum_left = p

    if pupil_datum_right and pupil_datum_left:
        return _binocular_eye_sample_from_gaze_3d(
            surface_datum=surface_datum,
            gaze_datum=gaze_datum,
            pupil_datum_right=pupil_datum_right,
            pupil_datum_left=pupil_datum_left,
            metadata=metadata
        )
    elif pupil_datum_right:
        return _monocular_eye_sample_from_gaze_3d(
            surface_datum=surface_datum,
            gaze_datum=gaze_datum,
            pupil_datum=pupil_datum_right,
            metadata=metadata
        )
    elif pupil_datum_left:
        return _monocular_eye_sample_from_gaze_3d(
            surface_datum=surface_datum,
            gaze_datum=gaze_datum,
            pupil_datum=pupil_datum_left,
            metadata=metadata
        )
    else:
        # This should never happen
        return None


def _binocular_eye_sample_from_gaze_3d(surface_datum, gaze_datum, pupil_datum_right, pupil_datum_left, metadata):

    gaze_x, gaze_y, gaze_z = surface_datum['norm_pos'][0], surface_datum['norm_pos'][1], 0

    right_eye_cam_x, right_eye_cam_y, right_eye_cam_z = pupil_datum_right['sphere']['center']
    left_eye_cam_x, left_eye_cam_y, left_eye_cam_z = pupil_datum_left['sphere']['center']

    right_angle_x, right_angle_y = pupil_datum_right['phi'], pupil_datum_right['theta']
    left_angle_x, left_angle_y = pupil_datum_left['phi'], pupil_datum_left['theta']

    right_raw_x, right_raw_y = pupil_datum_right['norm_pos']
    left_raw_x, left_raw_y = pupil_datum_left['norm_pos']

    pupil_measure1_type = EyeTrackerConstants.PUPIL_MAJOR_AXIS  # diameter 2d
    right_pupil_measure1 = pupil_datum_right['diameter']
    left_pupil_measure1 = pupil_datum_left['diameter']

    pupil_measure2_type = EyeTrackerConstants.PUPIL_DIAMETER_MM  # diameter 3d
    right_pupil_measure2 = pupil_datum_right.get('diameter_3d', None)
    left_pupil_measure2 = pupil_datum_left.get('diameter_3d', None)

    status = f"{pupil_datum_right['method']} --- {pupil_datum_left['method']}"

    return [  # BinocularEyeSampleEvent
        metadata['experiment_id'],
        metadata['session_id'],
        metadata['device_id'],
        metadata['event_id'],
        EventConstants.BINOCULAR_EYE_SAMPLE,  # type
        metadata['device_time'],
        metadata['logged_time'],
        metadata['time'],
        metadata['confidence_interval'],
        metadata['delay'],
        metadata['filter_id'],
        gaze_x,  # left_gaze_x
        gaze_y,  # left_gaze_y
        gaze_z,  # left_gaze_z
        left_eye_cam_x,
        left_eye_cam_y,
        left_eye_cam_z,
        left_angle_x,
        left_angle_y,
        left_raw_x,
        left_raw_y,
        left_pupil_measure1,
        pupil_measure1_type,  # left_pupil_measure1_type
        left_pupil_measure2,
        pupil_measure2_type,  # left_pupil_measure2_type
        EyeTrackerConstants.UNDEFINED,  # left_ppd_x
        EyeTrackerConstants.UNDEFINED,  # left_ppd_y
        EyeTrackerConstants.UNDEFINED,  # left_velocity_x
        EyeTrackerConstants.UNDEFINED,  # left_velocity_y
        EyeTrackerConstants.UNDEFINED,  # left_velocity_xy
        gaze_x,  # right_gaze_x
        gaze_y,  # right_gaze_y
        gaze_z,  # right_gaze_z
        right_eye_cam_x,
        right_eye_cam_y,
        right_eye_cam_z,
        right_angle_x,
        right_angle_y,
        right_raw_x,
        right_raw_y,
        right_pupil_measure1,
        pupil_measure1_type,  # right_pupil_measure1_type
        right_pupil_measure2,
        pupil_measure2_type,  # right_pupil_measure2_type
        EyeTrackerConstants.UNDEFINED,  # right_ppd_x
        EyeTrackerConstants.UNDEFINED,  # right_ppd_y
        EyeTrackerConstants.UNDEFINED,  # right_velocity_x
        EyeTrackerConstants.UNDEFINED,  # right_velocity_y
        EyeTrackerConstants.UNDEFINED,  # right_velocity_xy
        status
    ]


def _monocular_eye_sample_from_gaze_3d(surface_datum, gaze_datum, pupil_datum, metadata):

    gaze_x, gaze_y, gaze_z = surface_datum['norm_pos'][0], surface_datum['norm_pos'][1], 0

    eye_cam_x, eye_cam_y, eye_cam_z = pupil_datum['sphere']['center']

    angle_x, angle_y = pupil_datum['phi'], pupil_datum['theta']

    raw_x, raw_y = pupil_datum['norm_pos']

    pupil_measure1_type = EyeTrackerConstants.PUPIL_MAJOR_AXIS  # diameter 2d
    pupil_measure1 = pupil_datum["diameter"]

    pupil_measure2_type = EyeTrackerConstants.PUPIL_DIAMETER_MM  # diameter 3d
    pupil_measure2 = pupil_datum.get("diameter_3d", None)

    status = pupil_datum["method"]

    return [  # MonocularEyeSampleEvent
        metadata['experiment_id'],
        metadata['session_id'],
        metadata['device_id'],
        metadata['event_id'],
        EventConstants.MONOCULAR_EYE_SAMPLE,  # type
        metadata['device_time'],
        metadata['logged_time'],
        metadata['time'],
        metadata['confidence_interval'],
        metadata['delay'],
        metadata['filter_id'],
        gaze_x,
        gaze_y,
        gaze_z,
        eye_cam_x,
        eye_cam_y,
        eye_cam_z,
        angle_x,
        angle_y,
        raw_x,
        raw_y,
        pupil_measure1,
        pupil_measure1_type,
        pupil_measure2,
        pupil_measure2_type,
        EyeTrackerConstants.UNDEFINED,  # ppd_x
        EyeTrackerConstants.UNDEFINED,  # ppd_y
        EyeTrackerConstants.UNDEFINED,  # velocity_x
        EyeTrackerConstants.UNDEFINED,  # velocity_y
        EyeTrackerConstants.UNDEFINED,  # velocity_xy
        status
    ]
