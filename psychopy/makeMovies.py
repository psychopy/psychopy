# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
Not for users. To create a movie use win.getMovieFrame() and then win.saveMovieFrames(filename)

Many thanks to Ray Pascor (pascor at hotpop.com) for the public domain code on
building an optimised gif palette (makeRGBhistogram, makePalette, rgb2palette are
very heavily based on his code).
"""
from psychopy import logging
import string, time, tempfile, os, glob, random
try:
    from PIL import Image, ImageChops
    from PIL.GifImagePlugin import getheader, getdata #part of PIL
except ImportError:
    import Image, ImageChops
    from GifImagePlugin import getheader, getdata #part of PIL

try:
    import pymedia.video.vcodec as vcodec
    havePyMedia=True
except:
    havePyMedia=False

import numpy


# --------------------------------------------------------------------
# straightforward delta encoding

def makeAnimatedGIF(filename, images):
    """Convert list of image frames to a GIF animation file
    using simple delta coding"""

    frames = 0
    previous=None
    fp = open(filename, 'wb')
    if images[0].mode in ['RGB','RGBA']:
        #first make an optimised palette
        optimPalette=makePalette(images, verbose=True)

    for n, im in enumerate(images):
        print 'converting frame %i of %i to GIF' %(n+1,len(images))
        if im.mode=='RGB':
            im = rgb2palette(im, palette=optimPalette, verbose=False)
        if not previous:
            # global header
            for s in getheader(im) + getdata(im):
                fp.write(s)
        else:
            # delta frame
            delta = ImageChops.subtract_modulo(im, previous)
            bbox = delta.getbbox()
            # compress difference
            if bbox:
                for s in getdata(im.crop(bbox), offset = bbox[:2]):
                    fp.write(s)
            else:
                for s in getdata(im):
                    fp.write(s)

        previous = im.copy()
        frames = frames + 1
    fp.write(";")
    fp.close()
    return frames


def RgbHistogram (images, verbose=False):
    """build a histogram of the colors in the image(s)
    with which we can build an optimized color palette"""
    hist = None

    #make a list if given only one image
    if type(images)== type([]):
        nImages = len(images)
    else:
        nImages=1
        images= [images]

    # Form a histogram dictionary whose keys are the repr(color)
    if verbose:    print 'optimising palette ...'
    datalist=[]
    for imgRgb in images:
        datalist.extend(imgRgb.getdata())

    dicthist = {}
    xsize, ysize = imgRgb.size
    numcolors = 0
    for i in xrange (xsize * ysize * nImages):
        color = datalist [i]
        key = repr (color)

        if key in dicthist:  # color already exists
            dicthist [key] += 1     # increment the count
        else:                       # make a new key
            dicthist [key] = 1      # instantiate a new entry and init the count
            numcolors += 1

            if numcolors > 256:
                if verbose:    print '               ... too many colors'
                return None         # Error flag:  use PIL default color palette/dithering
    if verbose:    print '               ... OK'

    # reform the dictionary into a sorted histogram of the form: (count, (r, g, b))
    hist = []
    for key in dicthist.iterkeys():
        count = dicthist [key]
        color = eval (key)
        hist.append ( (count, color) )
    #end for

    hist.sort()
    hist.reverse()           # make largest counts first

    return hist

#end def RgbHistogram

def Getalphaindex (imgP, maskinv):

    # Find the least used color (palette entry, actually)
    # This will be the color to which transparency will be set when saving the file

    xsize, ysize = imgP.size
    hist = imgP.histogram (maskinv)     # get counts for all colors having non-active alphas

    indexleastused = 255                # arbitrary starting least used palette index
    leastcount = xsize * ysize          # max possible count
    for i in xrange (len (hist)):       # palette size
        if hist [i] < leastcount:
            leastcount = hist [i]       # the count
            indexleastused = i          # the palette index
        #end if

        if hist [i] == 0:    break      # first 0 entry: done
    #end if

    return (indexleastused, leastcount)

#end def Getalphaindex

def makePalette(images, verbose=False):
    palette = []                        # will be [0, 0, 0, ... 255, 255, 255]
    for i in xrange (256):
        palette.append (i); palette.append (i); palette.append (i)
    #end for

    hist = RgbHistogram (images, verbose=verbose)
    #check for alpha in one of the images
    if type(images)==type([]):
        img = images[0]
    else: img = images

    if hist is None: # colors > 256:  use PIL dithered image & palette
        palette=None
    else:
        # Make two lists of the colors.
        colors = []
        colorsAndIndices = []
        for i in xrange (len (hist)):
            if img.mode=='RGBA':
                r, g, b, a = hist [i][1]            # pick off the color tuple
            else:
                r, g, b = hist [i][1]               # pick off the color tuple
            #end if
            palette [i*3 + 0] = r
            palette [i*3 + 1] = g
            palette [i*3 + 2] = b
    return palette

def rgb2palette (imgRgb, palette=None, verbose=False):     # image could be a "RGBA"
    """
    Converts an RGB image to a palettised version (for saving as gif).
    """
    #verbose = False

    imgP = None
    datalist = None

    size = imgRgb.size
    xsize = size [0]
    ysize = size [1]

    hasalpha = False
    if imgRgb.mode == 'RGBA':
        hasalpha = True                            # for post=processing to create transparency
        if verbose:    print 'Rgb2p:  Input image is RGBA'

        # Create a mask and its inverse
        source = imgRgb.split()
        R, G, B, A = 0, 1, 2, 3         # band indices
        mask    = source [A].point (lambda i: i <  255 and 255)     # = True on active alphas
        maskinv = source [A].point (lambda i: i == 255        )     # = True on inactive alphas
    #end if

    # find the most popular colors, limiting the max number to 256
    # any "excess" colors with be transformed later to the closest palette match
    if palette is None:
        palette=makePalette(imgRgb)

    numPalette= numpy.reshape(numpy.asarray(palette), [256,3])
    listPalette = numPalette.tolist()
    imgP = Image.new ('P', size)            # Create a brand new paletted image
    imgP.putpalette (palette)               # Install the palette

    # Rewrite the entire image using new palette's indices.
    if verbose:    print 'Defining the new image using the newly created palette ...'

    # Each pixel gets a palette color index
    if datalist is None:
        datalist = list (imgRgb.getdata())      # xsize*ysize list of color 3-tuples
    #end if

    pxlctr = 0
    colctr = 0
    for yord in xrange (ysize):
        for xord in xrange (xsize):
            pxlcolor = list(datalist [yord*xsize + xord])     # org image color tuple

            if pxlcolor in listPalette:
                index = listPalette.index(list(pxlcolor))
            else: index=0
            #paletteindex = colorsAndIndices [index] [1]     # a simple lookup

            imgP.putpixel ((xord, yord), index)

    if hasalpha:
        indexleastused, leastcount = Getalphaindex (imgP, maskinv)
        if verbose:
            print
            print 'Low color-count image:   least used color index, leastcount =', indexleastused, leastcount
        #end if

        return (imgP, indexleastused, mask)
    else:
        return (imgP)
    #end if

#end def Rgb2p

def makeMPEG(filename, images, codec='mpeg1video', codecParams = None, verbose=False):
    if not havePyMedia:
        logging.error('pymedia (www.pymedia.org) needed to make mpeg movies')
        return 0

    fw= open( filename, 'wb' )
    t= time.time()

    #set bitrate
    if codec== 'mpeg1video':
        bitrate= 2700000
    else:
        bitrate= 9800000

    #set other params (or receive params dictionary)
    if codecParams is None:
        codecParams= { \
            'type': 0,
            'gop_size': 12,
            'frame_rate_base': 125,
            'max_b_frames': 0,
            'width': images[0].size[0],
            'height': images[0].size[1],
            'frame_rate': 3125,
            'deinterlace': 0,
            'bitrate': bitrate,
            'id': vcodec.getCodecID( codec )
            }
        logging.info('Setting codec to ' + str(codecParams))
    encoder= vcodec.Encoder( codecParams )

    for im in images:
        # Create VFrame
        imStr = im.tostring()
        bmpFrame= vcodec.VFrame( vcodec.formats.PIX_FMT_RGB24, im.size, (imStr,None,None))
        yuvFrame= bmpFrame.convert( vcodec.formats.PIX_FMT_YUV420P, im.size )
        d = encoder.encode( yuvFrame )
        try:
            fw.write( d.data )#this is what works!
        except:
            fw.write( d )#this is what pymedia demo recommends
    else:
        logging.info('%d frames written in %.2f secs' % ( len(images), time.time()- t))
        i= 0
    fw.close()


qtCodecQuality= {
  'lossless':   0x00000400,
  'max':        0x000003FF,
  'high':       0x00000300,
  'normal':     0x00000200,
  'low':        0x00000100,
  'min':        0x00000000,
}


class QuicktimeMovie(object):
    """DEPRECATED: the making of Quicktime movies is not possible in PsychoPy as of version 1.76+
    due to problems with the apple QTKit library under python 2.7

    Hopefully support for cross-platform movie outputs will return in future
    releases with the addition of direct support for the ffmpeg library.

    For now you need to save your frames as individual images and then
    """
    def __init__(self, filename=None, fps=30):
        """Deprecated
        """
        raise NotImplementedError, "Support for Quicktime movies has been removed (at least for now). You need to export your frames as images (e.g. png files) and combine them yourself (e.g. with ffmpeg)"
