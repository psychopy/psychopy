.. _mousecomponent:

-------------------------------
Mouse Component
-------------------------------

The Mouse component can be used to collect responses from a participant. The coordinates of the mouse location are 
given in the same coordinates as the Window, with (0,0) in the centre.

Categories:
    Responses
Works in:
    PsychoPy, PsychoJS

Scenarios
-------------------------------

This can be used in various ways. Here are some scenarios (email the list if you have other uses for your mouse):

Use the mouse to record the location of a button press

Use the mouse to control stimulus parameters
    Imagine you want to use your mouse to make your 'patch'_ bigger or smaller and save the final size.
    Call your :ref:`mousecomponent` 'mouse', set it to save its state at the end of the trial and set the button press to
    end the Routine. Then for the size setting of your Patch stimulus insert `$mouse.getPos()[0]` to use the 
    x position of the mouse to control the size or `$mouse.getPos()[1]` to use the y position.
    
Tracking the entire path of the mouse during a period

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _mousecomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _mousecomponent-startVal:
Start
    When the Mouse Component should start, see :ref:`startStop`.
    
.. _mousecomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _mousecomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _mousecomponent-stopVal:
Stop
    When the Mouse Component should stop, see :ref:`startStop`.
    
.. _mousecomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _mousecomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _mousecomponent-forceEndRoutineOnPress:
End Routine on press
    Should a button press force the end of the Routine (e.g end the trial)?
    
    Options:
    
    * never
    
    * any click
    
    * valid click
    
    * correct click
    
.. _mousecomponent-newClicksOnly:
New clicks only
    If the mouse button is already down when we start checking then wait for it to be released before recording as a new click.
    
.. _mousecomponent-clickable:
Clickable stimuli
    A comma-separated list of your stimulus names that can be "clicked" by the participant. e.g. target, foil
    
Data
===============================

What information about this Component should be saved?


.. _mousecomponent-saveMouseState:
Save mouse state
    How often should the mouse state (x,y,buttons) be stored? On every video frame, every click or just at the end of the Routine?
    
    Options:
    
    * final
    
    * on click
    
    * on valid click
    
    * every frame
    
    * never
    
.. _mousecomponent-timeRelativeTo:
Time relative to
    What should the values of mouse.time should be relative to?
    
    Options:
    
    * mouse onset
    
    * experiment
    
    * routine
    
.. _mousecomponent-saveParamsClickable:
Store params for clicked
    The params (e.g. name, text), for which you want to store the current value, for the stimulus that was"clicked" by the mouse. Make sure that all the clickable objects have all these params.
    
.. _mousecomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _mousecomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
.. _mousecomponent-storeCorrect:
Store correct
    Do you want to save the response as correct/incorrect?
    
.. _mousecomponent-correctAns:
Correct answer
    What is the 'correct' object? To specify an area, remember that you can create a shape Component with 0 opacity.
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _mousecomponent-disabled:
Disable Component
    Disable this Component
    