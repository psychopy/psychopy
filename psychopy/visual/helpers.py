#!/usr/bin/env python2

'''Helper functions shared by the visual classes'''

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import os

import psychopy  # so we can get the __path__
from psychopy import core, logging, colors

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import setAttribute

import numpy

reportNImageResizes = 5  # stop raising warning after this
global _nImageResizes
_nImageResizes = 0

try:
    import matplotlib
    if matplotlib.__version__ > '1.2':
        from matplotlib.path import Path as mpl_Path
    else:
        from matplotlib import nxutils
    haveMatplotlib = True
except:
    haveMatplotlib = False

def pointInPolygon(x, y, poly):
    """Determine if a point is inside a polygon; returns True if inside.

    (`x`, `y`) is the point to test. `poly` is a list of 3 or more vertices as
    (x,y) pairs. If given an object, such as a `ShapeStim`, will try to use its
    vertices and position as the polygon.

    Same as the `.contains()` method elsewhere.
    """
    try: #do this using try:...except rather than hasattr() for speed
        poly = poly.verticesPix #we want to access this only once
    except:
        pass
    nVert = len(poly)
    if nVert < 3:
        msg = 'pointInPolygon expects a polygon with 3 or more vertices'
        logging.warning(msg)
        return False

    # faster if have matplotlib tools:
    if haveMatplotlib:
        if matplotlib.__version__ > '1.2':
            return mpl_Path(poly).contains_point([x,y])
        else:
            try:
                return bool(nxutils.pnpoly(x, y, poly))
            except:
                pass

    # fall through to pure python:
    # as adapted from http://local.wasp.uwa.edu.au/~pbourke/geometry/insidepoly/
    # via http://www.ariel.com.au/a/python-point-int-poly.html

    inside = False
    # trace (horizontal?) rays, flip inside status if cross an edge:
    p1x, p1y = poly[-1]
    for p2x, p2y in poly:
        if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if p1x == p2x or x <= xints:
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def polygonsOverlap(poly1, poly2):
    """Determine if two polygons intersect; can fail for very pointy polygons.

    Accepts two polygons, as lists of vertices (x,y) pairs. If given an object
    with with (vertices + pos), will try to use that as the polygon.

    Checks if any vertex of one polygon is inside the other polygon. Same as
    the `.overlaps()` method elsewhere.
    """
    try: #do this using try:...except rather than hasattr() for speed
        poly1 = poly1.verticesPix #we want to access this only once
    except:
        pass
    try: #do this using try:...except rather than hasattr() for speed
        poly2 = poly2.verticesPix #we want to access this only once
    except:
        pass
    # faster if have matplotlib tools:
    if haveMatplotlib:
        if matplotlib.__version__ > '1.2':
            if any(mpl_Path(poly1).contains_points(poly2)):
                return True
            return any(mpl_Path(poly2).contains_points(poly1))
        else:
            try: # deprecated in matplotlib 1.2
                if any(nxutils.points_inside_poly(poly1, poly2)):
                    return True
                return any(nxutils.points_inside_poly(poly2, poly1))
            except: pass

    # fall through to pure python:
    for p1 in poly1:
        if pointInPolygon(p1[0], p1[1], poly2):
            return True
    for p2 in poly2:
        if pointInPolygon(p2[0], p2[1], poly1):
            return True
    return False

def setTexIfNoShaders(obj):
    """Useful decorator for classes that need to update Texture after other properties
    This doesn't actually perform the update, but sets a flag so the update occurs
    at draw time (in case multiple changes all need updates only do it once)
    """
    if hasattr(obj, 'useShaders') and not obj.useShaders:
        #we aren't using shaders
        if hasattr(obj, '_needTextureUpdate'):
            obj._needTextureUpdate = True

