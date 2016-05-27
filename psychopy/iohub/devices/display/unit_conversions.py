# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2013 Josh Borah
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
#
# fileauthor:: Sol Simpson <sol@isolver-software.com>
# fileauthor:: Josh Borah <josh@a-s-l.com>

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


def distToPixel(
        hpix_per_dist_unit,
        vpix_per_dist_unit,
        pixHres,
        pixVres,
        distH,
        distV):
    pixH = pixHres / 2.0 + (distH * hpix_per_dist_unit)
    pixV = pixVres / 2.0 + (distV * vpix_per_dist_unit)
    return pixH, pixV


def pixelToDist(
        hpix_per_dist_unit,
        vpix_per_dist_unit,
        pixHres,
        pixVres,
        pixH,
        pixV):
    distH = (pixH - pixHres / 2.0) / hpix_per_dist_unit
    distV = (pixV - pixVres / 2.0) / vpix_per_dist_unit
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


def convertDistToNd(eye2display, distH, distV):
    ndH = 57.2958 * distH / eye2display
    ndV = 57.2958 * distV / eye2display
    return ndH, ndV


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
    caH = 57.2958 * atan(distH / eye2display)
    caV = 57.2958 * atan(distV / eye2display)
    return caH, caV


def caToDist(eye2display, caH, caV):
    distH = eye2display * tan(caH / 57.2958)
    distV = eye2display * tan(caV / 57.2968)
    return distH, distV


#
# Convert between distance coordinates (distH, distV) and Fick Coordinates (as,el)
#
def distToFick(eye2display, distH, distV):
    az = 57.2958 * atan(distH / eye2display)
    el = 57.2958 * atan(distV / sqrt(eye2display *
                                     eye2display + distH * distH))
    return az, el


def fickToDist(eye2display, az, el):
    distH = eye2display * tan(az / 57.2958)
    distV = sqrt(eye2display * eye2display + distH * distH) * tan(el / 57.2958)
    return distH / distV

#
# Convert between distance coordinates (distH, distV) and 'symmetric angle'
# coordinates (saH, saV).
# 'Symmetric angles' are visual angles between a point on the display and the central
# axes lines, measured along lines parallel to the display axes.  The vertical coordinate is
# same as the Fick elevation angle.  The horizontal coordinate is measured in a
# symmetrical fashion and is not the same as the Fick azimuth angle.
#


def distToSa(eye2display, distH, distV):
    saH = 57.2958 * atan(distH / sqrt(eye2display *
                                      eye2display + distV * distV))
    saV = 57.2958 * atan(distV / sqrt(eye2display *
                                      eye2display + distH * distH))
    return saH, saV


def saToDist(eye2dsply, saH, saV):
    tansaV_sqrd = tan(saV / 57.2958) * tan(saV / 57.2958)
    tansaH_sqrd = tan(saH / 57.2958) * tan(saH / 57.2958)
    Dsqrd = eye2dsply * eye2dsply

    signsaV = 1.0
    if saV < 0.0:
        signsaV = -1.0

    signsaH = 1.0
    if saH < 0.0:
        signsaH = -1.0

    distV = signsaV * sqrt((Dsqrd * tansaV_sqrd + Dsqrd *
                            tansaH_sqrd * tansaV_sqrd) / (1 - tansaH_sqrd * tansaV_sqrd))

    distH = signsaH * sqrt((Dsqrd + distV * distV) * tansaH_sqrd)

    return distV, distH

#-------------------------------------
# Old code using matrix multiplication to convert between screen pix and
# experiment software coord system...

#        if coord_type=='pix':

