.. _staticcomponent:

-------------------------------
Static Component
-------------------------------

The Static Component allows you to have a period where you can preload images or perform other time-consuming operations
that not be possible while the screen is being updated. Static periods are also particularly useful for *online* studies to decrease the time taken to load resources at the start (see also :ref:`resourceManager`).

.. note:: For online studies, if you use a static component this will override the resources loaded at the beginning via Experiment settings > Online > Additional resources. You might therefore want to combine a static period with a :ref:`resourceManager` to make sure that all resources your study needs will be loaded and available for the experiment.

Typically a static period would be something like an inter-trial or inter-stimulus interval (ITI/ISI). During this period you should not have any other objects being presented that are being updated (this isn't checked for you - you have to make that check yourself), but you can have components being presented that are themselves static. For instance a fixation point never changes and so it can be presented during the static period (it will be presented and left on-screen while the other updates are being made).

.. figure:: /images/static_guide.png

	How to use a static component. 1) To use a static component first select it from the component panel. 2) highlights in red the time window you are treating as "static". If you click on the red highlighted window you can edit the static component. 3) To use the static window to load a resource, select the component where the resource will be load, and in the dropdown window choose "set during:trial.ISI" - here "trial" refers to the routine where the static component is and "ISI" refers to the name of the static component.

Any stimulus updates can be made to occur during any static period defined in the experiment (it does not have to be in the same Routine). This is done in the updates selection box- once a static period exists it will show up here as well as the standard options of `constant` and `every repeat` etc. Many parameter updates (e.g. orientation are made so quickly that using the static period is of no benefit but others, most notably the loading of images from disk, can take substantial periods of time and these should always be performed during a static period to ensure good timing.

If the updates that have been requested were not completed by the end of the static period (i.e. there was a timing overshoot) then you will receive a warning to that effect. In this case you either need a longer static period to perform the actions or you need to reduce the time required for the action (e.g. use an image with fewer pixels).

Categories:
    Custom
Works in:
    PsychoPy, PsychoJS


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _staticcomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _staticcomponent-startVal:
Start 
    When the Static Component should start, see :ref:`startStop`.
    
.. _staticcomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _staticcomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _staticcomponent-stopVal:
Stop 
    When the Static Component should stop, see :ref:`startStop`.
    
.. _staticcomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _staticcomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
Data
===============================

What information about this Component should be saved?


.. _staticcomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _staticcomponent-syncScreenRefresh:
Sync timing with screen refresh 
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Custom
===============================

Parameters for injecting custom code


.. _staticcomponent-code:
Custom code 
    After running the component updates (which are defined in each component, not here) any code inserted here will also be run
    
.. _staticcomponent-saveData:
Save data during 
    While the frame loop is paused, should we take the opportunity to save data now? This is only relevant locally, online data saving is either periodic or on close.
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _staticcomponent-disabled:
Disable Component 
    Disable this Component


.. seealso::

    API reference for :class:`~psychopy.clock.StaticPeriod`