def setColor(obj, color, colorSpace=None, operation='',
                rgbAttrib='rgb', #or 'fillRGB' etc
                colorAttrib='color', #or 'fillColor' etc
                colorSpaceAttrib=None, #e.g. 'colorSpace' or 'fillColorSpace'
                log=True):
    """Provides the workings needed by setColor, and can perform this for
    any arbitrary color type (e.g. fillColor,lineColor etc).

    OBS: log argument is deprecated - has no effect now. Logging should be done
    when setColor() is called.
    """

    #how this works:
    #rather than using obj.rgb=rgb this function uses setattr(obj,'rgb',rgb)
    #color represents the color in the native space
    #colorAttrib is the name that color will be assigned using setattr(obj,colorAttrib,color)
    #rgb is calculated from converting color
    #rgbAttrib is the attribute name that rgb is stored under, e.g. lineRGB for obj.lineRGB
    #colorSpace and takes name from colorAttrib+space e.g. obj.lineRGBSpace=colorSpace

    if colorSpaceAttrib is None:
        colorSpaceAttrib = colorAttrib+'Space'

    # Handle strings and returns immediately as operations, colorspace etc. does not apply here.
    if type(color) in [str, unicode, numpy.string_]:
        if operation not in ('', None):
            raise TypeError('Cannot do operations on named or hex color')
        if color.lower() in colors.colors255.keys():
            #set rgb, color and colorSpace
            setattr(obj,rgbAttrib,numpy.array(colors.colors255[color.lower()], float))
            obj.__dict__[colorSpaceAttrib] = 'named'  #e.g. 3rSpace='named'
            obj.__dict__[colorAttrib] = color  #e.g. obj.color='red'
            setTexIfNoShaders(obj)
            return
        elif color[0]=='#' or color[0:2]=='0x':
            setattr(obj,rgbAttrib,numpy.array(colors.hex2rgb255(color)))#e.g. obj.rgb=[0,0,0]
            obj.__dict__[colorSpaceAttrib] = 'hex'  #e.g. obj.colorSpace='hex'
            obj.__dict__[colorAttrib] = color  #e.g. Qr='#000000'
            setTexIfNoShaders(obj)
            return
        #we got a string, but it isn't in the list of named colors and doesn't work as a hex
        else:
            raise AttributeError("PsychoPy can't interpret the color string '%s'" %color)

    # If it wasn't a string, do check and conversion of scalars, sequences and other stuff.
    else:
        color = val2array(color, length=3)  # enforces length 1 or 3

        if color is None:
            setattr(obj,rgbAttrib,None)#e.g. obj.rgb=[0,0,0]
            obj.__dict__[colorSpaceAttrib] = None  #e.g. obj.colorSpace='hex'
            obj.__dict__[colorAttrib] = None  #e.g. obj.color='#000000'
            setTexIfNoShaders(obj)

    #at this point we have a numpy array of 3 vals
    #check if colorSpace is given and use obj.colorSpace if not
    if colorSpace is None:
        colorSpace=getattr(obj,colorSpaceAttrib)
        #using previous color space - if we got this far in the _stColor function
        #then we haven't been given a color name - we don't know what color space to use.
        if colorSpace in ('named', 'hex'):
            logging.error("If you setColor with a numeric color value then you need to specify a color space, e.g. setColor([1,1,-1],'rgb'), unless you used a numeric value previously in which case PsychoPy will reuse that color space.)")
            return
    #check whether combining sensible colorSpaces (e.g. can't add things to hex or named colors)
    if operation!='' and getattr(obj,colorSpaceAttrib) in ['named','hex']:
            raise AttributeError("setColor() cannot combine ('%s') colors within 'named' or 'hex' color spaces"\
                %(operation))
    elif operation!='' and colorSpace!=getattr(obj,colorSpaceAttrib) :
            raise AttributeError("setColor cannot combine ('%s') colors from different colorSpaces (%s,%s)"\
                %(operation, obj.colorSpace, colorSpace))
    else:#OK to update current color
        if colorSpace == 'named':
            obj.__dict__[colorAttrib] = color  # operations don't make sense for named
        else:
            setAttribute(obj, colorAttrib, color, log=False, operation=operation, stealth=True)
    #get window (for color conversions)
    if colorSpace in ['dkl','lms']: #only needed for these spaces
        if hasattr(obj,'dkl_rgb'):
            win=obj #obj is probably a Window
        elif hasattr(obj, 'win'):
            win=obj.win #obj is probably a Stimulus
        else:
            win=None
            logging.error("_setColor() is being applied to something that has no known Window object")
    #convert new obj.color to rgb space
    newColor=getattr(obj, colorAttrib)
    if colorSpace in ['rgb','rgb255']:
        setattr(obj,rgbAttrib, newColor)
    elif colorSpace=='dkl':
        if numpy.all(win.dkl_rgb==numpy.ones([3,3])):
            dkl_rgb=None
        else:
            dkl_rgb=win.dkl_rgb
        setattr(obj,rgbAttrib, colors.dkl2rgb(numpy.asarray(newColor).transpose(), dkl_rgb) )
    elif colorSpace=='lms':
        if numpy.all(win.lms_rgb==numpy.ones([3,3])):
            lms_rgb=None
        elif win.monitor.getPsychopyVersion()<'1.76.00':
            logging.error("The LMS calibration for this monitor was carried out before version 1.76.00." +\
                      " We would STRONGLY recommend that you repeat the color calibration before using this color space (contact Jon for further info)")
            lms_rgb=win.lms_rgb
        else:
            lms_rgb=win.lms_rgb
        setattr(obj,rgbAttrib, colors.lms2rgb(newColor, lms_rgb) )
    elif colorSpace=='hsv':
        setattr(obj,rgbAttrib, colors.hsv2rgb(numpy.asarray(newColor)) )
    else:
        logging.error('Unknown colorSpace: %s' %colorSpace)
    obj.__dict__[colorSpaceAttrib] = colorSpace  #store name of colorSpace for future ref and for drawing
    #if needed, set the texture too
    setTexIfNoShaders(obj)

