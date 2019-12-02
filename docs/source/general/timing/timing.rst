.. _timing:

Timing Issues and synchronisation
==================================

One of the key requirements of experimental control software is that it has good temporal precision. PsychoPy aims to be as precise as possible in this domain and can achieve excellent results depending on your experiment and hardware. It also provides you with a precise log file of your experiment to allow you to check the precision with which things occurred. Some general considerations are discussed here and there are links with :ref:`specificTiming`.

Many scientists have asked "Can PsychoPy provide sub-millisecond timing precision?". The short answer is yes it can - PsychoPy's timing is as good as any software package we've tested (we've tested quite a lot).

BUT there are many components to getting good timing, and many ways that your timing could be less-than-perfect. So if timing is important to you then you should really read this entire section of the PsychoPy manually and you should **test your timing** using dedicated hardware (photodiodes, microphones or, ideally the `Black Box Toolkit`_). We can't emphasise enough how many ways there are for your hardware and/or operating system to break the good timing that PsychoPy is providing.

.. toctree::
   :maxdepth: 1

   millisecondPrecision
   nonSlipTiming
   detectingFrameDrops
   reducingFrameDrops

.. _Black Box Toolkit: https://www.blackboxtoolkit.com/
