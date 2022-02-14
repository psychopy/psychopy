#################
Pupil Labs - Core
#################

.. contents:: Table of Contents

**********************************
High Level Pupil Core Introduction
**********************************

`Pupil Core <https://pupil-labs.com/products/core/>`__ is a wearable eye tracker. The
system consists of two inward-facing eye cameras and one forward-facing world camera
mounted on a wearable eyeglasses-like frame.

Pupil Core provides gaze data in its world camera's field of view, regardless of the wearer's
head position. As such, gaze can be analysed with the wearer looking and moving freely
in their environment.

Pupil Core differs from remote eye trackers often used with PsychoPy. Remote eye
trackers employ cameras mounted on or near a computer monitor. They provide gaze in
screen-based coordinates, and this facilitates closed-loop analyses of gaze based on the
known position of stimuli on-screen and eye gaze direction.

In order to use Pupil Core for screen-based work in PsychoPy, the screen will need to be
robustly located within the world camera's field of view, and Pupil Core's gaze data
subsequently transformed from world camera-based coordinates to screen-based coordinates.
This is achieved with the use of
`AprilTag Markers <https://docs.pupil-labs.com/core/software/pupil-capture/#markers>`__.

.. image:: https://raw.githubusercontent.com/wiki/pupil-labs/pupil/media/images/pupil-core-render.jpg
    :width: 700px
    :align: center
    :alt: Pupil Core binocular headset with high-speed scene camera

For a detailed overview of wearable *vs* remote eye trackers, check out
`this Pupil Labs blog post
<https://pupil-labs.com/blog/news/what-is-eye-tracking/>`_.

Join the Pupil Labs `Discord community <https://pupil-labs.com/chat>`_ to share
your research and/or questions.

**************************************
Device, Software, and Connection Setup
**************************************

Additional Software Requirements
================================

`Pupil Capture <https://github.com/pupil-labs/pupil/releases/latest>`_
version v2.0 or newer

Platforms:

-  Windows 10
-  macOS 10.14 or newer
-  Ubuntu 16.04 or newer

Supported Models:

-  Pupil Core headset

Setting Up the Eye Tracker
==========================

1. Follow `Pupil Core's Getting Started
   guide <https://docs.pupil-labs.com/core/#getting-started>`__ to setup
   the headset and Capture software

Setting Up PsychoPy
===================

1. Open ``experiment settings`` in the Builder Window (cog icon in top
   panel)
2. Open the ``Eyetracking`` tab
3. Modify the properties as follows:

   -  Select ``Pupil Labs`` from the ``Eyetracker Device`` drop down menu
   -  ``Pupil Remote Address`` / ``Port`` - Defines how to connect to
      Pupil Capture. See Pupil Capture's *Network API* menu to check
      address and port are correct. PsychoPy will wait the amount of
      milliseconds declared in ``Pupil Remote Timeout (ms)`` for the
      connection to be established. An error will be raised if the
      timeout is reached.
   -  ``Pupil Capture Recording`` - Enable this option to tell Pupil
      Capture to record the eye tracker's raw data during the
      experiment. You can read more about that in `Pupil Capture's
      official
      documentation <https://docs.pupil-labs.com/core/software/pupil-capture/#recording>`__.
      Leave ``Pupil Capture Recording Location`` empty to record to the
      default
   -  ``Gaze Confidence Threshold`` - Set the minimum data quality
      received from Pupil Capture. Ranges from 0.0 (all data) to 1.0
      (highest possible quality). We recommend using the default value
      of 0.6.
   -  ``Pupillometry Only`` - If this mode is selected you will only
      receive pupillometry data. No further setup is required. If you
      are interested in gaze data, keep this option disabled and read on
      below.

.. image:: https://raw.githubusercontent.com/wiki/pupil-labs/pupil/media/images/eye-tracker-properties.png
    :width: 700px
    :align: center
    :alt: Pupil Core eye tracking options, part of PsychoPy experiment settings

Pupillometry + Gaze Mode
======================

To receive gaze, enable Pupil Capture's Surface Tracking
plugin:

1. Start by `printing four apriltag
   markers <https://docs.pupil-labs.com/assets/img/apriltags_tag36h11_0-23.37196546.jpg>`__
   and attaching them at the screen corners. Avoid occluding the screen
   and leave sufficient white space around the marker squares. Read more
   about the general marker setup
   `here <https://docs.pupil-labs.com/core/software/pupil-capture/#surface-tracking>`__.

.. image:: https://raw.githubusercontent.com/wiki/pupil-labs/pupil/media/images/pc-sample-experiment.jpg
    :width: 700px
    :align: center
    :alt: Subject wearing Pupil Core headset, looking at a Computer screen setup with
        AprilTag markers

1. `Enable the surface tracker
   plugin <https://docs.pupil-labs.com/core/software/pupil-capture/#plugins>`__
