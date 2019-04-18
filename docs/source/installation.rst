Installation
===============

.. raw:: html

   <script>
    let name;
    let url;
    let version='3.0.7'
    if (navigator.platform === 'Win32') {
      name = '  Standalone PsychoPy '+version+' for 64bit Windows';
      url = 'https://github.com/psychopy/psychopy/releases/download/'+version+'/StandalonePsychoPy3-'+version+'-win64.exe';
    }
    else if (navigator.platform === 'MacIntel') {
      name = '  Standalone PsychoPy '+version+' for MacOS';
      url = 'https://github.com/psychopy/psychopy/releases/download/'+version+'/StandalonePsychoPy3-'+version+'-MacOS.dmg';
    }
    if (navigator.platform === 'Win32' || navigator.platform === 'MacIntel') {
      document.write( "For your detected platform ("+navigator.platform+") we recommend");
      document.write( "<button class='btn' onclick='window.location.href=url'><i class='fa fa-download'></i>" + name + "</button>" );
    }
   </script>



Download
~~~~~~~~~~~~~~~~~~~~~~

For the easiest installation download and install the Standalone package for your system:

For the **latest stable release** (the version we recommend you install):

* `PsychoPy 3.0.5 <https://github.com/psychopy/psychopy/releases>`_
* Ubuntu or debian-based systems:

  * `sudo apt-get install psychopy`
  * NB: the neurodebian package has newer versions than the default debian package: http://neuro.debian.net/

**For previous recent versions** see the `PsychoPy releases on github <https://github.com/psychopy/psychopy/releases>`_

See below for options if you don't want to use the Standalone releases:

* :ref:`manual_install`
* :ref:`conda`
* :ref:`neurodebian`
* :ref:`macports_install`
* :ref:`gentoo`

Notes on OpenGL drivers
~~~~~~~~~~~~~~~~~~~~~~~~

On Windows, if you get an error saying **"pyglet.gl.ContextException: Unable to share contexts"** then the most likely cause is that you need OpenGL drivers and your built-in Windows only has limited support for OpenGL (or possibly you have an Intel graphics card that isn't very good). Try installing new drivers for your graphics card **from its manufacturer's web page,** not from Microsoft. For example NVIDIA provides drivers for its cards here: https://www.nvidia.com/Download/index.aspx

.. _hardware:

Recommended hardware
~~~~~~~~~~~~~~~~~~~~~~

The minimum requirement for PsychoPy is a computer with a graphics card that supports OpenGL. Many newer graphics cards will work well. Ideally the graphics card should support OpenGL version 2.0 or higher. Certain visual functions run much faster if OpenGL 2.0 is available, and some require it (e.g. ElementArrayStim).

If you already have a computer, you can install PsychoPy and the Configuration Wizard will auto-detect the card and drivers, and provide more information. It is inexpensive to upgrade most desktop computers to an adequate graphics card. High-end graphics cards can be very expensive but are only needed for very intensive use.

Generally NVIDIA and ATI (AMD) graphics chips have higher performance than Intel graphics chips so try and get one of those instead. Some graphics cards that are known to work with PsychoPy `can be found here <http://upload.psychopy.org/benchmark/report.html>`_; that list is not exhaustive, many other cards will also work.


.. _manual_install:

Manual install
===============

Now that most python libraries can be install using `pip` it's relatively easy to manually install PsychoPy and all it's dependencies to your own installation of Python. That isn't the officially-supported method (because we can't track which versions of packages you have) but for many people it's the preferred option if they use Python for other things as well.

.. _dependencies:

Dependencies
~~~~~~~~~~~~~~~~~~~~~~

You need a copy of Python itself, and wxPython and probably pyo (or use an alternative audio library listed below). None of these support `pip install` yet so you need to download them:
  * Python itself: http://www.python.org/download/ (**version 3.6 is preferred, although 2.7 also remains supported for the time being** )
  * wxPython: https://wxpython.org/download.php
  * pyo audio: http://ajaxsoundstudio.com/software/pyo/
  * PyQt4 or PyQt5 are handy but not required and need manual installation

Then, if you want **everything** available you could paste this in to your terminal/command line and go and get a coffee. This could take upwards of 20 minutes to download and install everything::

  pip install numpy scipy matplotlib pandas pyopengl pyglet pillow moviepy lxml openpyxl xlrd configobj pyyaml gevent greenlet msgpack-python psutil tables requests[security] pyosf cffi pysoundcard pysoundfile seaborn psychopy_ext python-bidi psychopy
  pip install pyserial pyparallel egi iolabs
  pip install pytest coverage sphinx

Needed on Windows::

  pip install pypiwin32

