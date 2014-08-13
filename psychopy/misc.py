#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Wrapper for all miscellaneous functions and classes from psychopy.tools'''

from psychopy.tools.arraytools import (createXYs, extendArr, makeRadialMatrix,
                                       ratioRange, shuffleArray, val2array)

from psychopy.tools.attributetools import attributeSetter, setWithOperation

from psychopy.tools.colorspacetools import (dkl2rgb, dklCart2rgb,
                                            hsv2rgb, lms2rgb,
                                            rgb2dklCart, rgb2lms)

from psychopy.tools.coordinatetools import (cart2pol, pol2cart,
                                            cart2sph, sph2cart)

from psychopy.tools.fileerrortools import handleFileCollision

from psychopy.tools.filetools import toFile, fromFile, mergeFolder

from psychopy.tools.imagetools import array2image, image2array, makeImageAuto

from psychopy.tools.monitorunittools import (cm2deg, deg2cm, cm2pix, pix2cm,
                                             deg2pix, pix2deg, convertToPix)

from psychopy.tools.plottools import plotFrameIntervals

from psychopy.tools.typetools import float_uint8, float_uint16, uint8_float

from psychopy.tools.unittools import radians

def extendArr(inArray, newSize):
    """Takes a numpy array and returns it padded with zeros to the necessary size

    >>> misc.extendArr([1,2,3],5)
    array([1, 2, 3, 0, 0])
    """
    def copyDims(source, destination):
        if len(source.shape) == 1:
            destination[:len(source)] = source
        else:
            for i in range(len(source)):
                copyDims(source[i], destination[i])
    
    if type(inArray) in [tuple,list]:
        inArray=numpy.asarray(inArray)

    newArr = numpy.zeros(newSize,inArray.dtype)

    #e.g.
    #newArr[0:4,0:3]=inArray
    copyDims(inArray, newArr)
    return newArr