#############
Installation
#############

.. note:: As of the May 8th, 2013 release of PsychoPy, the ioHub Package has merged with
    the PsychoPy package and is now being distributed as part of PsychoPy. 
    
    The documentation provided here is still up to date however the installation instructions
    below are only needed if you can not use the PsychoPy Python Distribution Installer
    provided for Windows or OS X. Please visit the `PsychoPy <http://www.psychopy.org>`_ 
    website and follow the installation and download links to learn how to install one of these
    PsychoPy Python Distributions.

    If you do need to perform a manual installation of PsychoPy and wish to also
    use the ioHub submodule within it, then the following *manual* installation
    instructions can still be of use.
 
There are different installation options depending on the target OS.

Windows
########

Manually Installing ioHub
===========================

The following software must be installed on the computer before proceeding with 
the ioHub dependency installation list and installation of ioHub itself: 

    #. Python 2.6.8 or 2.7.3 32 bit is required as the Python interpreter. The 32 bit version of Python can be installed on a supported 64 bit OS.

    #. Psychopy 1.74.03 or higher and all of it's dependencies. See the `PsychoPy installation <http://www.psychopy.org/installation.html>`_ page for details. 

    #. For the NumPy package, please ensure 1.6.2 or greater is installed.

Dependency Installation List 
+++++++++++++++++++++++++++++

Once Python and PsychoPy (including all the stated PsychoPy dependencies) are installed, the following extra Python packages must be installed for the ioHub:

Python 2.7 Package List with URLs
++++++++++++++++++++++++++++++++++

    #. `psutil <http://code.google.com/p/psutil/downloads/detail?name=psutil-0.6.1.win32-py2.7.exe>`_ A cross-platform process and system utilities module for Python
    #. `msgpack <http://pypi.python.org/packages/2.7/m/msgpack-python/msgpack_python-0.2.0-py2.7-win32.egg#md5=d52bd856ca8c8d9a6ee86937e1b4c644>`_ It's like JSON. but fast and small.
    #. `greenlet <http://pypi.python.org/packages/2.7/g/greenlet/greenlet-0.4.0.win32-py2.7.exe#md5=910896116b1e4fd527b8afaadc7132f3>`_ The greenlet package is a spin-off of Stackless, a version of CPython that supports micro-threads called "tasklets".
    #. `gevent <https://github.com/downloads/SiteSupport/gevent/gevent-1.0rc2.win32-py2.7.exe>`_ A coroutine-based Python networking library that uses greenlet to provide a high-level synchronous API on top of the libevent event loop.
    #. `numexpr <http://code.google.com/p/numexpr/downloads/detail?name=numexpr-1.4.2.win32-py2.7.exe&can=2&q=>`_ Fast numerical array expression evaluator for Python and NumPy.
    #. `pytables <http://www.lfd.uci.edu/~gohlke/pythonlibs/#pytables>`_ PyTables is a package for managing hierarchical datasets and designed to efficiently and easily cope with extremely large amounts of data.
    #. `pyYAML <http://pyyaml.org/download/pyyaml/PyYAML-3.10.win32-py2.7.exe>`_ PyYAML is a YAML parser and emitter for Python.
    #. `pywin32 <http://sourceforge.net/projects/pywin32/files/pywin32/Build%20217/pywin32-217.win32-py2.7.exe/download>`_ Python Extensions for Windows
    #. `pyHook <http://sourceforge.net/projects/pyhook/files/pyhook/1.5.1/pyHook-1.5.1.win32-py2.7.exe/download>`_ Python wrapper for global input hooks in Windows.

