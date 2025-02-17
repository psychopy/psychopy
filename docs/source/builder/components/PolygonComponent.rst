.. _polygoncomponent:

-------------------------------
Polygon Component
-------------------------------

The Polygon stimulus allows you to present a wide range of regular geometric shapes. The basic control comes from setting the number of vertices:
    - 2 vertices give a line
    - 3 give a triangle
    - 4 give a rectangle etc.
    - a large number will approximate a circle/ellipse

The size parameter takes two values. For a line only the first is used (then use ori to specify the orientation). For triangles and rectangles the size specifies the height and width as expected. Note that for pentagons upwards, however, the size determines the width/height of the ellipse on which the vertices will fall, rather than the width/height of the vertices themselves (slightly smaller typically).

Categories:
    Stimuli
Works in:
    PsychoPy, PsychoJS

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _polygoncomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _polygoncomponent-startVal:
Start 
    When the Polygon Component should start, see :ref:`startStop`.
    
.. _polygoncomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _polygoncomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _polygoncomponent-stopVal:
Stop 
    When the Polygon Component should stop, see :ref:`startStop`.
    
.. _polygoncomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _polygoncomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _polygoncomponent-shape:
Shape 
    What shape is this?
    
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
    
.. _polygoncomponent-nVertices:
Num. vertices (*if :ref:`polygoncomponent-shape` is "Regular polygon..."*)
    How many vertices in your regular polygon?
    
.. _polygoncomponent-vertices:
Vertices (*if :ref:`polygoncomponent-shape` is "custom polygon..."*)
    What are the vertices of your polygon? Should be an nx2 array or a list of [x, y] lists
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _polygoncomponent-size:
Size [w,h] 
    Size of this stimulus [w,h]. Note that for a line only the first value is used, for triangle and rect the [w,h] is as expected, but for higher-order polygons it represents the [w,h] of the ellipse that the polygon sits on!! 
    
.. _polygoncomponent-pos:
Position [x,y] 
    Position of this stimulus (e.g. [1,2] )
    
.. _polygoncomponent-units:
Spatial units 
    Spatial units for this stimulus (e.g. for its :ref:`position <polygoncomponent-pos>` and :ref:`size <polygoncomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _polygoncomponent-anchor:
Anchor (*if :ref:`polygoncomponent-shape` isn't =='line'*)
    Which point in this stimulus should be anchored to the point specified by :ref:`polygoncomponent-pos`? 
    
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
    
.. _polygoncomponent-ori:
Orientation 
    Orientation of this stimulus (in deg)
    
    Options:
    
    * -360
    
    * 360
    
.. _polygoncomponent-draggable:
Draggable? 
    Should this stimulus be moveble by clicking and dragging?
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _polygoncomponent-fillColor:
Fill color 
    Fill color of this stimulus (e.g. $[1,1,0], red )
    
.. _polygoncomponent-lineColor:
Border color 
    Border color of this stimulus (e.g. $[1,1,0], red )
    
.. _polygoncomponent-colorSpace:
Color space 
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _polygoncomponent-opacity:
Opacity 
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _polygoncomponent-contrast:
Contrast 
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
.. _polygoncomponent-lineWidth:
Line width 
    Width of the shape's line (always in pixels - this does NOT use 'units')
    
Texture
===============================

Control how the stimulus handles textures.


.. _polygoncomponent-interpolate:
Interpolate 
    How should the image be interpolated if/when rescaled
    
    Options:
    
    * linear
    
    * nearest
    
Data
===============================

What information about this Component should be saved?


.. _polygoncomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _polygoncomponent-syncScreenRefresh:
Sync timing with screen refresh 
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _polygoncomponent-disabled:
Disable Component 
    Disable this Component
    
.. _polygoncomponent-validator:
Validate with... 
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.


.. seealso::

	API reference for :class:`~psychopy.visual.Polygon`
	API reference for :class:`~psychopy.visual.Rect`
	API reference for :class:`~psychopy.visual.ShapeStim`
    