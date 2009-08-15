Glossary
===========

.. glossary::
    
    csv
        Type of basic text file with 'comma-separated values'. This type of file can be opened with most spreadsheet packages (e.g. MS Excel) for easy reading and manipulation
    
    VBI
        Vertical Blank Interval. (aka the Vertical Retrace, or Vertical Blank, VBL). The period in-between video frames and can be used for synchronising purposes. On a CRT display the screen is black during the VBI and the display beam is returned to the top of the display
    
    VBI blocking
        The setting whereby all functions are synced to the VBI. After a call to :meth:`psychopy.visual.Window.flip()` nothing else occurs until the VBI has occurred. This is optimal and allows very precise timing, because as soon as the flip has occured a very precise time interval is known to have occured.
    
    VBI syncing
        (aka vsync)
        The setting whereby the video drawing commands are synced to the VBI. When psychopy.visual.Window.flip() is called, the current back buffer (where drawing commands are being executed) will be held and drawn on the next VBI. This does not necessarily entail :term:`VBI blocking` (because the system may return and continue executing commands) but does guarantee a fixed inteval between frames being drawn.