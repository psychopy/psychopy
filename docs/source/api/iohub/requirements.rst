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

Software Requirements
----------------------

When running PsychoPy using the macOS or Windows standalone distribution,
all the necessary python package dependencies have already been installed, so
the rest of this section can be skipped.

.. note::

   Hardware specific software may need to be installed depending on the
   device being used. See the documentation page for the specific device
   hardware in question for further details.

If psychopy.iohub is being manually installed, first ensure the python packages
listed in the :ref:`dependencies` section of the manual are installed.

psychopy.iohub requires the following extra dependencies to be installed:

    #. `psutil (version 1.2 +) <https://pypi.python.org/pypi/psutil>`_ A cross-platform process and system utilities module for Python.
    #. `msgpack <https://pypi.python.org/pypi/msgpack-python>`_ It's like JSON. but fast and small.
    #. `greenlet <https://pypi.python.org/pypi/greenlet>`_ The greenlet package is a spin-off of Stackless, a version of CPython that supports micro-threads called "tasklets".
    #. `gevent (version 1.0 or greater)** <http://www.gevent.org/>`_ A coroutine-based Python networking library.
    #. `numexpr <https://code.google.com/p/numexpr/>`_ Fast numerical array expression evaluator for Python and NumPy.
    #. `pytables <http://www.pytables.org>`_ PyTables is a package for managing hierarchical datasets.
    #. `pyYAML <http://pyyaml.org/>`_ PyYAML is a YAML parser and emitter for Python.

Windows installations only
    #. `pyHook <http://sourceforge.net/projects/pyhook/>`_ Python wrapper for global input hooks in Windows.

Linux installations only
    #. `python-xlib <http://sourceforge.net/projects/python-xlib/>`_ The Python X11R6 client-side implementation.

OSX installations only
    #. `pyobjc <http://pythonhosted.org/pyobjc/>`_ : A Python ObjectiveC binding.

