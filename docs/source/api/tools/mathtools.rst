
:mod:`psychopy.tools.mathtools`
----------------------------------------

Assorted math functions for working with vectors, matrices, and
quaternions. These functions are intended to provide basic support for common
mathematical operations associated with displaying stimuli (e.g. animation,
posing, rendering, etc.)

Warning
~~~~~~~
All functions and their sub-routines default to 32-bit precision for floating
point arithmetic. Specify ``'float64'`` to their `dtype` argument for higher
64-bit precision.


.. automodule:: psychopy.tools.mathtools
.. currentmodule:: psychopy.tools.mathtools
    
.. autosummary:: 

    normalize
    lerp
    slerp
    multQuat
    invertQuat
    quatToAxisAngle
    quatFromAxisAngle
    matrixFromQuat
    scaleMatrix
    rotationMatrix
    translationMatrix
    concatenate
    applyMatrix
    
Function details
~~~~~~~~~~~~~~~~

.. autofunction:: normalize
.. autofunction:: lerp
.. autofunction:: slerp
.. autofunction:: multQuat
.. autofunction:: invertQuat
.. autofunction:: quatToAxisAngle
.. autofunction:: quatFromAxisAngle
.. autofunction:: matrixFromQuat
.. autofunction:: scaleMatrix
.. autofunction:: rotationMatrix
.. autofunction:: translationMatrix
.. autofunction:: concatenate
.. autofunction:: applyMatrix