# for groupFlipVert:
immutables = set([int, float, str, tuple, long, bool,
                  numpy.float64, numpy.float, numpy.int, numpy.long])

def groupFlipVert(flipList, yReflect=0):
    """Reverses the vertical mirroring of all items in list ``flipList``.

    Reverses the .flipVert status, vertical (y) positions, and angular rotation
    (.ori). Flipping preserves the relations among the group's visual elements.
    The parameter ``yReflect`` is the y-value of an imaginary horizontal line
    around which to reflect the items; default = 0 (screen center).

    Typical usage is to call once prior to any display; call again to un-flip.
    Can be called with a list of all stim to be presented in a given routine.

    Will flip a) all psychopy.visual.xyzStim that have a setFlipVert method,
    b) the y values of .vertices, and c) items in n x 2 lists that are mutable
    (i.e., list, numpy.array, no tuples): [[x1, y1], [x2, y2], ...]
    """

    if type(flipList) != list:
        flipList = [flipList]
    for item in flipList:
        if type(item) in (list, numpy.ndarray):
            if type(item[0]) in (list, numpy.ndarray) and len(item[0]) == 2:
                for i in range(len(item)):
                    item[i][1] = 2 * yReflect - item[i][1]
            else:
                raise ValueError('Cannot vert-flip elements in "%s", type=%s' %
                                 (str(item), type(item[0])))
        elif type(item) in immutables:
            raise ValueError('Cannot change immutable item "%s"' % str(item))
        if hasattr(item, 'setPos'):
            item.setPos([1, -1], '*')
            item.setPos([0, 2 * yReflect], '+')
        elif hasattr(item, 'pos'):  # only if no setPos available
            item.pos[1] *= -1
            item.pos[1] += 2 * yReflect
        if hasattr(item, 'setFlipVert'):  # eg TextStim, custom marker
            item.setFlipVert(not item.flipVert)
        elif hasattr(item, 'vertices'):  # and lacks a setFlipVert method
            try:
                v = item.vertices * [1, -1]  # numpy.array
            except:
                v = [[item.vertices[i][0], -1 * item.vertices[i][1]]
                     for i in range(len(item.vertices))]
            item.setVertices(v)
        if hasattr(item, 'setOri') and item.ori:  # non-zero orientation angle
            item.setOri(-1, '*')
            item._needVertexUpdate = True
