.. _iohub_requirements:

psychopy.iohub Specific Requirements
======================================

Computer Specifications
------------------------

The design / requirements of your experiment itself can obviously influence
what the minimum computer specification should be to provide good timing /
performance.

The dual process design when running using psychopy.iohub also
influences the minimum suggested specifications as follows:

* Intel i5 or i7 CPU. A minimum of **two** CPU cores is needed.
* 8 GB of RAM
* Windows 7 +, OS X 10.7.5 +, or Linux Kernel 2.6 +

Please see the :ref:`hardware` section for further information
that applies to PsychoPy in general.

Usage Considerations
---------------------

When using psychopy.iohub, the following
constrains should be noted:

1. The pyglet graphics backend must be used; pygame is not supported.
2. ioHub devices that report position data use the unit type defined by the
   PsychoPy Window. However, position data is reported using the full screen
   area and size the window was created in. Therefore, for accurate window position
   reporting, the PsychoPy window must be made full screen.
3. On macOS, Assistive Device support must be enabled when using psychopy.iohub.
   * For OS X 10.7 - 10.8.5, instructions can be found
     `here <http://mizage.com/help/accessibility.html#10.8>`_.
   * For OS X 10.9 +, the program being used to start your experiment script must
     be specifically authorized. Example instructions on authorizing an OS X 10.9 + app
     can be viewed `here <http://mizage.com/help/accessibility.html#10.9>`_.