2. `Define a surface and align its surface
   corners <https://docs.pupil-labs.com/core/software/pupil-capture/#defining-a-surface>`__
   with the screen corners as good as possible
3. Rename the surface to the name set in the ``Surface Name`` field of
   the eye tracking project settings (default:
   ``psychopy_iohub_surface``)
4. Run the PsychoPy calibration component as part of your experiment


*******************************
Implementation and API Overview
*******************************

EyeTracker Class
================

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.pupil_labs.pupil_core.EyeTracker
    :members: surface_topic, trackerTime, trackerSec, setConnectionState, isConnected,
        runSetupProcedure, setRecordingState, isRecordingEnabled, getLastSample, 
        getLastGazePosition
    :undoc-members:
    :show-inheritance:

Supported Event Types
=====================

The Pupil Core–PsychoPy integration provides real-time access to monocular and binocular
sample data. In pupillometry-only mode, all events will be emitted as
:py:class:`MonocularEyeSampleEvents <psychopy.iohub.devices.eyetracker.MonocularEyeSampleEvent>`.
In pupillometry+gaze mode, the software only emits :py:class:`BinocularEyeSampleEvents
<psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent>` events if Pupil Capture is
driving a binocular headset and the detection from both eyes have sufficient `confidence
<https://docs.pupil-labs.com/core/terminology/#confidence>`_ to be paired. See this
high-level overview of the `Pupil Capture Data Matching algorithm
<https://github.com/N-M-T/pupil-docs/commit/1dafe298565720a4bb7500a245abab7a6a2cd92f>`_
for details.

The supported fields are described below.

.. autoclass:: psychopy.iohub.devices.eyetracker.MonocularEyeSampleEvent

    .. attribute:: device_time
        :type: float

        time of gaze measurement, in sec.msec format, using Pupil Capture clock

    .. attribute:: logged_time
        :type: float

        time at which the sample was received in PsychoPy, in sec.msec format, using
        PsychoPy clock

    .. attribute:: time
        :type: float

        time of gaze measurement, in sec.msec format, using PsychoPy clock

    .. attribute:: confidence_interval
        :type: float
        :value: -1.0

        currently not supported, always set to ``-1.0``

    .. attribute:: delay
        :type: float

        The difference between ``logged_time`` and ``time``, in sec.msec format

    .. attribute:: eye
        :type: int
        :value: 21 or 22

        :py:attr:`psychopy.iohub.constants.EyeTrackerConstants.RIGHT_EYE` (``22``)
        or :py:attr:`psychopy.iohub.constants.EyeTrackerConstants.LEFT_EYE` (``21``)

    .. attribute:: gaze_x
        :type: float

        x component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode.

    .. attribute:: gaze_y
        :type: float

        y component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode.

    .. attribute:: gaze_z
        :type: float
        :value: 0 or float("nan")

        z component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode. Set to ``0.0`` otherwise.

    .. attribute:: eye_cam_x
        :type: float

        x component of 3d eye model location in undistorted eye camera coordinates

    .. attribute:: eye_cam_y
        :type: float

        y component of 3d eye model location in undistorted eye camera coordinates

    .. attribute:: eye_cam_z
        :type: float

        z component of 3d eye model location in undistorted eye camera coordinates

    .. attribute:: angle_x
        :type: float

        phi angle / horizontal rotation of the 3d eye model location in radians.
        ``-π/2`` corresponds to looking directly into the eye camera

    .. attribute:: angle_y
        :type: float

        theta angle / vertical rotation of the 3d eye model location in radians.
        ``π/2`` corresponds to looking directly into the eye camera

    .. attribute:: raw_x
        :type: float

        x component of the pupil center location in `normalized coordinates
        <https://docs.pupil-labs.com/core/terminology/#coordinate-system>`_

    .. attribute:: raw_y
        :type: float

        y component of the pupil center location in `normalized coordinates
        <https://docs.pupil-labs.com/core/terminology/#coordinate-system>`_

    .. attribute:: pupil_measure1
        :type: float

        Major axis of the detected pupil ellipse in pixels

    .. attribute:: pupil_measure1_type
        :type: int
        :value: psychopy.iohub.constants.EyeTrackerConstants.PUPIL_MAJOR_AXIS

    .. attribute:: pupil_measure2
        :type: Optional[float]

        Diameter of the detected pupil in mm or ``None`` if not available

    .. attribute:: pupil_measure2_type
        :type: int
        :value: psychopy.iohub.constants.EyeTrackerConstants.PUPIL_DIAMETER_MM