#        origin=self.getOrigin()
#        if origin not in Display._supported_origin_types:
#            print2err(" *** Display device error: Unknown origin type: {0}".format(origin))
#            return
#
#        x1,y1,x2,y2=self.getBounds()
#        print2err('getBounds: ',self.getBounds(),  )
#
#        bounds_matrix=np.matrix([[x1,y1,1,0],[-y1,x1,0,1],[x2,y2,1,0],[-y2,x2,0,1]])
#
#        cx1=None
#        cy1=None
#        cx2=None
#        cy2=None
#
##        if coord_type == 'org':
##            cx1=x1
##            cy1=y1
##            cx2=x2
##            cy2=y2
#        if coord_type == 'pix':
#            if origin == 'center':
#                cx1=-pixel_width/2.0
#                cy1=pixel_height/2.0
#                cx2=pixel_width/2.0
#                cy2=-pixel_height/2.0
##            elif origin == 'top_left':
##                cx1=0
##                cy1=0
##                cx2=pixel_width
##                cy2=pixel_height
##            elif origin == 'bottom_left':
##                cx1=0
##                cy1=pixel_height
##                cx2=pixel_width
##                cy2=0
#        elif coord_type in ['mm','cm','inch']:
#            phys_to_coord_ratio=1.0
##            if coord_type == 'mm':
##                if phys_unit_type == 'cm':
##                    phys_to_coord_ratio=10.0
##                elif phys_unit_type == 'inch':
##                    phys_to_coord_ratio=25.4
#            if coord_type == 'cm':
#                if phys_unit_type == 'mm':
#                    phys_to_coord_ratio=0.1
#                elif phys_unit_type == 'inch':
#                    phys_to_coord_ratio=2.54
##            elif coord_type == 'inch':
##                if phys_unit_type == 'mm':
##                    phys_to_coord_ratio=0.0393701
##                elif phys_unit_type == 'cm':
##                    phys_to_coord_ratio=0.393701
#
#            if origin == 'center':
#                phys_to_coord_ratio=2.0*phys_to_coord_ratio
#                cx1=-phys_width/phys_to_coord_ratio
#                cy1=phys_height/phys_to_coord_ratio
#                cx2=phys_width/phys_to_coord_ratio
#                cy2=-phys_height/phys_to_coord_ratio
##            elif origin == 'top_left':
##                cx1=0.0
##                cy1=0.0
##                cx2=phys_width*phys_to_coord_ratio
##                cy2=phys_height*phys_to_coord_ratio
##            elif origin == 'bottom_left':
##                cx1=0.0
##                cy1=phys_height*phys_to_coord_ratio
##                cx2=phys_width*phys_to_coord_ratio
##                cy2=0.0
#        elif coord_type == 'norm':
#            if origin == 'center':
#                cx1=-1.0
#                cy1=1.0
#                cx2=1.0
#                cy2=-1.0
##            elif origin == 'top_left':
##                cx1=0.0
##                cy1=0.0
##                cx2=1.0
##                cy2=1.0
##            elif origin == 'bottom_left':
##                cx1=0.0
##                cy1=1.0
##                cx2=1.0
##                cy2=0.0
##        elif coord_type == 'percent':
##            if origin == 'center':
##                cx1=-50.0
##                cy1=50.0
##                cx2=50.0
##                cy2=-50.0
##            elif origin == 'top_left':
##                cx1=0.0
##                cy1=0.0
##                cx2=100.0
##                cy2=100.0
##            elif origin == 'bottom_left':
##                cx1=0.0
##                cy1=100.0
##                cx2=100.0
##                cy2=0.0
#        elif coord_type == 'deg':
#            if origin == 'center':
#                cx1=-degree_width/2.0
#                cy1=degree_height/2.0
#                cx2=degree_width/2.0
#                cy2=-degree_height/2.0
##            elif origin == 'top_left':
##                cx1=0.0
##                cy1=0.0
##                cx2=degree_width
##                cy2=degree_height
##            elif origin == 'bottom_left':
##                cx1=0.0
##                cy1=degree_height
##                cx2=degree_width
##                cy2=0.0
#
#        if cx1 is not None and cy1 is not None  and cx2 is not None and cy2 is not None :
#            coord_matrix=np.matrix( [[cx1],[cy1],[cx2],[cy2]] )
#            abcd = np.linalg.solve(bounds_matrix, coord_matrix)
#            a,b,c,d=np.array(abcd)[:,0]
#            #print2err('abcd: {0}\n a={1}, b={2} , c={3}, d={4}'.format(abcd,a,b,c,d))
#
#
#            def pix2coord(self, x,y,display_index=None):
#                #print2err('Display {0} bounds: {1}'.format(display_index,self.getBounds()))
#                if display_index == self.getIndex():
#                    return a*x+b*y+c, b*x-a*y+d
#                return x,y
#
#            self._pix2coord=pix2coord
#
#            def coord2pix(self,cx,cy,display_index=None):
#                if display_index == self.getIndex():
#                    aabb=(a**2+b**2)
#                    return (a*cx+b*cy-b*d-a*c)/aabb, (b*cx-a*cy-b*c+a*d)/aabb
#                return cx,cy
#
#            self._coord2pix=coord2pix