Python 2.6 Package List with URLs
+++++++++++++++++++++++++++++++++++

    #. `psutil <https://code.google.com/p/psutil/downloads/detail?name=psutil-0.6.1.win32-py2.6.exe>`_ A cross-platform process and system utilities module for Python
    #. `msgpack <http://www.lfd.uci.edu/~gohlke/pythonlibs/#msgpack>`_ It's like JSON. but fast and small.
    #. `greenlet <https://pypi.python.org/packages/2.6/g/greenlet/greenlet-0.4.0.win32-py2.6.exe>`_ The greenlet package is a spin-off of Stackless, a version of CPython that supports micro-threads called "tasklets".
    #. `gevent <https://code.google.com/p/gevent/downloads/detail?name=gevent-1.0b4.win32-py2.6.exe&can=2&q=>`_ A coroutine-based Python networking library that uses greenlet to provide a high-level synchronous API on top of the libevent event loop.
    #. `numexpr <http://code.google.com/p/numexpr/downloads/detail?name=numexpr-1.4.2.win32-py2.6.exe&can=2&q=>`_ Fast numerical array expression evaluator for Python and NumPy.
    #. `pytables <http://www.lfd.uci.edu/~gohlke/pythonlibs/#pytables>`_ PyTables is a package for managing hierarchical data sets and designed to efficiently and easily cope with extremely large amounts of data.
    #. `pyYAML <http://pyyaml.org/download/pyyaml/PyYAML-3.10.win32-py2.6.exe>`_ PyYAML is a YAML parser and emitter for Python.
    #. `pyHook <http://sourceforge.net/projects/pyhook/files/pyhook/1.5.1/pyHook-1.5.1.win32-py2.6.exe/download>`_ Python wrapper for global input hooks in Windows.
    #. `pywin32 <http://sourceforge.net/projects/pywin32/files/pywin32/Build%20217/pywin32-217.win32-py2.6.exe/download>`_ Python Extensions for Windows

Several of the devices supported by ioHub require the installation of a binary OS driver
for the device that can not be included with the ioHub package due to licensing 
considerations. Please refer to the documentation page for each device you will be using to ensure that
any device specific driver required is known about and is installed.

ioHub Package Installation
++++++++++++++++++++++++++++++

ioHub is now included with the PsychoPy package. Please ensure the most recent version
of PsychoPy is installed and ioHub is also then installed.

Linux
#######

Manually Installing ioHub
===========================

The following software must be installed on the computer before proceeding with 
the ioHub dependency installation list and installation of ioHub itself: 

    #. Python 2.6.8 or 2.7.3 32 bit is required as the Python interpreter. The 32 bit version of Python can be installed on a supported 64 bit OS.

    #. Psychopy 1.74.03 or higher and all of it's dependencies. See the `PsychoPy installation <http://www.psychopy.org/installation.html>`_ page for details. 

    #. For the NumPy package, please ensure 1.6.2 or greater is installed.

ioHub Dependency List Installation
+++++++++++++++++++++++++++++++++++

The following Python packages need to be installed on the system you plan to run
ioHub on. Some packages can be installed using *pip*, while other should be installed 
by downloading the package from the provided URL, unpacking the tarball, and 
installing the package by typing::

    > python setup.py install

in a terminal session where you have changed directories to the location of the uncompressed 
python package source that contains the setup.py script.

Some packages downloaded via a URL are a .deb file, in which case you just download
the file and install it by double clicking the .deb file once downloaded. 

Note that for both 'pip' and manual 'python setup.py install', depending on your
Linux distribution and system configuration, you may need to run pip or 
'python setup.py install' with root privileges by placing 'sudo ' in front of the
command line text to be run.

For example::

    > sudo pip install package_name

where package_name is the name of one of the required python packages.

Installing pip if it is not Already on the System
+++++++++++++++++++++++++++++++++++++++++++++++++++

If you type:: 

    > pip

in a console and are told the program does not exist, then you can install pip using::

    > sudo apt-get install pip

Packages To Download with URLs
++++++++++++++++++++++++++++++

#. `psutil <http://code.google.com/p/psutil/downloads/detail?name=psutil-0.6.1.tar.gz&can=2&q=>`_ A cross-platform process and system utilities module for Python
#. `gevent <https://github.com/downloads/SiteSupport/gevent/python-gevent_1.0rc2_i386.deb>`_ A coroutine-based Python networking library that uses greenlet to provide a high-level synchronous API on top of the libevent event loop.
#. `numexpr <http://code.google.com/p/numexpr/downloads/detail?name=numexpr-2.0.1.tar.gz&can=2&q=>`_ Fast numerical array expression evaluator for Python and NumPy.
#. `pyYAML <http://pyyaml.org/wiki/PyYAMLDocumentation>`_ Following install instructions on the page. PyYAML is a YAML parser and emitter for Python. For faster processing, also download and install `LibYAML <http://pyyaml.org/wiki/LibYAML>`_; following install instructions on the page.
#. `python-xlib <http://sourceforge.net/projects/python-xlib/>`_ The Python X Library is a complete X11R6 client-side implementation, written in pure Python.


