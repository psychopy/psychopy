#!/usr/bin/env python

'''Helper functions shared by the visual classes'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import os

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import core, logging, colors

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import makeRadialMatrix, val2array
from psychopy.tools.attributetools import setWithOperation
from psychopy.tools.typetools import float_uint8

try:
    from PIL import Image
except ImportError:
    import Image

import numpy
from numpy import pi

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


def createTexture(tex, id, pixFormat, stim, res=128, maskParams=None,
                  forcePOW2=True, dataType=None):
    """
    :params:

        id:
            is the texture ID

        pixFormat:
            GL.GL_ALPHA, GL.GL_RGB

        useShaders:
            bool

        interpolate:
            bool (determines whether texture will use GL_LINEAR or GL_NEAREST

        res:
            the resolution of the texture (unless a bitmap image is used)

        dataType:
            None, GL.GL_UNSIGNED_BYTE, GL_FLOAT. Only affects image files (numpy arrays will be float)

    For grating stimuli (anything that needs multiple cycles) forcePOW2 should
    be set to be True. Otherwise the wrapping of the texture will not work.

    """

    """
    Create an intensity texture, ranging -1:1.0
    """
    global _nImageResizes
    notSqr=False #most of the options will be creating a sqr texture
    wasImage=False #change this if image loading works
    useShaders = stim.useShaders
    interpolate = stim.interpolate
    if dataType==None:
        if useShaders and pixFormat==GL.GL_RGB:
            dataType = GL.GL_FLOAT
        else:
            dataType = GL.GL_UNSIGNED_BYTE

    if type(tex) == numpy.ndarray:
        #handle a numpy array
        #for now this needs to be an NxN intensity array
        intensity = tex.astype(numpy.float32)
        if intensity.max()>1 or intensity.min()<-1:
            logging.error('numpy arrays used as textures should be in the range -1(black):1(white)')
        if len(tex.shape)==3:
            wasLum=False
        else: wasLum = True
        ##is it 1D?
        if tex.shape[0]==1:
            stim._tex1D=True
            res=tex.shape[1]
        elif len(tex.shape)==1 or tex.shape[1]==1:
            stim._tex1D=True
            res=tex.shape[0]
        else:
            stim._tex1D=False
            #check if it's a square power of two
            maxDim = max(tex.shape)
            powerOf2 = 2**numpy.ceil(numpy.log2(maxDim))
            if forcePOW2 and (tex.shape[0]!=powerOf2 or tex.shape[1]!=powerOf2):
                logging.error("Requiring a square power of two (e.g. 16x16, 256x256) texture but didn't receive one")
                core.quit()
            res=tex.shape[0]
    elif tex in [None,"none", "None"]:
        res=1 #4x4 (2x2 is SUPPOSED to be fine but generates wierd colors!)
        intensity = numpy.ones([res,res],numpy.float32)
        wasLum = True
    elif tex == "sin":
        onePeriodX, onePeriodY = numpy.mgrid[0:res, 0:2*pi:1j*res]# NB 1j*res is a special mgrid notation
        intensity = numpy.sin(onePeriodY-pi/2)
        wasLum = True
    elif tex == "sqr":#square wave (symmetric duty cycle)
        onePeriodX, onePeriodY = numpy.mgrid[0:res, 0:2*pi:1j*res]# NB 1j*res is a special mgrid notation
        sinusoid = numpy.sin(onePeriodY-pi/2)
        intensity = numpy.where(sinusoid>0, 1, -1)
        wasLum = True
    elif tex == "saw":
        intensity = numpy.linspace(-1.0,1.0,res,endpoint=True)*numpy.ones([res,1])
        wasLum = True
    elif tex == "tri":
        intensity = numpy.linspace(-1.0,3.0,res,endpoint=True)#-1:3 means the middle is at +1
        intensity[int(res/2.0+1):] = 2.0-intensity[int(res/2.0+1):]#remove from 3 to get back down to -1
        intensity = intensity*numpy.ones([res,1])#make 2D
        wasLum = True
    elif tex == "sinXsin":
        onePeriodX, onePeriodY = numpy.mgrid[0:2*pi:1j*res, 0:2*pi:1j*res]# NB 1j*res is a special mgrid notation
        intensity = numpy.sin(onePeriodX-pi/2)*numpy.sin(onePeriodY-pi/2)
        wasLum = True
    elif tex == "sqrXsqr":
        onePeriodX, onePeriodY = numpy.mgrid[0:2*pi:1j*res, 0:2*pi:1j*res]# NB 1j*res is a special mgrid notation
        sinusoid = numpy.sin(onePeriodX-pi/2)*numpy.sin(onePeriodY-pi/2)
        intensity = numpy.where(sinusoid>0, 1, -1)
        wasLum = True
    elif tex == "circle":
        rad=makeRadialMatrix(res)
        intensity = (rad<=1)*2-1
        fromFile=0
        wasLum=True
    elif tex == "gauss":
        rad=makeRadialMatrix(res)
        sigma = 1/3.0;
        intensity = numpy.exp( -rad**2.0 / (2.0*sigma**2.0) )*2-1 #3sd.s by the edge of the stimulus
        fromFile=0
        wasLum=True
    elif tex == "radRamp":#a radial ramp
        rad=makeRadialMatrix(res)
        intensity = 1-2*rad
        intensity = numpy.where(rad<-1, intensity, -1)#clip off the corners (circular)
        fromFile=0
        wasLum=True
    elif tex == "raisedCos": # A raised cosine
        wasLum=True
        hamming_len = 1000 # This affects the 'granularity' of the raised cos

        # If no user input was provided:
        if maskParams is None:
            fringe_proportion = 0.2 # This one affects the proportion of the
                                # stimulus diameter that is devoted to the
                                # raised cosine.

        # Users can provide the fringe proportion through a dict, maskParams
        # input:
        else:
            fringe_proportion = maskParams['fringeWidth']

        rad = makeRadialMatrix(res)
        intensity = numpy.zeros_like(rad)
        intensity[numpy.where(rad < 1)] = 1
        raised_cos_idx = numpy.where(
            [numpy.logical_and(rad <= 1, rad >= 1-fringe_proportion)])[1:]

        # Make a raised_cos (half a hamming window):
        raised_cos = numpy.hamming(hamming_len)[:hamming_len/2]
        raised_cos -= numpy.min(raised_cos)
        raised_cos /= numpy.max(raised_cos)

        # Measure the distance from the edge - this is your index into the hamming window:
        d_from_edge = numpy.abs((1 - fringe_proportion)- rad[raised_cos_idx])
        d_from_edge /= numpy.max(d_from_edge)
        d_from_edge *= numpy.round(hamming_len/2)

        # This is the indices into the hamming (larger for small distances from the edge!):
        portion_idx = (-1 * d_from_edge).astype(int)

        # Apply the raised cos to this portion:
        intensity[raised_cos_idx] = raised_cos[portion_idx]

        # Scale it into the interval -1:1:
        intensity = intensity - 0.5
        intensity = intensity / numpy.max(intensity)

        #Sometimes there are some remaining artifacts from this process, get rid of them:
        artifact_idx = numpy.where(numpy.logical_and(intensity == -1,
                                                     rad < 0.99))
        intensity[artifact_idx] = 1
        artifact_idx = numpy.where(numpy.logical_and(intensity == 1, rad >
                                                     0.99))
        intensity[artifact_idx] = 0

    else:
        if type(tex) in [str, unicode, numpy.string_]:
            # maybe tex is the name of a file:
            if not os.path.isfile(tex):
                logging.error("Couldn't find image file '%s'; check path?" %(tex)); logging.flush()
                raise OSError, "Couldn't find image file '%s'; check path? (tried: %s)" \
                    % (tex, os.path.abspath(tex))#ensure we quit
            try:
                im = Image.open(tex)
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
            except IOError:
                logging.error("Found file '%s' but failed to load as an image" %(tex)); logging.flush()
                raise IOError, "Found file '%s' [= %s] but it failed to load as an image" \
                    % (tex, os.path.abspath(tex))#ensure we quit
        else:
            # can't be a file; maybe its an image already in memory?
            try:
                im = tex.copy().transpose(Image.FLIP_TOP_BOTTOM) # ? need to flip if in mem?
            except AttributeError: # nope, not an image in memory
                logging.error("Couldn't make sense of requested image."); logging.flush()
                raise AttributeError, "Couldn't make sense of requested image."#ensure we quit
        # at this point we have a valid im
        stim._origSize=im.size
        wasImage=True
        #is it 1D?
        if im.size[0]==1 or im.size[1]==1:
            logging.error("Only 2D textures are supported at the moment")
        else:
            maxDim = max(im.size)
            powerOf2 = int(2**numpy.ceil(numpy.log2(maxDim)))
            if im.size[0]!=powerOf2 or im.size[1]!=powerOf2:
                if not forcePOW2:
                    notSqr=True
                elif _nImageResizes<reportNImageResizes:
                    logging.warning("Image '%s' was not a square power-of-two image. Linearly interpolating to be %ix%i" %(tex, powerOf2, powerOf2))
                    _nImageResizes+=1
                    im=im.resize([powerOf2,powerOf2],Image.BILINEAR)
                elif _nImageResizes==reportNImageResizes:
                    logging.warning("Multiple images have needed resizing - I'll stop bothering you!")
                    im=im.resize([powerOf2,powerOf2],Image.BILINEAR)

        #is it Luminance or RGB?
        if im.mode=='L' and pixFormat==GL.GL_ALPHA:
            wasLum = True
        elif pixFormat==GL.GL_ALPHA:#we have RGB and need Lum
            wasLum = True
            im = im.convert("L")#force to intensity (in case it was rgb)
        elif pixFormat==GL.GL_RGB:#we have RGB and keep it that way
            #texture = im.tostring("raw", "RGB", 0, -1)
            im = im.convert("RGBA")#force to rgb (in case it was CMYK or L)
            wasLum=False
        if dataType==GL.GL_FLOAT:
            #convert from ubyte to float
            intensity = numpy.array(im).astype(numpy.float32)*0.0078431372549019607-1.0 # much faster to avoid division 2/255
        else:
            intensity = numpy.array(im)
        if wasLum and intensity.shape!=im.size:
            intensity.shape=im.size

    if pixFormat==GL.GL_RGB and wasLum and dataType==GL.GL_FLOAT: #grating stim on good machine
        #keep as float32 -1:1
        if sys.platform!='darwin' and stim.win.glVendor.startswith('nvidia'):
            #nvidia under win/linux might not support 32bit float
            internalFormat = GL.GL_RGB16F_ARB #could use GL_LUMINANCE32F_ARB here but check shader code?
        else:#we've got a mac or an ATI card and can handle 32bit float textures
            internalFormat = GL.GL_RGB32F_ARB #could use GL_LUMINANCE32F_ARB here but check shader code?
        data = numpy.ones((intensity.shape[0],intensity.shape[1],3),numpy.float32)#initialise data array as a float
        data[:,:,0] = intensity#R
        data[:,:,1] = intensity#G
        data[:,:,2] = intensity#B
    elif pixFormat==GL.GL_RGB and wasLum: #Grating on legacy hardware, or ImageStim with wasLum=True
        #scale by rgb and convert to ubyte
        internalFormat = GL.GL_RGB
        if stim.colorSpace in ['rgb', 'dkl', 'lms','hsv']:
            rgb=stim.rgb
        else:
            rgb=stim.rgb/127.5-1.0#colour is not a float - convert to float to do the scaling
        #scale by rgb
        data = numpy.ones((intensity.shape[0],intensity.shape[1],3),numpy.float32)#initialise data array as a float
        data[:,:,0] = intensity*rgb[0]  + stim.rgbPedestal[0]#R
        data[:,:,1] = intensity*rgb[1]  + stim.rgbPedestal[1]#G
        data[:,:,2] = intensity*rgb[2]  + stim.rgbPedestal[2]#B
        #convert to ubyte
        data = float_uint8(stim.contrast*data)
    elif pixFormat==GL.GL_RGB and dataType==GL.GL_FLOAT: #probably a custom rgb array or rgb image
        internalFormat = GL.GL_RGB32F_ARB
        data = intensity
    elif pixFormat==GL.GL_RGB:# not wasLum, not useShaders  - an RGB bitmap with no shader options
        internalFormat = GL.GL_RGB
        data = intensity #float_uint8(intensity)
    elif pixFormat==GL.GL_ALPHA:
        internalFormat = GL.GL_ALPHA
        if wasImage:
            data = intensity
        else:
            data = float_uint8(intensity)
    #check for RGBA textures
    if len(intensity.shape)>2 and intensity.shape[2] == 4:
        if pixFormat==GL.GL_RGB: pixFormat=GL.GL_RGBA
        if internalFormat==GL.GL_RGB: internalFormat=GL.GL_RGBA
        elif internalFormat==GL.GL_RGB32F_ARB: internalFormat=GL.GL_RGBA32F_ARB

    texture = data.ctypes#serialise
    #bind the texture in openGL
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, id)#bind that name to the target
    GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT) #makes the texture map wrap (this is actually default anyway)
    #important if using bits++ because GL_LINEAR
    #sometimes extrapolates to pixel vals outside range
    if interpolate:
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_LINEAR)
        if useShaders:#GL_GENERATE_MIPMAP was only available from OpenGL 1.4
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                data.shape[1],data.shape[0], 0, # [JRG] for non-square, want data.shape[1], data.shape[0]
                pixFormat, dataType, texture)
        else:#use glu
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_NEAREST)
            GL.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, internalFormat,
                data.shape[1],data.shape[0], pixFormat, dataType, texture)    # [JRG] for non-square, want data.shape[1], data.shape[0]
    else:
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                        data.shape[1],data.shape[0], 0, # [JRG] for non-square, want data.shape[1], data.shape[0]
                        pixFormat, dataType, texture)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)#?? do we need this - think not!
    return wasLum

def pointInPolygon(x, y, poly):
    """Determine if a point (`x`, `y`) is inside a polygon, using the ray casting method.

    `poly` is a list of 3+ vertices as (x,y) pairs.
    If given a `ShapeStim`-based object, will use the
    rendered vertices and position as the polygon.

    Returns True (inside) or False (outside). Used by :class:`~psychopy.visual.ShapeStim` `.contains()`
    """
    if hasattr(poly, '_verticesRendered') and hasattr(poly, '_posRendered'):
        poly = poly._verticesRendered + poly._posRendered
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
    """Determine if two polygons intersect; can fail for pointy polygons.

    Accepts two polygons, as lists of vertices (x,y) pairs. If given `ShapeStim`-based
    instances, will use rendered (vertices + pos) as the polygon.

    Checks if any vertex of one polygon is inside the other polygon; will fail in
    some cases, especially for pointy polygons. "crossed-swords" configurations
    overlap but may not be detected by the algorithm.

    Used by :class:`~psychopy.visual.ShapeStim` `.overlaps()`
    """
    if hasattr(poly1, '_verticesRendered') and hasattr(poly1, '_posRendered'):
        poly1 = poly1._verticesRendered + poly1._posRendered
    if hasattr(poly2, '_verticesRendered') and hasattr(poly2, '_posRendered'):
        poly2 = poly2._verticesRendered + poly2._posRendered

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
    """
    if hasattr(obj, 'setTex') and hasattr(obj, 'tex') and not obj.useShaders:
        obj.setTex(obj.tex)

def setColor(obj, color, colorSpace=None, operation='',
                rgbAttrib='rgb', #or 'fillRGB' etc
                colorAttrib='color', #or 'fillColor' etc
                colorSpaceAttrib=None, #e.g. 'colorSpace' or 'fillColorSpace'
                log=True):
    """Provides the workings needed by setColor, and can perform this for
    any arbitrary color type (e.g. fillColor,lineColor etc)
    """

    #how this works:
    #rather than using obj.rgb=rgb this function uses setattr(obj,'rgb',rgb)
    #color represents the color in the native space
    #colorAttrib is the name that color will be assigned using setattr(obj,colorAttrib,color)
    #rgb is calculated from converting color
    #rgbAttrib is the attribute name that rgb is stored under, e.g. lineRGB for obj.lineRGB
    #colorSpace and takes name from colorAttrib+space e.g. obj.lineRGBSpace=colorSpace

    if colorSpaceAttrib==None:
        colorSpaceAttrib = colorAttrib+'Space'

    # Handle strings and returns immediately as operations, colorspace etc. does not apply here.
    if type(color) in [str, unicode, numpy.string_]:
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

    # If it wasn't a strin, do check and conversion of scalars, sequences and other stuff.
    else:
        color = val2array(color, length=3)

        if color==None:
            setattr(obj,rgbAttrib,None)#e.g. obj.rgb=[0,0,0]
            obj.__dict__[colorSpaceAttrib] = None  #e.g. obj.colorSpace='hex'
            obj.__dict__[colorAttrib] = None  #e.g. obj.color='#000000'
            setTexIfNoShaders(obj)

    #at this point we have a numpy array of 3 vals (actually we haven't checked that there are 3)
    #check if colorSpace is given and use obj.colorSpace if not
    if colorSpace==None:
        colorSpace=getattr(obj,colorSpaceAttrib)
        #using previous color space - if we got this far in the _stColor function
        #then we haven't been given a color name - we don't know what color space to use.
        if colorSpace == 'named':
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
        setWithOperation(obj, colorAttrib, color, operation, True)
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

    if hasattr(obj, 'autoLog'):
        autoLog = obj.autoLog
    else:
        autoLog = False
    if autoLog and log:
        if hasattr(obj,'win'):
            obj.win.logOnFlip("Set %s.%s=%s (%s)" %(obj.name,colorAttrib,newColor,colorSpace),
                level=logging.EXP,obj=obj)
        else:
            obj.logOnFlip("Set Window %s=%s (%s)" %(colorAttrib,newColor,colorSpace),
                level=logging.EXP,obj=obj)


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
