
Overview
=====================================

PsychoPy is an open-source package for running experiments in `Python`_ (a real and free alternative to Matlab). PsychoPy combines the graphical strengths of OpenGL with the easy Python syntax to give scientists a free and simple stimulus presentation and control package. It is used by many labs worldwide for psychophysics, cognitive neuroscience and experimental psychology.

Because it's open source, you can download it and modify the package if you don't like it. And if you make changes that others might use then please consider giving them back to the community via the mailing list. PsychoPy has been written and provided to you absolutely for free. For it to get better it needs as much input from everyone as possible.

Features
----------------
There are many advantages to using PsychoPy, but here are some of the key ones

    - Simple install process
    - Huge variety of stimuli (see screenshots) generated in real-time:
        - linear gratings, bitmaps constantly updating
        - radial gratings
        - random dots
        - movies (DivX, mov, mpg...)
        - text (unicode in any truetype font)
        - shapes
        - sounds (tones, numpy arrays, wav, ogg...)
    - Platform independent - run the same script on Win, OS X or Linux
    - Flexible :ref:`stimulus units <units>` (degrees, cm, or pixels)
    - :ref:`coder` interface for those that like to program
    - :ref:`builder` interface for those that don't
    - Input from keyboard, mouse or button boxes
    - Multi-monitor support
    - Automated monitor calibration (requires PR650 or Minolta LS110)

Hardware Integration
---------------------
PsychoPy supports communication via serial ports, parallel ports and compiled drivers (dlls and dylibs), so it can talk to any hardware that your computer can! Interfaces are prebuilt for;
    - Spectrascan PR650
    - Minolta LS110
    - Cambridge Research Systems Bits++
    - Cedrus response boxes (RB7xx series)

System requirements
----------------------
Although PsychoPy runs on a wide variety of hardware, and on Windows, OS X or Linux, it really does benefit from a decent graphics card. Get an ATI or nVidia card that supports OpenGL 2.0. *Avoid built-in Intel graphics chips (e.g. GMA 950)*

How to cite PsychoPy
----------------------
A couple of papers have been written about PsychoPy already. Please cite them if you use the software.

       1. Peirce, JW (2007) PsychoPy - Psychophysics software in Python. `J Neurosci Methods, 162(1-2):8-13 <http://www.sciencedirect.com/science?_ob=ArticleURL&_udi=B6T04-4MWGYDH-1&_user=5939061&_rdoc=1&_fmt=&_orig=search&_sort=d&_docanchor=&view=c&_acct=C000009959&_version=1&_urlVersion=0&_userid=5939061&md5=4a09e4ec5b516e9220a1fa5bc3f8f10c>`_
       2. Peirce JW (2009) Generating stimuli for neuroscience using PsychoPy. `Front. Neuroinform. 2:10. doi:10.3389/neuro.11.010.2008 <http://www.frontiersin.org/neuroinformatics/paper/10.3389/neuro.11/010.2008/>`_
       
Help PsychoPy
----------------------
PsychoPy is an open-source, community-driven project. It is written and provided free out of goodwill by people that make no money from it and have other jobs to do. The way that open-source projects work is that users contribute back some of their time. If you can improve PsychoPy, either by;

    * fixing incorrect or unclear documentation - just email some improved text
    * fixing a minor bug in the code
    * writing a little feature that can be added
    * if nothing else, then at least tell the primary developers that a bug exists - they likely don't know!
    
For more information on how to view and edit the documentation and code see the section on :doc:`contributing`

.. _Python: http://www.python.org