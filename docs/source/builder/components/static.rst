.. _static:

Static Component
=================

(Added in Version 1.78.00. Made compatible for online use version 2022.1)

The Static Component allows you to have a period where you can preload images or perform other time-consuming operations
that not be possible while the screen is being updated. Static periods are also particularly useful for *online* studies to decrease the time taken to load resources at the start (see also :ref:`resourceManager`).

.. note:: For online studies, if you use a static component this will override the resources loaded at the beginning via Experiment settings > Online > Additional resources. You might therefore want to combine a static period with a :ref:`resourceManager` to make sure that all resources your study needs will be loaded and available for the experiment.

Typically a static period would be something like an inter-trial or inter-stimulus interval (ITI/ISI). During this period you should not have any other objects being presented that are being updated (this isn't checked for you - you have to make that check yourself), but you can have components being presented that are themselves static. For instance a fixation point never changes and so it can be presented during the static period (it will be presented and left on-screen while the other updates are being made).

.. figure:: /images/static_guide.png

	How to use a static component. 1) To use a static component first select it from the component panel. 2) highlights in red the time window you are treating as "static". If you click on the red highlighted window you can edit the static component. 3) To use the static window to load a resource, select the component where the resource will be load, and in the dropdown window choose "set during:trial.ISI" - here "trial" refers to the routine where the static component is and "ISI" refers to the name of the static component.

Any stimulus updates can be made to occur during any static period defined in the experiment (it does not have to be in the same Routine). This is done in the updates selection box- once a static period exists it will show up here as well as the standard options of `constant` and `every repeat` etc. Many parameter updates (e.g. orientation are made so quickly that using the static period is of no benefit but others, most notably the loading of images from disk, can take substantial periods of time and these should always be performed during a static period to ensure good timing.

If the updates that have been requested were not completed by the end of the static period (i.e. there was a timing overshoot) then you will receive a warning to that effect. In this case you either need a longer static period to perform the actions or you need to reduce the time required for the action (e.g. use an image with fewer pixels).

Parameters
~~~~~~~~~~~~

name :
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

start :
    The time that the static period begins. See :ref:`startStop` for details.

stop :
    The time that the static period ends. See :ref:`startStop` for details.

Custom
======
Parameters for injecting custom code

custom code :
    After running the component updates (which are defined in each component, not here) any code inserted here will also be run

.. seealso::

    API reference for :class:`~psychopy.clock.StaticPeriod`