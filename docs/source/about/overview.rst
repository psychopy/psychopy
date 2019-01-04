
Overview
=====================================

PsychoPy is an open-source package for running experiments in `Python`_ (a real and free alternative to Matlab). PsychoPy combines the graphical strengths of OpenGL with the easy Python syntax to give scientists a free and simple stimulus presentation and control package. It is used by many labs worldwide for psychophysics, cognitive neuroscience and experimental psychology.

Because it's open source, you can download it and modify the package if you don't like it. And if you make changes that others might use then please consider giving them back to the community via the mailing list. PsychoPy has been written and provided to you absolutely for free. For it to get better it needs as much input from everyone as possible.

Features
----------------
There are many advantages to using PsychoPy, but here are some of the key ones

- Simple install process
- Precise timing
- Huge variety of stimuli (see screenshots) generated in real-time:
    - linear gratings, bitmaps constantly updating
    - radial gratings
    - random dots
    - movies (DivX, mov, mpg...)
    - text (unicode in any truetype font)
    - shapes
    - sounds (tones, numpy arrays, wav, ogg...)
- Platform independent - run the same script on Win, macOS or Linux
- Flexible :ref:`stimulus units <units>` (degrees, cm, or pixels)
- :ref:`coder` interface for those that like to program
- :ref:`builder` interface for those that don't
- Input from keyboard, mouse, microphone or button boxes
- Multi-monitor support
- Automated monitor calibration (for supported photometers)

Hardware Integration
---------------------
PsychoPy supports communication via serial ports, parallel ports and compiled drivers (dlls and dylibs), so it can talk to any hardware that your computer can! Interfaces are prebuilt for:

- Spectrascan PR650, PR655, PR670
- Minolta LS110, LS100
- Cambridge Research Systems Bits++
- Cedrus response boxes (RB7xx series)

System requirements
----------------------
Although PsychoPy runs on a wide variety of hardware, and on Windows, macOS or Linux, it really does benefit from a decent graphics card. Get an ATI or nVidia card that supports OpenGL 2.0. *Avoid built-in Intel graphics chips (e.g. GMA 950)*

.. _Python: http://www.python.org
