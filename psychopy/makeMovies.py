# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
Not for users. To create a movie use win.getMovieFrame() and then win.saveMovieFrames(filename)

Many thanks to Ray Pascor (pascor at hotpop.com) for the public domain code on
building an optimised gif palette (makeRGBhistogram, makePalette, rgb2palette are
very heavily based on his code).
"""
from psychopy import logging
import string, time, tempfile, os, glob
import Image, ImageChops
from GifImagePlugin import getheader, getdata #part of PIL
try:
    import pymedia.video.vcodec as vcodec
    havePyMedia=True
except:
    havePyMedia=False
try:
    import QTKit, AppKit
    haveQT=True
except:
    haveQT=False

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

        if dicthist.has_key (key):  # color already exists
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

    if hist == None: # colors > 256:  use PIL dithered image & palette
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
    if palette==None:
        palette=makePalette(imgRgb)

    numPalette= numpy.reshape(numpy.asarray(palette), [256,3])
    listPalette = numPalette.tolist()
    imgP = Image.new ('P', size)            # Create a brand new paletted image
    imgP.putpalette (palette)               # Install the palette

    # Rewrite the entire image using new palette's indices.
    if verbose:    print 'Defining the new image using the newly created palette ...'

    # Each pixel gets a palette color index
    if datalist == None:
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
    if codecParams == None:
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
    """A class to allow creation of Quicktime movies (OS X only).

    These might be from frames provided by a PsychoPy `psychopy.visual.Window`, by
    sequences of numpy arrays or from image frames (jpg, png etc.) on a disk.

    """
    def __init__(self, filename=None, fps=30):
        """
        :Parameters:

            filename: a string giving the name of the file. If None then you can set a filename during save()

            fps: the number of frames per second, to be used throughout the movie

        """
        if not haveQT:
            raise ImportError("Quicktime movies can only be created under OSX and require QTKit and AppKit to be installed")
        self.frameN = 1
        self.filename = filename
        self.movie = None
        self.fps = fps
        self._movTmpFileName=None#we need a physical temp file to build the frames up?
    def addFrame(self, frame, duration=1):
        """Add a frame to the movie, from an image filename (anything that PIL can read)

        :Parameters:

            frame: can be;

                - an image filename (including path)
                - a numpy array
                - a PIL image
                - a `psychopy.visual.Window` movie frame (from win.getMovieFrame())

            duration: the length of time this frame should be displayed (in units of frame)

        """
        if self.movie is None:
            self._movTmpFileName=os.path.join(tempfile.gettempdir(), 'psychopyTmp.mov')#could this line fail if no permissions?
            #self._movTmpFileName='tmpMov'#this is handy if we want to inspect the temp file
            try:
                self.movie, err=QTKit.QTMovie.alloc().initToWritableFile_error_(self._movTmpFileName,None)#
            except:
                self.movie, err=QTKit.QTMovie.alloc().initToWritableFile_error_(self._movTmpFileName)#under some versions (10.5?) this call is different
            if err is not None:
                print str(err)
            self.movie.setEditable_(True)
#            self.movie.setLoops_(True)#makes no difference - probably needs to be set in the export settings

        #we now have an NSImage of the frame, so add it
        frameAttrs =  {QTKit.QTAddImageCodecType:'jpeg',# see QTKitdefines.h for compression options. These affect the size of the temp file
                                QTKit.QTAddImageCodecQuality:qtCodecQuality['max']}
        duration = QTKit.QTMakeTime(duration,self.fps)
        #for image filenames load file
        if type(frame)==numpy.ndarray:#convert to an image and let it go through the image pipeline below
            frame=Image.fromarray(frame).rotate(90)
        if isinstance(frame, Image.Image):#don't use elif here because of above
            #can't seem to make this work to remove the need for writing tmp.png files for each frame
            #            imgBuff=StringIO.StringIO()#a fake buffer to store the image (like tmpfile without disk access)
            #            pilIm = Image.fromarray(frame)#.save(imgBuff, 'png')
            #            img = NSImage.alloc().initWithContentsOfFile_(imgBuff)
            #                or:
            #            img = NSImage.alloc().initWithData_(AppKit.NSData.dataWithData_(frame.data))
            handle, tmpFileName=tempfile.mkstemp('.psychopyTmp.png')#could this line fail if no permissions?
            frame.save(tmpFileName)
            img = AppKit.NSImage.alloc().initByReferencingFile_(tmpFileName)
            self.movie.addImage_forDuration_withAttributes_(img, duration, frameAttrs)
        elif type(frame)==str and os.path.isfile(frame):
            img = AppKit.NSImage.alloc().initByReferencingFile_(frame)
        else:
            raise TypeError("Frames in QuicktimeMovie.addFrame() should be filenames, PIL images or numpy arrays. " +\
                "Got a %s" %type(frame))
        self.movie.addImage_forDuration_withAttributes_(img, duration, frameAttrs)
        del img
        os.remove(tmpFileName)
        self.frameN += 1

    def save(self, filename=None, compressed=True):
        """Save the movie to the self.filename or to a new one if given
        """
        if filename==None: filename = self.filename
        self.movie.writeToFile_withAttributes_(filename,
            {QTKit.QTMovieFlatten:(not compressed)})#if True then there is no inter-frame compression
        #self.movie.updateMovieFile()#this doesn't use QTExport settings and you end up with large files (uncompressed in time)
    def __del__(self):
        """Remove any tmp files if possible (including any from previous runs that garbage collection wasn't able to collect)
        """
        tmpFolder=tempfile.gettempdir()
        #would be nice also to remove self._movTmpFileName, but this fouls up movie writing (even deleting afterwards!?)
        files=glob.glob(os.path.join(tmpFolder,'*.psychopyTmp.png'))
        for thisFile in files:
            os.remove(thisFile)