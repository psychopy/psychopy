.. _regionofinterestcomponent:

-------------------------------
Region Of Interest Component
-------------------------------

Record eye movement events occurring within a defined Region of Interest (ROI). Note that you will still need to add an Eyetracker Record component to this routine to save eye movement data.

Categories:
    Eyetracking
Works in:
    PsychoPy

**Note: Since this is still in beta, keep an *eye* (haha) out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _regionofinterestcomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _regionofinterestcomponent-startVal:
Start 
    When the Region Of Interest Component should start, see :ref:`startStop`.
    
.. _regionofinterestcomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _regionofinterestcomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _regionofinterestcomponent-stopVal:
Stop 
    When the Region Of Interest Component should stop, see :ref:`startStop`.
    
.. _regionofinterestcomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _regionofinterestcomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _regionofinterestcomponent-shape:
Shape 
    A shape to outline the Region of Interest, see :ref:`polygoncomponent`
    
    Options:
    
    * Line
    
    * Triangle
    
    * Rectangle
    
    * Circle
    
    * Cross
    
    * Star
    
    * Arrow
    
    * Regular polygon...
    
    * Custom polygon...
    
.. _regionofinterestcomponent-nVertices:
Num. vertices (*if :ref:`regionofinterestcomponent-shape` is "Regular polygon..."*)
    How many vertices in your regular polygon?
    
.. _regionofinterestcomponent-vertices:
Vertices (*if :ref:`regionofinterestcomponent-shape` is "Custom polygon..."*)
    What are the vertices of your polygon? Should be an nx2 array or a list of [x, y] lists
    
.. _regionofinterestcomponent-endRoutineOn:
End Routine on... 
    Under what condition should this ROI end the Routine?
    
    Options:
    
    * Look at: End the Routine when this ROI is looked at, for more than the :ref:`regionofinterestcomponent-lookDur`
    
    * Look away: End the Routine when this ROI is *not* looked at, for more than the :ref:`regionofinterestcomponent-lookDur`
    
    * None: This ROI will not end the Routine
    
.. _regionofinterestcomponent-lookDur:
Min. look time (*if :ref:`regionofinterestcomponent-endroutineon` isn't None*)
    Minimum dwell time within roi (look at) or outside roi (look away).
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _regionofinterestcomponent-size:
Size [w,h] 
    Size of this stimulus [w,h]. Note that for a line only the first value is used, for triangle and rect the [w,h] is as expected, but for higher-order polygons it represents the [w,h] of the ellipse that the polygon sits on!! 
    
.. _regionofinterestcomponent-pos:
Position [x,y] 
    Position of this stimulus (e.g. [1,2] )
    
.. _regionofinterestcomponent-units:
Spatial units 
    Spatial units for the ROI is fixed to the same units as the window.
    
.. _regionofinterestcomponent-anchor:
Anchor (*if :ref:`regionofinterestcomponent-shape` isn't "Line"*)
    Which point in this stimulus should be anchored to the point specified by :ref:`regionofinterestcomponent-pos`? 
    
    Options:
    
    * center
    
    * top-center
    
    * bottom-center
    
    * center-left
    
    * center-right
    
    * top-left
    
    * top-right
    
    * bottom-left
    
    * bottom-right
    
.. _regionofinterestcomponent-ori:
Orientation 
    Orientation of this stimulus (in deg)
    
    Options:
    
    * -360
    
    * 360
    
.. _regionofinterestcomponent-draggable:
Draggable? 
    Should this stimulus be moveble by clicking and dragging?
    
Data
===============================

What information about this Component should be saved?


.. _regionofinterestcomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _regionofinterestcomponent-syncScreenRefresh:
Sync timing with screen refresh 
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
.. _regionofinterestcomponent-save:
Save... 
    What looks on this ROI should be saved to the data output?
    
    Options:
    
    * first look
    
    * last look
    
    * every look
    
    * none
    
.. _regionofinterestcomponent-timeRelativeTo:
Time relative to... 
    What should the values of roi.time should be relative to?
    
    Options:
    
    * roi onset
    
    * experiment
    
    * routine
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _regionofinterestcomponent-disabled:
Disable Component 
    Disable this Component
    
.. _regionofinterestcomponent-validator:
Validate with... 
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.
    
.. _regionofinterestcomponent-debug:
Debug mode 
    In debug mode, the ROI is drawn in red. Use this to see what area of the screen is in the ROI.
    