.. _monitorCenter:

Monitor Center
====================================

PsychoPy provides a simple and intuitive way for you to calibrate your monitor and provide other information about it and then import that information into your experiment.

Information is inserted in the |MC| (Tools menu), which allows you to store information about multiple monitors and keep track of multiple calibrations for the same monitor.

For experiments written in the Builder view, you can then import this information by simply specifying the name of the monitor that you wish to use in the :ref:`expSettings` dialog. For experiments created as scripts you can retrieve the information when creating the :class:`~psychopy.visual.Window` by simply naming the monitor that you created in Monitor Center. e.g.::

  from psychopy import visual
  win = visual.Window([1024,768], mon='SonyG500')

Of course, the name of the monitor in the script needs to match perfectly the name given in the Monitor Center.

Real world units
-----------------

One of the particular features of PsychoPy is that you can specify the size and location of stimuli in units that are independent of your particular setup, such as degrees of visual angle (see :ref:`units`). In order for this to be possible you need to inform PsychoPy of some characteristics of your monitor. Your choice of units determines the information you need to provide:

 ======================================  ============================================================
  Units                                             Requires    
 ======================================  ============================================================
  'norm' (normalised to width/height)     n/a
  'pix' (pixels)                          Screen width in pixels
  'cm' (centimeters on the screen)        Screen width in pixels and screen width in cm 
  'deg' (degrees of visual angle)         Screen width (pixels), screen width (cm) and distance (cm)
 ======================================  ============================================================


Calibrating your monitor
--------------------------

PsychoPy can also store and use information about the gamma correction required for your monitor. If you have a Spectrascan PR650 (other devices will hopefully be added) you can perform an automated calibration in which PsychoPy will measure the necessary gamma value to be applied to your monitor. Alternatively this can be added manually into the grid to the right of the Monitor Center. To run a calibration, connect the PR650 via the serial port and, immediately after turning it on press the `Find PR650` button in the |MC|. 

Note that, if you don't have a photometer to hand then there is a method for determining the necessary gamma value psychophysically included in PsychoPy (see gammaMotionNull and gammaMotionAnalysis in the demos menu).

The two additional tables in the Calibration box of the Monitor Center provide conversion from :ref:`DKL <DKL>` and :ref:`LMS <LMS>` colour spaces to :ref:`RGB <RGB>`. 

.. |MC| replace:: Monitor Center 

.. _windows:
