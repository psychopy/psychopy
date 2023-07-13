.. _timing:

Timing Issues and synchronisation
==================================

One of the key requirements of experimental control software is that it has good temporal precision. |PsychoPy| aims to be as precise as possible in this domain and can achieve excellent results depending on your experiment and hardware. It also provides you with a precise log file of your experiment to allow you to check the precision with which things occurred.

Many scientists have asked "Can |PsychoPy| provide sub-millisecond timing precision?". The short answer is yes it can - |PsychoPy|'s timing is as good as any software package we've tested `(we've tested quite a lot) <https://peerj.com/articles/9414/>`_.

BUT there are many components to getting good timing, and many ways that your timing could be less-than-perfect. So if timing is important to you then you should really read this entire section of the |PsychoPy| manual and you should **test your timing** using dedicated hardware (photodiodes, microphones or, ideally the `Black Box Toolkit`_). We can't emphasise enough how many ways there are for your hardware and/or operating system to break the good timing that |PsychoPy| is providing.

.. toctree::
   :maxdepth: 1

   millisecondPrecision
   nonSlipTiming
   detectingFrameDrops
   reducingFrameDrops

Understand and measuring your timing
---------------------------------------

There are certain steps that we strongly advise you to take before running an experiment that needs to be temporally precise in PsychoPy, or indeed any other software:

* Read `this timing megastudy <https://peerj.com/articles/9414/>`_ by Bridges et al (2020) which compares several pieces of behavioural software in terms of their temporal precision. You can find a summary of the results here: :ref:`timing2020`
* Check that your stimulus presentation monitor is not dropping frames. You can do this by running the timeByFrames.py demo. Find this demo in the `Coder` window > demos > timing. The timeByFrames demo examines the precision of your frame flips, and shows the results in a plot similar to the one below:

.. figure:: /images/timeByFrameRes.png

    The results here are for a 60Hz monitor, and you can see that there are no dropped frames from the left hand side of the screen, and also the timing of each frame is 16.7ms (shown on the right-hand side of the screen) which is what we would expect from a 60Hz monitor (1000ms/60 = 16.66ms).

* Use a photodiode or other physical stimulus detector to fully understand the lag, and more importantly the variability of that lag, between any triggers that you send to indicate the start of your stimulus and when the stimulus actually starts.

.. _Black Box Toolkit: https://www.blackboxtoolkit.com/
