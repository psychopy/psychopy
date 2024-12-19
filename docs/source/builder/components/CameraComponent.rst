.. _cameracomponent:

-------------------------------
Camera Component
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

The required attributes of the stimulus, controlling its basic function and behaviour


.. _cameracomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _cameracomponent-startVal:
Start
    When the Camera Component should start, see :ref:`startStop`.
    
.. _cameracomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _cameracomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _cameracomponent-stopVal:
Stop
    When the Camera Component should stop, see :ref:`startStop`.
    
.. _cameracomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _cameracomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _cameracomponent-deviceLabel:
Device label
    A label to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same label here.
    
.. _cameracomponent-cameraLib:
Backend
    Python package to use behind the scenes.
    
    Options:
    
    * FFPyPlayer
    
    * OpenCV
    
.. _cameracomponent-device:
Video device
    What device would you like to use to record video? This will only affect local experiments - online experiments ask the participant which device to use.
    
.. _cameracomponent-deviceManual:
Video device
    What device would you like to use to record video? This will only affect local experiments - online experiments ask the participant which device to use.
    
.. _cameracomponent-resolution:
Resolution
    Resolution (w x h) to record to, leave blank to use device default.
    
.. _cameracomponent-resolutionManual:
Resolution
    Resolution (w x h) to record to, leave blank to use device default.
    
.. _cameracomponent-frameRate:
Frame rate
    Frame rate (frames per second) to record at, leave blank to use device default.
    
.. _cameracomponent-frameRateManual:
Frame rate
    Frame rate (frames per second) to record at, leave blank to use device default. For some cameras, you may need to use `camera.CAMERA_FRAMERATE_NTSC` or `camera.CAMERA_FRAMERATE_NTSC / 2`.
    
Audio
===============================




.. _cameracomponent-micDeviceLabel:
Microphone device label
    A label to refer to this Component's associated microphone device by. If using the same device for multiple components, be sure to use the same label here.
    
.. _cameracomponent-mic:
Microphone
    What microphone device would you like the use to record? This will only affect local experiments - online experiments ask the participant which mic to use. Options are generated live, so will vary according to your setup.
    
.. _cameracomponent-micChannels:
Channels
    Record two channels (stereo) or one (mono, smaller file). Select 'auto' to use as many channels as the selected device allows.
    
    Options:
    
    * auto
    
    * mono
    
    * stereo
    
.. _cameracomponent-micSampleRate:
Sample rate (hz)
    How many samples per second (Hz) to record at
    
.. _cameracomponent-micMaxRecSize:
Max recording size (kb)
    To avoid excessively large output files, what is the biggest file size you are likely to expect?
    
Data
===============================

What information about this Component should be saved?


.. _cameracomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _cameracomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
.. _cameracomponent-saveFile:
Save file?
    Save webcam output to a file?
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _cameracomponent-disabled:
Disable Component
    Disable this Component
    