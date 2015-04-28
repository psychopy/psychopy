.. _mouse:

Mouse Component
-------------------------------

The Mouse component can be used to collect responses from a participant. The coordinates of the mouse location are 
given in the same coordinates as the Window, with (0,0) in the centre.

Scenarios
~~~~~~~~~~~~~~~~~

This can be used in various ways. Here are some scenarios (email the list if you have other uses for your mouse):

Use the mouse to record the location of a button press

Use the mouse to control stimulus parameters
    Imagine you want to use your mouse to make your 'patch'_ bigger or smaller and save the final size.
    Call your `mouse`_ 'mouse', set it to save its state at the end of the trial and set the button press to
    end the Routine. Then for the size setting of your Patch stimulus insert `$mouse.getPos()[0]` to use the 
    x position of the mouse to control the size or `$mouse.getPos()[1]` to use the y position.
    
Tracking the entire path of the mouse during a period

Parameters
~~~~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

start : 
    The time that the mouse should first be checked. See :ref:`startStop` for details.

stop : 
    When the mouse is no longer checked. See :ref:`startStop` for details.
    
Force End Routine on Press
    If this box is checked then the :ref:`Routine <Routines>` will end as soon as one of the mouse buttons is pressed.

Save Mouse State
    How often do you need to save the state of the mouse? Every time the subject presses a mouse button, at the end of the trial, or every single frame?
    Note that the text output for cases where you store the mouse data repeatedly per trial (e.g. every press or every frame) is likely to be very hard to interpret, so you may then need to analyse your data using the psydat file (with python code) instead.
    Hopefully in future releases the output of the text file will be improved.

Time Relative To
    Whenever the mouse state is saved (e.g. on button press or at end of trial) a time is saved too. Do you want this time to be relative to start of the :ref:`Routine <Routines>`, or the start of the whole experiment?
        
.. seealso::
    
    API reference for :mod:`~psychopy.event.Mouse`
     
