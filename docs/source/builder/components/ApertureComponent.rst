.. _aperture:

-------------------------------
Aperture Component
-------------------------------

.. only:: html

    .. image:: /images/aperture.gif
        :width: 60%

This component can be used to filter the visual display, as if the subject is looking at it through an opening (i.e. add an image component, as the background image, then add an aperture to show part of the image). Currently, in builder, only circular apertures are supported (you can change the shape by specifying your aperture in a code component- we are hoping to make it easier to do this through builder soon!). Moreover, only one aperture is enabled at a time. You can't "double up": a second aperture takes precedence. Currently this component **does not run online**  (`see the status of online options <https://www.psychopy.org/online/status.html>`_, but you can achieve something similar online using an image with a mask: see an `example demo here <https://run.pavlovia.org/demos/dynamic_selective_inspect/html/>`_ with corresponding `PsychoPy experiment files here <https://gitlab.pavlovia.org/demos/dynamic_selective_inspect>`_ or by using the `MouseView plugin <https://run.pavlovia.org/demos/mouseview_demo/>`_.

Categories:
    Stimuli
Works in:
    PsychoPy

Parameters
-------------------------------

Basic
===============================

Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
Start
    The time that the aperture should start having its effect. See :ref:`startStop` for details.

Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.

Stop
    When the aperture stops having its effect. See :ref:`startStop` for details.

Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.

Shape
    What shape is this? With 'regular polygon...' you can set number of vertices and with 'custom polygon...' you can set vertices
    
    Options:
    - Line
    - Triangle
    - Rectangle
    - Circle
    - Cross
    - Star
    - Arrow
    - Regular polygon...
    - Custom polygon...

Num. vertices
    How many vertices in your regular polygon?

Vertices
    What are the vertices of your custom polygon? Should be an nx2 array or a list of [x, y] lists

Layout
===============================

How should the stimulus be laid out? Padding, margins, size, position, etc.

Spatial units
    Units of dimensions for this stimulus
    
    Options:
    - from exp settings
    - deg
    - cm
    - pix
    - norm
    - height
    - degFlatPos
    - degFlat

Position [x,y]
    Where is the aperture centred?

Size
    How big is the aperture? (a single number for diameter)

Orientation
    Orientation of this stimulus (in deg)
    
    Options:
    - -360
    - 360

Anchor
    Which point on the aperture should be anchored to its exact position?
    
    Options:
    - center
    - top-center
    - bottom-center
    - center-left
    - center-right
    - top-left
    - top-right
    - bottom-left
    - bottom-right

Data
===============================

Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).

Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)

Testing
===============================

Disable Component
    Disable this Component

Validate with...
    Name of validator Component/Routine to use to check the timing of this stimulus.

    Options are generated live, so will vary according to your setup.


.. seealso::
	
	API reference for :class:`~psychopy.visual.Aperture`
