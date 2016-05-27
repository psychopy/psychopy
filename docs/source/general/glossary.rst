.. _glossary:

Glossary
===========

.. glossary::
    :sorted:
    
    csv
        **Comma-Separated Value files** Type of basic text file with 'comma-separated values'. This type of file can be opened with most spreadsheet packages (e.g. MS Excel) for easy reading and manipulation.

    VBI
        (**Vertical Blank Interval**, aka the Vertical Retrace, or Vertical Blank, VBL).
        The period in-between video frames and can be used for synchronising purposes. On a CRT display the screen is black during the VBI and the display beam is returned to the top of the display.
    
    VBI blocking
        The setting whereby all functions are synced to the VBI. After a call to :meth:`psychopy.visual.Window.flip()` nothing else occurs until the VBI has occurred. This is optimal and allows very precise timing, because as soon as the flip has occurred a very precise time interval is known to have occurred.
    
    VBI syncing
        (aka vsync)
        The setting whereby the video drawing commands are synced to the VBI. When psychopy.visual.Window.flip() is called, the current back buffer (where drawing commands are being executed) will be held and drawn on the next VBI. This does not necessarily entail :term:`VBI blocking` (because the system may return and continue executing commands) but does guarantee a fixed interval between frames being drawn.

    Method of constants
        An experimental method whereby the parameters controlling trials are predetermined at the beginning of the experiment, rather than determined on each trial. For example, a stimulus may be presented for 3 pre-determined time periods  (100, 200, 300ms) on different trials, and then repeated a number of times. The order of presentation of the different conditions can be randomised or sequential (in a fixed order). Contrast this method with the :term:`adaptive staircase`.

    Adaptive staircase
        An experimental method whereby the choice of stimulus parameters is not pre-determined but based on previous responses. For example, the difficulty of a task might be varied trial-to-trial based on the participant's responses. These are often used to find psychophysical thresholds. Contrast this with the :term:`method of constants`.

    CRT
        **Cathode Ray Tube**
        'Traditional' computer monitor (rather than an LCD or plasma flat screen).

    xlsx
        **Excel OpenXML file format**. A spreadsheet data format developed by Microsoft but with an open (published) format. This is the native file format for Excel (2007 or later) and can be opened by most modern spreadsheet applications including OpenOffice (3.0+), google docs, Apple iWork 08.

    GPU
        **Graphics Processing Unit** is the processor on your graphics card. The GPUs of modern computers are incredibly powerful and it is by allowing the GPU to do a lot of the work of rendering that PsychoPy is able to achieve good timing precision despite being written in an interpreted language

    CPU
        **Central Processing Unit** is the main processor of your computer. This has a lot to do, so we try to minimise the amount of processing that is needed, especially during a trial, when time is tight to get the stimulus presented on every screen refresh.
