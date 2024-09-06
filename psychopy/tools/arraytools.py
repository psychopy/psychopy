#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to array handling
"""

__all__ = ["createXYs",
           "extendArr",
           "makeRadialMatrix",
           "ratioRange",
           "shuffleArray",
           "val2array",
           "array2pointer",
           "createLumPattern"]

import numpy
import ctypes


class IndexDict(dict):
    """
    A dict which allows for keys to be accessed by index as well as by key. Can be initialised 
    from a dict, or from a set of keyword arguments.

    Example
    -------
    ```
    data = IndexDict({
        'someKey': "abc",
        'someOtherKey': "def",
        'anotherOne': "ghi",
        1: "jkl",
    })
    # using a numeric index will return the value for the key at that position
    print(data[0])  # prints: abc
    # ...unless that number is already a key
    print(data[1])  # prints: jkl
    ```
    """
    def __init__(self, arr=None, **kwargs):
        # initialise dict
        dict.__init__(self)
        # if given no dict, use a blank one
        if arr is None:
            arr = {}
        # if given a dict, update kwargs with it
        kwargs.update(arr)
        # set every key
        for key, value in kwargs.items():
            dict.__setitem__(self, key, value)
    
    def __getitem__(self, key):
        # if key is a valid numeric index not present as a normal key, get matching key
        if isinstance(key, int) and key < len(self) and key not in self:
            return list(self.values())[key]
        # index like normal
        return dict.__getitem__(self, key)
    
    def __setitem__(self, key, value):
        # if key is a valid numeric index not present as a normal key, get matching key
        if isinstance(key, int) and key < len(self) and key not in self:
            key = list(self.keys())[key]
        # set like normal
        return dict.__setitem__(self, key, value)


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


def makeRadialMatrix(matrixSize, center=(0.0, 0.0), radius=1.0):
    """DEPRECATED: please use psychopy.filters.makeRadialMatrix instead
    """
    from psychopy.visual import filters
    return filters.makeRadialMatrix(matrixSize, center, radius)


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
        stepRatio = 10.0 ** (stepdB / 20.0)  # dB = 20*log10(ratio)

    if stepLogUnits is not None:
        stepRatio = 10.0 ** stepLogUnits  # logUnit = log10(ratio)

    if stepRatio is not None and nSteps is not None:
        factors = stepRatio ** numpy.arange(nSteps, dtype='d')
        output = start * factors
    elif nSteps is not None and stop is not None:
        if stop <= 0:
            raise RuntimeError(badRange)
        lgStart = numpy.log10(start)
        lgStop = numpy.log10(stop)
        lgStep = (lgStop - lgStart) / (nSteps - 1)
        lgArray = numpy.arange(lgStart, lgStop + lgStep, lgStep)
        # if the above is a badly rounded float it may have one extra entry
        if len(lgArray) > nSteps:
            lgArray = lgArray[:-1]
        output = 10 ** lgArray
    elif stepRatio is not None and stop is not None:
        thisVal = float(start)
        outList = []
        while thisVal < stop:
            outList.append(thisVal)
            thisVal *= stepRatio
        output = numpy.asarray(outList)
    else:
        # if any of the conditions above are not satisfied, throw this error.
        raise ValueError('Invalid input parameters.')

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


def snapto(values, points):
    """
    Snap values in array x to their closest equivalent in an array of target values, returning an array of the closest value in `points` to each value in `x`.

    Parameters
    ----------
    values : list, tuple or numpy.ndarray
        Array of values to be snapped to `points`
    points : list, tuple or numpy.ndarray
        Array of values to be snapped to

    Returns
    -------
    snapped
        Array of values, each corresponds to a value in `x` and is the closest value in `points`.

    Examples
    --------
    Snap labels on a Slider to the x positions of each tick::

        labelPositions = [-1, -2/3, -1/3, 1/3, 2/3, 1]
        tickPositions = [-1, -0.8, -0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8, 1]
        snappedLabelPositions = snapto(x=labelPositions, points=tickPositions)

        assert snappedLabelPositions = [-1, -0.6, -0.4, 0.4, 0.6, 1]
    """

    # Force values to 1d numpy arrays, though keep track of original shape of x
    ogShape = numpy.asarray(values).shape
    values = numpy.asarray(values).reshape((1, -1))
    points = numpy.asarray(points).reshape((1, -1))

    # Get sort order of values and points
    valuesi = numpy.argsort(values[0])
    pointsi = numpy.argsort(points[0])
    # Shift values indices to sit evenly within points indices
    valuesi -= min(pointsi)
    valuesi = valuesi / max(valuesi) * max(pointsi)
    valuesi = valuesi.round().astype(int)
    # Get indices of points corresponding to each x value
    i = pointsi[valuesi]
    # Get corresponding points
    snapped1d = points[0, i]
    # Reshape to original shape of x
    snapped = snapped1d.reshape(ogShape)

    return snapped


def createLumPattern(patternType, res, texParams=None, maskParams=None):
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
    texParams : dict or None
        Additional parameters to control texture generation. Not currently used
        but may in the future. These can be settings like duty-cycle, etc.
        Passing valid values to this parameter do nothing yet.
    maskParams : dict or None
        Additional parameters to control how the texture's mask is applied.

    Returns
    -------
    ndarray
        Array of normalized intensity values containing the desired pattern
        specified by `mode`.

    Examples
    --------
    Create a gaussian bump luminance map with resolution 1024x1024 and standard
    deviation of 0.5::

        res = 1024
        maskParams = {'sd': 0.5}
        intensity = createLumPattern('gauss', res, None, maskParams)

    """
    # This code was originally in `TextureMixin._createTexture`, but moved here
    # to clean up that class and to provide a reusable way of generating these
    # textures.

    # Check and sanitize parameters passed to this function before generating
    # anything with them.
    if res <= 0:
        raise ValueError('invalid value for parameter `res`, must be >0')

    # parameters to control texture generation, unused but roughed in for now
    allTexParams = {}
    if isinstance(texParams, dict):  # specified, override defaults if so
        allTexParams.update(texParams)
    elif texParams is None:  # if not specified, use empty dict
        pass  # nop for now, change to `allTexParams = {}` when needed
    else:
        raise TypeError('parameter `texParams` must be type `dict` or `None`')

    # mask parameters for additional parameters to control how maks are applied
    allMaskParams = {'fringeWidth': 0.2, 'sd': 3}
    if isinstance(maskParams, dict):  # specified, override defaults if so
        allMaskParams.update(maskParams)
    elif maskParams is None:  # if not specified, use empty dict
        allMaskParams = {}
    else:
        raise TypeError('parameter `maskParams` must be type `dict` or `None`')

    # correct `makeRadialMatrix` from filters, duplicated her to avoid importing
    # all of visual to test this function out
    def _makeRadialMatrix(matrixSize, center=(0.0, 0.0), radius=1.0):
        if type(radius) in [int, float]:
            radius = [radius, radius]

        # NB need to add one step length because
        yy, xx = numpy.mgrid[0:matrixSize, 0:matrixSize]
        xx = ((1.0 - 2.0 / matrixSize * xx) + center[0]) / radius[0]
        yy = ((1.0 - 2.0 / matrixSize * yy) + center[1]) / radius[1]
        rad = numpy.sqrt(numpy.power(xx, 2) + numpy.power(yy, 2))

        return rad

    # here is where we generate textures
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
        rad = _makeRadialMatrix(res)
        intensity = (rad <= 1) * 2 - 1
    elif patternType == "gauss":
        rad = _makeRadialMatrix(res)
        # 3sd.s by the edge of the stimulus
        try:
            maskStdev = allMaskParams['sd']
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
        rad = _makeRadialMatrix(res)
        intensity = 1 - 2 * rad
        # clip off the corners (circular)
        intensity = numpy.where(rad < -1, intensity, -1)
    elif patternType == "raisedCos":  # A raised cosine
        hammingLen = 1000  # affects the 'granularity' of the raised cos
        rad = _makeRadialMatrix(res)
        intensity = numpy.zeros_like(rad)
        intensity[numpy.where(rad < 1)] = 1

        maskFringeWidth = allMaskParams['fringeWidth']
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


class AliasDict(dict):
    """
    Similar to a dict, but with the option to alias certain keys such that they always have the same value.
    """
    def __getitem__(self, k):
        # if key is aliased, use its alias
        if k in self.aliases:
            k = self.aliases[k]
        # get as normal
        return dict.__getitem__(self, k)

    def __setitem__(self, k, v):
        # if key is aliased, set its alias
        if k in self.aliases:
            k = self.aliases[k]
        # set as normal
        return dict.__setitem__(self, k, v)
    set = __setitem__

    def __contains__(self, item):
        # return True to "in" queries if item is in aliases
        return dict.__contains__(self, item) or item in self.aliases

    @property
    def aliases(self):
        """
        Dict mapping name aliases to the key they are an alias for
        """
        # if not set yet, set as blank dict
        if not hasattr(self, "_aliases"):
            self._aliases = {}

        return self._aliases

    @aliases.setter
    def aliases(self, value: dict):
        self._aliases = value

    def alias(self, key, alias):
        """
        Add an alias for a key in this dict. Setting/getting one key will set/get the other.

        Parameters
        ----------
        key : str
            Key to alias
        alias : str
            Name to alias key with
        """
        # assign alias
        self.aliases[alias] = key


if __name__ == "__main__":
    pass
