.. _aperturecomponent:

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

The required attributes of the stimulus, controlling its basic function and behaviour


.. _aperturecomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _aperturecomponent-startVal:
Start
    When the Aperture Component should start, see :ref:`startStop`.
    
.. _aperturecomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _aperturecomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _aperturecomponent-stopVal:
Stop
    When the Aperture Component should stop, see :ref:`startStop`.
    
.. _aperturecomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _aperturecomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _aperturecomponent-shape:
Shape
    What shape is this? With 'regular polygon...' you can set number of vertices and with 'custom polygon...' you can set vertices
    
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
    
.. _aperturecomponent-nVertices:
Num. vertices
    How many vertices in your regular polygon?
    
.. _aperturecomponent-vertices:
Vertices
    What are the vertices of your polygon? Should be an nx2 array or a list of [x, y] lists
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _aperturecomponent-size:
Size
    How big is the aperture? (a single number for diameter)
    
.. _aperturecomponent-pos:
Position [x,y]
    Where is the aperture centred?
    
.. _aperturecomponent-units:
Spatial units
    Spatial units for this stimulus (e.g. for its :ref:`position <aperturecomponent-pos>` and :ref:`size <aperturecomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _aperturecomponent-anchor:
Anchor
    Which point in this stimulus should be anchored to the point specified by :ref:`aperturecomponent-pos`? 
    
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
    
.. _aperturecomponent-ori:
Orientation
    Orientation of this stimulus (in deg)
    
    Options:
    
    * -360
    
    * 360
    
.. _aperturecomponent-draggable:
Draggable?
    Should this stimulus be moveble by clicking and dragging?
    
Data
===============================

What information about this Component should be saved?


.. _aperturecomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _aperturecomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _aperturecomponent-disabled:
Disable Component
    Disable this Component
    
.. _aperturecomponent-validator:
Validate with...
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.


.. seealso::
	
	API reference for :class:`~psychopy.visual.Aperture`    