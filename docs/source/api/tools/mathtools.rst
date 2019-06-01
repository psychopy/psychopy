
:mod:`psychopy.tools.mathtools`
----------------------------------------

Assorted math functions for working with vectors, matrices, and
quaternions. These functions are intended to provide basic support for common
mathematical operations associated with displaying stimuli (e.g. animation,
posing, rendering, etc.)

Warning
~~~~~~~
Sub-routines used by functions here will perform arithmetic using the highest
floating-point precision of the provided input arguments. Vectors provided as
Python lists and tuples will be coerced into 64-bit floating-point arrays.

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
    poseToMatrix
    
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
.. autofunction:: poseToMatrix
