#!/usr/bin/env python

"""Tools, nothing to do with psychophysics or experiments
- just handy things like conversion functions etc...
"""

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import numpy  # this is imported by psychopy.core
import random
from psychopy import logging, monitors

import os
import shutil
import glob
import cPickle
try:
    from PIL import Image
except ImportError:
    import Image




def float_uint8(inarray):
    """Converts arrays, lists, tuples and floats ranging -1:1
    into an array of Uint8s ranging 0:255

    >>> float_uint8(-1)
    0
    >>> float_uint8(0)
    128

    """
    retVal = numpy.around(255*(0.5+0.5*numpy.asarray(inarray)))
    return retVal.astype(numpy.uint8)
def uint8_float(inarray):
    """Converts arrays, lists, tuples and UINTs ranging 0:255
    into an array of floats ranging -1:1
    """
    return numpy.asarray(inarray,'f')/127.5 - 1
def float_uint16(inarray):
    """Converts arrays, lists, tuples and floats ranging -1:1
    into an array of Uint16s ranging 0:2^16
    """
    i16max = 2**16 - 1
    retVal = numpy.around(i16max*(1.0+numpy.asarray(inarray))/2.0)
    return retVal.astype(numpy.UnsignedInt16)

def sph2cart(*args):
    """Convert from spherical coordinates (elevation, azimuth, radius)
    to cartesian (x,y,z)

    usage:
        array3xN[x,y,z] = sph2cart(array3xN[el,az,rad])
        OR
        x,y,z = sph2cart(elev, azim, radius)
    """
    if len(args)==1:    #received an Nx3 array
        elev = args[0][0,:]
        azim = args[0][1,:]
        radius = args[0][2,:]
        returnAsArray = True
    elif len(args)==3:
        elev = args[0]
        azim = args[1]
        radius = args[2]
        returnAsArray = False

    z = radius * numpy.sin(radians(elev))
    x = radius * numpy.cos(radians(elev))*numpy.cos(radians(azim))
    y = radius * numpy.cos(radians(elev))*numpy.sin(radians(azim))
    if returnAsArray:
        return numpy.asarray([x, y, z])
    else:
        return x, y, z

def cart2sph(z, y, x):
    """Convert from cartesian coordinates (x,y,z) to spherical (elevation,
    azimuth, radius). Output is in degrees.

    usage:
        array3xN[el,az,rad] = cart2sph(array3xN[x,y,z])
        OR
        elevation, azimuth, radius = cart2sph(x,y,z)

        If working in DKL space, z = Luminance, y = S and x = LM"""
    width = len(z)

    elevation = numpy.empty([width,width])
    radius = numpy.empty([width,width])
    azimuth = numpy.empty([width,width])

    radius = numpy.sqrt(x**2 + y**2 + z**2)
    azimuth = numpy.arctan2(y, x)
    #Calculating the elevation from x,y up
    elevation = numpy.arctan2(z, numpy.sqrt(x**2+y**2))

#convert azimuth and elevation angles into degrees
    azimuth *=(180.0/numpy.pi)
    elevation *=(180.0/numpy.pi)

    sphere = numpy.array([elevation, azimuth, radius])
    sphere = numpy.rollaxis(sphere, 0, 3)

    return sphere


#---color conversions---#000000#FFFFFF------------------------------------------

def dkl2rgb(dkl, conversionMatrix=None):
    """Convert from DKL color space (cone-opponent space from Derrington,
    Krauskopf & Lennie) to RGB.

    Requires a conversion matrix, which will be generated from generic
    Sony Trinitron phosphors if not supplied (note that this will not be
    an accurate representation of the color space unless you supply a
    conversion matrix).

    usage::

        rgb(Nx3) = dkl2rgb(dkl_Nx3(el,az,radius), conversionMatrix)
        rgb(NxNx3) = dkl2rgb(dkl_NxNx3(el,az,radius), conversionMatrix)

    """
    if conversionMatrix==None:
        conversionMatrix = numpy.asarray([ \
            #LUMIN    %L-M    %L+M-S  (note that dkl has to be in cartesian coords first!)
            [1.0000, 1.0000, -0.1462],#R
            [1.0000, -0.3900, 0.2094],#G
            [1.0000, 0.0180, -1.0000]])#B
        logging.warning('This monitor has not been color-calibrated. Using default DKL conversion matrix.')

    if len(dkl.shape)==3:
        dkl_NxNx3 = dkl
        """convert a 2D (image) of Spherical DKL colours to RGB space"""
        origShape = dkl_NxNx3.shape#remember for later
        NxN = origShape[0]*origShape[1]#find nPixels
        dkl = numpy.reshape(dkl_NxNx3,[NxN,3])#make Nx3
        rgb = dkl2rgb(dkl,conversionMatrix)#convert
        return numpy.reshape(rgb,origShape)#reshape and return

    else:
        dkl_Nx3=dkl
        dkl_3xN = numpy.transpose(dkl_Nx3)#its easier to use in the other orientation!
        if numpy.size(dkl_3xN)==3:
            RG, BY, LUM = sph2cart(dkl_3xN[0],dkl_3xN[1],dkl_3xN[2])
        else:
            RG, BY, LUM = sph2cart(dkl_3xN[0,:],dkl_3xN[1,:],dkl_3xN[2,:])
        dkl_cartesian = numpy.asarray([LUM, RG, BY])
        rgb = numpy.dot(conversionMatrix, dkl_cartesian)

        return numpy.transpose(rgb)#return in the shape we received it


