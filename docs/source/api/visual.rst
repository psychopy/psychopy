:mod:`psychopy.visual` - many visual stimuli
==============================================================================

:class:`.Window` to display all stimuli below.


.. toctree::
    :hidden:
    :glob:

    visual/*

Commonly used:

	* :class:`.ImageStim` to show images
	* :class:`.TextStim` to show text
	* :class:`.TextBox` rewrite of TextStim (faster/better but only monospace fonts)

Shapes (all special classes of :class:`ShapeStim`):

	* :class:`.ShapeStim` to draw shapes with arbitrary numbers of vertices
	* :class:`.Rect` to show rectangles
	* :class:`.Circle` to show circles
	* :class:`.Polygon` to show polygons
	* :class:`.Line` to show a line

Images and patterns:

	* :class:`.ImageStim` to show images
	* :class:`.SimpleImageStim` to show images without bells and whistles
	* :class:`.GratingStim` to show gratings
	* :class:`.RadialStim` to show annulus, a rotating wedge, a checkerboard etc

Multiple stimuli:

	* :class:`.ElementArrayStim` to show many stimuli of the same type
	* :class:`.DotStim` to show and control movement of dots

Other stimuli:

	* :class:`.MovieStim` to show movies
	* :class:`.RatingScale` to collect ratings
	* :class:`.CustomMouse` to change the cursor in windows with GUI. OBS: will be deprecated soon

Meta stimuli (stimuli that operate on other stimuli):

	* :class:`.BufferImageStim` to make a faster-to-show "screenshot" of other stimuli
	* :class:`.Aperture` to restrict visibility area of other stimuli

Helper functions:

  * :ref:`psychopy.visual.filters` for creating grating textures and Gaussian masks etc.
  * :ref:`visualhelperfunctions` for tests about whether one stimulus contains another
  * :mod:`~psychopy.tools.unittools` to convert deg<->radians
  * :mod:`~psychopy.tools.monitorunittools` to convert cm<->pix<->deg etc.
  * :mod:`psychopy.tools.colorspacetools` to convert between supported color spaces
