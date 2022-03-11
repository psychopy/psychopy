.. _aperture:

Aperture Component
-------------------------------

This component can be used to filter the visual display, as if the subject is looking at it through an opening (i.e. add an image component, as the background image, then add an aperture to show part of the image). Currently, in builder, only circular apertures are supported (you can change the shape by specifying your aperture in a code component- we are hoping to make it easier to do this through builder soon!). Moreover, only one aperture is enabled at a time. You can't "double up": a second aperture takes precedence. Currently this component **does not run online**  (`see the status of online options <https://www.psychopy.org/online/status.html>`_, but you can achieve something similar online using an image with a mask: see an `example demo here <https://run.pavlovia.org/demos/dynamic_selective_inspect/html/>`_ with corresponding `PsychoPy experiment files here <https://gitlab.pavlovia.org/demos/dynamic_selective_inspect>`_ or by using the `MouseView plugin <https://run.pavlovia.org/demos/mouseview_demo/>`_.

.. only:: html

    .. image:: /images/aperture.gif
        :width: 60%

Basic
======

name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
start : float or integer
    The time that the aperture should start having its effect. See :ref:`startStop` for details.

expected start(s) :
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.

stop : 
    When the aperture stops having its effect. See :ref:`startStop` for details.

expected duration(s) :
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.


Layout
======

How should the stimulus be laid out? Padding, margins, size, position, etc.

size : integer
    The size controls how big the aperture will be, in pixels, default = 120

pos : [X,Y]
    The position of the centre of the aperture, in the units specified by the stimulus or window.

.. note::
    Top tip: You can make an aperture (or anything!) track the position of your mouse by adding a mouse component, then setting the position of your aperture to be :code:`mouse.getPos()` (and *set every frame*), where "mouse" corresponds to the name of your mouse component.

spatial units :
    What units to use.


.. seealso::
	
	API reference for :class:`~psychopy.visual.Aperture`
