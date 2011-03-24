.. _aperture:

Aperture Component
-------------------------------

This component can be used to filter the visual display, as if the subject is looking at it through an opening. Currently only circular apertures are supported. Moreover, only one aperture is enabled at a time. You can't "double up": a second aperture takes precedence.

name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).

pos : [X,Y]
    The position of the centre of the aperture, in the units specified by the stimulus or window.
    
size : int
    The size controls how big the aperture will be, in pixels, default = 120

units: pix
    What units to use (currently only pix).

.. seealso::
	
	API reference for :class:`~psychopy.visual.Aperture`
