#!/usr/bin/env python

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Container for all miscellaneous functions and classes'''

from psychopy.misc.arraytools import (createXYs, extendArr, makeRadialMatrix,
                                      ratioRange, shuffleArray, val2array)

from psychopy.misc.attributetools import attributeSetter, setWithOperation

from psychopy.misc.colorspacetools import (dkl2rgb, dklCart2rgb,
                                           hsv2rgb, lms2rgb,
                                           rgb2dklCart, rgb2lms)

from psychopy.misc.coordinatetools import (cart2pol, pol2cart,
                                           cart2sph, sph2cart)

from psychopy.misc.fileerrortools import handleFileCollision

from psychopy.misc.filetools import toFile, fromFile, mergeFolder

from psychopy.misc.imagetools import array2image, image2array, makeImageAuto

from psychopy.misc.monitorunittools import (cm2deg, deg2cm, cm2pix, pix2cm,
                                            deg2pix, pix2deg)

from psychopy.misc.plottools import plotFrameIntervals

from psychopy.misc.typetools import float_uint8, float_uint16, uint8_float

from psychopy.misc.unittools import radians