Packages to install using pip
++++++++++++++++++++++++++++++

#. msgpack: It's like JSON. but fast and small. ( pip install msgpack-python )
#. greenlet: The greenlet package is a spin-off of Stackless, a version of CPython that supports micro-threads called "tasklets". ( pip install greenlet )
#. pytables: PyTables is a package for managing hierarchical data sets and designed to efficiently and easily cope with extremely large amounts of data. ( pip install tables )

ioHub Package Installation
++++++++++++++++++++++++++++++

ioHub is now included with the PsychoPy package. Please ensure the most recent version
of PsychoPy is installed and ioHub is also then installed.

OSX 10.6 - 10.8
################

This is not suggested for the faint of heart. Instead you should strongly consider 
installing the PsychoPy Python Distribution for OS X discussed at the start of this page.

Manual Installation
====================

The following software must be installed on the computer before proceeding with 
the ioHub dependency installation list and installation of ioHub itself: 

    #. Python 2.6.8 or 2.7.3 32 bit is required as the Python interpreter. The 32 bit version of Python can be installed on a supported 64 bit OS.

    #. Psychopy 1.74.03 or higher and all of it's dependencies. See the `PsychoPy installation <http://www.psychopy.org/installation.html>`_ page for details. 

    #. For the NumPy package, please ensure 1.6.2 or greater is installed.

Dependency List Installation
++++++++++++++++++++++++++++++

The following Python packages need to be installed on the system you plan to run
ioHub on. Some packages can be installed using *pip*, while other should be installed 
by downloading the package from the provided URL, unpacking the tarball, and 
installing the package by typing::

    > python setup.py install

in a terminal session where you have changed directories to the location of the uncompressed 
python package source that contains the setup.py script.

Note that for both 'pip' and manual 'python setup.py install', depending on your
OS X settings and python configuration, you may need to run pip or 
'python setup.py install' with root priveledges.

If your user has admin rights, this can be done by running the command with 'sudo'
at the start of the command and entering your password when prompted. For example::

    > sudo pip install package_name

where package_name is the name of one of the required python packages.

Installing pip if it is not Already on the System
++++++++++++++++++++++++++++++++++++++++++++++++++

If you type:: 

    > pip

in a console and are told the program does not exist, then you can install pip or easy_install before proceeding.


Packages to install using pip or easy_install
++++++++++++++++++++++++++++++++++++++++++++++

#. **msgpack** It's like JSON. but fast and small. ( pip install msgpack-python )
#. **greenlet** The greenlet package is a spin-off of Stackless, a version of CPython that supports micro-threads called "tasklets". ( pip install greenlet )
#. **pytables** PyTables is a package for managing hierarchical datasets and designed to efficiently and easily cope with extremely large amounts of data. ( pip install tables ). FIRST INSTALL 'numexpr' from the list below, as it is a dependency of tables) 

Packages To Download
++++++++++++++++++++

#. `pyobjc <https://pypi.python.org/packages/source/p/pyobjc/pyobjc-2.5.1.tar.gz#md5=f242cff4a25ce397bb381c21a35db885>`_ : A  Python ObjectiveC binding.    
#. **gevent**: A coroutine-based Python networking library that uses greenlet to provide a high-level synchronous API on top of the libevent event loop::

		pip install cython -e git://github.com/surfly/gevent.git@1.0rc2#egg=gevent

#. `numexpr <http://code.google.com/p/numexpr/downloads/detail?name=numexpr-2.0.1.tar.gz&can=2&q=>`_ Fast numerical array expression evaluator for Python and NumPy.    
#. `pyYAML <http://pyyaml.org/download/pyyaml/PyYAML-3.10.tar.gz>`_ PyYAML is a YAML parser and emitter for Python. First install the C side package `LibYAML <http://pyyaml.org/wiki/LibYAML>`_, before installing ptYAML.

ioHub Package Installation
+++++++++++++++++++++++++++

ioHub is now included with the PsychoPy package. Please ensure the most recent version
of PsychoPy is installed and ioHub is also then installed.
