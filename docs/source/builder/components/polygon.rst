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
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

stop :
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

shape : line, triangle, rectangle, cross, star, regular polygon
    What shape the stimulus is

num vertices : int
    The number of vertices for your shape (2 gives a line, 3 gives a triangle,... a large number results in a circle/ellipse).
    It is not (currently) possible to vary the number of vertices dynamically.

Appearance
==========
How should the stimulus look? Colour, borders, etc.

fill color : color
    See :ref:`colorspaces`

color space : rgb, dkl, lms, hsv
    See :ref:`colorspaces`

border color : color
    See :ref:`colorspaces`

line width : int | float
    How wide should the line be? Width is specified in chosen spatial units, see :doc:`../../general/units`

opacity :
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

Layout
======
How should the stimulus be laid out? Padding, margins, size, position, etc.

ori : degrees
    The orientation of the entire patch (texture and mask) in degrees.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

size : (width, height)
    Size of the stimulus on screen

spatial units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

Texture
=======
Control how the stimulus handles textures.

interpolate : linear, nearest
    Should textures be interpolated?





units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`


.. seealso::

	API reference for :class:`~psychopy.visual.Polygon`
	API reference for :class:`~psychopy.visual.Rect`
	API reference for :class:`~psychopy.visual.ShapeStim` #for arbitrary vertices
