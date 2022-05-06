.. _hardware_docs:

Communicating with external hardware using PsychoPy
=========================================================================

PsychoPy is able to communicate with a range of external hardware, like EEG recording devices and eye trackers. 

This page provides step-by-step instructions on how to communicate with some of the more commonly used hardware. The page is being updated regularly so if you don't see your device listed here please do post in the forum as we keep an eye on commonly-faced issues (and solutions!) there.


Communicating with EEG
-----------------------------

If you use EEG in your research, you'll know that it is essential to make timing very precise in your experiments. We recommend that you read `this timing megastudy <https://peerj.com/articles/9414/>`_ by Bridges et al (2020) and run calibration tests to understand the timing lag, and more importantly the variability of that lag, on the hardware you're using before conducting EEG research with PsychoPy or indeed any other software. 

Although these guides will talk you through how to communicate with EEG hardware, they can be used to communicate with any device that is connected via the same method:

- Communicating via parallel port and USB (link)
- Communicating via serial port (link)
- Communicating with EGI Netstation (link)
- Communicating with Emotiv (link)


Communicating with an eyetracker
------------------------------------------

- Setting up (link)
- Calibration (link)
- Recording (link)


Communicating with other devices
------------------------------------------

- Recording GSR or Heart Rate via an Arduino