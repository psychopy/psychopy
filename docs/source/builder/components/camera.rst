.. _cameraComponent:

Camera Component
----------------

The camera component provides a way to use the webcam to record participants during an experiment. 
**Note: For online experiments, the browser will notify participants to allow use of webcam before the start of the task.**

When recording via webcam, specify the starting time relative to the start of the routine (see `start` below) and a stop time (= duration in seconds).
A blank duration evaluates to recording for 0.000s.

The resulting video files are saved in .mp4 format if recorded locally and saved in .webm if recorded online. There will be one file per recording. The files appear in a new folder within the data directory in a folder called data_cam_recorded. The file names include the unix (epoch) time of the onset of the recording with milliseconds, e.g., `recording_cam_2022-06-16_14h32.42.064.mp4`.
**Note: For online experiments, the recordings can only be downloaded from the "Download results" button from the study's Pavlovia page.**


For a demo in builder mode, after unpacking the demos, click on Demos > Feature Demos > camera.
For a demo in coder mode, click on Demos > hardware > camera.py


Parameters
~~~~~~~~~~~~

Basic
====================

name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

start : float or integer
    The time that the stimulus should first play. See :ref:`startStop` for details.

stop (duration):
    The length of time (sec) to record for. An `expected duration` can be given for
    visualisation purposes. See :ref:`startStop` for details; note that only seconds are allowed.


Data
====================

Save onset/offset times: bool
    Whether to save the onset and offset times of the component.

Sync timing with screen refresh: bool
    Whether to sync the start time of the component with the window refresh.

Output File Type:
    File type the video is saved as locally is mp4 and for online it is webm.

