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


def eye_sample_from_gaze_3d(gaze_datum, metadata):
    pupil_datum_right, pupil_datum_left = None, None

    for p in gaze_datum['base_data']:
        if p['id'] == EYE_ID_RIGHT:
            pupil_datum_right = p
        if p['id'] == EYE_ID_LEFT:
            pupil_datum_left = p

    if pupil_datum_right and pupil_datum_left:
        return _binocular_eye_sample_from_gaze_3d(
            gaze_datum=gaze_datum,
            pupil_datum_right=pupil_datum_right,
            pupil_datum_left=pupil_datum_left,
            metadata=metadata
        )
    elif pupil_datum_right:
        return _monocular_eye_sample_from_gaze_3d(
            gaze_datum=gaze_datum,
            pupil_datum=pupil_datum_right,
            metadata=metadata
        )
    elif pupil_datum_left:
        return _monocular_eye_sample_from_gaze_3d(
            gaze_datum=gaze_datum,
            pupil_datum=pupil_datum_left,
            metadata=metadata
        )
    else:
        # This should never happen
        return None


def _binocular_eye_sample_from_gaze_3d(gaze_datum, pupil_datum_right, pupil_datum_left, metadata):

    gaze_x, gaze_y, gaze_z = gaze_datum['gaze_point_3d']

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


def _monocular_eye_sample_from_gaze_3d(gaze_datum, pupil_datum, metadata):

    gaze_x, gaze_y, gaze_z = gaze_datum['gaze_point_3d']

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
        EventConstants.BINOCULAR_EYE_SAMPLE,  # type
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

# gaze_datum = {
#     'topic': 'gaze.3d.01.',
#     'timestamp': 194673.3556225,
#     'confidence': 0.8348832898281267,
#     'eye_centers_3d': {
#         '0': [19.63230003723274, 15.329813185345355, -19.71347927617327],
#         '1': [-36.5875006890438, 14.738771520843137, -19.30276778885174]
#     },
#     'gaze_normals_3d': {
#         '0': [-0.3412950039525646, -0.42734509482074445, 0.8371940576769927],
#         '1': [-0.21216810766819658, -0.2548802546902005, 0.9434091105440711]
#     },
#     'gaze_point_3d': [-118.57887897454275, -119.97205534599976, 332.8457623494092],
#     'norm_pos': [0.29594934146526963, 0.8049384454868861],
#     'base_data': [
#         {
#             'id': 0,
#             'topic': 'pupil.0.3d',
#             'method': 'pye3d 0.1.1 real-time',
#             'timestamp': 194673.355638,
#             'confidence': 0.799754798412323,
#             'norm_pos': [0.25594833587098137, 0.3508741717722542],
#             'diameter': 34.012955864077306,
#             'diameter_3d': 3.7158480504054503,
#             'sphere': {
#                 'center': [3.978231429553039, 0.43424456419396873, 41.17606287707503],
#                 'radius': 10.392304845413264},
#             'projected_sphere': {
#                 'center': [123.20373608249564, 98.90891810774345],
#                 'axes': [171.00502158937934, 171.00502158937934],
#                 'angle': 0.0
#             },
#             'circle_3d': {
#                 'center': [-3.040088877447326, 5.382678317608985, 35.32318465722377],
#                 'normal': [-0.6753381864176129, 0.4761632599335316, -0.5631934692942041],
#                 'radius': 1.8579240252027251
#             },
#             'ellipse': {
#                 'center': [49.14208048722842, 124.6321590197272],
#                 'axes': [18.74114178833173, 34.012955864077306],
#                 'angle': 146.0727033894438
#             },
#             'location': [49.14208048722842, 124.6321590197272],
#             'model_confidence': 1.0,
#             'theta': 1.0745099151119064,
#             'phi': -2.446494755255356
#         },
#         {
#             'id': 1,
#             'topic': 'pupil.1.3d',
#             'method': 'pye3d 0.1.1 real-time',
#             'norm_pos': [0.437603779313222, 0.8009502380958735],
#             'diameter': 38.317958154436,
#             'confidence': 0.8700117812439304,
#             'timestamp': 194673.355607,
#             'sphere': {
#                 'center': [-0.45580939533040543, -3.5450124158679484, 44.766945976288284],
#                 'radius': 10.392304845413264
#             },
#             'projected_sphere': {
#                 'center': [92.96599950418828, 73.499126542906],
#                 'axes': [157.08230989471977, 157.08230989471977],
#                 'angle': 0.0
#             }, 'circle_3d': {
#                 'center': [-1.3873945308943996, -6.832057817492002, 34.95228950431442],
#                 'normal': [-0.08964182146515434, -0.3162960912443614, -0.9444157593496352],
#                 'radius': 2.108544798422654
#             },
#             'diameter_3d': 4.217089596845308,
#             'ellipse': {
#                 'center': [84.01992562813862, 38.217554285592286],
#                 'axes': [34.813754250613094, 38.317958154436],
#                 'angle': 75.12684553397881
#             },
#             'location': [84.01992562813862, 38.217554285592286],
#             'model_confidence': 1.0,
#             'theta': 1.8926189031696699,
#             'phi': -1.665430560466961
#         }
#     ]
# }
