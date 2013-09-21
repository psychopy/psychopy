.. _timing:

Timing Issues and synchronisation
==================================

One of the key requirements of experimental control software is that it has good temporal precision. PsychoPy aims to be as precise as possible in this domain and can achieve excellent results depending on your experiment and hardware. It also provides you with a precise log file of your experiment to allow you to check the precision with which things occurred. Some general considerations are discussed here and there are links with :ref:`specificTiming`.

Something that people seem to forget (not helped by the software manufacturers that keep talking about their sub-millisecond precision) is that the monitor, keyboard and human participant DO NOT have anything like this sort of precision. Your monitor updates every 10-20ms depending on frame rate. If you use a CRT screen then the top is drawn before the bottom of the screen by several ms. If you use an LCD screen the whole screen can take around 20ms to switch from one image to the next. Your keyboard has a latency of 4-30ms, depending on brand and system. 

So, yes, PsychoPy's temporal precision is as good as most other equivalent applications, for instance the duration for which stimuli are presented can be synchronised precisely to the frame, but the overall accuracy is likely to be severely limited by your experimental hardware. To get **very** precise timing of responses etc., you need to use specialised hardware like button boxes and you need to think carefully about the physics of your monitor.

.. warning::
    The information about timing in PsychoPy assumes that your graphics card is capable of synchronising with the monitor frame rate. For integrated Intel graphics chips (e.g. GMA 945) under Windows, this is not true and the use of those chips is not recommended for serious experimental use as a result. Desktop systems can have a moderate graphics card added for around £30 which will be vastly superior in performance.

.. _specificTiming:

Specific considerations for specific designs
--------------------------------------------------

.. toctree::
   :maxdepth: 2
   
   nonSlipTiming
   detectingFrameDrops
   reducingFrameDrops
   timingTestByOS

.. _millisecondTiming:

Other questions about timing
--------------------------------------------------

.. toctree::
   :maxdepth: 2
   
   millisecondPrecision

