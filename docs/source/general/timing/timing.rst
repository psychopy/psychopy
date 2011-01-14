.. _timing:

Timing Issues and synchronisation
==================================

One of the key requirements of experimental control software is that it has good temporal precision. PsychoPy aims to be as precise as possible in this domain and does achieve excellent results where these are possible. To check the accuracy with which monitor frame times are recorded on your system run the timeByFrames demo from the Coder view.

Something that people seem to forget (not helped by the software manufacturers that keep talking about sub-millisecond precision) is that the monitor, keyboard and human participant DO NOT have anything like this sort of precision. Your monitor updates every 10-20ms depending on frame rate. If you use a CRT screen then the top is drawn before the bottom of the screen by several ms. If you use an LCD screen the whole screen refreshes at the same time, but takes around 20ms to switch from one image to the next. Your keyboard has a latency of 4-30ms, depending on brand and system. 

So, yes, PsychoPy's temporal precision can be very good, but the overall accuracy is likely to be severely limited by your experimental hardware. Below are some further details on timing issues.

.. warning::
	The information about timing in PsychoPy assumes that your graphics card is capable of synchronising with the monitor frame rate. For integrated Intel graphics chips (e.g. GMA 945) under Windows, this is not true and the use of those chips is not recommended for serious experimental use as a result. Desktop systems can have a moderate graphics card added for around £30 which will be vastly superior in performance.

Contents:

.. toctree::
   :maxdepth: 2
   
   detectingFrameDrops
   reducingFrameDrops
   synchronisingInfMRI
   synchronisingInEEG
