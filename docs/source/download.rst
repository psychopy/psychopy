Installation
===============

.. _download:

Download
-----------

For the easiest installation download and install the Standalone package.

.. raw:: html

   <script src="https://cdn.jsdelivr.net/npm/ua-parser-js@0/dist/ua-parser.min.js"></script>
   <script>

    let filename;
    let url;
    let version='2020.2.4'

    let clientInfo = UAParser(navigator.userAgent);
    var osLabel;
    var os = clientInfo.os.name;
    var arch = clientInfo.cpu.architecture;
    // create the platform dependent strings
    if (navigator.platform == 'Win32' && clientInfo.cpu.architecture == 'amd64') {
      osLabel = clientInfo.os.name+" "+clientInfo.cpu.architecture;
      filename = '  Standalone PsychoPy '+version+' for 64bit Windows (using Python3.6)';
      url = 'https://github.com/psychopy/psychopy/releases/download/'+version+'/StandalonePsychoPy3-'+version+'-win64.exe';
    }
    else if (navigator.platform == 'Win32') {
      filename = '  Standalone PsychoPy '+version+' for 32bit Windows (using Python3.6)';
      url = 'https://github.com/psychopy/psychopy/releases/download/'+version+'/StandalonePsychoPy3-'+version+'-win32.exe';
    }
    else if (navigator.platform == 'MacIntel') {
      osLabel = clientInfo.os.name+" "+clientInfo.os.version;
      filename = '  Standalone PsychoPy '+version+' for MacOS';
      url = 'https://github.com/psychopy/psychopy/releases/download/'+version+'/StandalonePsychoPy3-'+version+'-MacOS.dmg';
    }
    else {
      osLabel = clientInfo.os.name+" ("+clientInfo.cpu.architecture+")";
      filename = 'installing using pip';
      url = '#linux';
    }

    document.write( "<br><center>To install PsychoPy on <strong>"+osLabel+"</strong> we recommend<br>");
    document.write( "<button class='btn-primary btn-lg' onclick='window.location.href=url'>" +
        "<i class='fa fa-download'></i>" + filename + "</button></center><br>" );

   </script>

**For all versions** see the `PsychoPy releases on github <https://github.com/psychopy/psychopy/releases>`_

.. _manual_install:

Manual installations
---------------------

See below for options if you don't want to use the Standalone releases:

* :ref:`pip_install`
* :ref:`brew_install`
* :ref:`linux_install`
* :ref:`conda`
* :ref:`developers_install`

.. _pip_install:

pip install
~~~~~~~~~~~~~~~~~

Now that most python libraries can be installed using `pip` it's relatively easy
to manually install PsychoPy and all it's dependencies to your own installation
of Python.

The steps are to fetch Python. This method should work on any version of Python
but we recommend Python 3.6 for now.

You can install PsychoPy and its dependencies (more than you'll strictly need)
by::

  pip install psychopy

If you prefer *not* to install *all* the dependencies then you could do::

  pip install psychopy --no-deps

and then install them manually.

.. _brew_install:

brew install
~~~~~~~~~~~~~~~~~

On a MacOS machine, `brew` can be used to install PsychoPy::

  brew cask install psychopy

.. _linux_install:

Linux
~~~~~~~~~~~~~~~~~

There used to be neurodebian and Gentoo packages for PsychoPy but these are both
badly outdated. We'd recommend you do:

.. code-block:: bash

    # with --no-deps flag if you want to install dependencies manually
    pip install psychopy

**Then fetch a wxPython wheel** for your platform from:

https://extras.wxpython.org/wxPython4/extras/linux/gtk3/

and having downloaded the right wheel you can then install it with something like:

.. code-block:: bash

  pip install path/to/your/wxpython.whl

wxPython>4.0 and doesn't have universal wheels yet which is why you have to
find and install the correct wheel for your particular flavor of linux.

**Building Python PsychToolbox bindings:**

The PsychToolbox bindings for Python provide superior timing for sounds and
keyboard responses. Unfortunately we haven't been able to build universal wheels
for these yet so you may have to build the pkg yourself. That should not be hard.
You need the necessary dev libraries installed first:

.. code-block:: bash

    sudo apt-get install libusb-1.0-0-dev portaudio19-dev libasound2-dev

and then you should be able to install using pip and it will build the extensions
as needed:

    pip install psychtoolbox


.. _conda:

Anaconda and Miniconda
~~~~~~~~~~~~~~~~~~~~~~

We provide an `environment file <https://raw.githubusercontent.com/psychopy/psychopy/master/conda/psychopy-env.yml>`_
that can be used to install PsychoPy and its dependencies. Download the file,
open your terminal, navigate to the directory you saved the file to, and run::

  conda env create -n psychopy -f psychopy-env.yml

This will create an environment named ``psychopy``. On Linux, the ``wxPython`` dependency of PsychoPy is linked
against ``webkitgtk``, which needs to be installed manually, e.g. via ``sudo apt install libwebkitgtk-1.0`` on Debian-based
systems linke Ubuntu.

To activate the newly-created environment and run PsychoPy, exceute::

  conda activate psychopy
  psychopy

.. _developers_install:


Developers install
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

.. _hardware:

Recommended hardware
---------------------------

The minimum requirement for PsychoPy is a computer with a graphics card that
supports OpenGL. Many newer graphics cards will work well. Ideally the graphics
card should support OpenGL version 2.0 or higher. Certain visual functions run
much faster if OpenGL 2.0 is available, and some require it (e.g. ElementArrayStim).

If you already have a computer, you can install PsychoPy and the Configuration
Wizard will auto-detect the card and drivers, and provide more information. It
is inexpensive to upgrade most desktop computers to an adequate graphics card.
High-end graphics cards can be very expensive but are only needed for very
intensive use.

Generally NVIDIA and ATI (AMD) graphics chips have higher performance than
Intel graphics chips so try and get one of those instead.

Notes on OpenGL drivers
~~~~~~~~~~~~~~~~~~~~~~~~

On Windows, if you get an error saying
**"pyglet.gl.ContextException: Unable to share contexts"** then the most likely
cause is that you need OpenGL drivers and your built-in Windows only has limited
support for OpenGL (or possibly you have an Intel graphics card that isn't very
good). Try installing new drivers for your graphics card **from its
manufacturer's web page,** not from Microsoft. For example, NVIDIA provides
drivers for its cards here: https://www.nvidia.com/Download/index.aspx
