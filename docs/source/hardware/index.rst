.. _hardware_docs:

Communicating with external hardware using PsychoPy
=========================================================================

PsychoPy is able to communicate with a range of external hardware, like EEG recording devices and eye trackers. 

This page provides step-by-step instructions on how to communicate with some of the more commonly used hardware. The page is being updated regularly so if you don't see your device listed here please do post in the forum as we keep an eye on commonly-faced issues (and solutions!) there.


Communicating with EEG
-----------------------------

If you use EEG in your research, you'll know that it is essential to make timing very precise in your experiments. We recommend that you read `this timing megastudy <https://peerj.com/articles/9414/>`_ by Bridges et al (2020) and run calibration tests to understand the timing lag, and more importantly the variability of that lag, on the hardware you're using before conducting EEG research with PsychoPy or indeed any other software. 

Although these guides will talk you through how to communicate with EEG hardware, they can really be used to communicate with any device that is connected via the same method:

- Communicating via parallel port and USB
- Communicating via serial port
- Communicating with EGI Netstation
- Communicating with Emotiv


Communicating with an eye-tracker
------------------------------------------

- Communicating with an eye-tracker using Builder components


Communicating with other devices
------------------------------------------

- Recording information from an Arduino microcontroller