.. _pupil_labs_neon:

#################
Pupil Labs - Neon
#################

.. contents:: Table of Contents

**********************************
High Level Neon Introduction
**********************************

`Neon <https://pupil-labs.com/products/neon/>`__ is a calibration-free, wearable eye tracker.
The system consists of two inward-facing eye cameras and one forward-facing world camera
mounted on a wearable eyeglasses-like frame.

Neon provides gaze data in its world camera's field of view, regardless of the wearer's
head position. As such, gaze can be analysed with the wearer looking and moving freely
in their environment.

Neon is unlike remote eye trackers which employ cameras mounted on or near a computer monitor.
They provide gaze in screen-based coordinates, and this facilitates closed-loop analyses of
gaze based on the known position of stimuli on-screen and eye gaze direction.

To use Neon for screen-based work in |PsychoPy|, the screen needs to be robustly located within
the world camera's field of view, and Neon's gaze data subsequently transformed from world
camera-based coordinates to screen-based coordinates. This is achieved with the use of
`AprilTag Markers <https://docs.pupil-labs.com/core/software/pupil-capture/#markers>`__.

.. image:: https://raw.githubusercontent.com/wiki/pupil-labs/pupil/media/images/JAN_quarterfront_left_white.png
    :width: 700px
    :align: center
    :alt: Neon in the "Just Act Natural" frame

For a detailed overview of wearable *vs* remote eye trackers, check out
`this Pupil Labs blog post
<https://pupil-labs.com/blog/news/what-is-eye-tracking/>`_.

Join the Pupil Labs `Discord community <https://pupil-labs.com/chat>`_ to share
your research and/or questions.

**************************************
Device, Software, and Connection Setup
**************************************

Setting Up the Eye Tracker
==========================

1. Follow `Neon's Getting Started
   guide <https://docs.pupil-labs.com/neon/#getting-started>`_ to setup
   the headset and companion device.

Setting Up |PsychoPy|
=====================

1. Install the ``Pupil Labs`` plugin using the Plugin Manager and restart Builder.
2. Open ``experiment settings`` in the Builder Window (cog icon in top
   panel)
3. Open the ``Eyetracking`` tab
4. Modify the properties as follows:

   -  Select ``Pupil Labs (Neon)`` from the ``Eyetracker Device`` drop down menu
   -  ``Companion address`` / ``Companion port`` - Defines how to connect to
      the Companion Device. These values can be found in the Neon Companion app by clicking the
      ``Stream`` button in the top-left corner of the app.

.. raw:: html
<video src="https://raw.githubusercontent.com/wiki/pupil-labs/psychopy-eyetracker-pupil-labs/images/companion-stream-info.mp4" width="240" height="536"/>

   -  ``Recording enabled`` - Enable this option to create a recording on the Companion device.
   -  ``Camera calibration path`` - Specify the path of a camera calibration file. This is the
      ``scene_camera.json`` file from a saved recording.

5. Add AprilTag components to the routines that require eyetracking.
   -  Three tags is generally considered a bare minimum, but more tags will yield more robust detection
      more accurate mapping.
   -  All the tags which are visible together must each have a unique ID.
   -  Tags can be placed anywhere on the screen as long as they are fully visible and do not overlap.

A `sample experiment <https://github.com/pupil-labs/psychopy-gaze-contingent-demo>`_ is available for reference.

*******************************
Implementation and API Overview
*******************************

EyeTracker Class
================

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.pupil_labs.pupil_core.EyeTracker
    :members: surface_topic, trackerTime, trackerSec, setConnectionState, isConnected,
        setRecordingState, isRecordingEnabled, getLastSample, getLastGazePosition
    :undoc-members:
    :show-inheritance:

Supported Event Types
=====================

The Neon–|PsychoPy| integration provides real-time access to :py:class:`BinocularEyeSampleEvents
<psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent>`_ events. The supported fields are
described below.

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

    .. attribute:: delay
        :type: float

        The difference between ``logged_time`` and ``time``, in sec.msec format

    .. attribute:: gaze_x
        :type: float

        x component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode.

    .. attribute:: gaze_y
        :type: float

        y component of gaze location in display coordinates. Set to ``float("nan")`` in
        pupillometry-only mode.


Default Device Settings
-----------------------

.. literalinclude:: ../default_yaml_configs/default_pupil_neon_eyetracker.yaml
    :language: yaml


**Last Updated:** September, 2023
