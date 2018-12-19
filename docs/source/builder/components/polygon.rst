.. _polygonComponent:

Polygon (shape) Component
-------------------------------

(added in version 1.78.00)

The Polygon stimulus allows you to present a wide range of regular geometric shapes. The basic control comes from setting the number of vertices:
    - 2 vertices give a line
    - 3 give a triangle
    - 4 give a rectangle etc.
    - a large number will approximate a circle/ellipse

The size parameter takes two values. For a line only the first is used (then use ori to specify the orientation). For triangles and rectangles the size specifies the height and width as expected. Note that for pentagons upwards, however, the size determines the width/height of the ellipse on which the vertices will fall, rather than the width/height of the vertices themselves (slightly smaller typically).

Parameters
~~~~~~~~~~~~

name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

nVertices : integer

    The number of vertices for your shape (2 gives a line, 3 gives a triangle,... a large number results in a circle/ellipse).
    It is not (currently) possible to vary the number of vertices dynamically.

fill settings:

    Control the color inside the shape. If you set this to `None` then you will have a transparent shape (the line will remain)

line settings:

    Control color and width of the line. The line width is always specified in pixels - it does not honour the `units` parameter.

size : [w,h]
    See note above

start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

stop :
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

ori : degrees
    The orientation of the entire patch (texture and mask) in degrees.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window


units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`


.. seealso::

	API reference for :class:`~psychopy.visual.Polygon`
	API reference for :class:`~psychopy.visual.Rect`
	API reference for :class:`~psychopy.visual.ShapeStim` #for arbitrary vertices
