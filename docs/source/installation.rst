Installation
===============

Overview
~~~~~~~~~~~~~~~~~~~~~~

PsychoPy can be installed in three main ways:

* **As an application**: The "Stand Alone" versions include everything you need to create and run experiments. When in doubt, choose this option.

* **As libraries**: PsychoPy and the libraries it depends on can also be installed individually, providing greater flexibility. This option requires managing a python environment.

* **As source code**: If you want to customize how PsychoPy works, consult the :ref:`developer's guide <developers>` for installation and work-flow suggestions. 

When you start PsychoPy for the first time, a **Configuration Wizard** will retrieve and summarize key system settings. Based on the summary, you may want to adjust some preferences to better reflect your environment. In addition, this is a good time to unpack the Builder demos to a location of your choice. (See the Demo menu in the Builder.)

If you get stuck or have questions, please `email the mailing list <http://groups.google.com/group/psychopy-users>`_.

If all goes well, at this point your installation will be complete! See the next section of the manual, Getting started.

.. _hardware:

Recommended hardware
~~~~~~~~~~~~~~~~~~~~~~

The minimum requirement for PsychoPy is a computer with a graphics card that supports OpenGL. Many newer graphics cards will work well. Ideally the graphics card should support OpenGL version 2.0 or higher. Certain visual functions run much faster if OpenGL 2.0 is available, and some require it (e.g. ElementArrayStim). 

If you already have a computer, you can install PsychoPy and the Configuration Wizard will auto-detect the card and drivers, and provide more information. It is inexpensive to upgrade most desktop computers to an adequate graphics card. High-end graphics cards can be very expensive but are only needed for vision research (and high-end gaming).

If you're thinking of buying a laptop for running experiments, **avoid the built-in Intel graphics chips (e.g. GMA 950)**. The drivers are crummy and performance is poor; graphics cards on laptops are more difficult to exchange. Get something with nVidia or ATI chips instead. Some graphics cards that are known to work with PsychoPy `can be found here <http://upload.psychopy.org/benchmark/report.html>`_; that list is not exhaustive, many cards will also work.

Windows
~~~~~~~~~~~~~~~~~~~~~~

Once installed, you'll now find a link to the PsychoPy application in > Start > Programs > PsychoPy2. Click that and the Configuration Wizard should start. 

The wizard will try to make sure you have reasonably current drivers for your graphics card. You may be directed to download the latest drivers from the vendor, rather than using the pre-installed windows drivers. If necessary, get new drivers directly from the graphics card vendor; don't rely on Windows updates. The windows-supplied drivers are buggy and sometimes don't support OpenGL at all.

The StandAlone installer adds the PsychoPy folder to your path, so you can run the included version of python from the command line. If you have your own version of python installed as well then you need to check which one is run by default, and change your path according to your personal preferences.


Mac OS X
~~~~~~~~~~~~~~~~~~~~~~

There are different ways to install PsychoPy on a Mac that will suit different users. Almost all Mac's come with a suitable video card by default.

* Intel Mac users (with OS X v10.7 or higher; 10.5 and 10.6 might still work) can simply `download`_ the standalone application bundle (the **dmg** file) and drag it to their Applications folder. (Installing it elsewhere should work fine too.)

* Users of `macports <http://www.macports.org/>`_ can install PsychoPy and all its dependencies simply with::
    
    sudo port install py25-psychopy
    
  (Thanks to James Kyles.)

* For PPC Macs (or for Intel Mac users that want their own custom python for running PsychoPy) you need to install the dependencies and PsychoPy manually. The easiest way is to use the `Enthought Python Distribution` (see Dependencies, below).

* You could alternatively manually install the 'framework build' of python and the dependencies (see below). One advantage to this is that you can then upgrade versions with::
    
    sudo easy_install -N -Z -U psychopy

Linux
~~~~~~~~~~~~~~~~~~~~~~
**Debian** systems:
  PsychoPy is in the Debian packages index so you can simply do::
    
    sudo apt-get install psychopy

**Ubuntu** (and other Debian-based distributions):
	
#. Add the following sources in Synaptic, in the Configuration > Repository dialog box, under "Other software"::
	
    deb http://neuro.debian.net/debian karmic main contrib non-free 
    deb-src http://neuro.debian.net/debian karmic main contrib non-free 
	
#. Then follow the 'Package authentification' procedure described in http://neuro.debian.net/ 
#. Then install the psychopy package under Synaptic or through `sudo apt-get install psychopy` which will install all dependencies. 

  (Thanks to Yaroslav Halchenko for the Debian and NeuroDebian package.)

