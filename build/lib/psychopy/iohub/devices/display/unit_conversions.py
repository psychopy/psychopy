"""
ioHub
.. file: iohub/devices/display/unit_conversion.py

Sudo code provided by Josh Borah
Converted to Python by Sol Simpson

This file Copyright (C) 2012 Josh Borah, 2012-2013 iSolver Software Solutions

Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>, Josh Borah <josh@a-s-l.com>
"""

from math import atan, tan, sqrt

#
# distToPixel
#
# Convert between distance coordinates and pixel coordinates.
#
# Distance coordinates are 2D Cartesian coordinates, measured from an origin at the
# center pixel,  and are real distance units (inches, centimeters, etc.) along horizontal and
# vertical screen axes.
#
def distToPixel(hpix_per_dist_unit, vpix_per_dist_unit, pixHres, pixVres, distH, distV):
    pixH = pixHres/2.0 + (distH * hpix_per_dist_unit)
    pixV = pixVres/2.0 + (distV * vpix_per_dist_unit)
    return pixH, pixV

def pixelToDist(hpix_per_dist_unit,vpix_per_dist_unit,pixHres, pixVres, pixH, pixV):
    distH = (pixH - pixHres/2.0) / hpix_per_dist_unit
    distV = (pixV - pixVres/2.0) / vpix_per_dist_unit
    return distH, distV

#
# All of following assume a nominal eye point 'eye2display' distance units from display
# with line-of-gaze normal to the display at the display center.  Angle variable are
# assumed to have units of degrees.
#
# Since the Python math lib trig functions work with radians,
# a radian to angle conversion factor (deg/rad = 57.2958) is included to give angle
# variables 'degree' units.
#

#
# Convert between distance coordinates (distH, distV) and 'normalized Cartesian
# coordinates' (ndH, ndV).
#
# 'Normalized Cartesian coordinates' are Cartesian distance coordinates, normalized by
# by the distance from the nominal eye point to the display.  For very small distances
# from the origin, these values coorespond to visual angle from the origin along the
# horizontal and vertical display axes. A factor of 57.2958 is used so that the values
# correspond to degrees rather than radians.
#
def convertDistToNd(eye2display,distH,distV):
    ndH =  57.2958 * distH / eye2display
    ndV =  57.2958 * distV / eye2display
    return ndH,ndV

def convertNdToDist(eye2display, ndH, ndV):
    distH = ndH * eye2display / 57.2958
    distV = ndV * eye2display / 57.2958
    return distH, distV

#
# Convert between distance coordinates (distH, distV) and
# 'Cartesian Angles' (caH, caV).
# 'Cartesian Angles' are visual angles (from nominal eye point) along
# horizontal and vertical display axes.  In other words, the horizontal coordinate is the
# visual angle between the origin and the intersection of the Cartesian
# coordinate line with the horizontal axes.
#
def distToCa(eye2display, distH, distV):
    caH = 57.2958 * atan( distH/eye2display )
    caV = 57.2958 * atan( distV/eye2display )
    return caH,caV

def caToDist(eye2display, caH, caV):
    distH =  eye2display * tan(caH/57.2958)
    distV = eye2display * tan(caV/57.2968)
    return distH,distV


#
# Convert between distance coordinates (distH, distV) and Fick Coordinates (as,el)
#
def distToFick(eye2display,distH,distV):
    az = 57.2958 * atan( distH/eye2display )
    el =  57.2958 * atan( distV/ sqrt( eye2display * eye2display + distH * distH ) )
    return az,el

def fickToDist(eye2display, az, el):
    distH = eye2display * tan( az/57.2958 )
    distV = sqrt(eye2display * eye2display + distH * distH) * tan( el/57.2958 )
    return distH/distV

#
# Convert between distance coordinates (distH, distV) and 'symmetric angle'
# coordinates (saH, saV).
# 'Symmetric angles' are visual angles between a point on the display and the central
# axes lines, measured along lines parallel to the display axes.  The vertical coordinate is
# same as the Fick elevation angle.  The horizontal coordinate is measured in a
# symmetrical fashion and is not the same as the Fick azimuth angle.
#
def distToSa(eye2display, distH, distV):
    saH = 57.2958 * atan(distH/ sqrt(eye2display * eye2display + distV * distV))
    saV = 57.2958 * atan(distV/ sqrt(eye2display * eye2display + distH * distH))
    return saH,saV

def saToDist(eye2dsply, saH, saV):
    tansaV_sqrd = tan( saV/57.2958) * tan( saV/57.2958)
    tansaH_sqrd = tan( saH/57.2958) * tan( saH/57.2958)
    Dsqrd = eye2dsply * eye2dsply

    signsaV = 1.0
    if saV < 0.0:
        signsaV = -1.0

    signsaH = 1.0
    if saH < 0.0:
        signsaH = -1.0

    distV = signsaV * sqrt((Dsqrd * tansaV_sqrd  + Dsqrd * tansaH_sqrd * tansaV_sqrd)/ ( 1- tansaH_sqrd * tansaV_sqrd ))

    distH = signsaH * sqrt((Dsqrd + distV * distV) * tansaH_sqrd)

    return distV,distH