.. autoclass:: psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent

    .. attribute:: device_time
        :type: float

        time of gaze measurement, in sec.msec format, using Pupil Capture clock

    .. attribute:: logged_time
        :type: float

        time at which the sample was received in PsychoPy, in sec.msec format, using
        PsychoPy clock

    .. attribute:: time
        :type: float

        time of gaze measurement, in sec.msec format, using PsychoPy clock

    .. attribute:: confidence_interval
        :type: float
        :value: -1.0

        currently not supported, always set to ``-1.0``

    .. attribute:: delay
        :type: float

        The difference between ``logged_time`` and ``time``, in sec.msec format

    .. attribute:: left_gaze_x
        :type: float

        x component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode. Same as ``right_gaze_x``.

    .. attribute:: left_gaze_y
        :type: float

        y component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode. Same as ``right_gaze_y``.

    .. attribute:: left_gaze_z
        :type: float
        :value: 0 or float("nan")

        z component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode. Set to ``0.0`` otherwise. Same as ``right_gaze_z``.

    .. attribute:: left_eye_cam_x
        :type: float

        x component of 3d eye model location in undistorted eye camera coordinates

    .. attribute:: left_eye_cam_y
        :type: float

        y component of 3d eye model location in undistorted eye camera coordinates

    .. attribute:: left_eye_cam_z
        :type: float

        z component of 3d eye model location in undistorted eye camera coordinates

    .. attribute:: left_angle_x
        :type: float

        phi angle / horizontal rotation of the 3d eye model location in radians.
        ``-π/2`` corresponds to looking directly into the eye camera

    .. attribute:: left_angle_y
        :type: float

        theta angle / vertical rotation of the 3d eye model location in radians.
        ``π/2`` corresponds to looking directly into the eye camera

    .. attribute:: left_raw_x
        :type: float

        x component of the pupil center location in `normalized coordinates
        <https://docs.pupil-labs.com/core/terminology/#coordinate-system>`_

    .. attribute:: left_raw_y
        :type: float

        y component of the pupil center location in `normalized coordinates
        <https://docs.pupil-labs.com/core/terminology/#coordinate-system>`_

    .. attribute:: left_pupil_measure1
        :type: float

        Major axis of the detected pupil ellipse in pixels

    .. attribute:: left_pupil_measure1_type
        :type: int
        :value: psychopy.iohub.constants.EyeTrackerConstants.PUPIL_MAJOR_AXIS

    .. attribute:: left_pupil_measure2
        :type: Optional[float]

        Diameter of the detected pupil in mm or ``None`` if not available

    .. attribute:: pupil_measure2_type
        :type: int
        :value: psychopy.iohub.constants.EyeTrackerConstants.PUPIL_DIAMETER_MM

    .. attribute:: right_gaze_x
        :type: float

        x component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode. Same as ``left_gaze_x``.

    .. attribute:: right_gaze_y
        :type: float

        y component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode. Same as ``left_gaze_y``.

    .. attribute:: right_gaze_z
        :type: float
        :value: 0 or float("nan")

        z component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode. Set to ``0.0`` otherwise. Same as ``left_gaze_z``.

    .. attribute:: right_eye_cam_x
        :type: float

        x component of 3d eye model location in undistorted eye camera coordinates

    .. attribute:: right_eye_cam_y
        :type: float

        y component of 3d eye model location in undistorted eye camera coordinates

    .. attribute:: right_eye_cam_z
        :type: float

        z component of 3d eye model location in undistorted eye camera coordinates

    .. attribute:: right_angle_x
        :type: float

        phi angle / horizontal rotation of the 3d eye model location in radians.
        ``-π/2`` corresponds to looking directly into the eye camera

    .. attribute:: right_angle_y
        :type: float

        theta angle / vertical rotation of the 3d eye model location in radians.
        ``π/2`` corresponds to looking directly into the eye camera

    .. attribute:: right_raw_x
        :type: float

        x component of the pupil center location in `normalized coordinates
        <https://docs.pupil-labs.com/core/terminology/#coordinate-system>`_

    .. attribute:: right_raw_y
        :type: float

        y component of the pupil center location in `normalized coordinates
        <https://docs.pupil-labs.com/core/terminology/#coordinate-system>`_

    .. attribute:: right_pupil_measure1
        :type: float

        Major axis of the detected pupil ellipse in pixels

    .. attribute:: right_pupil_measure1_type
        :type: int
        :value: psychopy.iohub.constants.EyeTrackerConstants.PUPIL_MAJOR_AXIS

    .. attribute:: right_pupil_measure2
        :type: Optional[float]

        Diameter of the detected pupil in mm or ``None`` if not available

    .. attribute:: right_pupil_measure2_type
        :type: int
        :value: psychopy.iohub.constants.EyeTrackerConstants.PUPIL_DIAMETER_MM

Default Device Settings
-----------------------

.. literalinclude:: ../default_yaml_configs/default_pupil_core_eyetracker.yaml
    :language: yaml


**Last Updated:** February, 2022