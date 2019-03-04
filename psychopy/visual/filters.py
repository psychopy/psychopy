#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Various useful functions for creating filters and textures
(e.g. for PatchStim)
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

from past.utils import old_div
import numpy
from numpy.fft import fft2, ifft2, fftshift, ifftshift
from psychopy import logging
try:
    from PIL import Image
except ImportError:
    import Image


def makeGrating(res,
                ori=0.0,  # in degrees
                cycles=1.0,
                phase=0.0,  # in degrees
                gratType="sin",
                contr=1.0):
    """Make an array containing a luminance grating of the specified params

    :Parameters:
        res: integer
            the size of the resulting matrix on both dimensions (e.g 256)
        ori: float or int (default=0.0)
            the orientation of the grating in degrees
        cycles:float or int (default=1.0)
            the number of grating cycles within the array
        phase: float or int (default=0.0)
            the phase of the grating in degrees (NB this differs to most
            PsychoPy phase arguments which use units of fraction of a cycle)
        gratType: 'sin', 'sqr', 'ramp' or 'sinXsin' (default="sin")
            the type of grating to be 'drawn'
        contr: float (default=1.0)
            contrast of the grating

    :Returns:
        a square numpy array of size resXres

    """
    # to prevent the sinusoid ever being exactly at zero (for sqr wave):
    tiny = 0.0000000000001
    ori *= (old_div(-numpy.pi, 180))
    phase *= (old_div(numpy.pi, 180))
    cyclesTwoPi = cycles * 2.0 * numpy.pi
    xrange, yrange = numpy.mgrid[0.0: cyclesTwoPi: old_div(cyclesTwoPi, res),
                                 0.0: cyclesTwoPi: old_div(cyclesTwoPi, res)]

    sin, cos = numpy.sin, numpy.cos
    if gratType is "none":
        res = 2
        intensity = numpy.ones((res, res), float)
    elif gratType is "sin":
        intensity = contr * sin(xrange * sin(ori) + yrange * cos(ori) + phase)
    elif gratType is "ramp":
        intensity = contr * (xrange * cos(ori) +
                             yrange * sin(ori)) / (2 * numpy.pi)
    elif gratType is "sqr":  # square wave (symmetric duty cycle)
        intensity = numpy.where(sin(xrange * sin(ori) + yrange * cos(ori) +
                                    phase + tiny) >= 0, 1, -1)
    elif gratType is "sinXsin":
        intensity = sin(xrange) * sin(yrange)
    else:
        # might be a filename of an image
        try:
            im = Image.open(gratType)
        except Exception:
            logging.error("couldn't find tex...", gratType)
            return
        # todo: opened it, now what?
    return intensity


def maskMatrix(matrix, shape='circle', radius=1.0, center=(0.0, 0.0)):
    """Make and apply a mask to an input matrix (e.g. a grating)

    :Parameters:
         matrix:  a square numpy array
             array to which the mask should be applied
         shape:  'circle','gauss','ramp' (linear gradient from center)
             shape of the mask
         radius:  float
             scale factor to be applied to the mask (circle with radius of
             [1,1] will extend just to the edge of the matrix). Radius can
             be asymmetric, e.g. [1.0,2.0] will be wider than it is tall.
         center:  2x1 tuple or list (default=[0.0,0.0])
             the centre of the mask in the matrix ([1,1] is top-right
             corner, [-1,-1] is bottom-left)
    """
    # NB makeMask now returns a value -1:1
    alphaMask = makeMask(matrix.shape[0], shape, radius,
                         center=(0.0, 0.0), range=[0, 1])
    return matrix * alphaMask


