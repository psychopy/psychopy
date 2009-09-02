Installation
===============

Like many python modules PsychoPy is built and dependent on a number of other libraries (OpenGL, numpy...). Details on how to install those are below.

.. warning: **Python versions.** If you are downloading and installing python manually, note that you should use **Python 2.5**. PsychoPy may work with Python 2.6 will work, but it's untested. Certainly Python 3.0 will not work for now. This version is a complete rewrite of the language and will require substantial rewriting of both the PsychoPy code and the code of the dependencies.

Recommended hardware
~~~~~~~~~~~~~~~~~~~~~~

The bare minimum requirements for PsychoPy are a graphics card that supports OpenGL (most graphics cards do, but on windows you often need to install new drivers).

Ideally OpenGL 2.0 should be supported - certain functions run much faster with where it is available and one stimulus (e.g. ElementArrayStim) even requires it. At the time this was last updated dabs.co.uk were selling the `GeForce 9500GT <http://www.nvidia.com/object/product_geforce_9500gt_us.html|nVidia>`_ for £45, which would be an excellent card for most experiments. 

If you're thinking of buying a laptop for running experiments, *avoid the built-in intel graphics chips (e.g. GMA 950)*. The drivers are crumby and performance is poor. Get something with nVidia or ATI chips instead.


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

* For PPC macs (or for intel mac users that want their own custom python for running PsychoPy) you need to install the dependencies and PsychoPy manually. The easiest way is to use the `Enthought Python Distribution <http://www.enthought.com/products/epddownload.php>`_. It's free (for academic use) and the only things it misses are `avbin <http://code.google.com/p/avbin/>`_ (if you want to play movies) and `pygame`_ (for sound reproduction). You could alternatively manually install the 'framework build' of python and download all the dependencies below. One advantage to this is that you can then upgrade versions with;
    ``sudo /usr/local/bin/easy_install-2.5 -N -Z -U psychopy``

Linux:
~~~~~~~~~~~~~~~~~~~~~~
PsychoPy is in the Debian packages index so users of Debian-based distributions (e.g. Ubuntu) can simply do;
    
    ``sudo apt-get install psychopy``

For non-Debian systems you need to install the dependencies below manually and then PsychoPy (with easy_install?). Thanks to Yaroslav Halchenko for his work on the Debian package.

.. _dependencies:

Dependencies
~~~~~~~~~~~~~~~~~~~~~~

If you want to install each library individually rather than use the simple distributions of packages above then you can download the following. Make sure you get the correct version for your OS and your version of Python.

* `Python <http://www.python.org/download/>`_ (2.4.x or 2.5.x, NOT version 3)
* `setuptools <http://peak.telecommunity.com/DevCenter/setuptools>`_
* `numpy <http://www.numpy.org/>`_ (version 0.9.6 or greater)
* `scipy <http://www.scipy.org/Download>`_ (version 0.4.8 or greater)
* `pyglet <http://www.pyglet.org>`_ (version 1.1 or greater)
* `pygame <http://www.pygame.org>`_ (for playing sounds. Must be version 1.8 or greater)
* `pywin32 <https://sourceforge.net/projects/pywin32/>`_ (only needed for *Windows*)
* `wxPython <http://www.wxpython.org>`_ (version 2.8 or greater)
* `Python Imaging Library <http://www.pythonware.com/products/pil/>`_ (easier to install with setuptools/easy_install)
* `matplotlib <http://matplotlib.sourceforge.net/>`_ (for plotting stuff)
* `winioport <http://www.geocities.com/dinceraydin/python/indexeng.html>`_ (to use the parallel port, win32 only)
* `ctypes <http://python.net/crew/theller/ctypes/>`_ (this is already included in python 2.5)
* `pyxml (needed for printing saving builder experiment files)`

Please send feedback to the mailing list.

.. _download : http://code.google.com/p/psychopy