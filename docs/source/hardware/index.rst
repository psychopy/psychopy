.. _hardware_docs:

Communicating with external hardware using PsychoPy
=========================================================================

PsychoPy is able to communicate with a range of external hardware, like EEG recording devices and eye trackers. 

This page provides step-by-step instructions on how to communicate with some of the more commonly used hardware. The page is being updated regularly so if you don't see your device listed here please do post in the forum as we keep an eye on commonly-faced issues (and solutions!) there.


Understand your timing
-----------------------------

It is essential to make timing very precise in your experiments, especially if you're looking to collect EEG data.
There are certain steps that we strongly advise you to take before running an experiment that needs to be temporally precise in PsychoPy, or indeed any other software:

* Read `this timing megastudy <https://peerj.com/articles/9414/>`_ by Bridges et al (2020) which compares several pieces of behavioural software in terms of their temporal precision.
* Check that your stimulus presentation monitor is not dropping frames. You can do this by running the timeByFrames.py demo. Find this demo in the `Coder` window > demos > timing. The timeByFrames demo examines the precision of your frame flips, and shows the results in a plot similar to the one below:

.. figure:: /images/timeByFrameRes.png

    The results here are for a 60Hz monitor, and you can see that there are no dropped frames from the left hand side of the screen, and also the timing of each frame is 16.7ms (shown on the right-hand side of the screen) which is what we would expect from a 60Hz monitor (1000ms/60 = 16.66ms).

* Use a photodiode or other physical stimulus detector to fully understand the lag, and more importantly the variability of that lag, between any triggers that you send to indicate the start of your stimulus and when the stimulus actually starts.

Communicating with EEG
-----------------------------
Although these guides will talk you through how to communicate with EEG hardware, they can really be used to communicate with any device that is connected via the same method:

- `Communicating via parallel port and USB <https://psychopy.org/hardware/parallelPortInstr.html>`_
- `Communicating via serial port <https://psychopy.org/hardware/serialPortInstr.html>`_
- `Communicating with EGI NetStation <https://psychopy.org/hardware/egiNetStation.html>`_
-  `Communicating with Emotiv <https://www.psychopy.org/builder/components/emotiv_record.html>`_ please also see `this video tutorial <https://www.youtube.com/watch?v=rRoqGa4PoN8>`_.

.. note::
    If you'd like to use a `Parallel Port` to **record** responses (for example from a button box) please read `this excellent thread <https://discourse.psychopy.org/t/issue-reading-parallel-port-pin-for-button-box/9759>`_ from our Discourse Forum user `jtseng <https://discourse.psychopy.org/u/jtseng>`_.

Communicating with an eye-tracker
------------------------------------------

- `Communicating with an eye-tracker using Builder components <https://psychopy.org/hardware/eyeTracking.html>`_


Communicating with other devices
------------------------------------------

- `Recording information from an Arduino microcontroller <https://psychopy.org/hardware/arduino.html>`_