def makeMask(matrixSize, shape='circle', radius=1.0, center=(0.0, 0.0),
             range=(-1, 1), fringeWidth=0.2):
    """Returns a matrix to be used as an alpha mask (circle,gauss,ramp).

    :Parameters:
            matrixSize: integer
                the size of the resulting matrix on both dimensions (e.g 256)
            shape:  'circle','gauss','ramp' (linear gradient from center),
                'raisedCosine' (the edges are blurred by a raised cosine)
                shape of the mask
            radius:  float
                scale factor to be applied to the mask (circle with radius of
                [1,1] will extend just to the edge of the matrix). Radius can
                asymmetric, e.g. [1.0,2.0] will be wider than it is tall.
            center:  2x1 tuple or list (default=[0.0,0.0])
                the centre of the mask in the matrix ([1,1] is top-right
                corner, [-1,-1] is bottom-left)
            fringeWidth: float (0-1)
                The proportion of the raisedCosine that is being blurred.
            range: 2x1 tuple or list (default=[-1,1])
                The minimum and maximum value in the mask matrix
    """
    rad = makeRadialMatrix(matrixSize, center, radius)
    if shape == 'ramp':
        outArray = 1 - rad
    elif shape == 'circle':
        # outArray=numpy.ones(matrixSize,'f')
        outArray = numpy.where(numpy.greater(rad, 1.0), 0.0, 1.0)
    elif shape == 'gauss':
        outArray = makeGauss(rad, mean=0.0, sd=0.33333)
    elif shape == 'raisedCosine':
        hammingLen = 1000  # This affects the 'granularity' of the raised cos
        fringeProportion = fringeWidth  # This one affects the proportion of
        # the stimulus diameter that is devoted to the raised cosine.

        rad = makeRadialMatrix(matrixSize, center, radius)
        outArray = numpy.zeros_like(rad)
        outArray[numpy.where(rad < 1)] = 1
        raisedCosIdx = numpy.where(
            [numpy.logical_and(rad <= 1, rad >= 1 - fringeProportion)])[1:]

        # Make a raised_cos (half a hamming window):
        raisedCos = numpy.hamming(hammingLen)[:hammingLen//2]
        raisedCos -= numpy.min(raisedCos)
        raisedCos /= numpy.max(raisedCos)

        # Measure the distance from the edge - this is your index into the
        # hamming window:
        dFromEdge = numpy.abs((1 - fringeProportion) - rad[raisedCosIdx])
        dFromEdge /= numpy.max(dFromEdge)
        dFromEdge *= numpy.round(hammingLen/2)

        # This is the indices into the hamming (larger for small distances
        # from the edge!):
        portion_idx = (-1 * dFromEdge).astype(int)

        # Apply the raised cos to this portion:
        outArray[raisedCosIdx] = raisedCos[portion_idx]

        # Sometimes there are some remaining artifacts from this process, get
        # rid of them:
        artifact_idx = numpy.where(
            numpy.logical_and(outArray == 0, rad < 0.99))
        outArray[artifact_idx] = 1
        artifact_idx = numpy.where(
            numpy.logical_and(outArray == 1, rad > 0.99))
        outArray[artifact_idx] = 0

    else:
        raise ValueError('Unknown value for shape argument %s' % shape)
    mag = range[1] - range[0]
    offset = range[0]
    return outArray * mag + offset


def makeRadialMatrix(matrixSize, center=(0.0, 0.0), radius=1.0):
    """Generate a square matrix where each element val is
    its distance from the centre of the matrix

    :Parameters:
        matrixSize: integer
            the size of the resulting matrix on both dimensions (e.g 256)
        radius:  float
            scale factor to be applied to the mask (circle with radius of
            [1,1] will extend just to the edge of the matrix). Radius can
            be asymmetric, e.g. [1.0,2.0] will be wider than it is tall.
        center:  2x1 tuple or list (default=[0.0,0.0])
            the centre of the mask in the matrix ([1,1] is top-right
            corner, [-1,-1] is bottom-left)
    """
    if type(radius) in [int, float]:
        radius = [radius, radius]

    # NB need to add one step length because
    yy, xx = numpy.mgrid[0:matrixSize, 0:matrixSize]
    xx = ((1.0 - 2.0 / matrixSize * xx) + center[0]) / radius[0]
    yy = ((1.0 - 2.0 / matrixSize * yy) + center[1]) / radius[1]
    rad = numpy.sqrt(numpy.power(xx, 2) + numpy.power(yy, 2))
    return rad


def makeGauss(x, mean=0.0, sd=1.0, gain=1.0, base=0.0):
    """
    Return the gaussian distribution for a given set of x-vals

   :Parameters:
        mean: float
            the centre of the distribution
        sd: float
            the width of the distribution
        gain: float
            the height of the distribution
        base: float
            an offset added to the result

    """
    simpleGauss = numpy.exp((-numpy.power(mean - x, 2) / (2 * sd**2)))
    return base + gain * (simpleGauss)

def make2DGauss(x,y, mean=0.0, sd=1.0, gain=1.0, base=0.0):
    """
    Return the gaussian distribution for a given set of x-vals

   :Parameters:
        x,y should be x and y indexes  as might be created by numpy.mgrid
        mean: float
            the centre of the distribution - may be a tuple
        sd: float
            the width of the distribution - may be a tuple
        gain: float
            the height of the distribution
        base: float
            an offset added to the result

    """
    
    if numpy.size(sd)==1:
        sd = [sd, sd]
    if numpy.size(mean)==1:
        mean = [mean, mean]
        
    simpleGauss = numpy.exp((-numpy.power(x - mean[0], 2) / (2 * sd[0]**2))-(numpy.power(y - mean[1], 2) / (2 * sd[1]**2)))
    return base + gain * (simpleGauss)

def getRMScontrast(matrix):
    """Returns the RMS contrast (the sample standard deviation) of a array
    """
    RMScontrast = numpy.std(matrix)
    return RMScontrast


def conv2d(smaller, larger):
    """Convolve a pair of 2d numpy matrices.

    Uses fourier transform method, so faster if larger matrix
    has dimensions of size 2**n

    Actually right now the matrices must be the same size (will sort out
    padding issues another day!)
    """
    smallerFFT = fft2(smaller)
    largerFFT = fft2(larger)

    invFFT = ifft2(smallerFFT * largerFFT)
    return invFFT.real


def imfft(X):
    """Perform 2D FFT on an image and center low frequencies
    """
    return fftshift(fft2(X))


def imifft(X):
    """Inverse 2D FFT with decentering
    """
    return numpy.abs(ifft2(ifftshift(X)))


def butter2d_lp(size, cutoff, n=3):
    """Create lowpass 2D Butterworth filter.

       :Parameters:
           size : tuple
               size of the filter
           cutoff : float
               relative cutoff frequency of the filter (0 - 1.0)
           n : int, optional
               order of the filter, the higher n is the sharper
               the transition is.

       :Returns:
           numpy.ndarray
             filter kernel in 2D centered
       """
    if not 0 < cutoff <= 1.0:
        raise ValueError('Cutoff frequency must be between 0 and 1.0')

    if not isinstance(n, int):
        raise ValueError('n must be an integer >= 1')

    rows, cols = size

    x = numpy.linspace(-0.5, 0.5, cols)
    y = numpy.linspace(-0.5, 0.5, rows)

    # An array with every pixel = radius relative to center
    radius = numpy.sqrt((x**2)[numpy.newaxis] + (y**2)[:, numpy.newaxis])

    f = 1 / (1.0 + (radius/cutoff)**(2 * n))   # The filter
    return f


def butter2d_bp(size, cutin, cutoff, n):
    """Bandpass Butterworth filter in two dimensions.

    :Parameters:
        size : tuple
            size of the filter
        cutin : float
            relative cutin  frequency of the filter (0 - 1.0)
        cutoff : float
            relative cutoff frequency of the filter (0 - 1.0)
        n : int, optional
            order of the filter, the higher n is the sharper
            the transition is.

    :Returns:
        numpy.ndarray
          filter kernel in 2D centered

    """

    return butter2d_lp(size, cutoff, n) - butter2d_lp(size, cutin, n)


def butter2d_hp(size, cutoff, n=3):
    """Highpass Butterworth filter in two dimensions.

    :Parameters:
        size : tuple
            size of the filter
        cutoff : float
            relative cutoff frequency of the filter (0 - 1.0)
        n : int, optional
            order of the filter, the higher n is the sharper
            the transition is.

    :Returns:
        numpy.ndarray:
            filter kernel in 2D centered

    """
    return 1.0 - butter2d_lp(size, cutoff, n)


def butter2d_lp_elliptic(size, cutoff_x, cutoff_y, n=3,
                         alpha=0, offset_x=0, offset_y=0):
    """Butterworth lowpass filter of any elliptical shape.

    :Parameters:
        size : tuple
            size of the filter
        cutoff_x, cutoff_y : float, float
            relative cutoff frequency of the filter (0 - 1.0) for x and y axes
        alpha : float, optional
            rotation angle (in radians)
        offset_x, offset_y : float
            offsets for the ellipsoid
        n : int, optional
            order of the filter, the higher n is the sharper
            the transition is.

    :Returns:
        numpy.ndarray:
            filter kernel in 2D centered

    """

    if not (0 < cutoff_x <= 1.0):
        raise ValueError('cutoff_x frequency must be between 0 and 1')
    if not (0 < cutoff_y <= 1.0):
        raise ValueError('cutoff_y frequency must be between 0 and 1')

    rows, cols = size

    # this time we start up with 2D arrays for easy broadcasting
    x = (numpy.linspace(-0.5, 0.5, cols) - offset_x)[numpy.newaxis]
    y = (numpy.linspace(-0.5, 0.5, rows) - offset_y)[:, numpy.newaxis]

    x2 = (x * numpy.cos(alpha) - y * numpy.sin(-alpha))
    y2 = (x * numpy.sin(-alpha) + y * numpy.cos(alpha))

    f = 1 / (1+((x2/(cutoff_x))**2+(y2/(cutoff_y))**2)**n)

    return f
