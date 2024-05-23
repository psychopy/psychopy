.. _cameraComponent:

-------------------------------
CameraComponent
-------------------------------

This component provides a way to use the webcam to record participants during an experiment.

**Note: For online experiments, the browser will notify participants to allow use of webcam before the start of the task.**

When recording via webcam, specify the starting time relative to the start of the routine (see `start` below) and a stop time (= duration in seconds).
A blank duration evaluates to recording for 0.000s.

The resulting video files are saved in .mp4 format if recorded locally and saved in .webm if recorded online. There will be one file per recording. The files appear in a new folder within the data directory in a folder called data_cam_recorded. The file names include the unix (epoch) time of the onset of the recording with milliseconds, e.g., `recording_cam_2022-06-16_14h32.42.064.mp4`.

**Note: For online experiments, the recordings can only be downloaded from the "Download results" button from the study's Pavlovia page.**


For a demo in builder mode, after unpacking the demos, click on Demos > Feature Demos > camera.
For a demo in coder mode, click on Demos > hardware > camera.py

Categories:
    Responses
Works in:
    PsychoPy, PsychoJS

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start
    The time that the stimulus should first play. See :ref:`startStop` for details.

Stop
    The length of time (sec) to record for. An `expected duration` can be given for
    visualisation purposes. See :ref:`startStop` for details; note that only seconds are allowed.

Device
===============================

Device label
    A label to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same label here.

Backend
    Python package to use behind the scenes.
    
    Options:
    - FFPyPlayer
    - OpenCV

Video device
    What device would you like to use to record video? This will only affect local experiments - online experiments ask the participant which device to use.

    Options are generated live, so will vary according to your setup.

Video device
    What device would you like to use to record video? This will only affect local experiments - online experiments ask the participant which device to use.

Resolution
    Resolution (w x h) to record to, leave blank to use device default.

    Options are generated live, so will vary according to your setup.

Resolution
    Resolution (w x h) to record to, leave blank to use device default.

Frame rate
    Frame rate (frames per second) to record at, leave blank to use device default.

    Options are generated live, so will vary according to your setup.

Frame rate
    Frame rate (frames per second) to record at, leave blank to use device default. For some cameras, you may need to use `camera.CAMERA_FRAMERATE_NTSC` or `camera.CAMERA_FRAMERATE_NTSC / 2`.

Audio
===============================

Microphone device label
    A label to refer to this Component's associated microphone device by. If using the same device for multiple components, be sure to use the same label here.

Microphone
    What microphone device would you like the use to record? This will only affect local experiments - online experiments ask the participant which mic to use.

    Options are generated live, so will vary according to your setup.

Channels
    Record two channels (stereo) or one (mono, smaller file). Select 'auto' to use as many channels as the selected device allows.
    
    Options:
    - auto
    - mono
    - stereo

Sample rate (hz)
    How many samples per second (Hz) to record at
    
    Options:
    - Telephone/Two-way radio (8kHz)
    - Voice (16kHz)
    - CD Audio (44.1kHz)
    - DVD Audio (48kHz)
    - High-Def (96kHz)
    - Ultra High-Def (192kHz)

Max recording size (kb)
    To avoid excessively large output files, what is the biggest file size you are likely to expect?

Data
====================

Save onset/offset times: bool
    Whether to save the onset and offset times of the component.

Sync timing with screen refresh: bool
    Whether to sync the start time of the component with the window refresh.

Save file?
    File type the video is saved as locally is mp4 and for online it is webm.

Testing
===============================

Disable Component
    Disable this Component