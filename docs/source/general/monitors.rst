Monitor Center
====================================

PsychoPy provides a simple and intuitive way for you to calibrate your monitor and provide other information about it and then import that information into your experiment.

Information is inserted in the Monitor Center (Tools menu), which allows you to store information about multiple monitors and keep track of multiple calibrations for the same monitor.

For experiments written in the Builder view, you can then import this information by simply specifying the name of the monitor that you wish to use in the :ref:`expSettings` dialog. For experiments created as scripts you can retrieve the information when creating the :class:`~psychopy.visual.Window` by simply naming the monitor that you created in Monitor Center. e.g.::

  from psychopy import visual
  win = visual.Window([1024,768], mon='SonyG500')

Of course, the name of the monitor in the script needs to match perfectly the name given in the Monitor Center.

Real world units
-----------------

One of the particular features of PsychoPy is that you can specify the size and location of stimuli in units that are independent of your particular setup, such as degrees of visual angle (see :ref:`units`). In order for this to be possible you need to inform PsychoPy of the size and distance of your monitor.

Depending on the units you choose to use to specify your 