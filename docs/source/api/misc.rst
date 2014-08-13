:mod:`psychopy.misc` - miscellaneous routines for converting units etc
=========================================================================

.. automodule:: psychopy.misc

`psychopy.misc` has gradually grown very large and the underlying code for its functions are distributed in multiple files. You can still (at least for now) import the functions here using `from psychopy import misc` but you can also import them from the `tools` sub-modules.

From :mod:`psychopy.tools.filetools`
------------------------------------------------------------
.. currentmodule:: psychopy.tools.filetools
.. autosummary:: 
    toFile
    fromFile
    mergeFolder
    
From :mod:`psychopy.tools.colorspacetools`
------------------------------------------------------------
.. currentmodule:: psychopy.tools.colorspacetools
.. autosummary:: 
    dkl2rgb
    dklCart2rgb
    rgb2dklCart
    hsv2rgb
    lms2rgb
    rgb2lms
    dkl2rgb
    
From :mod:`psychopy.tools.coordinatetools`
------------------------------------------------------------
.. currentmodule:: psychopy.tools.coordinatetools
.. autosummary:: 
    cart2pol
    cart2sph
    pol2cart
    sph2cart
    
From :mod:`psychopy.tools.monitorunittools`
------------------------------------------------------------
.. currentmodule:: psychopy.tools.monitorunittools
.. autosummary:: 
    convertToPix
    cm2pix
    cm2deg
    deg2cm
    deg2pix
    pix2cm
    pix2deg

From :mod:`psychopy.tools.imagetools`
------------------------------------------------------------
.. currentmodule:: psychopy.tools.imagetools
.. autosummary:: 
    array2image
    image2array
    makeImageAuto
    
From :mod:`psychopy.tools.plottools`
------------------------------------------------------------
.. currentmodule:: psychopy.tools.plottools
.. autosummary:: 
    plotFrameIntervals
    
From :mod:`psychopy.tools.typetools`
------------------------------------------------------------
.. currentmodule:: psychopy.tools.typetools
.. autosummary:: 
    float_uint8
    uint8_float
    float_uint16
    
From :mod:`psychopy.tools.unittools`
------------------------------------------------------------
.. currentmodule:: psychopy.tools.unittools
.. autosummary:: 
    radians
    degrees
    