**non-Debian** systems:
  You need to install the dependencies below. Then install PsychoPy::

    $ sudo easy_install psychopy
    ...
    Downloading http://psychopy.googlecode.com/files/PsychoPy-1.75.01-py2.7.egg

.. _dependencies:

Dependencies
===============

Like many open-source programs, PsychoPy depends on the work of many other people in the form of libraries.

Essential packages
~~~~~~~~~~~~~~~~~~~~~~
**Python**: If you need to install python, or just want to, the easiest way is to use the `Enthought Python Distribution <http://www.enthought.com>`_, which is `free for academic use <http://www.enthought.com/products/edudownload.php>`_. Be sure to get a 32-bit version. The only things it misses are `avbin`, `pyo`, and `flac`.

If you want to install each library individually rather than use the simpler distributions of packages above then you can download the following. Make sure you get the correct version for your OS and your version of Python. easy_install will work for many of these, but some require compiling from source.

* `python <http://www.python.org/download/>`_ (32-bit only, version 2.6 or 2.7; 2.5 might work, 3.x will not)
* `avbin <http://code.google.com/p/avbin/>`_ (movies) On mac: 1) Download version 5 `from google <http://code.google.com/p/avbin/>`_ (not a higher version). 2) Start terminal, type `sudo mkdir -p /usr/local/lib` . 3) `cd` to the unpacked avbin directory, type `sh install.sh` . 4) Start or restart PsychoPy, and from PsychoPy's coder view shell, this should work: `from pyglet.media import avbin` . If you run a script and get an error saying `'NoneType' object has no attribute 'blit'`, it probably means you did not install version 5.
* `setuptools <http://peak.telecommunity.com/DevCenter/setuptools>`_
* `numpy <http://www.numpy.org/>`_ (version 0.9.6 or greater)
* `scipy <http://www.scipy.org/Download>`_ (version 0.4.8 or greater)
* `pyglet <http://www.pyglet.org>`_ (version 1.1.4, not version 1.2)
* `wxPython <http://www.wxpython.org>`_ (version 2.8.10 or 2.8.11, not 2.9)
* `Python Imaging Library <http://www.pythonware.com/products/pil/>`_ (`sudo easy_install PIL`)
* `matplotlib <http://matplotlib.sourceforge.net/>`_ (for plotting and fast polygon routines)
* `lxml <http://lxml.de/>`_ (needed for loading/saving builder experiment files)
* `openpyxl <https://bitbucket.org/ericgazoni/openpyxl/downloads>`_ (for loading params from xlsx files)
* `pyo <http://code.google.com/p/pyo/>`_ (sound, version 0.6.2 or higher, compile with `----no-messages`)

These packages are only needed for Windows:

* `pywin32 <https://sourceforge.net/projects/pywin32/>`_
* `winioport <http://www.geocities.com/dinceraydin/python/indexeng.html>`_ (to use the parallel port)
* `inpout32 <http://logix4u.net/parallel-port/16-inpout32dll-for-windows-982000ntxp>`_ (an alternative method to using the parallel port on Windows)
* `inpoutx64 <http://logix4u.net/parallel-port/26-inpoutx64dll-for-win-xp-64-bit>`_ (to use the parallel port on 64-bit Windows)

These packages are only needed for Linux:

* `pyparallel <http://pyserial.sourceforge.net/pyparallel.html>`_ (to use the parallel port)

.. _suggestedPackages:

Suggested packages
~~~~~~~~~~~~~~~~~~~~~~
In addition to the required packages above, additional packages can be useful to PsychoPy users, e.g. for controlling hardware and performing specific tasks. These are packaged with the Standalone versions of PsychoPy but users with their own custom Python environment need to install these manually. Most of these can be installed with `easy_install`.

General packages:

- psignifit for bootstrapping and other resampling tests
- pyserial for interfacing with the serial port
- parallel python (aka pp) for parallel processing
- `flac <http://flac.sourceforge.net>`_ audio codec, for working with google-speech

Specific hardware interfaces:

- `pynetstation <http://code.google.com/p/pynetstation/>`_ to communicate with EGI netstation. See notes on using :ref:`egi` 
- ioLabs toolbox
- labjack toolbox

For developers:

- `pytest` and `coverage` for running unit tests
- `sphinx` for building documentation

.. _download : https://sourceforge.net/projects/psychpy/files/