Needed on macOS::

  pip install pyobjc-core pyobjc-framework-Quartz


OR you could just install the subsets of packages that you want::

  # REQUIRED
  pip install numpy scipy matplotlib pandas pyopengl pyglet pillow moviepy lxml openpyxl configobj psychopy

  # to use iohub
  # you need to install the hdf5 lib before installing tables (`brew install hdf5` on mac))
  pip install pyyaml gevent greenlet msgpack-python psutil tables

  # better excel file reading (than openpyxl)
  pip install xlrd

  # making online connections (e.g. OSF.io)
  pip install requests[security] pyosf

  # alternative audio (easier than pyo to install)
  pip install cffi sounddevice pysoundfile

Handy extra options::

  pip install seaborn  # nice graphing
  pip install psychopy_ext  # common workflows made easy
  pip install python-bidi  # for left-right language formatting

For hardware boxes::

  pip install pyserial pyparallel
  pip install egi  # for egi/pynetstation
  pip install iolabs  # button box
  pip install pyxid  # possible but the version on github has fewer bugs!
  # labjack needs manual install: https://github.com/labjack/LabJackPython

For developers::

  pip install pytest coverage sphinx
  #this installs psychopy links rather than copying the package
  pip install -e /YOUR/PsychoPy/Repository

.. _conda:

Anaconda and Miniconda
~~~~~~~~~~~~~~~~~~~~~~~~

The following should allow you to get PsychoPy working using Ana/MiniConda with Python 2.7::

  conda create -n psypy python=2.7
  conda activate psypy
  conda install numpy scipy matplotlib pandas pyopengl pillow lxml openpyxl xlrd configobj pyyaml gevent greenlet msgpack-python psutil pytables requests[security] cffi seaborn wxpython cython future pyzmq pyserial
  conda install -c conda-forge pyglet pysoundfile python-bidi moviepy pyosf
  pip install zmq json-tricks pyparallel sounddevice pygame pysoundcard psychopy_ext psychopy

and with Python 3.5 (recommended)::

  conda create -n psypy3 python=3.5
  conda activate psypy3
  conda install numpy scipy matplotlib pandas pyopengl pillow lxml openpyxl xlrd configobj pyyaml gevent greenlet msgpack-python psutil pytables requests[security] cffi seaborn wxpython cython pyzmq pyserial
  conda install -c conda-forge pyglet pysoundfile python-bidi moviepy pyosf
  pip install zmq json-tricks pyparallel sounddevice pygame pysoundcard psychopy_ext psychopy

.. _macports_install:

Macports
~~~~~~~~~~~~~~~~~~~~~~

This may be/get out of date but users of `macports <http://www.macports.org/>`_ should be able to install PsychoPy and all its dependencies simply with::

    sudo port install py25-psychopy

  (Thanks to James Kyles.)


.. _neurodebian:

Neurodebian
~~~~~~~~~~~~~~~~~~~~~~

**Debian** and **Ubuntu** systems:
  PsychoPy is in the Debian packages index so you can simply do::

    sudo apt-get install psychopy

To get the newer version you may need to `add the NeuroDebian repository <http://neuro.debian.net/>` (Thanks to Yaroslav Halchenko for packaging for Debian and NeuroDebian.)

.. _gentoo:

Gentoo
~~~~~~~~~~~~~~~~~~~~~~

PsychoPy is in the Gentoo Science Overlay (see `sci-biology/psychopy <https://github.com/gentoo-science/sci/tree/master/sci-biology/psychopy>`_ for the ebuild files).

After you have `enabled the overlay <http://wiki.gentoo.org/wiki/Overlay>`_ simply run::

  emerge psychopy


.. _download : https://github.com/psychopy/psychopy/releases

Developers
~~~~~~~~~~~~~~~~~~~~~~

Ensure you have Python 3.6 and the latest version of pip installed::

  python --version
  pip --version

Next, follow instructions :ref:`here <usingRepos>` to fork and fetch the latest version of the PsychoPy repository.

From the directory where you cloned the latest PsychoPy repository (i.e., where setup.py resides), run::

  pip install -e .

This will install all PsychoPy dependencies to your default Python distribution (which should be Python 3.6). Next, you should create a new PsychoPy shortcut linking your newly installed dependencies to your current version of PsychoPy in the cloned repository. To do this, simply create a new .BAT file containing::

"C:\PATH_TO_PYTHON3.6\python.exe C:\PATH_TO_CLONED_PSYCHOPY_REPO\psychopy\app\psychopyApp.py"

Alternatively, you can run the psychopyApp.py from the command line::

  python C:\PATH_TO_CLONED_PSYCHOPY_REPO\psychopy\app\psychopyApp