def dklCart2rgb(LUM, LM, S, conversionMatrix=None):
    """Like dkl2rgb except that it uses cartesian coords (LM,S,LUM) rather than
    spherical coords for DKL (elev, azim, contr)

    NB: this may return rgb values >1 or <-1
    """
    NxNx3=list(LUM.shape)
    NxNx3.append(3)
    dkl_cartesian = numpy.asarray([LUM.reshape([-1]), LM.reshape([-1]), S.reshape([-1])])

    if conversionMatrix==None:
        conversionMatrix = numpy.asarray([ \
            #LUMIN    %L-M    %L+M-S  (note that dkl has to be in cartesian coords first!)
            [1.0000, 1.0000, -0.1462],#R
            [1.0000, -0.3900, 0.2094],#G
            [1.0000, 0.0180, -1.0000]])#B
    rgb = numpy.dot(conversionMatrix, dkl_cartesian)
    return numpy.reshape(numpy.transpose(rgb), NxNx3)

def rgb2dklCart(picture, conversionMatrix=None):
    """Convert an RGB image into Cartesian DKL space"""
    #Turn the picture into an array so we can do maths
    picture=numpy.array(picture)
    #Find the original dimensions of the picture
    origShape = picture.shape

    #this is the inversion of the dkl2rgb conversion matrix
    if conversionMatrix==None:
        conversionMatrix = numpy.asarray([\
            #LUMIN->%L-M->L+M-S
            [ 0.25145542,  0.64933633,  0.09920825],
            [ 0.78737943, -0.55586618, -0.23151325],
            [ 0.26562825,  0.63933074, -0.90495899]])
        logging.warning('This monitor has not been color-calibrated. Using default DKL conversion matrix.')
    else:
        conversionMatrix = numpy.linalg.inv(conversionMatrix)

    #Reshape the picture so that it can multiplied by the conversion matrix
    red = picture[:,:,0]
    green = picture[:,:,1]
    blue = picture[:,:,2]

    dkl = numpy.asarray([red.reshape([-1]), green.reshape([-1]), blue.reshape([-1])])

    #Multiply the picture by the conversion matrix
    dkl=numpy.dot(conversionMatrix, dkl)

    #Reshape the picture so that it's back to it's original shape
    dklPicture = numpy.reshape(numpy.transpose(dkl), origShape)
    return dklPicture

def lms2rgb(lms_Nx3, conversionMatrix=None):
    """Convert from cone space (Long, Medium, Short) to RGB.

    Requires a conversion matrix, which will be generated from generic
    Sony Trinitron phosphors if not supplied (note that you will not get
    an accurate representation of the color space unless you supply a
    conversion matrix)

    usage::

        rgb_Nx3 = lms2rgb(dkl_Nx3(el,az,radius), conversionMatrix)

    """

    lms_3xN = numpy.transpose(lms_Nx3)#its easier to use in the other orientation!

    if conversionMatrix==None:
        cones_to_rgb = numpy.asarray([ \
            #L        M        S
            [ 4.97068857, -4.14354132, 0.17285275],#R
            [-0.90913894, 2.15671326, -0.24757432],#G
            [-0.03976551, -0.14253782, 1.18230333]#B
            ])
        logging.warning('This monitor has not been color-calibrated. Using default LMS conversion matrix.')
    else:
        cones_to_rgb=conversionMatrix

    rgb = numpy.dot(cones_to_rgb, lms_3xN)
    return numpy.transpose(rgb)#return in the shape we received it

