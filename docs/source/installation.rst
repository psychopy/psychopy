Installation
===============

Like many python modules PsychoPy is built and dependent on a number of other libraries (OpenGL, numpy...). Details on how to install those are below.

.. warning: **Python versions.** If you are downloading and installing python manually, note that you should use **Python 2.5**. PsychoPy may work with Python 2.6 will work, but it's untested. Certainly Python 3.0 will not work for now. This version is a complete rewrite of the language and will require substantial rewriting of both the PsychoPy code and the code of the dependencies.

Recommended hardware
~~~~~~~~~~~~~~~~~~~~~~

The bare minimum requirements for PsychoPy are a graphics card that supports OpenGL (most graphics cards do, but on windows you should install new drivers from the graphics card the windows-supplied drivers are buggy and sometimes don't support OpenGL at all).

Ideally OpenGL 2.0 should be supported - certain functions run much faster with where it is available and some stimuli (e.g. ElementArrayStim) even requires it. 

If you're thinking of buying a laptop for running experiments, *avoid the built-in intel graphics chips (e.g. GMA 950)*. The drivers are crummy and performance is poor. Get something with nVidia or ATI chips instead.

Windows:
~~~~~~~~~~~~~~~~~~~~~~

If you're new to python then you probably want to install the standalone package. This includes a copy of python and all the dependent libraries (if you do have python already installed, that won't be touched by this installation). Once installed, you'll now find a link to the PsychoPy application in >Start>Progams>PsychoPy2. Click that and then on the demos menu to get going.

You should **make sure you have reasonably current drivers for your graphics card** (download the latest from the vendor, rather than using the pre-installed windows drivers). 

The standalone installer adds the PsychoPy folder to your path, so you can run the included version of python from the command line etc. If you have your own version of python installed as well then you need to check which one is run by default, and change your path according to your personal preferences.

Mac OS X:
~~~~~~~~~~~~~~~~~~~~~~

There are different ways to install PsychoPy on a mac that will suit different users

* Intel Mac users (with OS X v10.5) can simply `download`_ the standalone application bundle (the *dmg* file) and drag it to their Applications folder. The app bundle contains its own independent python and all the dependencies and will not interact with anything else on your system (except its own preferences).

* Users of `macports <http://www.macports.org/>`_ can install PsychoPy and all its dependencies simply with:
    ``sudo port install py25-psychopy``
    
    (thanks James Kyles for that).

* For PPC macs (or for intel mac users that want their own custom python for running PsychoPy) you need to install the dependencies and PsychoPy manually. The easiest way is to use the `Enthought Python Distribution <http://www.enthought.com>`_. `It's free for academic use <http://www.enthought.com/products/edudownload.php>`_ and the only things it misses are `avbin <http://code.google.com/p/avbin/>`_ (if you want to play movies) and `pygame`_ (for sound reproduction). You could alternatively manually install the 'framework build' of python and download all the dependencies below. One advantage to this is that you can then upgrade versions with::
    
    sudo /usr/local/bin/easy_install-2.5 -N -Z -U psychopy

Linux:
~~~~~~~~~~~~~~~~~~~~~~
For **Debian** users, PsychoPy is in the Debian packages index so you can simply do::
    
    sudo apt-get install psychopy

For **Debian-based** distributions (e.g. Ubuntu):
	
	#. Add the following sources in Synaptic, in the Configuration>Repository dialog box, under "Other software"::
	
	    deb http://neuro.debian.net/debian karmic main contrib non-free 
	    deb-src http://neuro.debian.net/debian karmic main contrib non-free 
	
	#. Then follow the 'Package authentification' procedure described in http://neuro.debian.net/ 
	#. Then install the psychopy package under Synaptic or through `sudo apt-get install psychopy` which will install all dependencies. 

For **non-Debian** systems you need to install the dependencies below manually and then PsychoPy (with easy_install?). 

Thanks to Yaroslav Halchenko for his work on the Debian package.

.. _dependencies:

Dependencies
~~~~~~~~~~~~~~~~~~~~~~

If you want to install each library individually rather than use the simple distributions of packages above then you can download the following. Make sure you get the correct version for your OS and your version of Python.

* `Python <http://www.python.org/download/>`_ (2.5.x-2.7.x, NOT version 3)
* `setuptools <http://peak.telecommunity.com/DevCenter/setuptools>`_
* `numpy <http://www.numpy.org/>`_ (version 0.9.6 or greater)
* `scipy <http://www.scipy.org/Download>`_ (version 0.4.8 or greater)
* `pyglet <http://www.pyglet.org>`_ (version 1.1.4, not version 1.2?)
* `pygame <http://www.pygame.org>`_ (for playing sounds and/or as an alternative to pyglet. Must be version 1.8 or greater)
* `pywin32 <https://sourceforge.net/projects/pywin32/>`_ (only needed for *Windows*)
* `wxPython <http://www.wxpython.org>`_ (version 2.8, not 2.9)
* `Python Imaging Library <http://www.pythonware.com/products/pil/>`_ (easier to install with setuptools/easy_install)
* `matplotlib <http://matplotlib.sourceforge.net/>`_ (for plotting stuff)
* `winioport <http://www.geocities.com/dinceraydin/python/indexeng.html>`_ (to use the parallel port, win32 only)
* `lxml <http://lxml.de/>`_ (needed for loading/saving builder experiment files)
* `openpyxl <https://bitbucket.org/ericgazoni/openpyxl/downloads>`_ (for loading params from xlsx files)

.. _suggestedPackages:

Suggested packages
~~~~~~~~~~~~~~~~~~~~~~
In addition to the required packages above, there are numerous other additional packages that are useful to PsychoPy users, e.g. for controlling hardware and performing specific tasks. These are packaged with the Standalone versions of `PsychoPy` but users with their own custom Python environment need to install these manually to use them. Most of these can be installed with easy_install

General packages:

    - psignifit for bootsrtapping and other resampling tests
    - pyserial for interfacing with the serial port
    - parallel python (aka pp) for parallel processing

Specific hardware interfaces:

    - `pynetstation <http://code.google.com/p/pynetstation/>`_ to communicate with EGI netstation. See notes on using :ref:`egi` 
    - ioLabs toolbox
    - labjack tolbox

For developers:

    - `nose` and `coverage` for running unit tests (if this means nothing to you don't worry)
    - `sphinx` for documentation

Please send feedback to the mailing list.

.. _download : http://code.google.com/p/psychopy