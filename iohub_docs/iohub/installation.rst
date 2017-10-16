#############
Installation
#############

.. note:: As of the May 8th, 2013 release of PsychoPy, the ioHub Package has merged with
    the PsychoPy package and is now being distributed as part of PsychoPy. 
    
    The documentation provided here is still up to date but the instructions
    below are only needed if you do not use the PsychoPy Standalone Installer
    provided for Windows or macOS. Please visit the `PsychoPy <http://www.psychopy.org>`_
    website and follow the installation and download links to learn how to install one of these
    PsychoPy Python Distributions.

    If you do need to perform a manual installation of PsychoPy and wish to also
    use the ioHub submodule within it, then the following *manual* installation
    instructions can still be of use.
 
Manually Installing ioHub
##########################

You can use ioHub with your own installation of Python, with the following
requirements:

    #. Python 2.6.8 or 2.7.x 32-bit. The 32-bit version of Python can be installed on a supported 64-bit OS.
    #. PsychoPy 1.74.03 or higher and all of it's dependencies. See the `PsychoPy installation <http://www.psychopy.org/installation.html>`_ page for details. ioHub is included.
    #. `NumPy <http://www.numpy.org/>`_ version 1.6.2 or greater.

The following packages are also required:
   
    #. `psutil <https://pypi.python.org/pypi/psutil>`_ A cross-platform process and system utilities module for Python.
    #. `msgpack <https://pypi.python.org/pypi/msgpack-python>`_ It's like JSON. but fast and small.
    #. `greenlet <https://pypi.python.org/pypi/greenlet>`_ The greenlet package is a spin-off of Stackless, a version of CPython that supports micro-threads called "tasklets".
    #. `gevent **(version 1.0 or greater)** <http://www.gevent.org/>`_ A coroutine-based Python networking library.
    #. `numexpr <https://code.google.com/p/numexpr/>`_ Fast numerical array expression evaluator for Python and NumPy.
    #. `pytables <http://www.pytables.org>`_ PyTables is a package for managing hierarchical datasets.
    #. `pyYAML <http://pyyaml.org/>`_ PyYAML is a YAML parser and emitter for Python.

Windows installations only
    #. `pywin32 <http://sourceforge.net/projects/pywin32/>`_ Python Extensions for Windows
    #. `pyHook <http://sourceforge.net/projects/pyhook/>`_ Python wrapper for global input hooks in Windows.

Linux installations only
    #. `python-xlib <http://sourceforge.net/projects/python-xlib/>`_ The Python X11R6 client-side implementation.

OSX installations only
    #. `pyobjc <http://pythonhosted.org/pyobjc/>`_ : A  Python ObjectiveC binding.    

If you are using a Python distribution like `Enthought Canopy <https://www.enthought.com/products/canopy/>`_ or 
`Continuum Analytics Anaconda <https://store.continuum.io/cshop/anaconda/>`_, 
most of these packages can be installed through the package manager, which
takes care any of the dependencies between packages.

Several of the devices supported by ioHub require the installation of a binary OS driver
for the device that can not be included with the ioHub package due to licensing 
considerations. Please refer to the documentation page for each device you will be using to ensure that
any device specific driver required is known about and is installed.