def rgb2lms(rgb_Nx3, conversionMatrix=None):
    """Convert from RGB to cone space (LMS)

    Requires a conversion matrix, which will be generated from generic
    Sony Trinitron phosphors if not supplied (note that you will not get
    an accurate representation of the color space unless you supply a
    conversion matrix)

    usage::

        lms_Nx3 = rgb2lms(rgb_Nx3(el,az,radius), conversionMatrix)

    """

    rgb_3xN = numpy.transpose(rgb_Nx3)#its easier to use in the other orientation!

    if conversionMatrix==None:
        cones_to_rgb = numpy.asarray([ \
            #L        M        S
            [ 4.97068857, -4.14354132, 0.17285275],#R
            [-0.90913894, 2.15671326, -0.24757432],#G
            [-0.03976551, -0.14253782, 1.18230333]#B
            ])
        logging.warning('This monitor has not been color-calibrated. Using default LMS conversion matrix.')
    else:
        cones_to_rgb=conversionMatrix
    rgb_to_cones = numpy.linalg.inv(cones_to_rgb)

    lms = numpy.dot(rgb_to_cones, rgb_3xN)
    return numpy.transpose(lms)#return in the shape we received it

def hsv2rgb(hsv_Nx3):
    """Convert from HSV color space to RGB gun values

    usage::

        rgb_Nx3 = hsv2rgb(hsv_Nx3)

    Note that in some uses of HSV space the Hue component is given in radians or
    cycles (range 0:1]). In this version H is given in degrees (0:360).

    Also note that the RGB output ranges -1:1, in keeping with other PsychoPy functions
    """
    #based on method in http://en.wikipedia.org/wiki/HSL_and_HSV#Converting_to_RGB
    hsv_Nx3 = numpy.asarray(hsv_Nx3, dtype=float)
    #we expect a 2D array so convert there if needed
    origShape = hsv_Nx3.shape
    hsv_Nx3 = hsv_Nx3.reshape([-1,3])

    H_ = (hsv_Nx3[:,0]%360)/60.0 #this is H' in the wikipedia version
    C = hsv_Nx3[:,1]*hsv_Nx3[:,2] #multiply H and V to give chroma (color intensity)
    X = C*(1-abs(H_%2-1))

    #rgb starts
    rgb=hsv_Nx3*0#only need to change things that are no longer zero
    II = (0<=H_)*(H_<1)
    rgb[II,0]=C[II]
    rgb[II,1]=X[II]
    II = (1<=H_)*(H_<2)
    rgb[II,0]=X[II]
    rgb[II,1]=C[II]
    II = (2<=H_)*(H_<3)
    rgb[II,1]=C[II]
    rgb[II,2]=X[II]
    II = (3<=H_)*(H_<4)
    rgb[II,1]=X[II]
    rgb[II,2]=C[II]
    II = (4<=H_)*(H_<5)
    rgb[II,0]=X[II]
    rgb[II,2]=C[II]
    II = (5<=H_)*(H_<6)
    rgb[II,0]=C[II]
    rgb[II,2]=X[II]
    m=(hsv_Nx3[:,2] - C)
    rgb +=  m.reshape([len(m),1])# V-C is sometimes called m
    return rgb.reshape(origShape)*2-1


#--- coordinate transforms ---------------------------------------------


def pol2cart(theta, radius, units='deg'):
    """Convert from polar to cartesian coordinates

    usage::

        x,y = pol2cart(theta, radius, units='deg')

    """
    if units in ['deg', 'degs']:
        theta = theta*numpy.pi/180.0
    xx = radius*numpy.cos(theta)
    yy = radius*numpy.sin(theta)

    return xx,yy


#----------------------------------------------------------------------
def  cart2pol(x,y, units='deg'):
    """Convert from cartesian to polar coordinates

    :usage:

        theta, radius = pol2cart(x, y, units='deg')

    units refers to the units (rad or deg) for theta that should be returned
    """
    radius= numpy.hypot(x,y)
    theta= numpy.arctan2(y,x)
    if units in ['deg', 'degs']:
        theta=theta*180/numpy.pi
    return theta, radius

def plotFrameIntervals(intervals):
    """Plot a histogram of the frame intervals.

    Where `intervals` is either a filename to a file, saved by Window.saveFrameIntervals
    or simply a list (or array) of frame intervals

    """
    from pylab import hist, show, plot

    if type(intervals)==str:
        f = open(intervals, 'r')
        exec("intervals = [%s]" %(f.readline()))
    #    hist(intervals, int(len(intervals)/10))
    plot(intervals)
    show()

