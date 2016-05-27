.. _iohub_requirements:

ioHub Specific Requirements
===========================

Computer Specifications
------------------------

When an experiment is using ioHub, it is running 
two seperate processes, one for the main PsychoPy experiment 
and a second for the ioHub Server. For the two processes to
run in parallel, a minimum of two CPU cores need to be available.
 
The following are minimum suggested computer specifications 
for running a PsychoPy experiemnt that uses ioHub:

* Intel i5 or i7 CPU. A minimum of **two** CPU cores is needed,
  four is recommended.
* 8 GB of RAM
* Windows 7 +, OS X 10.7.5 +, or Linux Kernel 2.6 +

Please see the :ref:`hardware` section for further information
that applies to PsychoPy in general.

Usage Considerations
---------------------

When using psychopy.iohub, the following
constrains should be noted:

1. pyglet must be used; pygame is not supported.
2. If using ioHub devices that report screen position information,
   the experiment must use a single, full screen, PsychoPy Window.
3. By default ioHub reports **all** Keyboard and Mouse events that are
   received by the operating system, regardless of what 
   PsychoPy Window or Desktop application has focus when the 
   event occurs. In fact, ioHub can report keyboard events when 
   no PsychoPy Window has been created at all. This capability
   very useful in some situations but may not be desired others.
   Reported Keyboard and Mouse events can be limited to
   those targeted for the PsychoPy Window by changing the
   'report_system_wide_events' setting to False for each of these 
   devices when starting the ioHub Server Process.   
4. On OS X, Assistive Device support must be enabled for ioHub to
   detect Keyboard and Mouse events. The steps used to do this
   depend on the version of OS X being used:
   
   * For OS X 10.7 - 10.8.5, instructions can be found
     `here <http://mizage.com/help/accessibility.html#10.8>`_.
   * For OS X 10.9 +, the program being used to start your experiment script
     must be specifically authorized. Example instructions on authorizing
     an OS X 10.9 + app can be viewed 
     `here <http://mizage.com/help/accessibility.html#10.9>`_.

Software Requirements
----------------------

When running PsychoPy using the OS X or Windows standalone distribution,
all the necessary python package dependencies have already been installed, so
the rest of this section can be skipped.

.. note::

   Hardware specific software may need to be installed depending on the
   device being used. For example, if an eye tracker is being used, it is
   likely that the eye tracker's driver and / or SDK will need to be 
   installed on the computer running PsychoPy. See the documentation page
   for the device hardware in question for further details.

Manual Installation
~~~~~~~~~~~~~~~~~~~~

If ioHub is being manually installed, first ensure the PsychoPy 
Python package :ref:`dependencies`have been installed.

In addition, ioHub depends on the following Python packages:

    #. `psutil (version 1.2 +) <https://pypi.python.org/pypi/psutil>`_: A cross-platform process and system utilities module for Python.
    #. `msgpack <https://pypi.python.org/pypi/msgpack-python>`_: It's like JSON. but fast and small.
    #. `greenlet <https://pypi.python.org/pypi/greenlet>`_: Greenlet is a spin-off of Stackless, supporting micro-threads called "tasklets".
    #. `gevent (version 1.0 or greater)** <http://www.gevent.org/>`_: A coroutine-based Python networking library.
    #. `numexpr <https://code.google.com/p/numexpr/>`_: Fast numerical array expression evaluator for Python and NumPy.
    #. `pytables <http://www.pytables.org>`_: PyTables is a package for managing hierarchical datasets.
    #. `pyYAML <http://pyyaml.org/>`_: PyYAML is a YAML parser and emitter for Python.
    #. (Windows OS Only) `pyHook <http://sourceforge.net/projects/pyhook/>`_: Python wrapper for global input hooks in Windows.
    #. (Linux Only) `python-xlib <http://sourceforge.net/projects/python-xlib/>`_: The Python X11R6 client-side implementation.
    #. (OS X Only) `pyobjc <http://pythonhosted.org/pyobjc/>`_: A Python ObjectiveC binding.

