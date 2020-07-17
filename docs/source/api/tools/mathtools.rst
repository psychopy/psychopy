
:mod:`psychopy.tools.mathtools`
----------------------------------------

Assorted math functions for working with vectors, matrices, and
quaternions. These functions are intended to provide basic support for common
mathematical operations associated with displaying stimuli (e.g. animation,
posing, rendering, etc.)

For tools related to view transformations, see :mod:`~psychopy.tools.viewtools`.

Performance and Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most functions listed here are very fast, however they are optimized to work on
arrays of values (vectorization). Calling functions repeatedly (for instance
within a loop), should be avoided as the CPU overhead associated with each
function call (not to mention the loop itself) can be considerable.

For example, one may want to normalize a bunch of randomly generated vectors by
calling :func:`normalize` on each row::

    v = np.random.uniform(-1.0, 1.0, (1000, 4,))  # 1000 length 4 vectors
    vn = np.zeros((1000, 4))  # place to write values

    # don't do this!
    for i in range(1000):
        vn[i, :] = normalize(v[i, :])

The same operation is completed in considerably less time by passing the whole
array to the function like so::

    normalize(v, out=vn)  # very fast!
    vn = normalize(v)  # also fast if `out` is not provided

Specifying an output array to `out` will improve performance by reducing
overhead associated with allocating memory to store the result (functions do
this automatically if `out` is not provided). However, `out` should only be
provided if the output array is reused multiple times. Furthermore, the
function still returns a value if `out` is provided, but the returned value is a
reference to `out`, not a copy of it. If `out` is not provided, the function
will return the result with a freshly allocated array.

Data Types
~~~~~~~~~~

Sub-routines used by the functions here will perform arithmetic using 64-bit
floating-point precision unless otherwise specified via the `dtype` argument.
This functionality is helpful in certain applications where input and output
arrays demand a specific type (eg. when working with data passed to and from
OpenGL functions).

If a `dtype` is specified, input arguments will be coerced to match that type
and all floating-point arithmetic will use the precision of the type. If input
arrays have the same type as `dtype`, they will automatically pass-through
without being recast as a different type. As a performance consideration, all
input arguments should have matching types and `dtype` set accordingly.

Most functions have an `out` argument, where one can specify an array to write
values to. The value of `dtype` is ignored if `out` is provided, and all input
arrays will be converted to match the `dtype` of `out` (if not already). This
ensures that the type of the destination array is used for all arithmetic.


.. automodule:: psychopy.tools.mathtools
.. currentmodule:: psychopy.tools.mathtools

Overview
~~~~~~~~

.. autosummary::

    length
    normalize
    orthogonalize
    reflect
    dot
    cross
    project
    perp
    lerp
    distance
    angleTo
    bisector
    surfaceNormal
    surfaceBitangent
    surfaceTangent
    vertexNormal
    fixTangentHandedness
    fitBBox
    computeBBoxCorners
    intersectRayPlane
    intersectRaySphere
    intersectRayAABB
    intersectRayOBB
    intersectRayTriangle
    ortho3Dto2D
    articulate
    slerp
    quatToAxisAngle
    quatFromAxisAngle
    quatYawPitchRoll
    alignTo
    quatMagnitude
    multQuat
    accumQuat
    invertQuat
    applyQuat
    quatToMatrix
    matrixToQuat
    matrixFromEulerAngles
    scaleMatrix
    rotationMatrix
    matrixAngle
    translationMatrix
    invertMatrix
    isOrthogonal
    isAffine
    multMatrix
    concatenate
    normalMatrix
    forwardProject
    reverseProject
    applyMatrix
    posOriToMatrix
    transform
    scale
    lensCorrection
    zeroFix


Details
~~~~~~~

.. autofunction:: length
.. autofunction:: normalize
.. autofunction:: orthogonalize
.. autofunction:: reflect
.. autofunction:: dot
.. autofunction:: cross
.. autofunction:: project
.. autofunction:: perp
.. autofunction:: lerp
.. autofunction:: distance
.. autofunction:: angleTo
.. autofunction:: bisector
.. autofunction:: surfaceNormal
.. autofunction:: surfaceBitangent
.. autofunction:: surfaceTangent
.. autofunction:: vertexNormal
.. autofunction:: fixTangentHandedness
.. autofunction:: fitBBox
.. autofunction:: computeBBoxCorners
.. autofunction:: intersectRayPlane
.. autofunction:: intersectRaySphere
.. autofunction:: intersectRayAABB
.. autofunction:: intersectRayOBB
.. autofunction:: intersectRayTriangle
.. autofunction:: ortho3Dto2D
.. autofunction:: articulate
.. autofunction:: slerp
.. autofunction:: quatToAxisAngle
.. autofunction:: quatFromAxisAngle
.. autofunction:: quatYawPitchRoll
.. autofunction:: alignTo
.. autofunction:: quatMagnitude
.. autofunction:: multQuat
.. autofunction:: accumQuat
.. autofunction:: invertQuat
.. autofunction:: applyQuat
.. autofunction:: quatToMatrix
.. autofunction:: matrixToQuat
.. autofunction:: matrixFromEulerAngles
.. autofunction:: scaleMatrix
.. autofunction:: rotationMatrix
.. autofunction:: matrixAngle
.. autofunction:: translationMatrix
.. autofunction:: invertMatrix
.. autofunction:: isOrthogonal
.. autofunction:: isAffine
.. autofunction:: multMatrix
.. autofunction:: concatenate
.. autofunction:: normalMatrix
.. autofunction:: forwardProject
.. autofunction:: reverseProject
.. autofunction:: applyMatrix
.. autofunction:: posOriToMatrix
.. autofunction:: transform
.. autofunction:: scale
.. autofunction:: lensCorrection
.. autofunction:: zeroFix
