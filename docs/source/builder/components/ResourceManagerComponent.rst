.. _resourcemanagercomponent:

-------------------------------
Resource Manager Component
-------------------------------

Pre-load resources into memory so that components using them can start without having to load first.

**This component is only relevant to online studies. If you use this component it will override loading of resources at the beginning of the experiment. This means that any resources specified in the Experiment Settings > Online > Additional Resources will not be used, make sure to load all required resources within the experiment**.

Most experiments need "resources" in order to run. Be it images, sounds, spreadsheets or movies. When running a study online through `pavlovia.org <https://pavlovia.org/>`_, these resources are loaded by default at the beginning of the experiment, and you will usually see a loading bar.

.. only:: html

    .. image:: /images/load_gif.gif
        :width: 60%

However, sometimes this loading can take a pretty long time. This happens either because you have a very large number of resources or because individual files are large (e.g. long movies) . In cases like this, it may be preferred to load these within your experiment, for example whilst your participants are reading through the instructions, in an inter-trial interval or during a break between blocks. This is where the *Resource Manager* component and/or the :ref:`staticcomponent` come in.

You can find the Resource Manager under "Custom" in the Component Panel. The component has many properties similar to any other component, a start time, a duration etc. The most important fields in the component are **Resources**, indicating the list of resources to load, and **Preload Actions**, indicating if we are initiating loading (Start), checking previously initiated loading has completed (Check), or both (Start and Check). For experiments where we might have several resource manager components, we can also check if the resources from *all* components currently exist in memory by selecting "Check All".

.. image:: /images/resource_manager.png
        :width: 60%

Categories:
    Custom
Works in:
    PsychoJS

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Examples
-------------------------------

Loading resources in the background of instructions
===============================
A common use case for resource manager might be to load resources in the background of instructions (or any routine!), and only let your participants move forward when the resources are loaded. To do this:

1. Add a resource manager component.
2. Populate the resources field with the resources to be loaded.
3. Set *Preload Actions* to *Start and Check*.
4. Add a code component and use this in the "Each Frame" tab (where "resources" refers to the name of your resource manager component)::

    if resources.status == FINISHED:
        continueRoutine = False


5. Alternatively to step 4, you might want to have an image or text that is clickable, but have *Start* set to :code:`resources.status == FINISHED`. This will make the button "pop-up" when the resources have finished loading!

.. note:: The resource manager has an attribute "status" and we can check if it has finished using `resources.status == FINISHED` (where *resources* corresponds to the name of your resource manager component).

Loading resources for blocked or branched designs, or loading trial-by-trial
===============================

Sometimes we might have a design where participants only need to be presented with a subset of resources. We might have 100 movies, but group 1 sees 50 movies and group 2 sees the other 50. In cases like this you might ask "How to I make the resources in my resource manager conditional?". Well, for designs like this we actually recommend you use something a little different, the :ref:`staticcomponent` - so check it out!.

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _resourcemanagercomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _resourcemanagercomponent-startVal:
Start 
    When the Resource Manager Component should start, see :ref:`startStop`.
    
.. _resourcemanagercomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _resourcemanagercomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _resourcemanagercomponent-stopVal:
Check 
    When the Resource Manager Component should stop, see :ref:`startStop`.
    
.. _resourcemanagercomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _resourcemanagercomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _resourcemanagercomponent-resources:
Resources 
    Resources to download/check
    
.. _resourcemanagercomponent-checkAll:
Check all 
    When checking these resources, also check for all currently downloading?
    
.. _resourcemanagercomponent-actionType:
Preload actions 
    Should this Component start an / or check resource preloading?
    
    Options:
    
    * Start and Check
    
    * Start Only
    
    * Check Only
    
.. _resourcemanagercomponent-forceEndRoutine:
Force end Routine 
    Should we end the Routine when the resource download is complete?
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _resourcemanagercomponent-disabled:
Disable Component 
    Disable this Component
    