#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to array handling
"""
from __future__ import absolute_import, division, print_function

__all__ = ["createXYs",
           "extendArr",
           "makeRadialMatrix",
           "ratioRange",
           "shuffleArray",
           "val2array",
           "array2pointer",
           "createLumPattern"]

from builtins import str
from past.utils import old_div
import numpy
import ctypes


def createXYs(x, y=None):
    """Create an Nx2 array of XY values including all combinations of the
    x and y values provided.

    >>> createXYs(x=[1, 2, 3], y=[4, 5, 6])
    array([[1, 4],
       [2, 4],
       [3, 4],
       [1, 5],
       [2, 5],
       [3, 5],
       [1, 6],
       [2, 6],
       [3, 6]])
    >>> createXYs(x=[1, 2, 3])  # assumes y == x
    array([[1, 1],
       [2, 1],
       [3, 1],
       [1, 2],
       [2, 2],
       [3, 2],
       [1, 3],
       [2, 3],
       [3, 3]])

    """
    if y is None:
        y = x
    xs = numpy.resize(x, len(x) * len(y))  # [1,2,3, 1,2,3, 1,2,3]
    ys = numpy.repeat(y, len(x))  # [1,1,1 ,2,2,2, 3,3,3]
    return numpy.vstack([xs, ys]).transpose()


def extendArr(inArray, newSize):
    """Takes a numpy array and returns it padded with zeros
    to the necessary size

    >>> extendArr([1, 2, 3], 5)
    array([1, 2, 3, 0, 0])

    """
    if type(inArray) in [tuple, list]:
        inArray = numpy.asarray(inArray)

    newArr = numpy.zeros(newSize, inArray.dtype)
    # create a string to eval (see comment below)
    indString = ''
    for thisDim in inArray.shape:
        indString += '0:' + str(thisDim) + ','
    indString = indString[0:-1]  # remove the final comma

    # e.g.
    # newArr[0:4, 0:3] = inArray

    exec("newArr[" + indString + "] = inArray")
    return newArr


def makeRadialMatrix(matrixSize):
    """Generate a square matrix where each element val is
    its distance from the centre of the matrix
    """
    oneStep = old_div(2.0, (matrixSize - 1) or -1)
    # NB need to add one step length because
    xx, yy = numpy.mgrid[0:2 + oneStep:oneStep, 0:2 + oneStep:oneStep] - 1.0
    rad = numpy.sqrt(xx**2 + yy**2)
    return rad


def ratioRange(start, nSteps=None, stop=None,
               stepRatio=None, stepdB=None, stepLogUnits=None):
    """Creates a  array where each step is a constant ratio
    rather than a constant addition.

    Specify *start* and any 2 of, *nSteps*, *stop*, *stepRatio*,
        *stepdB*, *stepLogUnits*

    >>> ratioRange(1,nSteps=4,stop=8)
    array([ 1.,  2.,  4.,  8.])
    >>> ratioRange(1,nSteps=4,stepRatio=2)
    array([ 1.,  2.,  4.,  8.])
    >>> ratioRange(1,stop=8,stepRatio=2)
    array([ 1.,  2.,  4.,  8.])

    """

    badRange = "Can't calculate ratio ranges on negatives or zero"
    if start <= 0:
        raise RuntimeError(badRange)
    if stepdB is not None:
        stepRatio = 10.0**(old_div(stepdB, 20.0))  # dB = 20*log10(ratio)
    if stepLogUnits is not None:
        stepRatio = 10.0**stepLogUnits  # logUnit = log10(ratio)

    if (stepRatio != None) and (nSteps != None):
        factors = stepRatio**numpy.arange(nSteps, dtype='d')
        output = start * factors

    elif (nSteps != None) and (stop != None):
        if stop <= 0:
            raise RuntimeError(badRange)
        lgStart = numpy.log10(start)
        lgStop = numpy.log10(stop)
        lgStep = old_div((lgStop - lgStart), (nSteps - 1))
        lgArray = numpy.arange(lgStart, lgStop + lgStep, lgStep)
        # if the above is a badly rounded float it may have one extra entry
        if len(lgArray) > nSteps:
            lgArray = lgArray[:-1]
        output = 10**lgArray

    elif (stepRatio != None) and (stop != None):
        thisVal = float(start)
        outList = []
        while thisVal < stop:
            outList.append(thisVal)
            thisVal *= stepRatio
        output = numpy.asarray(outList)

    return output


def shuffleArray(inArray, shuffleAxis=-1, seed=None):
    """DEPRECATED: use `numpy.random.shuffle`
    """
    # arrAsList = shuffle(list(inArray))
    # return numpy.array(arrAsList)
    rng = numpy.random.default_rng(seed=seed)

    inArray = numpy.array(inArray, 'O')  # convert to array if necess
    # create a random array of the same shape
    rndArray = rng.random(inArray.shape)
    # and get the arguments that would sort it
    newIndices = numpy.argsort(rndArray, shuffleAxis)
    # return the array with the sorted random indices
    return numpy.take(inArray, newIndices)


def val2array(value, withNone=True, withScalar=True, length=2):
    """Helper function: converts different input to a numpy array.

    Raises informative error messages if input is invalid.

    withNone: True/False. should 'None' be passed?
    withScalar: True/False. is a scalar an accepted input?
        Will be converted to array of this scalar
    length: False / 2 / 3. Number of elements input should have or be
        converted to. Might be False (do not accept arrays or convert to such)
    """
    if value is None:
        if withNone:
            return None
        else:
            raise ValueError('Invalid parameter. None is not accepted as '
                             'value.')
    value = numpy.array(value, float)
    if numpy.product(value.shape) == 1:
        if withScalar:
            # e.g. 5 becomes array([5.0, 5.0, 5.0]) for length=3
            return numpy.repeat(value, length)
        else:
            msg = ('Invalid parameter. Single numbers are not accepted. '
                   'Should be tuple/list/array of length %s')
            raise ValueError(msg % str(length))
    elif value.shape[-1] == length:
        return numpy.array(value, float)
    else:
        msg = 'Invalid parameter. Should be length %s but got length %s.'
        raise ValueError(msg % (str(length), str(len(value))))


def array2pointer(arr, dtype=None):
    """Convert a Numpy array to a `ctypes` pointer.

    Arrays are checked if they are contiguous before conversion, if not, they
    will be converted to contiguous arrays.

    Parameters
    ----------
    arr : ndarray
        N-dimensions array to convert, should be contiguous (C-ordered).
    dtype : str or dtype, optional
        Data type for the array pointer. If the data type of the array does not
        match `dtype`, it will be converted to `dtype` prior to using it. If
        `None` is specified, the data type for the pointer will be implied from
        the input array type.

    Returns
    -------
    ctypes.POINTER
        Pointer to the first value of the array.

    """
    dtype = arr.dtype if dtype is None else numpy.dtype(dtype).type

    # convert to ctypes, also we ensure the array is contiguous
    return numpy.ascontiguousarray(arr, dtype=dtype).ctypes.data_as(
        ctypes.POINTER(numpy.ctypeslib.as_ctypes_type(dtype)))


def createLumPattern(patternType, res, maskParams=None):
    """Create a luminance (single channel) defined pattern.
    
    Parameters
    ----------
    patternType : str or None
        Pattern to generate. Value may be one of: 'sin', 'sqr', 'saw', 'tri',
        'sinXsin', 'sqrXsqr', 'circle', 'gauss', 'cross', 'radRamp' or
        'raisedCos'. If `None`, 'none', 'None' or 'color' are specified, an
        array of ones will be returned with `size==(res, res)`.
    res : int
        Resolution for the texture in texels.
    maskParams : dict
        Additional parameters to control how the mask is applied.

    Returns
    -------
    ndarray
        Array of normalized intensity values containing the desired pattern
        specified by `mode`.
    
    """
    if res <= 0:
        raise ValueError('invalid value for parameter `res`, must be >0')

    # set defaults if not provided
    reqMaskParams = {'fringeWidth': 0.2, 'sd': 3}
    if maskParams is None:  # if not specified, set defaults
        maskParams = reqMaskParams
    elif isinstance(maskParams, dict):  # specified, override defaults if so
        maskParams = reqMaskParams.update(maskParams)
    else:
        raise TypeError('parameter `maskParams` must be type `dict` or `None`')

    pi = numpy.pi
    if patternType in (None, "none", "None", "color"):
        res = 1
        intensity = numpy.ones([res, res], numpy.float32)
    elif patternType == "sin":
        # NB 1j*res is a special mgrid notation
        onePeriodX, onePeriodY = numpy.mgrid[0:res, 0:2 * pi:1j * res]
        intensity = numpy.sin(onePeriodY - pi / 2)
    elif patternType == "sqr":  # square wave (symmetric duty cycle)
        # NB 1j*res is a special mgrid notation
        onePeriodX, onePeriodY = numpy.mgrid[0:res, 0:2 * pi:1j * res]
        sinusoid = numpy.sin(onePeriodY - pi / 2)
        intensity = numpy.where(sinusoid > 0, 1, -1)
    elif patternType == "saw":
        intensity = \
            numpy.linspace(-1.0, 1.0, res, endpoint=True) * numpy.ones([res, 1])
    elif patternType == "tri":
        # -1:3 means the middle is at +1
        intens = numpy.linspace(-1.0, 3.0, res, endpoint=True)
        # remove from 3 to get back down to -1
        intens[res // 2 + 1:] = 2.0 - intens[res // 2 + 1:]
        intensity = intens * numpy.ones([res, 1])  # make 2D
    elif patternType == "sinXsin":
        # NB 1j*res is a special mgrid notation
        onePeriodX, onePeriodY = numpy.mgrid[0:2 * pi:1j * res,
                                             0:2 * pi:1j * res]
        intensity = \
            numpy.sin(onePeriodX - pi / 2) * numpy.sin(onePeriodY - pi / 2)
    elif patternType == "sqrXsqr":
        # NB 1j*res is a special mgrid notation
        onePeriodX, onePeriodY = numpy.mgrid[0:2 * pi:1j * res,
                                             0:2 * pi:1j * res]
        sinusoid = \
            numpy.sin(onePeriodX - pi / 2) * numpy.sin(onePeriodY - pi / 2)
        intensity = numpy.where(sinusoid > 0, 1, -1)
    elif patternType == "circle":
        rad = makeRadialMatrix(res)
        intensity = (rad <= 1) * 2 - 1
    elif patternType == "gauss":
        rad = makeRadialMatrix(res)
        # 3sd.s by the edge of the stimulus
        try:
            maskStdev = maskParams['sd']
        except KeyError:
            raise ValueError(
                "Mask parameter 'sd' not provided but is required by "
                "`mode='gauss'`")

        invVar = (1.0 / maskStdev) ** 2.0
        intensity = numpy.exp(-rad ** 2.0 / (2.0 * invVar)) * 2 - 1
    elif patternType == "cross":
        X, Y = numpy.mgrid[-1:1:1j * res, -1:1:1j * res]
        tfNegCross = (((X < -0.2) & (Y < -0.2)) |
                      ((X < -0.2) & (Y > 0.2)) |
                      ((X > 0.2) & (Y < -0.2)) |
                      ((X > 0.2) & (Y > 0.2)))
        # tfNegCross == True at places where the cross is transparent,
        # i.e. the four corners
        intensity = numpy.where(tfNegCross, -1, 1)
    elif patternType == "radRamp":  # a radial ramp
        rad = makeRadialMatrix(res)
        intensity = 1 - 2 * rad
        # clip off the corners (circular)
        intensity = numpy.where(rad < -1, intensity, -1)
    elif patternType == "raisedCos":  # A raised cosine
        hammingLen = 1000  # affects the 'granularity' of the raised cos
        rad = makeRadialMatrix(res)
        intensity = numpy.zeros_like(rad)
        intensity[numpy.where(rad < 1)] = 1

        maskFringeWidth = maskParams['fringeWidth']
        raisedCosIdx = numpy.where(
            [numpy.logical_and(rad <= 1, rad >= 1 - maskFringeWidth)])[1:]

        # Make a raised_cos (half a hamming window):
        raisedCos = numpy.hamming(hammingLen)[:hammingLen // 2]
        raisedCos -= numpy.min(raisedCos)
        raisedCos /= numpy.max(raisedCos)

        # Measure the distance from the edge - this is your index into the
        # hamming window:
        dFromEdge = numpy.abs(
            (1 - maskFringeWidth) - rad[raisedCosIdx])
        dFromEdge /= numpy.max(dFromEdge)
        dFromEdge *= numpy.round(hammingLen / 2)

        # This is the indices into the hamming (larger for small distances
        # from the edge!):
        portionIdx = (-1 * dFromEdge).astype(int)

        # Apply the raised cos to this portion:
        intensity[raisedCosIdx] = raisedCos[portionIdx]

        # Scale it into the interval -1:1:
        intensity = intensity - 0.5
        intensity /= numpy.max(intensity)

        # Sometimes there are some remaining artifacts from this process,
        # get rid of them:
        artifactIdx = numpy.where(
            numpy.logical_and(intensity == -1, rad < 0.99))
        intensity[artifactIdx] = 1
        artifactIdx = numpy.where(
            numpy.logical_and(intensity == 1, rad > 0.99))
        intensity[artifactIdx] = 0

    else:
        raise ValueError("invalid keyword or value for parameter `patternType`")

    return intensity


if __name__ == "__main__":
    pass
