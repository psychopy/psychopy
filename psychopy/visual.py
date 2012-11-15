"""To control the screen and visual stimuli for experiments
"""
# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, os, glob, copy
#on windows try to load avbin now (other libs can interfere)
if sys.platform=='win32':
    #make sure we also check in SysWOW64 if on 64-bit windows
    if 'C:\\Windows\\SysWOW64' not in os.environ['PATH']:
        os.environ['PATH']+=';C:\\Windows\\SysWOW64'
    try:
        from pyglet.media import avbin
        haveAvbin=True
    except ImportError:
        haveAvbin=False#either avbin isn't installed or scipy.stats has been imported (prevents avbin loading)

import psychopy #so we can get the __path__
from psychopy import core, platform_specific, logging, preferences, monitors, event
import colors
import psychopy.event
#misc must only be imported *after* event or MovieStim breaks on win32 (JWP has no idea why!)
import psychopy.misc
import Image
import makeMovies

if sys.platform=='win32' and not haveAvbin:
    logging.error("""avbin.dll failed to load. Try importing psychopy.visual as the first
    library (before anything that uses scipy) and make sure that avbin is installed.""")

import numpy
from numpy import sin, cos, pi

from core import rush

prefs = preferences.Preferences()#load the site/user config files
reportNDroppedFrames=5#stop raising warning after this
reportNImageResizes=5
global _nImageResizes
_nImageResizes=0

#shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import ctypes
import pyglet
pyglet.options['debug_gl'] = False#must be done before importing pyglet.gl or pyglet.window
GL = pyglet.gl

import psychopy.gamma
#import pyglet.gl, pyglet.window, pyglet.image, pyglet.font, pyglet.event
import _shadersPyglet as _shaders
try:
    from pyglet import media
    havePygletMedia=True
except:
    havePygletMedia=False

try:
    import pygame
    havePygame=True
except:
    havePygame=False

#check for advanced drawing abilities
#actually FBO isn't working yet so disable
try:
    #import OpenGL.GL.EXT.framebuffer_object as FB
    #for pyglet these functions are under .gl like everything else
    haveFB=False
except:
    haveFB=False

try:
    from matplotlib import nxutils
    haveNxutils = True
except:
    haveNxutils = False

global DEBUG; DEBUG=False

#symbols for MovieStim
from psychopy.constants import *
#PLAYING=1
#STARTED=1
#PAUSED=2
#NOT_STARTED=0
#FINISHED=-1

#keep track of windows that have been opened
openWindows=[]

class Window:
    """Used to set up a context in which to draw objects,
    using either PyGame (python's SDL binding) or pyglet.

    The pyglet backend allows multiple windows to be created, allows the user to specify
    which screen to use (if more than one is available, duh!) and allows movies to be
    rendered.

    Pygame has fewer bells and whistles, but does seem a little faster in text rendering.
    Pygame is used for all sound production and for monitoring the joystick.

    """
    def __init__(self,
                 size = (800,600),
                 pos = None,
                 color=(0,0,0),
                 colorSpace='rgb',
                 rgb = None,
                 dkl=None,
                 lms=None,
                 fullscr=None,
                 allowGUI=None,
                 monitor=dict([]),
                 bitsMode=None,
                 winType=None,
                 units=None,
                 gamma = None,
                 blendMode='avg',
                 screen=0,
                 viewScale = None,
                 viewPos  = None,
                 viewOri  = 0.0,
                 waitBlanking=True,
                 allowStencil=False,
                 stereo=False,
                 name='window1'):
        """
        :Parameters:

            size : (800,600)
                Size of the window in pixels (X,Y)
            pos : *None* or (x,y)
                Location of the window on the screen
            rgb : [0,0,0]
                Color of background as [r,g,b] list or single value. Each gun can take values betweeen -1 and 1
            fullscr : *None*, True or False
                Better timing can be achieved in full-screen mode
            allowGUI :  *None*, True or False (if None prefs are used)
                If set to False, window will be drawn with no frame and no buttons to close etc...
            winType :  *None*, 'pyglet', 'pygame'
                If None then PsychoPy will revert to user/site preferences
            monitor : *None*, string or a `~psychopy.monitors.Monitor` object
                The monitor to be used during the experiment
            units :  *None*, 'height' (of the window), 'norm' (normalised),'deg','cm','pix'
                Defines the default units of stimuli drawn in the window (can be overridden by each stimulus)
                See :ref:`units` for explanation of options.
            screen : *0*, 1 (or higher if you have many screens)
                Specifies the physical screen that stimuli will appear on (pyglet winType only)
            viewScale : *None* or [x,y]
                Can be used to apply a custom scaling to the current units of the :class:`~psychopy.visual.Window`.
            viewPos : *None*, or [x,y]
                If not None, redefines the origin for the window
            viewOri : *0* or any numeric value
                A single value determining the orientation of the view in degs
            waitBlanking : *None*, True or False.
                After a call to flip() should we wait for the blank before the script continues
            gamma :
                Monitor gamma for linearisation (will use Bits++ if possible). Overrides monitor settings
            bitsMode : None, 'fast', ('slow' mode is deprecated).
                Defines how (and if) the Bits++ box will be used. 'fast' updates every frame by drawing a hidden line on the top of the screen.
            allowStencil : True or *False*
                When set to True, this allows operations that use the OpenGL stencil buffer
                (notably, allowing the class:`~psychopy.visual.Aperture` to be used).
            stereo : True or *False*
                If True and your graphics card supports quad buffers then this will be enabled.
                You can switch between left and right-eye scenes for drawing operations using
                :func:`~psychopy.visual.Window.setBuffer`

            :note: Preferences. Some parameters (e.g. units) can now be given default values in the user/site preferences and these will be used if None is given here. If you do specify a value here it will take precedence over preferences.

        """
        self.name=name
        self.size = numpy.array(size, numpy.int)
        self.pos = pos
        self.winHandle=None#this will get overridden once the window is created

        self._defDepth=0.0
        self._toLog=[]

        #settings for the monitor: local settings (if available) override monitor
        #if we have a monitors.Monitor object (psychopy 0.54 onwards)
        #convert to a Monitor object
        if monitor==None:
            self.monitor = monitors.Monitor('__blank__')
        if type(monitor) in [str, unicode]:
            self.monitor = monitors.Monitor(monitor)
        elif type(monitor)==dict:
            #convert into a monitor object
            self.monitor = monitors.Monitor('temp',currentCalib=monitor,verbose=False)
        else:
            self.monitor = monitor

        #otherwise monitor will just be a dict
        self.scrWidthCM=self.monitor.getWidth()
        self.scrDistCM=self.monitor.getDistance()

        scrSize = self.monitor.getSizePix()
        if scrSize==None:
            self.scrWidthPIX=None
        else:self.scrWidthPIX=scrSize[0]

        if fullscr==None: self._isFullScr = prefs.general['fullscr']
        else: self._isFullScr = fullscr
        if units==None: self.units = prefs.general['units']
        else: self.units = units
        if allowGUI==None: self.allowGUI = prefs.general['allowGUI']
        else: self.allowGUI = allowGUI
        self.screen = screen

        #parameters for transforming the overall view
        #scale
        if type(viewScale) in [list, tuple]:
            self.viewScale = numpy.array(viewScale, numpy.float64)
        elif type(viewScale) in [int, float]:
            self.viewScale = numpy.array([viewScale,viewScale], numpy.float64)
        else: self.viewScale = viewScale
        #pos
        if type(viewPos) in [list, tuple]:
            self.viewPos = numpy.array(viewPos, numpy.float64)
        else: self.viewPos = viewPos
        self.viewOri  = float(viewOri)
        self.stereo = stereo #use quad buffer if requested (and if possible)

        #setup bits++ if possible
        self.bitsMode = bitsMode #could be [None, 'fast', 'slow']
        if self.bitsMode!=None:
            from psychopy.hardware.crs import bits
            self.bits = bits.BitsBox(self)
            self.haveBits = True

        #gamma
        if self.bitsMode!=None and hasattr(self.monitor, 'lineariseLums'):
            #rather than a gamma value we could use bits++ and provide a complete linearised lookup table
            #using monitor.lineariseLums(lumLevels)
            self.gamma=None
        if gamma != None and (type(gamma) in [float, int]):
            #an integer that needs to be an array
            self.gamma=[gamma,gamma,gamma]
            self.useNativeGamma=False
        elif gamma != None:# and (type(gamma) not in [float, int]):
            #an array (hopefully!)
            self.gamma=gamma
            self.useNativeGamma=False
        elif type(self.monitor.getGammaGrid())==numpy.ndarray:
            self.gamma = self.monitor.getGammaGrid()[1:,2]
            if self.monitor.gammaIsDefault(): #are we using the default gamma for all monitors?
                self.useNativeGamma=True
            else:self.useNativeGamma=False
        elif self.monitor.getGamma()!=None:
            self.gamma = self.monitor.getGamma()
            self.useNativeGamma=False
        else:
            self.gamma = None #gamma wasn't set anywhere
            self.useNativeGamma=True

        #load color conversion matrices
        dkl_rgb = self.monitor.getDKL_RGB()
        if dkl_rgb!=None:
            self.dkl_rgb=dkl_rgb
        else: self.dkl_rgb = None
        lms_rgb = self.monitor.getLMS_RGB()
        if lms_rgb!=None:
            self.lms_rgb=lms_rgb
        else: self.lms_rgb = None

        #set screen color
        self.colorSpace=colorSpace
        if rgb!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb')
        elif dkl!=None:
            logging.warning("Use of dkl arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(dkl, colorSpace='dkl')
        elif lms!=None:
            logging.warning("Use of lms arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(lms, colorSpace='lms')
        else:
            self.setColor(color, colorSpace=colorSpace)

        #check whether FBOs are supported
        if blendMode=='add' and not haveFB:
            logging.warning("""User requested a blendmode of "add" but framebuffer objects not available. You need PyOpenGL3.0+ to use this blend mode""")
            self.blendMode='average' #resort to the simpler blending without float rendering
        else: self.blendMode=blendMode

        self.allowStencil=allowStencil
        #setup context and openGL()
        if winType==None:#choose the default windowing
            self.winType=prefs.general['winType']
        else:
            self.winType = winType
        if self.winType=='pygame' and not havePygame:
            logging.warning("Requested pygame backend but pygame is not installed or not fully working")
            self.winType='pyglet'
        #setup the context
        if self.winType == "pygame": self._setupPygame()
        elif self.winType == "pyglet": self._setupPyglet()

        #check whether shaders are supported
        if self.winType=='pyglet':#we can check using gl_info
            if pyglet.gl.gl_info.get_version()>='2.0':
                self._haveShaders=True #also will need to check for ARB_float extension, but that should be done after context is created
            else:
                self._haveShaders=False
        else:
            self._haveShaders=False

        self._setupGL()
        self.frameClock = core.Clock()#from psycho/core
        self.frames = 0         #frames since last fps calc
        self.movieFrames=[] #list of captured frames (Image objects)

        self.recordFrameIntervals=False
        self.recordFrameIntervalsJustTurnedOn=False # Allows us to omit the long timegap that follows each time turn it off
        self.nDroppedFrames=0
        self.frameIntervals=[]
        self._toDraw=[]
        self._toDrawDepths=[]
        self._eventDispatchers=[]
        try:
            self.origGammaRamp=psychopy.gamma.getGammaRamp(self.winHandle)
        except:
            self.origGammaRamp=None
        if self.useNativeGamma:
            logging.info('Using gamma table of operating system')
        else:
            logging.info('Using gamma: self.gamma' + str(self.gamma))
            self.setGamma(self.gamma)#using either pygame or bits++
        self.lastFrameT = core.getTime()

        self.waitBlanking = waitBlanking

        self._refreshThreshold=1/1.0#initial val needed by flip()
        self._monitorFrameRate = self._getActualFrameRate()#over several frames with no drawing
        if self._monitorFrameRate != None:
            self._refreshThreshold = (1.0/self._monitorFrameRate)*1.2
        else:
            self._refreshThreshold = (1.0/60)*1.2#guess its a flat panel

        openWindows.append(self)

    def setRecordFrameIntervals(self, value=True):
        """To provide accurate measures of frame intervals, to determine whether frames
        are being dropped. Set this to False while the screen is not being updated
        e.g. during event.waitkeys() and set to True during critical parts of the script

        see also:
            Window.saveFrameIntervals()
        """

        if self.recordFrameIntervals != True and value==True: #was off, and now turning it on
            self.recordFrameIntervalsJustTurnedOn = True
        else:
            self.recordFrameIntervalsJustTurnedOn = False
        self.recordFrameIntervals=value

        self.frameClock.reset()
    def saveFrameIntervals(self, fileName=None, clear=True):
        """Save recorded screen frame intervals to disk, as comma-separated values.

        :Parameters:

        fileName : *None* or the filename (including path if necessary) in which to store the data.
            If None then 'lastFrameIntervals.log' will be used.

        """
        if fileName==None:
            fileName = 'lastFrameIntervals.log'
        if len(self.frameIntervals):
            intervalStr = str(self.frameIntervals)[1:-1]
            f = open(fileName, 'w')
            f.write(intervalStr)
            f.close()
        if clear:
            self.frameIntervals=[]
            self.frameClock.reset()
    def onResize(self, width, height):
        '''A default resize event handler.

        This default handler updates the GL viewport to cover the entire
        window and sets the ``GL_PROJECTION`` matrix to be orthagonal in
        window space.  The bottom-left corner is (0, 0) and the top-right
        corner is the width and height of the :class:`~psychopy.visual.Window` in pixels.

        Override this event handler with your own to create another
        projection, for example in perspective.
        '''
        if height==0:
            height=1
        GL.glViewport(0, 0, width, height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-1,1,-1,1, -1, 1)
        #GL.gluPerspective(90, 1.0*width/height, 0.1, 100.0)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
    def logOnFlip(self,msg,level,obj=None):
        """Send a log message that should be time-stamped at the next .flip()
        command.

        :parameters:
            - msg: the message to be logged
            - level: the level of importance for the message
            - obj (optional): the python object that might be associated with this message
                if desired
        """

        self._toLog.append({'msg':msg,'level':level,'obj':str(obj)})
    def flip(self, clearBuffer=True):
        """Flip the front and back buffers after drawing everything for your frame.
        (This replaces the win.update() method, better reflecting what is happening underneath).

        win.flip(clearBuffer=True)#results in a clear screen after flipping
        win.flip(clearBuffer=False)#the screen is not cleared (so represent the previous screen)
        """
        for thisStim in self._toDraw:
            thisStim.draw()

        if haveFB:
            #need blit the frambuffer object to the actual back buffer

            FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, 0)#unbind the framebuffer as the render target

            #before flipping need to copy the renderBuffer to the frameBuffer
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.frameTexture)
            GL.glBegin( GL.GL_QUADS )
            GL.glTexCoord2f( 0.0, 0.0 ) ; GL.glVertex2f( -1.0,-1.0 )
            GL.glTexCoord2f( 0.0, 1.0 ) ; GL.glVertex2f( -1.0, 1.0 )
            GL.glTexCoord2f( 1.0, 1.0 ) ; GL.glVertex2f( 1.0,   1.0 )
            GL.glTexCoord2f( 1.0, 0.0 ) ; GL.glVertex2f( 1.0,   -1.0 )
            GL.glEnd()

        #update the bits++ LUT
        if self.bitsMode in ['fast','bits++']:
            self.bits._drawLUTtoScreen()

        if self.winType =="pyglet":
            #make sure this is current context
            self.winHandle.switch_to()

            GL.glTranslatef(0.0,0.0,-5.0)

            for dispatcher in self._eventDispatchers:
                dispatcher._dispatch_events()
            self.winHandle.dispatch_events()#this might need to be done even more often than once per frame?
            pyglet.media.dispatch_events()#for sounds to be processed
            self.winHandle.flip()
            #self.winHandle.clear()
            GL.glLoadIdentity()
        else:
            if pygame.display.get_init():
                pygame.display.flip()
                pygame.event.pump()#keeps us in synch with system event queue
            else:
                core.quit()#we've unitialised pygame so quit

        #rescale/reposition view of the window
        if self.viewScale != None:
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GL.glOrtho(-1,1,-1,1,-1,1)
            GL.glScalef(self.viewScale[0], self.viewScale[1], 1)
        if self.viewPos != None:
            GL.glMatrixMode(GL.GL_MODELVIEW)
#            GL.glLoadIdentity()
            if self.viewScale==None: scale=[1,1]
            else: scale=self.viewScale
            norm_rf_pos_x = self.viewPos[0]/scale[0]
            norm_rf_pos_y = self.viewPos[1]/scale[1]
            GL.glTranslatef( norm_rf_pos_x, norm_rf_pos_y, 0.0)
        if self.viewOri != None:
            GL.glRotatef( self.viewOri, 0.0, 0.0, -1.0)

        if haveFB:
            #set rendering back to the framebuffer object
            FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, self.frameBuffer)

        #reset returned buffer for next frame
        if clearBuffer: GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        else: GL.glClear(GL.GL_DEPTH_BUFFER_BIT)#always clear the depth bit
        self._defDepth=0.0#gets gradually updated through frame

        #waitBlanking
        if self.waitBlanking:
            GL.glBegin(GL.GL_POINTS)
            GL.glColor4f(0,0,0,0)
            if sys.platform=='win32' and self.glVendor.startswith('ati'):
                pass
            else:
                GL.glVertex2i(10,10)#this corrupts text rendering on win with some ATI cards :-(
            GL.glEnd()
            GL.glFinish()

        #get timestamp
        now = logging.defaultClock.getTime()
        if self.recordFrameIntervals:
            self.frames +=1
            deltaT = now - self.lastFrameT
            self.lastFrameT=now
            if self.recordFrameIntervalsJustTurnedOn: #don't do anything
                self.recordFrameIntervalsJustTurnedOn = False
            else: #past the first frame since turned on
              self.frameIntervals.append(deltaT)
              if deltaT > self._refreshThreshold:
                   self.nDroppedFrames+=1
                   if self.nDroppedFrames<reportNDroppedFrames:
                       logging.warning('t of last frame was %.2fms (=1/%i)' %(deltaT*1000, 1/deltaT), t=now)
                   elif self.nDroppedFrames==reportNDroppedFrames:
                       logging.warning("Multiple dropped frames have occurred - I'll stop bothering you about them!")

        #log events
        for logEntry in self._toLog:
            #{'msg':msg,'level':level,'obj':copy.copy(obj)}
            logging.log(msg=logEntry['msg'], level=logEntry['level'], t=now, obj=logEntry['obj'])
        self._toLog = []

        #    If self.waitBlanking is True, then return the time that
        # GL.glFinish() returned, set as the 'now' variable. Otherwise
        # return None as before
        #
        if self.waitBlanking is True:
            return now


    def update(self):
        """Deprecated: use Window.flip() instead
        """
        self.flip(clearBuffer=True)#clearBuffer was the original behaviour for win.update()

    def multiFlip(self, flips=1, clearBuffer=True):
        """
        Flips multiple times while maintaining display constant. Use this method for precise timing.

        :Parameters:

            flips: number of monitor frames to flip image. Window.multiFlip(flips=1) is equivalent to Window.flip().

            clearBuffer: as in Window.flip(). This is applied to the last flip.

        Example::

            myStim1.draw()					# Draws myStim1 to buffer
            myWin.multiFlip(clearBuffer=False, flips=6)	# Show stimulus for 4 frames (90 ms at 60Hz)
            myStim2.draw()					# Draw myStim2 "on top of" myStim1 (because buffer was not cleared above)
            myWin.multiFlip(flips=2)		# Show this for 2 frames (30 ms at 60Hz)
            myWin.multiFlip(flips=3)		# Show blank screen for 3 frames (because buffer was cleared above)
        """

        #Sanity checking
        if flips < 1 and int(flips) == flips:
            logging.error("flips argument for multiFlip should be a positive integer")
        if flips > 1 and not self.waitBlanking:
            logging.warning("Call to Window.multiFlip() with flips > 1 is unnecessary because Window.waitBlanking=False")

        #Do the flipping with last flip as special case
        for frame in range(flips-1):
            self.flip(clearBuffer=False)
        self.flip(clearBuffer=clearBuffer)

    def setBuffer(self, buffer, clear=True):
        """Choose which buffer to draw to ('left' or 'right').

        Requires the Window to be initialised with stereo=True and requires a
        graphics card that supports quad buffering (e,g nVidia Quadro series)

        PsychoPy always draws to the back buffers, so 'left' will use GL_BACK_LEFT
        This then needs to be flipped once both eye's buffers have been rendered.

        Typical usage::

            win = visual.Window(...., stereo=True)
            while True:
                win.setBuffer('left',clear=True) #clear may not actually be needed
                #do drawing for left eye
                win.setBuffer('right', clear=True)
                #do drawing for right eye
                win.flip()

        """
        if buffer=='left':
            GL.glDrawBuffer(GL.GL_BACK_LEFT)
        elif buffer=='right':
            GL.glDrawBuffer(GL.GL_BACK_RIGHT)
        else:
            raise "Unknown buffer '%s' requested in Window.setBuffer" %buffer
        if clear:
            self.clearBuffer()

    def clearBuffer(self):
        """Clear the back buffer (to which you are currently drawing) without flipping the window.
        Useful if you want to generate movie sequences from the back buffer without actually
        taking the time to flip the window.
        """
        #reset returned buffer for next frame
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self._defDepth=0.0#gets gradually updated through frame

    def getMovieFrame(self, buffer='front'):
        """
        Capture the current Window as an image.
        This can be done at any time (usually after a .update() command).

        Frames are stored in memory until a .saveMovieFrames(filename) command
        is issued. You can issue getMovieFrame() as often
        as you like and then save them all in one go when finished.
        """
        im = self._getFrame(buffer=buffer)
        self.movieFrames.append(im)

    def _getFrame(self, buffer='front'):
        """
        Return the current Window as an image.
        """
        #GL.glLoadIdentity()
        #do the reading of the pixels
        if buffer=='back':
            GL.glReadBuffer(GL.GL_BACK)
        else:
            GL.glReadBuffer(GL.GL_FRONT)

        #fetch the data with glReadPixels
        #pyglet.gl stores the data in a ctypes buffer
        bufferDat = (GL.GLubyte * (4 * self.size[0] * self.size[1]))()
        GL.glReadPixels(0,0,self.size[0],self.size[1], GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,bufferDat)
        im = Image.fromstring(mode='RGBA',size=self.size, data=bufferDat)

        im=im.transpose(Image.FLIP_TOP_BOTTOM)
        im=im.convert('RGB')

        return im

    def saveMovieFrames(self, fileName, mpgCodec='mpeg1video',
        fps=30, clearFrames=True):
        """
        Writes any captured frames to disk. Will write any format
        that is understood by PIL (tif, jpg, bmp, png...)

        :parameters:

            filename: name of file, including path (required)
                The extension at the end of the file determines the type of file(s)
                created. If an image type is given the multiple static frames are created.
                If it is .gif then an animated GIF image is created (although you will get higher
                quality GIF by saving PNG files and then combining them in dedicated
                image manipulation software (e.g. GIMP). On windows and linux `.mpeg` files
                can be created if `pymedia` is installed. On OS X `.mov` files can be created
                if the pyobjc-frameworks-QTKit is installed.

            mpgCodec: the code to be used **by pymedia** if the filename ends in .mpg

            fps: the frame rate to be used throughout the movie **only for quicktime (.mov) movies**

            clearFrames: set this to False if you want the frames to be kept for
                additional calls to `saveMovieFrames`

        Examples::

            myWin.saveMovieFrames('frame.tif')#writes a series of static frames as frame001.tif, frame002.tif etc...
            myWin.saveMovieFrames('stimuli.mov', fps=25)#on OS X only
            myWin.saveMovieFrames('stimuli.gif')#not great quality animated gif
            myWin.saveMovieFrames('stimuli.mpg')#not on OS X

        """
        fileRoot, fileExt = os.path.splitext(fileName)
        if len(self.movieFrames)==0:
            logging.error('no frames to write - did you forget to update your window?')
            return
        else:
            logging.info('writing %i frames' %len(self.movieFrames))
        if fileExt=='.gif': makeMovies.makeAnimatedGIF(fileName, self.movieFrames)
        elif fileExt in ['.mpg', '.mpeg']:
            if sys.platform=='darwin':
                raise IOError('Mpeg movies are not currently available under OSX.'+\
                    ' You can use quicktime movies (.mov) instead though.')
            makeMovies.makeMPEG(fileName, self.movieFrames, codec=mpgCodec)
        elif fileExt in ['.mov', '.MOV']:
            if sys.platform!='darwin':
                raise IOError('Quicktime movies are only currently available under OSX.'+\
                    ' Try using mpeg compression instead (.mpg).')
            mov = makeMovies.QuicktimeMovie(fileName, fps=fps)
            for frame in self.movieFrames:
                mov.addFrame(frame)
            mov.save()
        elif len(self.movieFrames)==1:
            self.movieFrames[0].save(fileName)
        else:
            frame_name_format = "%s%%0%dd%s" % (fileRoot, numpy.ceil(numpy.log10(len(self.movieFrames)+1)), fileExt)
            for frameN, thisFrame in enumerate(self.movieFrames):
               thisFileName = frame_name_format % (frameN+1,)
               thisFrame.save(thisFileName)
        if clearFrames: self.movieFrames=[]

    def _getRegionOfFrame(self, rect=[-1,1,1,-1], buffer='front', power2=False, squarePower2=False):
        """
        Capture a rectangle (Left Top Right Bottom, norm units) of the window as an RBGA image.

        power2 can be useful with older OpenGL versions to avoid interpolation in PatchStim.
        If power2 or squarePower2, it will expand rect dimensions up to next power of two.
        squarePower2 uses the max dimenions. You need to check what your hardware &
        opengl supports, and call _getRegionOfFrame as appropriate.
        """
        # Ideally: rewrite using GL frame buffer object; glReadPixels == slow

        x, y = self.size # of window, not image
        imType = 'RGBA' # not tested with anything else

        box = [(rect[0]/2. + 0.5)*x, (rect[1]/-2. + 0.5)*y, # Left Top in pix
                (rect[2]/2. + 0.5)*x, (rect[3]/-2. + 0.5)*y] # Right Bottom in pix
        box = map(int, box)
        if buffer=='back':
            GL.glReadBuffer(GL.GL_BACK)
        else:
            GL.glReadBuffer(GL.GL_FRONT)

        if self.winType == 'pyglet': #pyglet.gl stores the data in a ctypes buffer
            bufferDat = (GL.GLubyte * (4 * (box[2]-box[0]) * (box[3]-box[1])))()
            GL.glReadPixels(box[0], box[1], box[2]-box[0], box[3]-box[1], GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, bufferDat)
            #http://www.opengl.org/sdk/docs/man/xhtml/glGetTexImage.xml
            #GL.glGetTexImage(GL.GL_TEXTURE_1D, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, bufferDat) # not right
            im = Image.fromstring(mode='RGBA', size=(box[2]-box[0], box[3]-box[1]), data=bufferDat)
        else: # works but much slower #pyopengl returns the data
            im = Image.fromstring(mode='RGBA', size=(box[2]-box[0], box[3]-box[1]),
                                  data=GL.glReadPixels(box[0], box[1], (box[2]-box[0]),
                                        (box[3]-box[1]), GL.GL_RGBA,GL.GL_UNSIGNED_BYTE),)
        region = im.transpose(Image.FLIP_TOP_BOTTOM)

        if power2 or squarePower2: # use to avoid interpolation in PatchStim
            if squarePower2:
                xPowerOf2 = yPowerOf2 = int(2**numpy.ceil(numpy.log2(max(region.size))))
            else:
                xPowerOf2 = int(2**numpy.ceil(numpy.log2(region.size[0])))
                yPowerOf2 = int(2**numpy.ceil(numpy.log2(region.size[1])))
            imP2 = Image.new(imType, (xPowerOf2, yPowerOf2))
            imP2.paste(region, (int(xPowerOf2/2. - region.size[0]/2.),
                                int(yPowerOf2/2. - region.size[1]/2))) # paste centered
            region = imP2

        return region

    def close(self):
        """Close the window (and reset the Bits++ if necess)."""
        if (not self.useNativeGamma) and self.origGammaRamp!=None:
            psychopy.gamma.setGammaRamp(self.winHandle, self.origGammaRamp)
        self.setMouseVisible(True)
        if self.winType=='pyglet':
            self.winHandle.close()
        else:
            #pygame.quit()
            pygame.display.quit()
        if self.bitsMode!=None:
            self.bits.reset()
        openWindows.remove(self)
        logging.flush()

    def fps(self):
        """Report the frames per second since the last call to this function
        (or since the window was created if this is first call)"""
        fps = self.frames/(self.frameClock.getTime())
        self.frameClock.reset()
        self.frames = 0
        return fps

    def setColor(self, color, colorSpace=None, operation=''):
        """Set the color of the window.

        NB This command sets the color that the blank screen will have on the next
        clear operation. As a result it effectively takes TWO `flip()` operations to become
        visible (the first uses the color to create the new screen, the second presents
        that screen to the viewer).

        See :ref:`colorspaces` for further information about the ways to specify colors and their various implications.

        :Parameters:

        color :
            Can be specified in one of many ways. If a string is given then it
            is interpreted as the name of the color. Any of the standard html/X11
            `color names <http://www.w3schools.com/html/html_colornames.asp>`
            can be used. e.g.::

                myStim.setColor('white')
                myStim.setColor('RoyalBlue')#(the case is actually ignored)

            A hex value can be provided, also formatted as with web colors. This can be
            provided as a string that begins with # (not using python's usual 0x000000 format)::

                myStim.setColor('#DDA0DD')#DDA0DD is hexadecimal for plum

            You can also provide a triplet of values, which refer to the coordinates
            in one of the :ref:`colorspaces`. If no color space is specified then the color
            space most recently used for this stimulus is used again.

                myStim.setColor([1.0,-1.0,-1.0], 'rgb')#a red color in rgb space
                myStim.setColor([0.0,45.0,1.0], 'dkl') #DKL space with elev=0, azimuth=45
                myStim.setColor([0,0,255], 'rgb255') #a blue stimulus using rgb255 space

            Lastly, a single number can be provided, x, which is equivalent to providing
            [x,x,x].

                myStim.setColor(255, 'rgb255') #all guns o max

        colorSpace : string or None

            defining which of the :ref:`colorspaces` to use. For strings and hex
            values this is not needed. If None the default colorSpace for the stimulus is
            used (defined during initialisation).

        operation : one of '+','-','*','/', or '' for no operation (simply replace value)

            for colors specified as a triplet of values (or single intensity value)
            the new value will perform this operation on the previous color

                thisStim.setColor([1,1,1],'rgb255','+')#increment all guns by 1 value
                thisStim.setColor(-1, 'rgb', '*') #multiply the color by -1 (which in this space inverts the contrast)
                thisStim.setColor([10,0,0], 'dkl', '+')#raise the elevation from the isoluminant plane by 10 deg
        """
        _setColor(self, color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='rgb', #or 'fillRGB' etc
                    colorAttrib='color')

        if self.colorSpace in ['rgb','dkl','lms','hsv']: #these spaces are 0-centred
            desiredRGB = (self.rgb+1)/2.0#RGB in range 0:1 and scaled for contrast
        else:
            desiredRGB = (self.rgb)/255.0
        if self.winHandle!=None:#if it is None then this will be done during window setup
            if self.winType=='pyglet': self.winHandle.switch_to()
            GL.glClearColor(desiredRGB[0], desiredRGB[1], desiredRGB[2], 1.0)

    def setRGB(self, newRGB):
        """Deprecated: As of v1.61.00 please use `setColor()` instead
        """
        global GL
        if type(newRGB) in [int, float]:
            self.rgb=[newRGB, newRGB, newRGB]
        else:
            self.rgb=newRGB
        if self.winType=='pyglet': self.winHandle.switch_to()
        GL.glClearColor((self.rgb[0]+1.0)/2.0, (self.rgb[1]+1.0)/2.0, (self.rgb[2]+1.0)/2.0, 1.0)

    def setScale(self, units, font='dummyFont', prevScale=(1.0,1.0)):
        """This method is called from within the draw routine and sets the
        scale of the OpenGL context to map between units. Could potentially be
        called by the user in order to draw OpenGl objects manually
        in each frame.

        The `units` can be 'height' (multiples of window height), 'norm'(normalised), 'pix'(pixels), 'cm' or
        'stroke_font'. The `font` parameter is only used if units='stroke_font'
        """
        if units=="norm":
            thisScale = numpy.array([1.0,1.0])
        elif units=="height":
            thisScale = numpy.array([2.0*self.size[1]/self.size[0],2.0])
        elif units in ["pix", "pixels"]:
            thisScale = 2.0/numpy.array(self.size)
        elif units=="cm":
            #windowPerCM = windowPerPIX / CMperPIX
            #                       = (window      /winPIX)        / (scrCm                               /scrPIX)
            if (self.scrWidthCM in [0,None]) or (self.scrWidthPIX in [0, None]):
                logging.error('you didnt give me the width of the screen (pixels and cm). Check settings in MonitorCentre.')
                core.wait(1.0); core.quit()
            thisScale = (numpy.array([2.0,2.0])/self.size)/(float(self.scrWidthCM)/float(self.scrWidthPIX))
        elif units in ["deg", "degs"]:
            #windowPerDeg = winPerCM*CMperDEG
            #               = winPerCM              * tan(pi/180) * distance
            if (self.scrWidthCM in [0,None]) or (self.scrWidthPIX in [0, None]):
                logging.error('you didnt give me the width of the screen (pixels and cm). Check settings in MonitorCentre.')
                core.wait(1.0); core.quit()
            cmScale = (numpy.array([2.0,2.0])/self.size)/(float(self.scrWidthCM)/float(self.scrWidthPIX))
            thisScale = cmScale * 0.017455 * self.scrDistCM
        elif units=="stroke_font":
            thisScale = numpy.array([2*font.letterWidth,2*font.letterWidth]/self.size/38.0)
        #actually set the scale as appropriate
        thisScale = thisScale/numpy.asarray(prevScale)#allows undoing of a previous scaling procedure
        GL.glScalef(thisScale[0], thisScale[1], 1.0)
        return thisScale #just in case the user wants to know?!

    def setGamma(self,gamma):
        """Set the monitor gamma, using Bits++ if possible"""
        if type(gamma) in [float, int]:
            self.gamma=[gamma,gamma,gamma]
        else:
            self.gamma=gamma

        if self.bitsMode != None:
            #first ensure that window gamma is 1.0
            if self.winType=='pygame':
                pygame.display.set_gamma(1.0,1.0,1.0)
            elif self.winType=='pyglet':
                self.winHandle.setGamma(self.winHandle, 1.0)
            #then set bits++ to desired gamma
            self.bits.setGamma(self.gamma)
        elif self.winType=='pygame':
            pygame.display.set_gamma(self.gamma[0], self.gamma[1], self.gamma[2])
        elif self.winType=='pyglet':
            self.winHandle.setGamma(self.winHandle, self.gamma)

    def _setupPyglet(self):
        self.winType = "pyglet"
        if self.allowStencil:
            stencil_size=8
        else:
            stencil_size=0
        config = GL.Config(depth_size=8, double_buffer=True,
            stencil_size=stencil_size, stereo=self.stereo) #options that the user might want
        allScrs = pyglet.window.get_platform().get_default_display().get_screens()
        if len(allScrs)>self.screen:
            thisScreen = allScrs[self.screen]
            logging.info('configured pyglet screen %i' %self.screen)
        else:
            logging.error("Requested an unavailable screen number")
        #if fullscreen check screen size
        if self._isFullScr:
            self._checkMatchingSizes(self.size,[thisScreen.width, thisScreen.height])
            w=h=None
        else:w,h=self.size
        if self.allowGUI: style=None
        else: style='borderless'
        self.winHandle = pyglet.window.Window(width=w,height=h,
                                              caption="PsychoPy",
                                              fullscreen=self._isFullScr,
                                              config=config,
                                              screen=thisScreen,
                                              style=style
                                          )
        #provide warning if stereo buffers are requested but unavailable
        if self.stereo and not GL.gl_info.have_extension(GL.GL_STEREO):
            logging.warning('A stereo window was requested but the graphics card does not appear to support GL_STEREO')
        #add these methods to the pyglet window
        self.winHandle.setGamma = psychopy.gamma.setGamma
        self.winHandle.setGammaRamp = psychopy.gamma.setGammaRamp
        self.winHandle.getGammaRamp = psychopy.gamma.getGammaRamp
        self.winHandle.set_vsync(True)
        self.winHandle.on_text = psychopy.event._onPygletText
        self.winHandle.on_key_press = psychopy.event._onPygletKey
        self.winHandle.on_mouse_press = psychopy.event._onPygletMousePress
        self.winHandle.on_mouse_release = psychopy.event._onPygletMouseRelease
        self.winHandle.on_mouse_scroll = psychopy.event._onPygletMouseWheel
        if not self.allowGUI:
            #make mouse invisible. Could go further and make it 'exclusive' (but need to alter x,y handling then)
            self.winHandle.set_mouse_visible(False)
        self.winHandle.on_resize = self.onResize
        if self.pos==None:
            #work out where the centre should be
            self.pos = [ (thisScreen.width-self.size[0])/2 , (thisScreen.height-self.size[1])/2 ]
        self.winHandle.set_location(self.pos[0]+thisScreen.x, self.pos[1]+thisScreen.y)#add the necessary amount for second screen

        try: #to load an icon for the window
            iconFile = os.path.join(psychopy.prefs.paths['resources'], 'psychopy.ico')
            icon = pyglet.image.load(filename=iconFile)
            self.winHandle.set_icon(icon)
        except: pass#doesn't matter
    def _checkMatchingSizes(self, requested,actual):
        """Checks whether the requested and actual screen sizes differ. If not
        then a warning is output and the window size is set to actual
        """
        if list(requested)!=list(actual):
            logging.warning("User requested fullscreen with size %s, but screen is actually %s. Using actual size" \
                %(requested, actual))
            self.size=numpy.array(actual)
    def _setupPygame(self):
        #we have to do an explicit import of pyglet.gl from pyglet (only when using pygem backend)
        #Not clear why it's needed but otherwise drawing is corrupt. Using a
        #pyglet Window presumably gets around the problem
        import pyglet.gl as GL

        self.winType = "pygame"
        #pygame.mixer.pre_init(22050,16,2)#set the values to initialise sound system if it gets used
        pygame.init()
        if self.allowStencil: pygame.display.gl_set_attribute(pygame.locals.GL_STENCIL_SIZE, 8)

        try: #to load an icon for the window
            iconFile = os.path.join(psychopy.__path__[0], 'psychopy.png')
            icon = pygame.image.load(iconFile)
            pygame.display.set_icon(icon)
        except: pass#doesn't matter

        winSettings = pygame.OPENGL|pygame.DOUBLEBUF #these are ints stored in pygame.locals
        if self._isFullScr:
            winSettings = winSettings | pygame.FULLSCREEN
            #check screen size if full screen
            scrInfo=pygame.display.Info()
            self._checkMatchingSizes(self.size,[scrInfo.current_w,scrInfo.current_h])
        elif self.pos==None:
            #centre video
            os.environ['SDL_VIDEO_CENTERED']="1"
        else: os.environ['SDL_VIDEO_WINDOW_POS']= '%i,%i' %(self.pos[0], self.pos[1])
        if sys.platform=='win32':
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        if not self.allowGUI:
            winSettings = winSettings |pygame.NOFRAME
            self.setMouseVisible(False)
            pygame.display.set_caption('PsychoPy (NB use with allowGUI=False when running properly)')
        else:
            self.setMouseVisible(True)
            pygame.display.set_caption('PsychoPy')
        self.winHandle = pygame.display.set_mode(self.size.astype('i'),winSettings)
        pygame.display.set_gamma(1.0) #this will be set appropriately later
    def _setupGL(self):

        #setup screen color
        if self.colorSpace in ['rgb','dkl','lms','hsv']: #these spaces are 0-centred
            desiredRGB = (self.rgb+1)/2.0#RGB in range 0:1 and scaled for contrast
        else:
            desiredRGB = self.rgb/255.0
        GL.glClearColor(desiredRGB[0],desiredRGB[1],desiredRGB[2], 1.0)
        GL.glClearDepth(1.0)

        GL.glViewport(0, 0, int(self.size[0]), int(self.size[1]))

        GL.glMatrixMode(GL.GL_PROJECTION) # Reset The Projection Matrix
        GL.glLoadIdentity()
        GL.gluOrtho2D(-1,1,-1,1)

        GL.glMatrixMode(GL.GL_MODELVIEW)# Reset The Projection Matrix
        GL.glLoadIdentity()

        GL.glDisable(GL.GL_DEPTH_TEST)
        #GL.glEnable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
        #GL.glDepthFunc(GL.GL_LESS)                      # The Type Of Depth Test To Do
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        GL.glShadeModel(GL.GL_SMOOTH)                   # Color Shading (FLAT or SMOOTH)
        GL.glEnable(GL.GL_POINT_SMOOTH)

        #check for GL_ARB_texture_float (which is needed for shaders to be useful)
        #this needs to be done AFTER the context has been created
        if not GL.gl_info.have_extension('GL_ARB_texture_float'):
            self._haveShaders=False

        if self.winType=='pyglet' and self._haveShaders:
            #we should be able to compile shaders (don't just 'try')
            self._progSignedTexMask = _shaders.compileProgram(_shaders.vertSimple, _shaders.fragSignedColorTexMask)#fragSignedColorTexMask
            self._progSignedTex = _shaders.compileProgram(_shaders.vertSimple, _shaders.fragSignedColorTex)
            self._progSignedTexMask1D = _shaders.compileProgram(_shaders.vertSimple, _shaders.fragSignedColorTexMask1D)
            self._progSignedTexFont = _shaders.compileProgram(_shaders.vertSimple, _shaders.fragSignedColorTexFont)
#        elif self.winType=='pygame':#on PyOpenGL we should try to get an init value
#            from OpenGL.GL.ARB import shader_objects
#            if shader_objects.glInitShaderObjectsARB():
#                self._haveShaders=True
#                self._progSignedTexMask = _shaders.compileProgram(_shaders.vertSimple, _shaders.fragSignedColorTexMask)#fragSignedColorTexMask
#                self._progSignedTex = _shaders.compileProgram(_shaders.vertSimple, _shaders.fragSignedColorTex)
#            else:
#                self._haveShaders=False

        GL.glClear(GL.GL_COLOR_BUFFER_BIT|GL.GL_DEPTH_BUFFER_BIT)

        #identify gfx card vendor
        self.glVendor=GL.gl_info.get_vendor().lower()

        if sys.platform=='darwin':
            platform_specific.syncSwapBuffers(1)

        if haveFB:
            self._setupFrameBuffer()

    def _setupFrameBuffer(self):
        # Setup framebuffer
        self.frameBuffer = FB.glGenFramebuffersEXT(1)

        FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, self.frameBuffer)
        # Setup depthbuffer
        self.depthBuffer = FB.glGenRenderbuffersEXT(1)
        FB.glBindRenderbufferEXT (FB.GL_RENDERBUFFER_EXT,self.depthBuffer)
        FB.glRenderbufferStorageEXT (FB.GL_RENDERBUFFER_EXT, GL.GL_DEPTH_COMPONENT, int(self.size[0]), int(self.size[1]))

        # Create texture to render to
        self.frameTexture = GL.glGenTextures (1)
        GL.glBindTexture (GL.GL_TEXTURE_2D, self.frameTexture)
        GL.glTexParameteri (GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri (GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexImage2D (GL.GL_TEXTURE_2D, 0, GL.GL_RGBA32F_ARB, int(self.size[0]), int(self.size[1]), 0,
                         GL.GL_RGBA, GL.GL_FLOAT, None)

        #attach texture to the frame buffer
        FB.glFramebufferTexture2DEXT (FB.GL_FRAMEBUFFER_EXT, GL.GL_COLOR_ATTACHMENT0_EXT,
                                      GL.GL_TEXTURE_2D, self.frameTexture, 0)
        FB.glFramebufferRenderbufferEXT(FB.GL_FRAMEBUFFER_EXT, GL.GL_DEPTH_ATTACHMENT_EXT,
                                        FB.GL_RENDERBUFFER_EXT, self.depthBuffer)

        status = FB.glCheckFramebufferStatusEXT (FB.GL_FRAMEBUFFER_EXT)
        if status != FB.GL_FRAMEBUFFER_COMPLETE_EXT:
            logging.warning("Error in framebuffer activation")
            return
        GL.glDisable(GL.GL_TEXTURE_2D)

    def setMouseVisible(self,visibility):
        """Sets the visibility of the mouse cursor.

        If Window was initilised with noGUI=True then the mouse is initially
        set to invisible, otherwise it will initially be visible.

        Usage:
            ``setMouseVisible(False)``
            ``setMouseVisible(True)``
        """
        if self.winType=='pygame':wasVisible = pygame.mouse.set_visible(visibility)
        elif self.winType=='pyglet':self.winHandle.set_mouse_visible(visibility)
        self.mouseVisible = visibility
    def _getActualFrameRate(self,nMaxFrames=100,nWarmUpFrames=10, threshold=1):
        """Measures the actual fps for the screen.

        This is done by waiting (for a max of nMaxFrames) until 10 frames in a
        row have identical frame times (std dev below 1ms).

        If there are no 10 consecutive identical frames a warning is logged and
        `None` will be returned.

        :parameters:

            nMaxFrames:
                the maxmimum number of frames to wait for a matching set of 10

            nWarmUpFrames:
                the number of frames to display before starting the test (this is
                in place to allow the system to settle after opening the
                `Window` for the first time.

            threshold:
                the threshold for the std deviation (in ms) before the set are considered
                a match

        """
        recordFrmIntsOrig = self.recordFrameIntervals
        #run warm-ups
        self.setRecordFrameIntervals(False)
        for frameN in range(nWarmUpFrames):
            self.flip()
        #run test frames
        self.setRecordFrameIntervals(True)
        for frameN in range(nMaxFrames):
            self.flip()
            if len(self.frameIntervals)>=10 and numpy.std(self.frameIntervals[-10:])<(threshold/1000.0):
                rate = 1.0/numpy.mean(self.frameIntervals[-10:])
                if self.screen==None:scrStr=""
                else: scrStr = " (%i)" %self.screen
                logging.debug('Screen%s actual frame rate measured at %.2f' %(scrStr,rate))
                self.setRecordFrameIntervals(recordFrmIntsOrig)
                self.frameIntervals=[]
                return rate
        #if we got here we reached end of maxFrames with no consistent value
        logging.warning("Couldn't measure a consistent frame rate.\n" + \
            "  - Is your graphics card set to sync to vertical blank?\n" + \
            "  - Are you running other processes on your computer?\n")
        return None

class _BaseVisualStim:
    """A template for a stimulus class, on which GratingStim, TextStim etc... are based.
    Not finished...?
    """
    def __init__(self, win, units=None, name='', autoLog=True):
        self.win=win
        self.name=name
        self.autoLog=autoLog
        self.status = NOT_STARTED
        #unit conversions
        if units!=None and len(units): self.units = units
        else: self.units = win.units
        if self.units in ['norm','height']: self._winScale=self.units
        else: self._winScale='pix' #set the window to have pixels coords

    def draw(self):
        raise NotImplementedError('Stimulus classes must overide _BaseVisualStim.draw')
    def setPos(self, newPos, operation='', units=None, log=True):
        """Set the stimulus position in the specified (or inherited) `units`
        """
        self._set('pos', val=newPos, op=operation, log=log)
        self._calcPosRendered()
    def setDepth(self,newDepth, operation='', log=True):
        self._set('depth', newDepth, operation, log)
    def setSize(self, newSize, operation='', units=None, log=True):
        """Set the stimulus size [X,Y] in the specified (or inherited) `units`
        """
        if units==None: units=self.units#need to change this to create several units from one
        self._set('size', newSize, op=operation, log=log)
        self._requestedSize=newSize#to track whether we're just using a default
        self._calcSizeRendered()
        if hasattr(self, '_calcCyclesPerStim'):
            self._calcCyclesPerStim()
        self.needUpdate=True
    def setOri(self, newOri, operation='', log=True):
        """Set the stimulus orientation in degrees
        """
        self._set('ori',val=newOri, op=operation, log=log)
    def setOpacity(self,newOpacity,operation='', log=True):
        """Set the opacity of the stimulus.
        :parameters:
            newOpacity: float between 0 (transparent) and 1 (opaque).

            operation: one of '+','-','*','/', or '' for no operation (simply replace value)
        """
        if not 0 <= newOpacity <= 1 and log:
            logging.warning('Setting opacity outside range 0.0 - 1.0 has no additional effect')

        self._set('opacity', newOpacity, operation, log=log)

        #opacity is coded by the texture, if not using shaders
        if hasattr(self, '_useShaders') and not self._useShaders:
            if hasattr(self,'setMask'):
                self.setMask(self._maskName, log=False)

    def setContrast(self, newContrast, operation='', log=True):
        """"
        Set the contrast of the stimulus.

        :Parameters:

        newContrast : float
            The contrast of the stimulus::

                # 0.0 to 1.0 decreases contrast #Here
                # 1.0 means unchanged

                # 0.0 to -1.0 inverts with decreased contrast
                # -1.0 means exactly inverted.

                # >1.0 increases contrast. (See warning below)
                # <-1.0 inverts with increased contrast (See warning below)

            WARNING. Setting contrast below -1 og above 1 will produce strange results if this forces the stimulus to blacker-than-black or whiter-than-white.

        operation : one of '+','-','*','/', or '' for no operation (simply replace value)
        """

        self._set('contrast', newContrast, operation, log=log)

        # If we don't have shaders we need to rebuild the stimulus
        if hasattr(self, '_useShaders'):
            if not self._useShaders:
                if self.__class__.__name__ == 'TextStim':
                    self.setText(self.text)
                if self.__class__.__name__ == 'ImageStim':
                    self.setImage(self._imName)
                if self.__class__.__name__ in ('GratingStim', 'RadialStim'):
                    self.setTex(self._texName)
                if self.__class__.__name__ in ('ShapeStim','DotStim'):
                    pass # They work fine without shaders?
                elif log:
                    logging.warning('Called setContrast while _useShaders = False but stimulus was not rebuild. Contrast might remain unchanged.')
        elif log:
            logging.warning('Called setContrast() on class where _useShaders was undefined. Contrast might remain unchanged')

    def setDKL(self, newDKL, operation=''):
        """DEPRECATED since v1.60.05: Please use setColor
        """
        self._set('dkl', val=newDKL, op=operation)
        self.setRGB(psychopy.misc.dkl2rgb(self.dkl, self.win.dkl_rgb))
    def setLMS(self, newLMS, operation=''):
        """DEPRECATED since v1.60.05: Please use setColor
        """
        self._set('lms', value=newLMS, op=operation)
        self.setRGB(psychopy.misc.lms2rgb(self.lms, self.win.lms_rgb))
    def setRGB(self, newRGB, operation=''):
        """DEPRECATED since v1.60.05: Please use setColor
        """
        self._set('rgb', newRGB, operation)
        _setTexIfNoShaders(self)

    def setColor(self, color, colorSpace=None, operation='', log=True):
        """Set the color of the stimulus. See :ref:`colorspaces` for further information
        about the various ways to specify colors and their various implications.

        :Parameters:

        color :
            Can be specified in one of many ways. If a string is given then it
            is interpreted as the name of the color. Any of the standard html/X11
            `color names <http://www.w3schools.com/html/html_colornames.asp>`
            can be used. e.g.::

                myStim.setColor('white')
                myStim.setColor('RoyalBlue')#(the case is actually ignored)

            A hex value can be provided, also formatted as with web colors. This can be
            provided as a string that begins with # (not using python's usual 0x000000 format)::

                myStim.setColor('#DDA0DD')#DDA0DD is hexadecimal for plum

            You can also provide a triplet of values, which refer to the coordinates
            in one of the :ref:`colorspaces`. If no color space is specified then the color
            space most recently used for this stimulus is used again.::

                myStim.setColor([1.0,-1.0,-1.0], 'rgb')#a red color in rgb space
                myStim.setColor([0.0,45.0,1.0], 'dkl') #DKL space with elev=0, azimuth=45
                myStim.setColor([0,0,255], 'rgb255') #a blue stimulus using rgb255 space

            Lastly, a single number can be provided, x, which is equivalent to providing
            [x,x,x].::

                myStim.setColor(255, 'rgb255') #all guns o max

        colorSpace : string or None

            defining which of the :ref:`colorspaces` to use. For strings and hex
            values this is not needed. If None the default colorSpace for the stimulus is
            used (defined during initialisation).

        operation : one of '+','-','*','/', or '' for no operation (simply replace value)

            for colors specified as a triplet of values (or single intensity value)
            the new value will perform this operation on the previous color::

                thisStim.setColor([1,1,1],'rgb255','+')#increment all guns by 1 value
                thisStim.setColor(-1, 'rgb', '*') #multiply the color by -1 (which in this space inverts the contrast)
                thisStim.setColor([10,0,0], 'dkl', '+')#raise the elevation from the isoluminant plane by 10 deg
        """
        _setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='rgb', #or 'fillRGB' etc
                    colorAttrib='color',
                    log=log)
    def _set(self, attrib, val, op='', log=True):
        """
        Deprecated. Use methods specific to the parameter you want to set

        e.g. ::

             stim.setPos([3,2.5])
             stim.setOri(45)
             stim.setPhase(0.5, "+")

        NB this method does not flag the need for updates any more - that is
        done by specific methods as described above.
        """
        if op==None: op=''
        #format the input value as float vectors
        if type(val) in [tuple,list]:
            val=numpy.asarray(val,float)

        if op=='':#this routine can handle single value inputs (e.g. size) for multi out (e.g. h,w)
            exec('self.'+attrib+'*=0') #set all values in array to 0
            exec('self.'+attrib+'+=val') #then add the value to array
        else:
            exec('self.'+attrib+op+'=val')

        if log and self.autoLog:
            self.win.logOnFlip("Set %s %s=%s" %(self.name, attrib, getattr(self,attrib)),
                level=logging.EXP,obj=self)

    def setUseShaders(self, val=True):
        """Set this stimulus to use shaders if possible.
        """
        #NB TextStim overrides this function, so changes here may need changing there too
        if val==True and self.win._haveShaders==False:
            logging.error("Shaders were requested but aren't available. Shaders need OpenGL 2.0+ drivers")
        if val!=self._useShaders:
            self._useShaders=val
            if hasattr(self,'_texName'):
                self.setTex(self._texName, log=False)
            elif hasattr(self,'_imName'):
                self.setIm(self._imName, log=False)
            self.setMask(self._maskName, log=False)
            self.needUpdate=True

    def _updateList(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set()
        Chooses between using and not using shaders each call.
        """
        if self._useShaders:
            self._updateListShaders()
        else:
            self._updateListNoShaders()
    def _calcSizeRendered(self):
        """Calculate the size of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix', 'height']: self._sizeRendered=copy.copy(self.size)
        elif self.units in ['deg', 'degs']: self._sizeRendered=psychopy.misc.deg2pix(self.size, self.win.monitor)
        elif self.units=='cm': self._sizeRendered=psychopy.misc.cm2pix(self.size, self.win.monitor)
        else:
            logging.ERROR("Stimulus units should be 'height', 'norm', 'deg', 'cm' or 'pix', not '%s'" %self.units)
    def _calcPosRendered(self):
        """Calculate the pos of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix', 'height']: self._posRendered= copy.copy(self.pos)
        elif self.units in ['deg', 'degs']: self._posRendered=psychopy.misc.deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm': self._posRendered=psychopy.misc.cm2pix(self.pos, self.win.monitor)
    def setAutoDraw(self, val, log=True):
        """Add or remove a stimulus from the list of stimuli that will be
        automatically drawn on each flip. You do NOT need to call this on every frame flip!

        :parameters:
            - val: True/False
                True to add the stimulus to the draw list, False to remove it
        """
        toDraw=self.win._toDraw
        toDrawDepths=self.win._toDrawDepths
        beingDrawn = (self in toDraw)
        if val == beingDrawn:
            return #nothing to do
        elif val:
            #work out where to insert the object in the autodraw list
            depthArray = numpy.array(toDrawDepths)
            iis = numpy.where(depthArray<self.depth)[0]#all indices where true
            if len(iis):#we featured somewhere before the end of the list
                toDraw.insert(iis[0], self)
                toDrawDepths.insert(iis[0], self.depth)
            else:
                toDraw.append(self)
                toDrawDepths.append(self.depth)
            #update log and status
            if self.autoLog: self.win.logOnFlip(msg=u"Started presenting %s" %self.name,
                level=logging.EXP, obj=self)
            self.status = STARTED
        elif val==False:
            #remove from autodraw lists
            toDrawDepths.pop(toDraw.index(self))#remove from depths
            toDraw.remove(self)#remove from draw list
            #update log and status
            if log and self.autoLog:
                self.win.logOnFlip(msg=u"Stopped presenting %s" %self.name,
                    level=logging.EXP, obj=self)
            self.status = STOPPED
    def setAutoLog(self,val=True):
        """Turn on (or off) autoLogging for this stimulus.
        When autologging is enabled it can be overridden for an individual set()
        operation using the log=False argument.

        :parameters:
            - val: True (default) or False

        """
        self.autoLog=val
    def contains(self, x, y=None):
        """Determines if a point x,y is inside the extent of the stimulus.

        Can accept: a) two args, x and y; b) one arg, as a point (x,y) that is
        list-like; or c) an object with a getPos() method that returns x,y, such
        as a mouse. Returns True if the point is within the area defined by `vertices`.
        This handles complex shapes, including concavities and self-crossings.

        Note that, if your stimulus uses a mask (such as a Gaussian blob) then
        this is not accounted for by the `contains` method; the extent of the
        stmulus is determined purely by the size, pos and orientation settings
        (and by the vertices for shape stimuli).

        See coder demo, shapeContains.py
        """
        if self.needVertexUpdate:
            self._calcVerticesRendered()
        if hasattr(x, 'getPos'):
            x, y = x.getPos()
        elif type(x) in [list, tuple, numpy.ndarray]:
            x, y = x[0], x[1]
        if self.units in ['deg','degs']:
            x, y = psychopy.misc.deg2pix(numpy.array((x, y)), self.win.monitor)
        elif self.units == 'cm':
            x, y = psychopy.misc.cm2pix(numpy.array((x, y)), self.win.monitor)
        if self.ori:
            oriRadians = numpy.radians(self.ori)
            sinOri = numpy.sin(oriRadians)
            cosOri = numpy.cos(oriRadians)
            x0, y0 = x-self._posRendered[0], y-self._posRendered[1]
            x = x0 * cosOri - y0 * sinOri + self._posRendered[0]
            y = x0 * sinOri + y0 * cosOri + self._posRendered[1]
        
        return pointInPolygon(x, y, self)

    def _getPolyAsRendered(self):
        """return a list of vertices as rendered; used by overlaps(), centroid()
        """
        oriRadians = numpy.radians(self.ori)
        sinOri = numpy.sin(-oriRadians)
        cosOri = numpy.cos(-oriRadians)
        x = self._verticesRendered[:,0] * cosOri - self._verticesRendered[:,1] * sinOri
        y = self._verticesRendered[:,0] * sinOri + self._verticesRendered[:,1] * cosOri
        return numpy.column_stack((x,y)) + self._posRendered

    def overlaps(self, polygon):
        """Determines if this stimulus intersects another one. If `polygon` is
        another stimulus instance, then the vertices and location of that stimulus
        will be used as the polygon. Overlap detection is only approximate; it
        can fail with pointy shapes. Returns `True` if the two shapes overlap.

        Note that, if your stimulus uses a mask (such as a Gaussian blob) then
        this is not accounted for by the `overlaps` method; the extent of the
        stimulus is determined purely by the size, pos, and orientation settings
        (and by the vertices for shape stimuli).

        See coder demo, shapeContains.py
        """
        if self.needVertexUpdate:
            self._calcVerticesRendered()
        if self.ori:
            polyRendered = self._getPolyAsRendered()
            return polygonsOverlap(polyRendered, polygon)
        else:
            return polygonsOverlap(self, polygon)

    def _getDesiredRGB(self, rgb, colorSpace, contrast):
        """ Convert color to RGB while adding contrast
        Requires self.rgb, self.colorSpace and self.contrast"""
        # Ensure that we work on 0-centered color (to make negative contrast values work)
        if colorSpace not in ['rgb','dkl','lms','hsv']:
            rgb = (rgb/255.0)*2-1


        # Convert to RGB in range 0:1 and scaled for contrast
        desiredRGB = (rgb*contrast+1)/2.0

        # Check that boundaries are not exceeded
        if numpy.any(desiredRGB>1.0) or numpy.any(desiredRGB<0):
            logging.warning('Desired color %s (in RGB 0->1 units) falls outside the monitor gamut. Drawing blue instead'%desiredRGB) #AOH
            desiredRGB=[0.0,0.0,1.0]

        return desiredRGB

class DotStim(_BaseVisualStim):
    """
    This stimulus class defines a field of dots with an update rule that determines how they change
    on every call to the .draw() method.

    This single class can be used to generate a wide variety of dot motion types. For a review of
    possible types and their pros and cons see Scase, Braddick & Raymond (1996). All six possible
    motions they describe can be generated with appropriate choices of the signalDots (which
    determines whether signal dots are the 'same' or 'different' on each frame), noiseDots
    (which determines the locations of the noise dots on each frame) and the dotLife (which
    determines for how many frames the dot will continue before being regenerated).

    The default settings (as of v1.70.00) is for the noise dots to have identical velocity
    but random direction and signal dots remain the 'same' (once a signal dot, always a signal dot).

    For further detail about the different configurations see :ref:`dots` in the Builder
    Components section of the documentation.

    If further customisation is required, then the DotStim should be subclassed and its
    _update_dotsXY and _newDotsXY methods overridden.
    """
    def __init__(self,
                 win,
                 units  ='',
                 nDots  =1,
                 coherence      =0.5,
                 fieldPos       =(0.0,0.0),
                 fieldSize      = (1.0,1.0),
                 fieldShape     = 'sqr',
                 dotSize        =2.0,
                 dotLife = 3,
                 dir    =0.0,
                 speed  =0.5,
                 rgb    =None,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 opacity = 1.0,
                 contrast = 1.0,
                 depth  =0,
                 element=None,
                 signalDots='same',
                 noiseDots='direction',
                 name='', autoLog=True):
        """
        :Parameters:

            win :
                a :class:`~psychopy.visual.Window` object (required)
            units : **None**, 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window` will be used.
                See :ref:`units` for explanation of other options.
            nDots : int
                number of dots to be generated
            fieldPos : (x,y) or [x,y]
                specifying the location of the centre of the stimulus.
            fieldSize : (x,y) or [x,y] or single value (applied to both dimensions)
                Sizes can be negative and can extend beyond the window.
            fieldShape : *'sqr'* or 'circle'
                Defines the envelope used to present the dots
            dotSize
                specified in pixels (overridden if `element` is specified)
            dotLife : int
                Number of frames each dot lives for (default=3, -1=infinite)
            dir : float (degrees)
                direction of the coherent dots
            speed : float
                speed of the dots (in *units*/frame)
            signalDots : 'same' or *'different'*
                If 'same' then the signal and noise dots are constant. If different
                then the choice of which is signal and which is noise gets
                randomised on each frame. This corresponds to Scase et al's (1996) categories of RDK.
            noiseDots : *'direction'*, 'position' or 'walk'
                Determines the behaviour of the noise dots, taken directly from
                Scase et al's (1996) categories. For 'position', noise dots take a
                random position every frame. For 'direction' noise dots follow a
                random, but constant direction. For 'walk' noise dots vary their
                direction every frame, but keep a constant speed.

            color:

                Could be a:

                    - web name for a color (e.g. 'FireBrick');
                    - hex value (e.g. '#FF0047');
                    - tuple (1.0,1.0,1.0); list [1.0,1.0, 1.0]; or numpy array.

                If the last three are used then the color space should also be given
                See :ref:`colorspaces`

            colorSpace:

                The color space controlling the interpretation of the `color`
                See :ref:`colorspaces`

            opacity : float (default= *1.0* )
                1.0 is opaque, 0.0 is transparent

            contrast: float (default= *1.0* )
                How far the stimulus deviates from the middle grey.
                Contrast can vary -1:1 (this is a multiplier for the
                values given in the color description of the stimulus).

            depth:

                The depth argument is deprecated and may be removed in future versions.
                Depth is controlled simply by drawing order.

            element : *None* or a visual stimulus object
                This can be any object that has a ``.draw()`` method and a
                ``.setPos([x,y])`` method (e.g. a GratingStim, TextStim...)!!
                See `ElementArrayStim` for a faster implementation of this idea.

            name : string
                The name of the object to be using during logged messages about
                this stimulus

            """
        _BaseVisualStim.__init__(self, win, units=units, name=name, autoLog=autoLog)
        self.nDots = nDots
        #size
        if type(fieldPos) in [tuple,list]:
            self.fieldPos = numpy.array(fieldPos,float)
        else: self.fieldPos=fieldPos
        if type(fieldSize) in [tuple,list]:
            self.fieldSize = numpy.array(fieldSize)
        elif type(fieldSize) in [float,int]:
            self.fieldSize=numpy.array([fieldSize,fieldSize])
        else:
            self.fieldSize=fieldSize
        if type(dotSize) in [tuple,list]:
            self.dotSize = numpy.array(dotSize)
        else:self.dotSize=dotSize
        self.fieldShape = fieldShape
        self.dir = dir
        self.speed = speed
        self.element = element
        self.dotLife = dotLife
        self.signalDots = signalDots
        self.noiseDots = noiseDots
        self.opacity = float(opacity)
        self.contrast = float(contrast)

        #'rendered' coordinates represent the stimuli in the scaled coords of the window
        #(i.e. norm for units==norm, but pix for all other units)
        self._dotSizeRendered=None
        self._speedRendered=None
        self._fieldSizeRendered=None
        self._fieldPosRendered=None

        self._useShaders=False#not needed for dots?
        self.colorSpace=colorSpace
        if rgb!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb')
        else:
            self.setColor(color)

        self.depth=depth

        #initialise the dots themselves - give them all random dir and then
        #fix the first n in the array to have the direction specified

        self.coherence=round(coherence*self.nDots)/self.nDots#store actual coherence

        self._dotsXY = self._newDotsXY(self.nDots) #initialise a random array of X,Y
        self._dotsSpeed = numpy.ones(self.nDots, 'f')*self.speed#all dots have the same speed
        self._dotsLife = abs(dotLife)*numpy.random.rand(self.nDots)#abs() means we can ignore the -1 case (no life)
        #determine which dots are signal
        self._signalDots = numpy.zeros(self.nDots, dtype=bool)
        self._signalDots[0:int(self.coherence*self.nDots)]=True
        #numpy.random.shuffle(self._signalDots)#not really necessary
        #set directions (only used when self.noiseDots='direction')
        self._dotsDir = numpy.random.rand(self.nDots)*2*pi
        self._dotsDir[self._signalDots] = self.dir*pi/180

        self._calcFieldCoordsRendered()
        self._update_dotsXY()

    def _set(self, attrib, val, op='', log=True):
        """Use this to set attributes of your stimulus after initialising it.

        :Parameters:

        attrib : a string naming any of the attributes of the stimulus (set during init)
        val : the value to be used in the operation on the attrib
        op : a string representing the operation to be performed (optional) most maths operators apply ('+','-','*'...)

        examples::

            myStim.set('rgb',0) #will simply set all guns to zero (black)
            myStim.set('rgb',0.5,'+') #will increment all 3 guns by 0.5
            myStim.set('rgb',(1.0,0.5,0.5),'*') # will keep the red gun the same and halve the others

        """
        #format the input value as float vectors
        if type(val) in [tuple,list]:
            val=numpy.array(val,float)

        #change the attribute as requested
        if op=='':
            #note: this routine can handle single value inputs (e.g. size) for multi out (e.g. h,w)
            exec('self.'+attrib+'*=0') #set all values in array to 0
            exec('self.'+attrib+'+=val') #then add the value to array
        else:
            exec('self.'+attrib+op+'=val')

        #update the actual coherence for the requested coherence and nDots
        if attrib in ['nDots','coherence']:
            self.coherence=round(self.coherence*self.nDots)/self.nDots

        if log and self.autoLog:
            self.win.logOnFlip("Set %s %s=%s" %(self.name, attrib, getattr(self,attrib)),
                level=logging.EXP,obj=self)

    def set(self, attrib, val, op='', log=True):
        """DotStim.set() is obsolete and may not be supported in future
        versions of PsychoPy. Use the specific method for each parameter instead
        (e.g. setFieldPos(), setCoherence()...)
        """
        self._set(attrib, val, op, log=log)
    def setPos(self, newPos=None, operation='', units=None, log=True):
        """Obsolete - users should use setFieldPos instead of setPos
        """
        logging.error("User called DotStim.setPos(pos). Use DotStim.SetFieldPos(pos) instead.")
    def setFieldPos(self,val, op='', log=True):
        self._set('fieldPos', val, op, log=log)
        self._calcFieldCoordsRendered()
    def setFieldCoherence(self,val, op='', log=True):
        """Change the coherence (%) of the DotStim. This will be rounded according
        to the number of dots in the stimulus.
        """
        self._set('coherence', val, op, log=log)
        self.coherence=round(self.coherence*self.nDots)/self.nDots#store actual coherence rounded by nDots
        self._signalDots = numpy.zeros(self.nDots, dtype=bool)
        self._signalDots[0:int(self.coherence*self.nDots)]=True
        #for 'direction' method we need to update the direction of the number
        #of signal dots immediately, but for other methods it will be done during updateXY
        if self.noiseDots in ['direction','position']:
            self._dotsDir=numpy.random.rand(self.nDots)*2*pi
            self._dotsDir[self._signalDots]=self.dir*pi/180
    def setDir(self,val, op='', log=True):
        """Change the direction of the signal dots (units in degrees)
        """
        #check which dots are signal
        signalDots = self._dotsDir==(self.dir*pi/180)
        self._set('dir', val, op, log=log)
        #dots currently moving in the signal direction also need to update their direction
        self._dotsDir[signalDots] = self.dir*pi/180
    def setSpeed(self,val, op='', log=True):
        """Change the speed of the dots (in stimulus `units` per second)
        """
        self._set('speed', val, op, log=log)
    def draw(self, win=None):
        """Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if win==None: win=self.win
        if win.winType=='pyglet': win.winHandle.switch_to()

        self._update_dotsXY()

        GL.glPushMatrix()#push before drawing, pop after

        #draw the dots
        if self.element==None:
            win.setScale(self._winScale)
            #scale the drawing frame etc...
            GL.glTranslatef(self._fieldPosRendered[0],self._fieldPosRendered[1],0)
            GL.glPointSize(self.dotSize)

            #load Null textures into multitexteureARB - they modulate with glColor
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self._dotsXYRendered.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
            desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)

            GL.glColor4f(desiredRGB[0], desiredRGB[1], desiredRGB[2], self.opacity)
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDrawArrays(GL.GL_POINTS, 0, self.nDots)
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        else:
            #we don't want to do the screen scaling twice so for each dot subtract the screen centre
            initialDepth=self.element.depth
            for pointN in range(0,self.nDots):
                self.element.setPos(self._dotsXY[pointN,:]+self.fieldPos)
                self.element.draw()
            self.element.setDepth(initialDepth)#reset depth before going to next frame
        GL.glPopMatrix()

    def _newDotsXY(self, nDots):
        """Returns a uniform spread of dots, according to the fieldShape and fieldSize

        usage::

            dots = self._newDots(nDots)

        """
        if self.fieldShape=='circle':#make more dots than we need and only use those that are within circle
            while True:#repeat until we have enough
                new=numpy.random.uniform(-1, 1, [nDots*2,2])#fetch twice as many as needed
                inCircle= (numpy.hypot(new[:,0],new[:,1])<1)
                if sum(inCircle)>=nDots:
                    return new[inCircle,:][:nDots,:]*self.fieldSize/2.0
        else:
            return numpy.random.uniform(-self.fieldSize/2.0, self.fieldSize/2.0, [nDots,2])

    def _update_dotsXY(self):
        """
        The user shouldn't call this - its gets done within draw()
        """

        """Find dead dots, update positions, get new positions for dead and out-of-bounds
        """
        #renew dead dots
        if self.dotLife>0:#if less than zero ignore it
            self._dotsLife -= 1 #decrement. Then dots to be reborn will be negative
            dead = (self._dotsLife<=0.0)
            self._dotsLife[dead]=self.dotLife
        else:
            dead=numpy.zeros(self.nDots, dtype=bool)

        ##update XY based on speed and dir
        #NB self._dotsDir is in radians, but self.dir is in degs
        #update which are the noise/signal dots
        if self.signalDots =='different':
            #  **up to version 1.70.00 this was the other way around, not in keeping with Scase et al**
            #noise and signal dots change identity constantly
            numpy.random.shuffle(self._dotsDir)
            self._signalDots = (self._dotsDir==(self.dir*pi/180))#and then update _signalDots from that

        #update the locations of signal and noise
        if self.noiseDots=='walk':
            # noise dots are ~self._signalDots
            self._dotsDir[~self._signalDots] = numpy.random.rand((~self._signalDots).sum())*pi*2
            #then update all positions from dir*speed
            self._dotsXY[:,0] += self.speed*numpy.reshape(numpy.cos(self._dotsDir),(self.nDots,))
            self._dotsXY[:,1] += self.speed*numpy.reshape(numpy.sin(self._dotsDir),(self.nDots,))# 0 radians=East!
        elif self.noiseDots == 'direction':
            #simply use the stored directions to update position
            self._dotsXY[:,0] += self.speed*numpy.reshape(numpy.cos(self._dotsDir),(self.nDots,))
            self._dotsXY[:,1] += self.speed*numpy.reshape(numpy.sin(self._dotsDir),(self.nDots,))# 0 radians=East!
        elif self.noiseDots=='position':
            #update signal dots
            self._dotsXY[self._signalDots,0] += \
                self.speed*numpy.reshape(numpy.cos(self._dotsDir[self._signalDots]),(self._signalDots.sum(),))
            self._dotsXY[self._signalDots,1] += \
                self.speed*numpy.reshape(numpy.sin(self._dotsDir[self._signalDots]),(self._signalDots.sum(),))# 0 radians=East!
            #update noise dots
            dead = dead+(~self._signalDots)#just create new ones

        #handle boundaries of the field
        if self.fieldShape in  [None, 'square', 'sqr']:
            dead = dead+(numpy.abs(self._dotsXY[:,0])>(self.fieldSize[0]/2.0))+(numpy.abs
                                                                                  (self
                                                                                   ._dotsXY[:,1])>(self.fieldSize[1]/2.0))
        elif self.fieldShape == 'circle':
            #transform to a normalised circle (radius = 1 all around) then to polar coords to check
            normXY = self._dotsXY/(self.fieldSize/2.0)#the normalised XY position (where radius should be <1)
            dead = dead + (numpy.hypot(normXY[:,0],normXY[:,1])>1) #add out-of-bounds to those that need replacing

        #update any dead dots
        if sum(dead):
            self._dotsXY[dead,:] = self._newDotsXY(sum(dead))

        #update the pixel XY coordinates
        self._calcDotsXYRendered()

    def _calcDotsXYRendered(self):
        if self.units in ['norm','pix', 'height']: self._dotsXYRendered=self._dotsXY
        elif self.units in ['deg','degs']: self._dotsXYRendered=psychopy.misc.deg2pix(self._dotsXY, self.win.monitor)
        elif self.units=='cm': self._dotsXYRendered=psychopy.misc.cm2pix(self._dotsXY, self.win.monitor)
    def _calcFieldCoordsRendered(self):
        if self.units in ['norm', 'pix', 'height']:
            self._fieldSizeRendered=self.fieldSize
            self._fieldPosRendered=self.fieldPos
        elif self.units in ['deg', 'degs']:
            self._fieldSizeRendered=psychopy.misc.deg2pix(self.fieldSize, self.win.monitor)
            self._fieldPosRendered=psychopy.misc.deg2pix(self.fieldPos, self.win.monitor)
        elif self.units=='cm':
            self._fieldSizeRendered=psychopy.misc.cm2pix(self.fieldSize, self.win.monitor)
            self._fieldPosRendered=psychopy.misc.cm2pix(self.fieldPos, self.win.monitor)

class SimpleImageStim:
    """A simple stimulus for loading images from a file and presenting at exactly
    the resolution and color in the file (subject to gamma correction if set).

    Unlike the ImageStim, this type of stimulus cannot be rescaled, rotated or
    masked (although flipping horizontally or vertically is possible). Drawing will
    also tend to be marginally slower, because the image isn't preloaded to the
    graphics card. The slight advantage, however is that the stimulus will always be in its
    original aspect ratio, with no interplotation or other transformation.

    SimpleImageStim does not support a depth parameter (the OpenGL method
    that draws the pixels does not support it). Simple images will obscure any other
    stimulus type.


    """
    def __init__(self,
                 win,
                 image     ="",
                 units   ="",
                 pos     =(0.0,0.0),
                 flipHoriz=False,
                 flipVert=False,
                 name='', autoLog=True):
        """
        :Parameters:


            win :
                a :class:`~psychopy.visual.Window` object (required)
            image :
                The filename, including relative or absolute path. The image
                can be any format that the Python Imagin Library can import
                (which is almost all).
            units : **None**, 'height', 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window` will be used.
                See :ref:`units` for explanation of other options.
            pos :
                a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y of the centre of the stimulus.
                The origin is the screen centre, the units are determined
                by units (see above). Stimuli can be position beyond the
                window!
            name : string
                The name of the object to be using during logged messages about
                this stim
        """
        #NB most stimuli use _BaseVisualStim for the _set method and for
        # setting up win, name, units and autolog in __init__ but SimpleImage
        # shares very little with _Base so we do it manually here
        self.win=win
        self.name=name
        self.autoLog=autoLog
        #unit conversions
        if units!=None and len(units): self.units = units
        else: self.units = win.units
        if self.units in ['norm','height']: self._winScale=self.units
        else: self._winScale='pix' #set the window to have pixels coords

        if win._haveShaders: self._useShaders=True#by default, this is a good thing
        else: self._useShaders=False

        self.pos = numpy.array(pos, float)
        self.setImage(image)
        #check image size against window size
        if (self.size[0]>self.win.size[0]) or (self.size[1]>self.win.size[1]):
            logging.warning("Image size (%s, %s)  was larger than window size (%s, %s). Will draw black screen." % (self.size[0], self.size[1], self.win.size[0], self.win.size[1]))

        #check position with size, warn if stimuli not fully drawn
        if ((self.pos[0]+(self.size[0]/2.0) > self.win.size[0]/2.0) or (self.pos[0]-(self.size[0]/2.0) < -self.win.size[0]/2.0)):
            logging.warning("Image position and width mean the stimuli does not fit the window in the X direction.")

        if ((self.pos[1]+(self.size[1]/2.0) > self.win.size[1]/2.0) or (self.pos[1]-(self.size[1]/2.0) < -self.win.size[1]/2.0)):
            logging.warning("Image position and height mean the stimuli does not fit the window in the Y direction.")

        #flip if necessary
        self.flipHoriz=False#initially it is false, then so the flip according to arg above
        self.setFlipHoriz(flipHoriz)
        self.flipVert=False#initially it is false, then so the flip according to arg above
        self.setFlipVert(flipVert)

        self._calcPosRendered()
    def setFlipHoriz(self,newVal=True, log=True):
        """If set to True then the image will be flipped horiztonally (left-to-right).
        Note that this is relative to the original image, not relative to the current state.
        """
        if newVal!=self.flipHoriz: #we need to make the flip
            self.imArray = numpy.flipud(self.imArray)#numpy and pyglet disagree about ori so ud<=>lr
        self.flipHoriz=newVal
        self._needStrUpdate=True
        if log and self.autoLog:
            self.win.logOnFlip("Set %s flipHoriz=%s" %(self.name, newVal),
                level=logging.EXP,obj=self)
    def setFlipVert(self,newVal=True, log=True):
        """If set to True then the image will be flipped vertically (top-to-bottom).
        Note that this is relative to the original image, not relative to the current state.
        """
        if newVal!=self.flipVert: #we need to make the flip
            self.imArray = numpy.fliplr(self.imArray)#numpy and pyglet disagree about ori so ud<=>lr
        self.flipVert=newVal
        self._needStrUpdate=True
        if log and self.autoLog:
            self.win.logOnFlip("Set %s flipVert=%s" %(self.name, newVal),
                level=logging.EXP,obj=self)
    def setUseShaders(self, val=True):
        """Set this stimulus to use shaders if possible.
        """
        #NB TextStim overrides this function, so changes here may need changing there too
        if val==True and self.win._haveShaders==False:
            logging.error("Shaders were requested but aren't available. Shaders need OpenGL 2.0+ drivers")
        if val!=self._useShaders:
            self._useShaders=val
            self.setImage()
    def _updateImageStr(self):
        self._imStr=self.imArray.tostring()
        self._needStrUpdate=False
    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        #set the window to draw to
        if win==None: win=self.win
        if win.winType=='pyglet': win.winHandle.switch_to()
        #push the projection matrix and set to orthorgaphic
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glOrtho( 0, self.win.size[0],0, self.win.size[1], 0, 1 )#this also sets the 0,0 to be top-left
        #but return to modelview for rendering
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        if self._needStrUpdate: self._updateImageStr()
        #unbind any textures
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        #move to centre of stimulus and rotate
        GL.glRasterPos2f(self.win.size[0]/2.0 - self.size[0]/2.0 + self._posRendered[0],
            self.win.size[1]/2.0 - self.size[1]/2.0 + self._posRendered[1])

        #GL.glDrawPixelsub(GL.GL_RGB, self.imArr)
        GL.glDrawPixels(self.size[0],self.size[1],
            self.internalFormat,self.dataType,
            self._imStr)
        #return to 3D mode (go and pop the projection matrix)
        GL.glMatrixMode( GL.GL_PROJECTION )
        GL.glPopMatrix()
        GL.glMatrixMode( GL.GL_MODELVIEW )
    def _set(self, attrib, val, op='', log=True):
        """
        Deprecated. Use methods specific to the parameter you want to set

        e.g. ::

             stim.setPos([3,2.5])
             stim.setOri(45)
             stim.setPhase(0.5, "+")

        NB this method does not flag the need for updates any more - that is
        done by specific methods as described above.
        """
        if op==None: op=''
        #format the input value as float vectors
        if type(val) in [tuple,list]:
            val=numpy.asarray(val,float)

        if op=='':#this routine can handle single value inputs (e.g. size) for multi out (e.g. h,w)
            exec('self.'+attrib+'*=0') #set all values in array to 0
            exec('self.'+attrib+'+=val') #then add the value to array
        else:
            exec('self.'+attrib+op+'=val')

        if log and self.autoLog:
            self.win.logOnFlip("Set %s %s=%s" %(self.name, attrib, getattr(self,attrib)),
                level=logging.EXP,obj=self)
    def setPos(self, newPos, operation='', units=None, log=True):
        self._set('pos', val=newPos, op=operation, log=log)
        self._calcPosRendered()
    def setDepth(self,newDepth, operation='', log=True):
        self._set('depth', newDepth, operation, log=log)
    def _calcPosRendered(self):
        """Calculate the pos of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['pix', 'pixels', 'height', 'norm']: self._posRendered=self.pos
        elif self.units in ['deg', 'degs']: self._posRendered=psychopy.misc.deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm': self._posRendered=psychopy.misc.cm2pix(self.pos, self.win.monitor)
    def setImage(self,filename=None, log=True):
        """Set the image to be drawn.

        :Parameters:
            - filename:
                The filename, including relative or absolute path if necessary.
                Can actually also be an image loaded by PIL.

        """
        self.image=filename
        if type(filename) in [str, unicode]:
        #is a string - see if it points to a file
            if os.path.isfile(filename):
                self.filename=filename
                im = Image.open(self.filename)
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                logging.error("couldn't find image...%s" %(filename))
                core.quit()
                raise #so thatensure we quit
        else:
        #not a string - have we been passed an image?
            try:
                im = filename.copy().transpose(Image.FLIP_TOP_BOTTOM)
            except AttributeError: # ...but apparently not
                logging.error("couldn't find image...%s" %(filename))
                core.quit()
                raise #ensure we quit
            self.filename = repr(filename) #'<Image.Image image ...>'

        self.size = im.size
        #set correct formats for bytes/floats
        if im.mode=='RGBA':
            self.imArray = numpy.array(im).astype(numpy.float32)/255
            self.internalFormat = GL.GL_RGBA
        else:
            self.imArray = numpy.array(im.convert("RGB")).astype(numpy.float32)/255
            self.internalFormat = GL.GL_RGB
        self.dataType = GL.GL_FLOAT
        self._needStrUpdate = True

        if log and self.autoLog:
            self.win.logOnFlip("Set %s image=%s" %(self.name, filename),
                level=logging.EXP,obj=self)
class GratingStim(_BaseVisualStim):
    """Stimulus object for drawing arbitrary bitmaps that can repeat (cycle) in either dimension
    One of the main stimuli for PsychoPy.

    Formally GratingStim is just a texture behind an optional
    transparency mask (an 'alpha mask'). Both the texture and mask can be
    arbitrary bitmaps and their combination allows an enormous variety of
    stimuli to be drawn in realtime.

    **Examples**::

        myGrat = GratingStim(tex='sin',mask='circle') #gives a circular patch of grating
        myGabor = GratingStim(tex='sin',mask='gauss') #gives a 'Gabor'

    A GratingStim can be rotated scaled and shifted in position, its texture can
    be drifted in X and/or Y and it can have a spatial frequency in X and/or Y
    (for an image file that simply draws multiple copies in the patch).

    Also since transparency can be controlled two GratingStims can combine e.g.
    to form a plaid.

    **Using GratingStim with images from disk (jpg, tif, png...)**

    Ideally texture images to be rendered should be square with 'power-of-2' dimensions
    e.g. 16x16, 128x128. Any image that is not will be upscaled (with linear interpolation)
    to the nearest such texture by PsychoPy. The size of the stimulus should be
    specified in the normal way using the appropriate units (deg, pix, cm...). Be
    sure to get the aspect ratio the same as the image (if you don't want it
    stretched!).

    """
    def __init__(self,
                 win,
                 tex     ="sin",
                 mask    ="none",
                 units   ="",
                 pos     =(0.0,0.0),
                 size    =None,
                 sf      =None,
                 ori     =0.0,
                 phase   =(0.0,0.0),
                 texRes =128,
                 rgb   =None,
                 dkl=None,
                 lms=None,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=1.0,
                 depth=0,
                 rgbPedestal = (0.0,0.0,0.0),
                 interpolate=False,
                 name='', autoLog=True,
                 maskParams=None):
        """
        :Parameters:

            win :
                a :class:`~psychopy.visual.Window` object (required)
            tex :
                The texture forming the image

                + **'sin'**,'sqr', 'saw', 'tri', None
                + or the name of an image file (most formats supported)
                + or a numpy array (1xN or NxN) ranging -1:1

            mask :
                The alpha mask (forming the shape of the image)

                + **None**, 'circle', 'gauss', 'raisedCos'
                + or the name of an image file (most formats supported)
                + or a numpy array (1xN or NxN) ranging -1:1

            units : **None**, 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window` will be used.
                See :ref:`units` for explanation of other options.

            pos :
                a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y of the centre of the stimulus.
                The origin is the screen centre, the units are determined
                by units (see above). Stimuli can be position beyond the
                window!

            size :
                a tuple (0.5,0.5) or a list [0.5,0.5] for the x and y
                OR a single value (which will be applied to x and y).
                Units are specified by 'units' (see above).
                Sizes can be negative and can extend beyond the window.

                .. note::

                    If the mask is Gaussian ('gauss'), then the 'size' parameter refers to
                    the stimulus at 3 standard deviations on each side of the
                    centre (ie. sd=size/6)

            sf:
                a tuple (1.0,1.0) or a list [1.0,1.0] for the x and y
                OR a single value (which will be applied to x and y).
                Where `units` == 'deg' or 'cm' units are in cycles per deg/cm.
                If `units` == 'norm' then sf units are in cycles per stimulus (so scale with stimulus size).
                If texture is an image loaded from a file then sf defaults to 1/stim size to give one cycle of the image.

            ori:
                orientation of stimulus in degrees

            phase:
                a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y
                OR a single value (which will be applied to x and y).
                Phase of the stimulus in each direction.
                **NB** phase has modulus 1 (rather than 360 or 2*pi)
                This is a little unconventional but has the nice effect
                that setting phase=t*n drifts a stimulus at n Hz

            texRes:
                resolution of the texture (if not loading from an image file)

            color:

                Could be a:

                    - web name for a color (e.g. 'FireBrick');
                    - hex value (e.g. '#FF0047');
                    - tuple (1.0,1.0,1.0); list [1.0,1.0, 1.0]; or numpy array.

                If the last three are used then the color space should also be given
                See :ref:`colorspaces`

            colorSpace:
                the color space controlling the interpretation of the `color`
                See :ref:`colorspaces`

            contrast: float (default= *1.0* )
                How far the stimulus deviates from the middle grey.
                Contrast can vary -1:1 (this is a multiplier for the
                values given in the color description of the stimulus).

            opacity: float (default= *1.0* )
                1.0 is opaque, 0.0 is transparent

            depth:
                The depth argument is deprecated and may be removed in future versions.
                Depth is controlled simply by drawing order.

            name : string
                The name of the object to be using during logged messages about
                this stim

            maskParams: Various types of input. Default to None.
                This is used to pass additional parameters to the mask if those
                are needed.
                - For the 'raisedCos' mask, pass a dict: {'fringeWidth':0.2},
                where 'fringeWidth' is a parameter (float, 0-1), determining
                the proportion of the patch that will be blurred by the raised
                cosine edge.

        """
        _BaseVisualStim.__init__(self, win, units=units, name=name, autoLog=autoLog)

        if win._haveShaders: self._useShaders=True#by default, this is a good thing
        else: self._useShaders=False

        self.ori = float(ori)
        self.texRes = texRes #must be power of 2
        self.contrast = float(contrast)
        self.opacity = float(opacity)
        self.interpolate=interpolate
        self.origSize=None#if an image texture is loaded this will be updated

        self.colorSpace=colorSpace
        if rgb!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb', log=False)
        elif dkl!=None:
            logging.warning("Use of dkl arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(dkl, colorSpace='dkl', log=False)
        elif lms!=None:
            logging.warning("Use of lms arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(lms, colorSpace='lms', log=False)
        else:
            self.setColor(color, colorSpace=colorSpace, log=False)

        #NB Pedestal isn't currently being used during rendering - this is a place-holder
        if type(rgbPedestal)==float or type(rgbPedestal)==int: #user may give a luminance val
            self.rgbPedestal=numpy.array((rgbPedestal,rgbPedestal,rgbPedestal), float)
        else:
            self.rgbPedestal = numpy.asarray(rgbPedestal, float)

        #phase (ranging 0:1)
        if type(phase) in [tuple,list]:
            self.phase = numpy.array(phase, float)
        else:
            self.phase = numpy.array((phase,0),float)

        #initialise textures for stimulus
        self.texID=GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self.texID))
        self.maskID=GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self.maskID))

        # Set the maskParams (defaults to None):
        self.maskParams= maskParams

        self.setTex(tex, log=False)
        self.setMask(mask, log=False)

        #size
        self._requestedSize=size
        if size==None:
            self._setSizeToDefault()
        elif type(size) in [tuple,list]:
            self.size = numpy.array(size,float)
        else:
            self.size = numpy.array((size,size),float)#make a square if only given one dimension

        #sf
        self._requestedSf=sf
        if sf==None:
            self._setSfToDefault()
        elif type(sf) in [float, int] or len(sf)==1:
            self.sf = numpy.array((sf,sf),float)
        else:
            self.sf = numpy.array(sf,float)

        self.pos = numpy.array(pos,float)

        self.depth=depth
        #fix scaling to window coords
        self._calcCyclesPerStim()
        self._calcSizeRendered()
        self._calcPosRendered()

        #generate a displaylist ID
        self._listID = GL.glGenLists(1)
        self._updateList()#ie refresh display list


    def setSF(self,value,operation='', log=True):
        self._set('sf', value, operation, log=log)
        self.needUpdate = 1
        self._calcCyclesPerStim()
        self._requestedSf=value#to track whether we're just using a default value
    def _setSfToDefault(self):
        """Set the sf to default (e.g. to the 1.0/size of the loaded image etc)
        """
        #calculate new sf
        if self.units in ['norm','height']:
            self.sf=numpy.array([1.0,1.0])
        elif self.units in ['pix', 'pixels'] \
            or self.origSize is not None and self.units in ['deg','cm']:
            self.sf=1.0/self.size#default to one cycle
        else:
            self.sf=numpy.array([1.0,1.0])
        #set it
        self._calcCyclesPerStim()
        self.needUpdate=True
    def _setSizeToDefault(self):
        """Set the size to default (e.g. to the size of the loaded image etc)
        """
        #calculate new size
        if self.origSize is None:#not an image from a file
            self.size=numpy.array([0.5,0.5])#this was PsychoPy's original default
        else:
            #we have an image - calculate the size in `units` that matches original pixel size
            if self.units=='pix': self.size=numpy.array(self.origSize)
            elif self.units=='deg': self.size= psychopy.misc.pix2deg(numpy.array(self.origSize, float), self.win.monitor)
            elif self.units=='cm': self.size= psychopy.misc.pix2cm(numpy.array(self.origSize, float), self.win.monitor)
            elif self.units=='norm': self.size= 2*numpy.array(self.origSize, float)/self.win.size
            elif self.units=='height': self.size= numpy.array(self.origSize, float)/self.win.size[1]
        #set it
        self._calcSizeRendered()
        if hasattr(self, 'sf'):
            self._calcCyclesPerStim()
        self.needUpdate=True
    def setPhase(self,value, operation='', log=True):
        self._set('phase', value, operation, log=log)
        self.needUpdate = 1
    def setTex(self,value, log=True):
        self._texName = value
        createTexture(value, id=self.texID, pixFormat=GL.GL_RGB, stim=self,
            res=self.texRes, maskParams=self.maskParams)
        #if user requested size=None then update the size for new stim here
        if hasattr(self, '_requestedSize') and self._requestedSize==None:
            self._setSizeToDefault()
        if hasattr(self, '_requestedSf') and self._requestedSf==None:
            self._setSfToDefault()
        if log and self.autoLog:
            self.win.logOnFlip("Set %s tex=%s" %(self.name, value),
                level=logging.EXP,obj=self)
    def setMask(self,value, log=True):
        self._maskName = value
        createTexture(value, id=self.maskID, pixFormat=GL.GL_ALPHA, stim=self,
        res=self.texRes, maskParams=self.maskParams)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s mask=%s" %(self.name, value),
                level=logging.EXP,obj=self)

    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        #set the window to draw to
        if win==None: win=self.win
        if win.winType=='pyglet': win.winHandle.switch_to()

        #do scaling
        GL.glPushMatrix()#push before the list, pop after
        win.setScale(self._winScale)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],0)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        #the list just does the texture mapping

        desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
        GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)

        if self.needUpdate: self._updateList()
        GL.glCallList(self._listID)

        #return the view to previous state
        GL.glPopMatrix()

    def _updateListShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self.needUpdate=0
        GL.glNewList(self._listID,GL.GL_COMPILE)
        #setup the shaderprogram
        GL.glUseProgram(self.win._progSignedTexMask)
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "texture"), 0) #set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "mask"), 1)  # mask is texture unit 1
        #mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)#implicitly disables 1D

        #main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        #calculate coords in advance:
        L = -self._sizeRendered[0]/2#vertices
        R =  self._sizeRendered[0]/2
        T =  self._sizeRendered[1]/2
        B = -self._sizeRendered[1]/2
        #depth = self.depth
        Ltex = -self._cycles[0]/2 - self.phase[0]+0.5
        Rtex = +self._cycles[0]/2 - self.phase[0]+0.5
        Ttex = +self._cycles[1]/2 - self.phase[1]+0.5
        Btex = -self._cycles[1]/2 - self.phase[1]+0.5
        Lmask=Bmask= 0.0; Tmask=Rmask=1.0#mask

        GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Rtex, Btex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,Rmask,Bmask)
        GL.glVertex2f(R,B)
        # left bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Ltex,Btex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,Lmask,Bmask)
        GL.glVertex2f(L,B)
        # left top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Ltex,Ttex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,Lmask,Tmask)
        GL.glVertex2f(L,T)
        # right top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Rtex,Ttex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,Rmask,Tmask)
        GL.glVertex2f(R,T)
        GL.glEnd()

        #unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)#implicitly disables 1D
        #main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glUseProgram(0)

        GL.glEndList()

    #for the sake of older graphics cards------------------------------------
    def _updateListNoShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self.needUpdate=0

        GL.glNewList(self._listID,GL.GL_COMPILE)
        GL.glColor4f(1.0,1.0,1.0,1.0)#glColor can interfere with multitextures
        #mask
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)#implicitly disables 1D
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.maskID)

        #main texture
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)
        #calculate coords in advance:
        L = -self._sizeRendered[0]/2#vertices
        R =  self._sizeRendered[0]/2
        T =  self._sizeRendered[1]/2
        B = -self._sizeRendered[1]/2
        #depth = self.depth
        Ltex = -self._cycles[0]/2 - self.phase[0]+0.5
        Rtex = +self._cycles[0]/2 - self.phase[0]+0.5
        Ttex = +self._cycles[1]/2 - self.phase[1]+0.5
        Btex = -self._cycles[1]/2 - self.phase[1]+0.5
        Lmask=Bmask= 0.0; Tmask=Rmask=1.0#mask

        GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Rtex, Btex)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,Rmask,Bmask)
        GL.glVertex2f(R,B)
        # left bottom
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Ltex,Btex)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,Lmask,Bmask)
        GL.glVertex2f(L,B)
        # left top
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Ltex,Ttex)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,Lmask,Tmask)
        GL.glVertex2f(L,T)
        # right top
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Rtex,Ttex)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,Rmask,Tmask)
        GL.glVertex2f(R,T)
        GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEndList()


    def __del__(self):
        self.clearTextures()#remove textures from graphics card to prevent crash

    def clearTextures(self):
        """
        Clear the textures associated with the given stimulus.
        As of v1.61.00 this is called automatically during garbage collection of
        your stimulus, so doesn't need calling explicitly by the user.
        """
        GL.glDeleteTextures(1, self.texID)
        GL.glDeleteTextures(1, self.maskID)

    def _calcCyclesPerStim(self):
        if self.units in ['norm', 'height']: self._cycles=self.sf#this is the only form of sf that is not size dependent
        else: self._cycles=self.sf*self.size


class PatchStim(GratingStim):
    def __init__(self, *args, **kwargs):
        """
        Deprecated (as of version 1.74.00): please use the :class:`~psychopy.visual.GratingStim` or the :class:`~psychopy.visual.ImageStim` classes.

        The GratingStim has identical abilities to the PatchStim (but possibly different initial values)
        whereas the ImageStim is designed to be use for non-cyclic images (photographs, not gratings).
        """
        GratingStim.__init__(self, *args, **kwargs)
        self.setImage = self.setTex

class RadialStim(GratingStim):
    """Stimulus object for drawing radial stimuli, like an annulus, a rotating wedge,
    a checkerboard etc...

    Ideal for fMRI retinotopy stimuli!

    Many of the capabilities are built on top of the GratingStim.

    This stimulus is still relatively new and I'm finding occasional gliches. it also takes longer to draw
    than a typical GratingStim, so not recommended for tasks where high frame rates are needed.
    """
    def __init__(self,
                 win,
                 tex     ="sqrXsqr",
                 mask    ="none",
                 units   ="",
                 pos     =(0.0,0.0),
                 size    =(1.0,1.0),
                 radialCycles=3,
                 angularCycles=4,
                 radialPhase=0,
                 angularPhase=0,
                 ori     =0.0,
                 texRes =64,
                 angularRes=100,
                 visibleWedge=(0, 360),
                 rgb   =None,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 dkl=None,
                 lms=None,
                 contrast=1.0,
                 opacity=1.0,
                 depth=0,
                 rgbPedestal = (0.0,0.0,0.0),
                 interpolate=False,
                 name='', autoLog=True):
        """
        :Parameters:

            win :
                a :class:`~psychopy.visual.Window` object (required)
            tex :
                The texture forming the image

                - 'sqrXsqr', 'sinXsin', 'sin','sqr',None
                - or the name of an image file (most formats supported)
                - or a numpy array (1xN, NxNx1, NxNx3) ranging -1:1

            mask : **none** or 'gauss'
                Unlike the mask in the GratingStim, this is a 1-D mask dictating the behaviour
                from the centre of the stimulus to the surround.
            units : **None**, 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window` will be used.
                See :ref:`units` for explanation of other options.
            pos :
                a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y of the centre of the stimulus.
                Stimuli can be position beyond the window!
            size :
                a tuple (0.5,0.5) or a list [0.5,0.5] for the x and y
                OR a single value (which will be applied to x and y).
                Sizes can be negative and stimuli can extend beyond the window.
            ori :
                orientation of stimulus in degrees.
            texRes : (default= *128* )
                resolution of the texture (if not loading from an image file)
            angularRes : (default= *100* )
                100, the number of triangles used to make the sti
            radialPhase :
                the phase of the texture from the centre to the perimeter
                of the stimulus (in radians)
            angularPhase :
                the phase of the texture around the stimulus (in radians)

            color:

                Could be a:

                    - web name for a color (e.g. 'FireBrick');
                    - hex value (e.g. '#FF0047');
                    - tuple (1.0,1.0,1.0); list [1.0,1.0, 1.0]; or numpy array.

                If the last three are used then the color space should also be given
                See :ref:`colorspaces`

            colorSpace:
                the color space controlling the interpretation of the `color`
                See :ref:`colorspaces`
            contrast : float (default= *1.0* )
                How far the stimulus deviates from the middle grey.
                Contrast can vary -1:1 (this is a multiplier for the
                values given in the color description of the stimulus)
            opacity : float (default=*1.0*)
                Between 0.0 and 1.0. 1.0 is opaque, 0.0 is transparent
            depth:
                The depth argument is deprecated and may be removed in future versions.
                Depth is controlled simply by drawing order.
            name : string
                The name of the object to be using during logged messages about
                this stim
        """
        _BaseVisualStim.__init__(self, win, units=units, name=name, autoLog=autoLog)

        if win._haveShaders: self._useShaders=True#by default, this is a good thing
        else: self._useShaders=False

        self.ori = float(ori)
        self.texRes = texRes #must be power of 2
        self.angularRes = angularRes
        self.radialPhase = radialPhase
        self.radialCycles = radialCycles
        self.maskRadialPhase = 0
        self.visibleWedge = visibleWedge
        self.angularCycles = angularCycles
        self.angularPhase = angularPhase
        self.contrast = float(contrast)
        self.opacity = float(opacity)
        self.pos = numpy.array(pos, float)
        self.interpolate=interpolate

        #these are defined by the GratingStim but will just cause confusion here!
        self.setSF = None
        self.setPhase = None
        self.setSF = None

        self.colorSpace=colorSpace
        if rgb!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb')
        elif dkl!=None:
            logging.warning("Use of dkl arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(dkl, colorSpace='dkl')
        elif lms!=None:
            logging.warning("Use of lms arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(lms, colorSpace='lms')
        else:
            self.setColor(color)

        if type(rgbPedestal)==float or type(rgbPedestal)==int: #user may give a luminance val
            self.rgbPedestal=numpy.array((rgbPedestal,rgbPedestal,rgbPedestal), float)
        else:
            self.rgbPedestal = numpy.asarray(rgbPedestal, float)

        self.depth=depth
        #size
        if type(size) in [tuple,list]:
            self.size = numpy.array(size,float)
        else:
            self.size = numpy.array((size,size),float)#make a square if only given one dimension
        #initialise textures for stimulus
        self.texID=GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self.texID))
        self.maskID=GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self.maskID))
        self.setTex(tex, log=False)
        self.setMask(mask, log=False)

        #
        self._triangleWidth = pi*2/self.angularRes
        self._angles = numpy.arange(0,pi*2, self._triangleWidth, dtype='float64')
        #which vertices are visible?
        self._visible = (self._angles>=(self.visibleWedge[0]*pi/180))#first edge of wedge
        self._visible[(self._angles+self._triangleWidth)*180/pi>(self.visibleWedge[1])] = False#second edge of wedge
        self._nVisible = numpy.sum(self._visible)*3

        #do the scaling to the window coordinate system
        self._calcPosRendered()
        self._calcSizeRendered()#must be done BEFORE _updateXY

        self._updateTextureCoords()
        self._updateMaskCoords()
        self._updateXY()
        if not self._useShaders:
            #generate a displaylist ID
            self._listID = GL.glGenLists(1)
            self._updateList()#ie refresh display list

    def setSize(self, value, operation='', log=True):
        self._set('size', value, operation, log=log)
        self._calcSizeRendered()
        self._updateXY()
        self.needUpdate=True
    def setAngularCycles(self,value,operation='', log=True):
        """set the number of cycles going around the stimulus"""
        self._set('angularCycles', value, operation, log=log)
        self._updateTextureCoords()
        self.needUpdate=True
    def setRadialCycles(self,value,operation='', log=True):
        """set the number of texture cycles from centre to periphery"""
        self._set('radialCycles', value, operation, log=log)
        self._updateTextureCoords()
        self.needUpdate=True
    def setAngularPhase(self,value, operation='', log=True):
        """set the angular phase of the texture (radians)"""
        self._set('angularPhase', value, operation, log=log)
        self._updateTextureCoords()
        self.needUpdate=True
    def setRadialPhase(self,value, operation='', log=True):
        """set the radial phase of the texture (radians)"""
        self._set('radialPhase', value, operation, log=log)
        self._updateTextureCoords()
        self.needUpdate=True

    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.

        If win is specified then override the normal window of this stimulus.
        """
        #set the window to draw to
        if win==None: win=self.win
        if win.winType=='pyglet': win.winHandle.switch_to()

        #do scaling
        GL.glPushMatrix()#push before the list, pop after
        #scale the viewport to the appropriate size
        self.win.setScale(self._winScale)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],0)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)

        if self._useShaders:
            #setup color
            desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
            GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)

            #assign vertex array
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self._visibleXY.ctypes)

            #then bind main texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)
            GL.glEnable(GL.GL_TEXTURE_2D)
            #and mask
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glBindTexture(GL.GL_TEXTURE_1D, self.maskID)
            GL.glDisable(GL.GL_TEXTURE_2D)
            GL.glEnable(GL.GL_TEXTURE_1D)

            #setup the shaderprogram
            GL.glUseProgram(self.win._progSignedTexMask1D)
            GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask1D, "texture"), 0) #set the texture to be texture unit 0
            GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask1D, "mask"), 1)  # mask is texture unit 1

            #set pointers to visible textures
            GL.glClientActiveTexture(GL.GL_TEXTURE0)
            GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, self._visibleTexture.ctypes)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

            #mask
            GL.glClientActiveTexture(GL.GL_TEXTURE1)
            GL.glTexCoordPointer(1, GL.GL_DOUBLE, 0, self._visibleMask.ctypes)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

            #do the drawing
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible)

            #unbind the textures
            GL.glClientActiveTexture(GL.GL_TEXTURE1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            #main texture
            GL.glClientActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glDisable(GL.GL_TEXTURE_2D)
            #disable set states
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

            GL.glUseProgram(0)
        else:
            #the list does the texture mapping
            if self.needUpdate: self._updateList()
            GL.glCallList(self._listID)

        #return the view to previous state
        GL.glPopMatrix()

    def _updateXY(self):
        """Update if the SIZE changes
        Update AFTER _calcSizeRendered"""
        #triangles = [trisX100, verticesX3, xyX2]
        self._XY = numpy.zeros([self.angularRes, 3, 2])
        self._XY[:,1,0] = numpy.sin(self._angles)*self._sizeRendered[0]/2 #x position of 1st outer vertex
        self._XY[:,1,1] = numpy.cos(self._angles)*self._sizeRendered[1]/2#y position of 1st outer vertex
        self._XY[:,2,0] = numpy.sin(self._angles+self._triangleWidth)*self._sizeRendered[0]/2#x position of 2nd outer vertex
        self._XY[:,2,1] = numpy.cos(self._angles+self._triangleWidth)*self._sizeRendered[1]/2#y position of 2nd outer vertex

        self._visibleXY = self._XY[self._visible,:,:]
        self._visibleXY = self._visibleXY.reshape(self._nVisible,2)

    def _updateTextureCoords(self):
        #calculate texture coordinates if angularCycles or Phase change
        self._textureCoords = numpy.zeros([self.angularRes, 3, 2])
        self._textureCoords[:,0,0] = (self._angles+self._triangleWidth/2)*self.angularCycles/(2*pi)+self.angularPhase #x position of inner vertex
        self._textureCoords[:,0,1] = 0.25+-self.radialPhase #y position of inner vertex
        self._textureCoords[:,1,0] = (self._angles)*self.angularCycles/(2*pi)+self.angularPhase #x position of 1st outer vertex
        self._textureCoords[:,1,1] = 0.25+self.radialCycles-self.radialPhase#y position of 1st outer vertex
        self._textureCoords[:,2,0] = (self._angles+self._triangleWidth)*self.angularCycles/(2*pi)+self.angularPhase#x position of 2nd outer vertex
        self._textureCoords[:,2,1] = 0.25+self.radialCycles-self.radialPhase#y position of 2nd outer vertex
        self._visibleTexture = self._textureCoords[self._visible,:,:].reshape(self._nVisible,2)

    def _updateMaskCoords(self):
        #calculate mask coords
        self._maskCoords = numpy.zeros([self.angularRes,3]) + self.maskRadialPhase
        self._maskCoords[:,1:] = 1 + self.maskRadialPhase#all outer points have mask value of 1
        self._visibleMask = self._maskCoords[self._visible,:]

    def _updateListShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self.needUpdate=0
        GL.glNewList(self._listID,GL.GL_COMPILE)

        #assign vertex array
        arrPointer = self._visibleXY.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, arrPointer)

        #setup the shaderprogram
        GL.glUseProgram(self.win._progSignedTexMask1D)
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask1D, "texture"), 0) #set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask1D, "mask"), 1)  # mask is texture unit 1

        #set pointers to visible textures
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        arrPointer = self._visibleTexture.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, arrPointer)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        #then bind main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        #mask
        GL.glClientActiveTexture(GL.GL_TEXTURE1)
        arrPointer = self._visibleMask.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        GL.glTexCoordPointer(1, GL.GL_FLOAT, 0, arrPointer)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        #and mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_1D, self.maskID)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_TEXTURE_1D)

        #do the drawing
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible*3)
        #disable set states
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glUseProgram(0)
        #setup the shaderprogram
        GL.glEndList()

    def _updateListNoShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self.needUpdate=0
        GL.glNewList(self._listID,GL.GL_COMPILE)
        GL.glColor4f(1.0,1.0,1.0,self.opacity)#glColor can interfere with multitextures

        #assign vertex array
        GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self._visibleXY.ctypes)
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)

        #bind and enable textures
        #main texture
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        #mask
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glBindTexture(GL.GL_TEXTURE_1D, self.maskID)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_TEXTURE_1D)

        #set pointers to visible textures
        #mask
        GL.glClientActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, self._visibleMask.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        #texture
        GL.glClientActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0,self._visibleTexture.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        #do the drawing
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible)

        #disable set states
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glEndList()

    def setTex(self,value, log=True):
        """Update the texture of the stimulus"""
        self._texName = value
        createTexture(value, id=self.texID, pixFormat=GL.GL_RGB, stim=self, res=self.texRes)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s tex=%s" %(self.name, value),
                level=logging.EXP,obj=self)
    def setMask(self,value, log=True):
        """Change the alpha-mask for the stimulus
        """
        self._maskName = value
        res = self.texRes#resolution of texture - 128 is bearable
        step = 1.0/res
        rad = numpy.arange(0,1+step,step)
        if type(self._maskName) == numpy.ndarray:
            #handle a numpy array
            intensity = 255*self._maskName.astype(float)
            res = len(intensity)
            fromFile=0
        elif type(self._maskName) == list:
            #handle a numpy array
            intensity = 255*numpy.array(self._maskName, float)
            res = len(intensity)
            fromFile=0
        elif self._maskName == "circle":
            intensity = 255.0*(rad<=1)
            fromFile=0
        elif self._maskName == "gauss":
            sigma = 1/3.0;
            intensity = 255.0*numpy.exp( -rad**2.0 / (2.0*sigma**2.0) )#3sd.s by the edge of the stimulus
            fromFile=0
        elif self._maskName == "radRamp":#a radial ramp
            intensity = 255.0-255.0*rad
            intensity = numpy.where(rad<1, intensity, 0)#half wave rectify
            fromFile=0
        elif self._maskName in [None,"none","None"]:
            res=4
            intensity = 255.0*numpy.ones(res,float)
            fromFile=0
        else:#might be a filename of a tiff
            try:
                im = Image.open(self._maskName)
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                im = im.resize([max(im.size), max(im.size)],Image.BILINEAR)#make it square
            except IOError, (details):
                logging.error("couldn't load mask...%s: %s" %(value,details))
                return
            res = im.size[0]
            im = im.convert("L")#force to intensity (in case it was rgb)
            intensity = numpy.asarray(im)

        data = intensity.astype(numpy.uint8)
        mask = data.tostring()#serialise

        #do the openGL binding
        if self.interpolate: smoothing=GL.GL_LINEAR
        else: smoothing=GL.GL_NEAREST
        GL.glBindTexture(GL.GL_TEXTURE_1D, self.maskID)
        GL.glTexImage1D(GL.GL_TEXTURE_1D, 0, GL.GL_ALPHA,
                        res, 0,
                        GL.GL_ALPHA, GL.GL_UNSIGNED_BYTE, mask)
        GL.glTexParameteri(GL.GL_TEXTURE_1D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT) #makes the texture map wrap (this is actually default anyway)
        GL.glTexParameteri(GL.GL_TEXTURE_1D,GL.GL_TEXTURE_MAG_FILTER,smoothing)     #linear smoothing if texture is stretched
        GL.glTexParameteri(GL.GL_TEXTURE_1D,GL.GL_TEXTURE_MIN_FILTER,smoothing)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
        GL.glEnable(GL.GL_TEXTURE_1D)

        self.needUpdate=True

        if log and self.autoLog:
            self.win.logOnFlip("Set %s mask=%s" %(self.name, value),
                level=logging.EXP,obj=self)

    def __del__(self):
        self.clearTextures()#remove textures from graphics card to prevent crash

    def clearTextures(self):
        """
        Clear the textures associated with the given stimulus.
        As of v1.61.00 this is called automatically during garbage collection of
        your stimulus, so doesn't need calling explicitly by the user.
        """
        GL.glDeleteTextures(1, self.texID)
        GL.glDeleteTextures(1, self.maskID)

class ElementArrayStim:
    """
    This stimulus class defines a field of elements whose behaviour can be independently
    controlled. Suitable for creating 'global form' stimuli or more detailed random dot
    stimuli.
    This stimulus can draw thousands of elements without dropping a frame, but in order
    to achieve this performance, uses several OpenGL extensions only available on modern
    graphics cards (supporting OpenGL2.0). See the ElementArray demo.
    """
    def __init__(self,
                 win,
                 units = None,
                 fieldPos = (0.0,0.0),
                 fieldSize = (1.0,1.0),
                 fieldShape = 'circle',
                 nElements = 100,
                 sizes = 2.0,
                 xys = None,
                 rgbs = None,
                 colors=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 opacities = 1.0,
                 depths = 0,
                 fieldDepth = 0,
                 oris = 0,
                 sfs=1.0,
                 contrs = 1,
                 phases=0,
                 elementTex='sin',
                 elementMask='gauss',
                 texRes=48,
                 interpolate=True,
                 name='', autoLog=True):

        """
        :Parameters:

            win :
                a :class:`~psychopy.visual.Window` object (required)

            units : **None**, 'height', 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window`
                will be used. See :ref:`units` for explanation of other options.

            fieldPos :
                The centre of the array of elements

            fieldSize :
                The size of the array of elements (this will be overridden by
                setting explicit xy positions for the elements)

            fieldShape :
                The shape of the array ('circle' or 'sqr')

            nElements :
                number of elements in the array

            sizes :
                an array of sizes Nx1, Nx2 or a single value

            xys :
                the xy positions of the elements, relative to the field centre
                (fieldPos)

            colors :
                specifying the color(s) of the elements.
                Should be Nx1 (different intensities), Nx3 (different colors) or 1x3
                (for a single color).

            colorSpace :
                The type of color specified is the same as
                those in other stimuli ('rgb','dkl','lms'...) but note that for
                this stimulus you cannot currently use text-based colors (e.g. names
                or hex values)

            opacities :
                the opacity of each element (Nx1 or a single value)

            depths :
                the depths of the elements (Nx1), relative the overall depth
                of the field (fieldDepth)

            fieldDepth :
                the depth of the field (will be added to the depths of the
                elements)

            oris :
                the orientations of the elements (Nx1 or a single value)

            sfs :
                the spatial frequencies of the elements (Nx1, Nx2 or a single
                value)

            contrs :
                the contrasts of the elements, ranging -1 to +1 (Nx1 or a
                single value)

            phases :
                the spatial phase of the texture on the stimulus (Nx1 or a
                single value)

            elementTex :
                the texture, to be used by all elements (e.g. 'sin', 'sqr',.. ,
                'myTexture.tif', numpy.ones([48,48]))

            elementMask :
                the mask, to be used by all elements (e.g. 'circle', 'gauss',... ,
                'myTexture.tif', numpy.ones([48,48]))

            texRes :
                the number of pixels in the textures (overridden if an array
                or image is provided)

            name : string
                The name of the objec to be using during logged messages about
                this stim

        """
        self.win=win
        self.name=name
        self.autoLog=autoLog

        #unit conversions
        if units!=None and len(units): self.units = units
        else: self.units = win.units
        if self.units in ['norm','height']: self._winScale=self.units
        else: self._winScale='pix' #set the window to have pixels coords
        self.fieldPos = fieldPos
        self.fieldSize = fieldSize
        self.fieldShape = fieldShape
        self.nElements = nElements
        #info for each element
        self.sizes = sizes
        self.xys= xys
        self.opacities = opacities
        self.oris = oris
        self.contrs = contrs
        self.phases = phases
        self.needVertexUpdate=True
        self.needColorUpdate=True
        self._useShaders=True
        self.interpolate=interpolate
        self.fieldDepth=fieldDepth
        self.depths=depths
        if self.win.winType != 'pyglet':
            raise TypeError('ElementArrayStim requires a pyglet context')
        if not self.win._haveShaders:
            raise Exception("ElementArrayStim requires shaders support and floating point textures")

        self.colorSpace=colorSpace
        if rgbs!=None:
            logging.warning("Use of the rgb argument to ElementArrayStim is deprecated. Please use colors and colorSpace args instead")
            self.setColors(rgbs, colorSpace='rgb', log=False)
        else:
            self.setColors(colors, colorSpace=colorSpace, log=False)

        #Deal with input for fieldpos
        if type(fieldPos) in [tuple,list]:
            self.fieldPos = numpy.array(fieldPos,float)
        else:
            self.fieldPos = numpy.array((fieldPos,fieldPos),float)

        #Deal with input for fieldsize
        if type(fieldSize) in [tuple,list]:
            self.fieldSize = numpy.array(fieldSize,float)
        else:
            self.fieldSize = numpy.array((fieldSize,fieldSize),float)#make a square if only given one dimension

        #create textures
        self.texRes=texRes
        self.texID=GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self.texID))
        self.maskID=GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self.maskID))
        self.setMask(elementMask, log=False)
        self.setTex(elementTex, log=False)

        self.setContrs(contrs, log=False)
        self.setOpacities(opacities, log=False)#opacities is used by setRgbs, so this needs to be early
        self.setXYs(xys, log=False)
        self.setOris(oris, log=False)
        self.setSizes(sizes, log=False) #set sizes before sfs (sfs may need it formatted)
        self.setSfs(sfs, log=False)
        self.setPhases(phases, log=False)

        self._calcFieldCoordsRendered()
        self._calcSizesRendered()
        self._calcXYsRendered()


    def setXYs(self,value=None, operation='', log=True):
        """Set the xy values of the element centres (relative to the centre of the field).
        Values should be:

            - None
            - an array/list of Nx2 coordinates.

        If value is None then the xy positions will be generated automatically, based
        on the fieldSize and fieldPos. In this case opacity will also be overridden
        by this function (it is used to make elements outside the field invisible.
        """
        if value==None:
            if self.fieldShape in ['sqr', 'square']:
                self.xys = numpy.random.rand(self.nElements,2)*self.fieldSize - self.fieldSize/2 #initialise a random array of X,Y
                #gone outside the square
                self.xys[:,0] = ((self.xys[:,0]+self.fieldSize[0]/2) % self.fieldSize[0])-self.fieldSize[0]/2
                self.xys[:,1] = ((self.xys[:,1]+self.fieldSize[1]/2) % self.fieldSize[1])-self.fieldSize[1]/2
            elif self.fieldShape is 'circle':
                #take twice as many elements as we need (and cull the ones outside the circle)
                xys = numpy.random.rand(self.nElements*2,2)*self.fieldSize - self.fieldSize/2 #initialise a random array of X,Y
                #gone outside the square
                xys[:,0] = ((xys[:,0]+self.fieldSize[0]/2) % self.fieldSize[0])-self.fieldSize[0]/2
                xys[:,1] = ((xys[:,1]+self.fieldSize[1]/2) % self.fieldSize[1])-self.fieldSize[1]/2
                #use a circular envelope and flips dot to opposite edge if they fall
                #beyond radius.
                #NB always circular - uses fieldSize in X only
                normxy = xys/(self.fieldSize/2.0)
                dotDist = numpy.sqrt((normxy[:,0]**2.0 + normxy[:,1]**2.0))
                self.xys = xys[dotDist<1.0,:][0:self.nElements]
        else:
            #make into an array
            if type(value) in [int, float, list, tuple]:
                value = numpy.array(value, dtype=float)
            #check shape
            if not (value.shape in [(),(2,),(self.nElements,2)]):
                raise ValueError("New value for setXYs should be either None or Nx2")
            if operation=='':
                self.xys=value
            else: exec('self.xys'+operation+'=value')
        self.needVertexUpdate=True
        if log and self.autoLog:
            self.win.logOnFlip("Set %s XYs=%s" %(self.name, type(value)),
                level=logging.EXP,obj=self)
    def setOris(self,value,operation='', log=True):
        """Set the orientation for each element.
        Should either be a single value or an Nx1 array/list
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)

        #check shape
        if value.shape in [(),(1,)]:
            value = value.repeat(self.nElements)
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            pass #is already Nx1
        else:
            raise ValueError("New value for setOris should be either Nx1 or a single value")
        if operation=='':
            self.oris=value
        else: exec('self.oris'+operation+'=value')
        self.needVertexUpdate=True
        if log and self.autoLog:
            self.win.logOnFlip("Set %s oris=%s" %(self.name, type(value)),
                level=logging.EXP,obj=self)
    #----------------------------------------------------------------------
    def setSfs(self, value,operation='', log=True):
        """Set the spatial frequency for each element.
        Should either be:

          - a single value
          - an Nx1 array/list
          - an Nx2 array/list (spatial frequency of the element in X and Y).

        If the units for the stimulus are 'pix' or 'norm' then the units of sf
        are cycles per stimulus width. For units of 'deg' or 'cm' the units
        are c/cm or c/deg respectively.

        """

        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)

        #check shape
        if value.shape in [(),(1,),(2,)]:
            value = numpy.resize(value, [self.nElements,2])
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            value.shape=(self.nElements,1)#set to be 2D
            value = value.repeat(2,1) #repeat once on dim 1
        elif value.shape == (self.nElements,2):
            pass#all is good
        else:
            raise ValueError("New value for setSfs should be either Nx1, Nx2 or a single value")

        if operation=='':
            self.sfs=value
        else: exec('self.sfs'+operation+'=value')
        if log and self.autoLog:
            self.win.logOnFlip("Set %s sfs=%s" %(self.name, type(value)),
                level=logging.EXP,obj=self)

    def setOpacities(self,value,operation='', log=True):
        """Set the opacity for each element.
        Should either be a single value or an Nx1 array/list
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)

        #check shape
        if value.shape in [(),(1,)]:
            value = value.repeat(self.nElements)
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            pass #is already Nx1
        else:
            raise ValueError("New value for setOpacities should be either Nx1 or a single value")

        if operation=='':
            self.opacities=value
        else: exec('self.opacities'+operation+'=value')
        self.needColorUpdate =True

        if log and self.autoLog:
            self.win.logOnFlip("Set %s opacities=%s" %(self.name, type(value)),
                level=logging.EXP,obj=self)
    def setSizes(self,value,operation='', log=True):
        """Set the size for each element.
        Should either be:

          - a single value
          - an Nx1 array/list
          - an Nx2 array/list
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if value.shape in [(),(1,),(2,)]:
            value = numpy.resize(value, [self.nElements,2])
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            value.shape=(self.nElements,1)#set to be 2D
            value = value.repeat(2,1) #repeat once on dim 1
        elif value.shape == (self.nElements,2):
            pass#all is good
        else:
            raise ValueError("New value for setSizes should be either Nx1, Nx2 or a single value")

        if operation=='':
            self.sizes=value
        else: exec('self.sizes'+operation+'=value')
        self._calcSizesRendered()
        self.needVertexUpdate=True
        self.needTexCoordUpdate=True

        if log and self.autoLog:
            self.win.logOnFlip("Set %s sizes=%s" %(self.name, type(value)),
                level=logging.EXP,obj=self)
    def setPhases(self,value,operation='', log=True):
        """Set the phase for each element.
        Should either be:

          - a single value
          - an Nx1 array/list
          - an Nx2 array/list (for separate X and Y phase)
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)

        #check shape
        if value.shape in [(),(1,),(2,)]:
            value = numpy.resize(value, [self.nElements,2])
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            value.shape=(self.nElements,1)#set to be 2D
            value = value.repeat(2,1) #repeat once on dim 1
        elif value.shape == (self.nElements,2):
            pass#all is good
        else:
            raise ValueError("New value for setPhases should be either Nx1, Nx2 or a single value")

        if operation=='':
            self.phases=value
        else: exec('self.phases'+operation+'=value')
        self.needTexCoordUpdate=True

        if log and self.autoLog:
            self.win.logOnFlip("Set %s phases=%s" %(self.name, type(value)),
                level=logging.EXP,obj=self)
    def setRgbs(self,value,operation='', log=True):
        """DEPRECATED (as of v1.74.00). Please use setColors() instead
        """
        self.setColors(value,operation, log=log)
    def setColors(self, color, colorSpace=None, operation='', log=True):
        """Set the color of the stimulus. See :ref:`colorspaces` for further information
        about the various ways to specify colors and their various implications.

        :Parameters:

        color :
            Can be specified in one of many ways.

            You must provide a triplet of values, which refer to the coordinates
            in one of the :ref:`colorspaces`. If no color space is specified then the color
            space most recently used for this stimulus is used again.

                myStim.setColor([1.0,-1.0,-1.0], 'rgb')#a red color in rgb space
                myStim.setColor([0.0,45.0,1.0], 'dkl') #DKL space with elev=0, azimuth=45
                myStim.setColor([0,0,255], 'rgb255') #a blue stimulus using rgb255 space

            Lastly, a single number can be provided, x, which is equivalent to providing
            [x,x,x].

                myStim.setColor(255, 'rgb255') #all guns o max

        colorSpace : string or None

            defining which of the :ref:`colorspaces` to use. For strings and hex
            values this is not needed. If None the default colorSpace for the stimulus is
            used (defined during initialisation).

        operation : one of '+','-','*','/', or '' for no operation (simply replace value)

            for colors specified as a triplet of values (or single intensity value)
            the new value will perform this operation on the previous color

                thisStim.setColor([1,1,1],'rgb255','+')#increment all guns by 1 value
                thisStim.setColor(-1, 'rgb', '*') #multiply the color by -1 (which in this space inverts the contrast)
                thisStim.setColor([10,0,0], 'dkl', '+')#raise the elevation from the isoluminant plane by 10 deg
        """
        _setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='rgbs', #or 'fillRGB' etc
                    colorAttrib='colors',
                    colorSpaceAttrib='colorSpace',log=log)
        #check shape
        if self.rgbs.shape in [(), (1,),(3,)]:
            self.rgbs = numpy.resize(self.rgbs, [self.nElements,3])
        elif self.rgbs.shape in [(self.nElements,), (self.nElements,1)]:
            self.rgbs.shape=(self.nElements,1)#set to be 2D
            self.rgbs = self.rgbs.repeat(3,1) #repeat once on dim 1
        elif self.rgbs.shape == (self.nElements,3):
            pass#all is good
        else:
            raise ValueError("New value for setRgbs should be either Nx1, Nx3 or a single value")
        self.needColorUpdate=True
    def setContrs(self,value,operation='', log=True):
        """Set the contrast for each element.
        Should either be:

          - a single value
          - an Nx1 array/list
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if value.shape in [(),(1,)]:
            value = value.repeat(self.nElements)
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            pass #is already Nx1
        else:
            raise ValueError("New value for setContrs should be either Nx1 or a single value")

        if operation=='':
            self.contrs=value
        else: exec('self.contrs'+operation+'=value')
        self.needColorUpdate=True
        if log and self.autoLog:
            self.win.logOnFlip("Set %s contrs=%s" %(self.name, type(value)),
                level=logging.EXP,obj=self)
    def setFieldPos(self,value,operation='', log=True):
        """Set the centre of the array (X,Y)
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if value.shape != (2,):
            raise ValueError("New value for setFieldPos should be [x,y]")

        if operation=='':
            self.fieldPos=value
        else:
            exec('self.fieldPos'+operation+'=value')
        self._calcFieldCoordsRendered()
        if log and self.autoLog:
            self.win.logOnFlip("Set %s fieldPos=%s" %(self.name, type(value)),
                level=logging.EXP,obj=self)
    def setPos(self, newPos=None, operation='', units=None, log=True):
        """Obselete - users should use setFieldPos or instead of setPos
        """
        logging.error("User called ElementArrayStim.setPos(pos). Use ElementArrayStim.SetFieldPos(pos) instead.")

    def setFieldSize(self,value,operation='', log=True):
        """Set the size of the array on the screen (will override
        current XY positions of the elements)
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if value.shape not in [(2,),(1,)]:
            raise ValueError("New value for setFieldSize should be [x,y] or a single value")

        if operation=='':
            self.fieldSize=value
        else:
            exec('self.fieldSize'+operation+'=value')
        self.setXYs(log=False)#to reflect new settings, overriding individual xys

        if log and self.autoLog:
            self.win.logOnFlip("Set %s fieldSize=%s" %(self.name,value),
                level=logging.EXP,obj=self)
    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.update() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        #set the window to draw to
        if win==None: win=self.win
        if win.winType=='pyglet': win.winHandle.switch_to()

        if self.needVertexUpdate:
            self.updateElementVertices()
        if self.needColorUpdate:
            self.updateElementColors()
        if self.needTexCoordUpdate:
            self.updateTextureCoords()

        #scale the drawing frame and get to centre of field
        GL.glPushMatrix()#push before drawing, pop after
        GL.glPushClientAttrib(GL.GL_CLIENT_ALL_ATTRIB_BITS)#push the data for client attributes

        #GL.glLoadIdentity()
        self.win.setScale(self._winScale)

        GL.glTranslatef(self._fieldPosRendered[0],self._fieldPosRendered[1],0)

        GL.glColorPointer(4, GL.GL_DOUBLE, 0, self._RGBAs.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
        GL.glVertexPointer(3, GL.GL_DOUBLE, 0, self._visXYZvertices.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))

        #setup the shaderprogram
        GL.glUseProgram(self.win._progSignedTexMask)
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "texture"), 0) #set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "mask"), 1)  # mask is texture unit 1

        #bind textures
        GL.glActiveTexture (GL.GL_TEXTURE1)
        GL.glBindTexture (GL.GL_TEXTURE_2D, self.maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture (GL.GL_TEXTURE0)
        GL.glBindTexture (GL.GL_TEXTURE_2D, self.texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        #setup client texture coordinates first
        GL.glClientActiveTexture (GL.GL_TEXTURE0)
        GL.glTexCoordPointer (2, GL.GL_DOUBLE, 0, self._texCoords.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glClientActiveTexture (GL.GL_TEXTURE1)
        GL.glTexCoordPointer (2, GL.GL_DOUBLE, 0, self._maskCoords.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDrawArrays(GL.GL_QUADS, 0, self._visXYZvertices.shape[0]*4)

        #unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        #main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        #disable states
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glUseProgram(0)
        GL.glPopClientAttrib()
        GL.glPopMatrix()

    def _calcSizesRendered(self):
        if self.units in ['norm','pix', 'height']: self._sizesRendered=self.sizes
        elif self.units in ['deg', 'degs']: self._sizesRendered=psychopy.misc.deg2pix(self.sizes, self.win.monitor)
        elif self.units=='cm': self._sizesRendered=psychopy.misc.cm2pix(self.sizes, self.win.monitor)
    def _calcXYsRendered(self):
        if self.units in ['norm','pix','height']: self._XYsRendered=self.xys
        elif self.units in ['deg', 'degs']: self._XYsRendered=psychopy.misc.deg2pix(self.xys, self.win.monitor)
        elif self.units=='cm': self._XYsRendered=psychopy.misc.cm2pix(self.xys, self.win.monitor)
    def _calcFieldCoordsRendered(self):
        if self.units in ['norm', 'pix','height']:
            self._fieldSizeRendered=self.fieldSize
            self._fieldPosRendered=self.fieldPos
        elif self.units in ['deg', 'degs']:
            self._fieldSizeRendered=psychopy.misc.deg2pix(self.fieldSize, self.win.monitor)
            self._fieldPosRendered=psychopy.misc.deg2pix(self.fieldPos, self.win.monitor)
        elif self.units=='cm':
            self._fieldSizeRendered=psychopy.misc.cm2pix(self.fieldSize, self.win.monitor)
            self._fieldPosRendered=psychopy.misc.cm2pix(self.fieldPos, self.win.monitor)

    def updateElementVertices(self):
        self._calcXYsRendered()

        self._visXYZvertices=numpy.zeros([self.nElements , 4, 3],'d')
        wx = self._sizesRendered[:,0]*numpy.cos(self.oris[:]*numpy.pi/180)/2
        wy = self._sizesRendered[:,0]*numpy.sin(self.oris[:]*numpy.pi/180)/2
        hx = self._sizesRendered[:,1]*numpy.sin(self.oris[:]*numpy.pi/180)/2
        hy = -self._sizesRendered[:,1]*numpy.cos(self.oris[:]*numpy.pi/180)/2

        #X
        self._visXYZvertices[:,0,0] = self._XYsRendered[:,0] -wx + hx#TopL
        self._visXYZvertices[:,1,0] = self._XYsRendered[:,0] +wx + hx#TopR
        self._visXYZvertices[:,2,0] = self._XYsRendered[:,0] +wx - hx#BotR
        self._visXYZvertices[:,3,0] = self._XYsRendered[:,0] -wx - hx#BotL

        #Y
        self._visXYZvertices[:,0,1] = self._XYsRendered[:,1] -wy + hy
        self._visXYZvertices[:,1,1] = self._XYsRendered[:,1] +wy + hy
        self._visXYZvertices[:,2,1] = self._XYsRendered[:,1] +wy - hy
        self._visXYZvertices[:,3,1] = self._XYsRendered[:,1] -wy - hy

        #depth
        self._visXYZvertices[:,:,2] = numpy.tile(self.depths,(1,4)) + self.fieldDepth

        self.needVertexUpdate=False

    #----------------------------------------------------------------------
    def updateElementColors(self):
        """Create a new array of self._RGBAs based on self.rgbs. Not needed by the
        user (simple call setColors())

        For element arrays the self.rgbs values correspond to one element so
        this function also converts them to be one for each vertex of each element
        """
        N=self.nElements
        self._RGBAs=numpy.zeros([N,4],'d')
        if self.colorSpace in ['rgb','dkl','lms','hsv']: #these spaces are 0-centred
            self._RGBAs[:,0:3] = self.rgbs[:,:] * self.contrs[:].reshape([N,1]).repeat(3,1)/2+0.5
        else:
            self._RGBAs[:,0:3] = self.rgbs * self.contrs[:].reshape([N,1]).repeat(3,1)/255.0
        self._RGBAs[:,-1] = self.opacities.reshape([N,])
        self._RGBAs=self._RGBAs.reshape([N,1,4]).repeat(4,1)#repeat for the 4 vertices in the grid

        self.needColorUpdate=False

    def updateTextureCoords(self):
        """Create a new array of self._maskCoords"""

        N=self.nElements
        self._maskCoords=numpy.array([[0,1],[1,1],[1,0],[0,0]],'d').reshape([1,4,2])
        self._maskCoords = self._maskCoords.repeat(N,0)

        #for the main texture
        if self.units in ['norm', 'pix', 'height']:#sf is dependent on size (openGL default)
            L = -self.sfs[:,0]/2 - self.phases[:,0]+0.5
            R = +self.sfs[:,0]/2 - self.phases[:,0]+0.5
            T = +self.sfs[:,1]/2 - self.phases[:,1]+0.5
            B = -self.sfs[:,1]/2 - self.phases[:,1]+0.5
        else: #we should scale to become independent of size
            L = -self.sfs[:,0]*self.sizes[:,0]/2 - self.phases[:,0]+0.5
            R = +self.sfs[:,0]*self.sizes[:,0]/2 - self.phases[:,0]+0.5
            T = +self.sfs[:,1]*self.sizes[:,1]/2 - self.phases[:,1]+0.5
            B = -self.sfs[:,1]*self.sizes[:,1]/2 - self.phases[:,1]+0.5

        #self._texCoords=numpy.array([[1,1],[1,0],[0,0],[0,1]],'d').reshape([1,4,2])
        self._texCoords=numpy.concatenate([[L,T],[R,T],[R,B],[L,B]]) \
            .transpose().reshape([N,4,2]).astype('d')
        self.needTexCoordUpdate=False

    def setTex(self,value, log=True):
        """Change the texture (all elements have the same base texture). Avoid this
        during time-critical points in your script. Uploading new textures to the
        graphics card can be time-consuming.
        """
        self._texName = value
        createTexture(value, id=self.texID, pixFormat=GL.GL_RGB, stim=self, res=self.texRes)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s tex=%s" %(self.name, value),
                level=logging.EXP,obj=self)
    def setMask(self,value, log=True):
        """Change the mask (all elements have the same mask). Avoid doing this
        during time-critical points in your script. Uploading new textures to the
        graphics card can be time-consuming."""
        self._maskName = value
        createTexture(value, id=self.maskID, pixFormat=GL.GL_ALPHA, stim=self, res=self.texRes)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s mask=%s" %(self.name, value),
                level=logging.EXP,obj=self)
    def __del__(self):
        self.clearTextures()#remove textures from graphics card to prevent crash
    def clearTextures(self):
        """
        Clear the textures associated with the given stimulus.
        As of v1.61.00 this is called automatically during garbage collection of
        your stimulus, so doesn't need calling explicitly by the user.
        """
        GL.glDeleteTextures(1, self.texID)
        GL.glDeleteTextures(1, self.maskID)

class MovieStim(_BaseVisualStim):
    """A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.

    **Example**::

        mov = visual.MovieStim(myWin, 'testMovie.mp4', flipVert=False)
        print mov.duration
        print mov.format.width, mov.format.height #give the original size of the movie in pixels

        mov.draw() #draw the current frame (automagically determined)

    See MovieStim.py for demo.
    """
    def __init__(self, win,
                 filename = "",
                 units   = 'pix',
                 size    = None,
                 pos      =(0.0,0.0),
                 ori     =0.0,
                 flipVert = False,
                 flipHoriz = False,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 opacity=1.0,
                 name='',
                 loop=False,
                 autoLog=True,
                 depth=0.0,):
        """
        :Parameters:

            win :
                a :class:`~psychopy.visual.Window` object (required)
            filename :
                a string giving the relative or absolute path to the movie. Can be any movie that
                AVbin can read (e.g. mpeg, DivX)
            units : **None**, 'height', 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window` will be used.
                See :ref:`units` for explanation of other options.
            pos :
                position of the centre of the movie, given in the units specified
            flipVert : True or *False*
                If True then the movie will be top-bottom flipped
            flipHoriz : True or *False*
                If True then the movie will be right-left flipped
            ori :
                Orientation of the stimulus in degrees
            size :
                Size of the stimulus in units given. If not specified then the movie will take its
                original dimensions.
            color:
                Modified the weight of the colors in the movie. E,g, color="red"
                will only display the red parts of the movie and make all other
                things black. white (color=(1,1,1)) is the original colors.
                
                Could be a:

                    - web name for a color (e.g. 'FireBrick');
                    - hex value (e.g. '#FF0047');
                    - tuple (1.0,1.0,1.0); list [1.0,1.0, 1.0]; or numpy array.

                If the last three are used then the color space should also be given
                See :ref:`colorspaces`

            colorSpace:
                the color space controlling the interpretation of the `color`
                See :ref:`colorspaces`
            opacity :
                the movie can be made transparent by reducing this
            name : string
                The name of the object to be using during logged messages about
                this stim
            loop : bool, optional
                Whether to start the movie over from the beginning if draw is
                called and the movie is done.

        """
        _BaseVisualStim.__init__(self, win, units=units, name=name, autoLog=autoLog)

        if not havePygletMedia:
            raise ImportError, """pyglet.media is needed for MovieStim and could not be imported.
                This can occur for various reasons;
                    - psychopy.visual was imported too late (after a lib that uses scipy)
                    - no audio output is enabled (no audio card or no speakers attached)
                    - avbin is not installed
            """
        self._movie=None # the actual pyglet media object
        self._player=pyglet.media.ManagedSoundPlayer()
        self._player._on_eos=self._onEos
        self.filename=filename
        self.duration=None
        self.loadMovie( self.filename )
        self.format=self._movie.video_format
        self.pos=pos
        self.pos = numpy.asarray(pos, float)
        self.depth=depth
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.colorSpace=colorSpace
        self.setColor(color, colorSpace=colorSpace, log=False)
        self.opacity = float(opacity)
        self.loop = loop
        self.status=NOT_STARTED

        #size
        if size == None: self.size= numpy.array([self.format.width,
                                                 self.format.height] , float)

        elif type(size) in [tuple,list]: self.size = numpy.array(size,float)
        else: self.size = numpy.array((size,size),float)

        self.ori = ori

        self._calcPosRendered()
        self._calcSizeRendered()

        #check for pyglet
        if win.winType!='pyglet':
            logging.Error('Movie stimuli can only be used with a pyglet window')
            core.quit()
    def setMovie(self, filename, log=True):
        """See `~MovieStim.loadMovie` (the functions are identical).
        This form is provided for syntactic consistency with other visual stimuli.
        """
        self.loadMovie(filename, log=log)

    def loadMovie(self, filename, log=True):
        """Load a movie from file

        :Parameters:

            filename: string
                The name of the file, including path if necessary

        Brings up a warning if avbin is not found on the computer.
        After the file is loaded MovieStim.duration is updated with the movie
        duration (in seconds).
        """
        try:
            self._movie = pyglet.media.load(filename, streaming=True)
        except Exception, e:
            # pyglet.media.riff is N/A if avbin is available, and then
            # actual exception would get masked with a new one for unknown
            # (sub)module riff, thus catching any exception and tuning msg
            # up if it has to do anything with avbin
            estr = str(e)
            msg = ''
            if "avbin" in estr.lower():
                msg = "\n         It seems that avbin was not installed correctly." \
                      "\n         Please fetch/install it from http://code.google.com/p/avbin/."
            raise IOError("Caught exception '%s' while loading file '%s'.%s"
                          % (estr, filename, msg))
        self._player.queue(self._movie)
        self.duration = self._movie.duration
        while self._player.source!=self._movie:
            self._player.next()
        self.status=NOT_STARTED
        self._player.pause()#start 'playing' on the next draw command
        self.filename=filename
        if log and self.autoLog:
            self.win.logOnFlip("Set %s movie=%s" %(self.name, filename),
                level=logging.EXP,obj=self)

    def pause(self, log=True):
        """Pause the current point in the movie (sound will stop, current frame
        will not advance).  If play() is called again both will restart.
        """
        self._player.pause()
        self.status=PAUSED
        if log and self.autoLog:
            self.win.logOnFlip("Set %s paused" %(self.name),
                level=logging.EXP,obj=self)
    def stop(self, log=True):
        """Stop the current point in the movie (sound will stop, current frame
        will not advance). Once stopped the movie cannot be restarted - it must
        be loaded again. Use pause() if you may need to restart the movie.
        """
        self._player.stop()
        self.status=STOPPED
        if log and self.autoLog:
            self.win.logOnFlip("Set %s stopped" %(self.name),
                level=logging.EXP,obj=self)
    def play(self, log=True):
        """Continue a paused movie from current position
        """
        self._player.play()
        self.status=PLAYING
        if log and self.autoLog:
            self.win.logOnFlip("Set %s playing" %(self.name),
                level=logging.EXP,obj=self)
    def seek(self,timestamp, log=True):
        """ Seek to a particular timestamp in the movie.
        NB this does not seem very robust as at version 1.62 and may cause crashes!
        """
        self._player.seek(float(timestamp))
        if log and self.autoLog:
            self.win.logOnFlip("Set %s seek=" %(self.name,timestamp),
                level=logging.EXP,obj=self)
    def draw(self, win=None):
        """Draw the current frame to a particular visual.Window (or to the
        default win for this object if not specified). The current position in
        the movie will be determined automatically.

        This method should be called on every frame that the movie is meant to
        appear"""

        if self.status in [NOT_STARTED, FINISHED]:#haven't started yet, so start
            self.play()
        #set the window to draw to
        if win==None: win=self.win
        win.winHandle.switch_to()

        #make sure that textures are on and GL_TEXTURE0 is active
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)

        frameTexture = self._player.get_texture()
        
        desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, 1)  #Contrast=1
        GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2],self.opacity)
        GL.glPushMatrix()
        #do scaling
        #scale the viewport to the appropriate size
        self.win.setScale(self._winScale)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],0)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        flipBitX = 1-self.flipHoriz*2
        flipBitY = 1-self.flipVert*2
        frameTexture.blit(
                -self._sizeRendered[0]/2.0*flipBitX,
                -self._sizeRendered[1]/2.0*flipBitY,
                width=self._sizeRendered[0]*flipBitX,
                height=self._sizeRendered[1]*flipBitY,
                z=0)
        GL.glPopMatrix()

    def setContrast(self):
        """"Not yet implemented for MovieStim"""
        pass

    def _onEos(self):
        if self.loop:
            self.loadMovie(self.filename)
            self.play()
            self.status=PLAYING
        else:
            self.status=FINISHED
        if self.autoLog:
            self.win.logOnFlip("Set %s finished" %(self.name),
                level=logging.EXP,obj=self)
    def setAutoDraw(self, val, log=True):
        """Add or remove a stimulus from the list of stimuli that will be
        automatically drawn on each flip

        :parameters:
            - val: True/False
                True to add the stimulus to the draw list, False to remove it
        """
        if val:
            self.play(log=False)  # set to play in case stopped
        else:
            self.pause(log=False)
        #add to drawing list and update status
        _BaseVisualStim.setAutoDraw(self, val, log=log)

class TextStim(_BaseVisualStim):
    """Class of text stimuli to be displayed in a :class:`~psychopy.visual.Window`
    """
    def __init__(self, win,
                 text="Hello World",
                 font="",
                 pos=(0.0,0.0),
                 depth=0,
                 rgb=None,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 opacity=1.0,
                 contrast=1.0,
                 units="",
                 ori=0.0,
                 height=None,
                 antialias=True,
                 bold=False,
                 italic=False,
                 alignHoriz='center',
                 alignVert='center',
                 fontFiles=[],
                 wrapWidth=None,
                 name='', autoLog=True):
        """
        :Parameters:
            win: A :class:`Window` object.
                Required - the stimulus must know where to draw itself
            text:
                The text to be rendered
            pos:
                Position on the screen
            color:

                Could be a:

                    - web name for a color (e.g. 'FireBrick');
                    - hex value (e.g. '#FF0047');
                    - tuple (1.0,1.0,1.0); list [1.0,1.0, 1.0]; or numpy array.

                If the last three are used then the color space should also be given
                See :ref:`colorspaces`

            colorSpace:
                the color space controlling the interpretation of the `color`
                See :ref:`colorspaces`
            contrast: float (default= *1.0* )
                How far the stimulus deviates from the middle grey.
                Contrast can vary -1:1 (this is a multiplier for the
                values given in the color description of the stimulus).
            opacity: float (default= *1.0* )
                How transparent the object will be (0 for transparent, 1 for opaque)
            units : **None**, 'height', 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window` will be used.
                See :ref:`units` for explanation of other options.
            ori:
                Orientation of the text
            height:
                Height of the characters (including the ascent of the letter and the descent)
            antialias:
                boolean to allow (or not) antialiasing the text
            bold:
                Make the text bold (better to use a bold font name)
            italic:
                Make the text italic (better to use an actual italic font)
            alignHoriz:
                The horizontal alignment ('left', 'right' or 'center')
            alignVert:
                The vertical alignment ('top', 'bottom' or 'center')
            fontFiles:
                A list of additional files if the font is not in the standard system location (include the full path)
            wrapWidth:
                The width the text should run before wrapping
            name : string
                The name of the object to be using during logged messages about
                this stim
            depth:
                The depth argument is deprecated and may be removed in future versions.
                Depth is controlled simply by drawing order.
        """
        _BaseVisualStim.__init__(self, win, units=units, name=name, autoLog=autoLog)

        if win._haveShaders: self._useShaders=True
        else: self._useShaders=False
        self.needUpdate =1
        self.opacity = float(opacity)
        self.contrast = float(contrast)
        self.alignHoriz = alignHoriz
        self.alignVert = alignVert
        self.antialias = antialias
        self.bold=bold
        self.italic=italic
        self.text='' #NB just a placeholder - real value set below
        self.depth=depth
        self.ori=ori
        self.wrapWidth=wrapWidth
        self._pygletTextObj=None

        self.pos= numpy.array(pos, float)

        #height in pix (needs to be done after units which is done during _Base.__init__)
        if self.units=='cm':
            if height==None: self.height = 1.0#default text height
            else: self.height = height
            self.heightPix = psychopy.misc.cm2pix(self.height, win.monitor)
        elif self.units in ['deg', 'degs']:
            if height==None: self.height = 1.0
            else: self.height = height
            self.heightPix = psychopy.misc.deg2pix(self.height, win.monitor)
        elif self.units=='norm':
            if height==None: self.height = 0.1
            else: self.height = height
            self.heightPix = self.height*win.size[1]/2
        elif self.units=='height':
            if height==None: self.height = 0.2
            else: self.height = height
            self.heightPix = self.height*win.size[1]
        else: #treat units as pix
            if height==None: self.height = 20
            else: self.height = height
            self.heightPix = self.height

        if self.wrapWidth ==None:
            if self.units in ['height','norm']: self.wrapWidth=1
            elif self.units in ['deg', 'degs']: self.wrapWidth=15
            elif self.units=='cm': self.wrapWidth=15
            elif self.units in ['pix', 'pixels']: self.wrapWidth=500
        if self.units=='norm': self._wrapWidthPix= self.wrapWidth*win.size[0]/2
        elif self.units=='height': self._wrapWidthPix= self.wrapWidth*win.size[0]
        elif self.units in ['deg', 'degs']: self._wrapWidthPix= psychopy.misc.deg2pix(self.wrapWidth, win.monitor)
        elif self.units=='cm': self._wrapWidthPix= psychopy.misc.cm2pix(self.wrapWidth, win.monitor)
        elif self.units in ['pix', 'pixels']: self._wrapWidthPix=self.wrapWidth

        #generate the texture and list holders
        self._listID = GL.glGenLists(1)
        if not self.win.winType=="pyglet":#pygame text needs a surface to render to
            self._texID=GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(self._texID))

        self.colorSpace=colorSpace
        if rgb!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb', log=False)
        else:
            self.setColor(color, log=False)

        self._calcPosRendered()
        for thisFont in fontFiles:
            pyglet.font.add_file(thisFont)
        self.setFont(font, log=False)
        self.setText(text, log=False) #self.width and self.height get set with text and calcSizeRednered is called
        self.needUpdate=True
    def setHeight(self,height, log=True):
        """Set the height of the letters (including the entire box that surrounds the letters
        in the font). The width of the letters is then defined by the font.
        """
        #height in pix (needs to be done after units)
        if self.units=='cm':
            if height==None: self.height = 1.0#default text height
            else: self.height = height
            self.heightPix = psychopy.misc.cm2pix(self.height, self.win.monitor)
        elif self.units in ['deg', 'degs']:
            if height==None: self.height = 1.0
            else: self.height = height
            self.heightPix = psychopy.misc.deg2pix(self.height, self.win.monitor)
        elif self.units=='norm':
            if height==None: self.height = 0.1
            else: self.height = height
            self.heightPix = self.height*self.win.size[1]/2
        elif self.units=='height':
            if height==None: self.height = 0.2
            else: self.height = height
            self.heightPix = self.height*self.win.size[1]
        else: #treat units as pix
            if height==None: self.height = 20
            else: self.height = height
            self.heightPix = self.height
        #need to update the font to reflect the change
        self.setFont(self.fontname, log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s height=%.2f" %(self.name, height),
                level=logging.EXP,obj=self)
    def setFont(self, font, log=True):
        """Set the font to be used for text rendering.
        font should be a string specifying the name of the font (in system resources)
        """
        self.fontname=None#until we find one
        if self.win.winType=="pyglet":
            self._font = pyglet.font.load(font, int(self.heightPix), dpi=72, italic=self.italic, bold=self.bold)
            self.fontname=font
        else:
            if font==None or len(font)==0:
                self.fontname = pygame.font.get_default_font()
            elif font in pygame.font.get_fonts():
                self.fontname = font
            elif type(font)==str:
                #try to find a xxx.ttf file for it
                fontFilenames = glob.glob(font+'*')#check for possible matching filenames
                if len(fontFilenames)>0:
                    for thisFont in fontFilenames:
                        if thisFont[-4:] in ['.TTF', '.ttf']:
                            self.fontname = thisFont#take the first match
                            break #stop at the first one we find
                    #trhen check if we were successful
                    if self.fontname == None and font!="":
                        #we didn't find a ttf filename
                        logging.warning("Found %s but it doesn't end .ttf. Using default font." %fontFilenames[0])
                        self.fontname = pygame.font.get_default_font()

            if self.fontname is not None and os.path.isfile(self.fontname):
                self._font = pygame.font.Font(self.fontname, int(self.heightPix), italic=self.italic, bold=self.bold)
            else:
                try:
                    self._font = pygame.font.SysFont(self.fontname, int(self.heightPix), italic=self.italic, bold=self.bold)
                    self.fontname = font
                    logging.info('using sysFont ' + str(font))
                except:
                    self.fontname = pygame.font.get_default_font()
                    logging.error("Couldn't find font %s on the system. Using %s instead!\n \
                              Font names should be written as concatenated names all in lower case.\n \
                              e.g. 'arial', 'monotypecorsiva', 'rockwellextra'..." %(font, self.fontname))
                    self._font = pygame.font.SysFont(self.fontname, int(self.heightPix), italic=self.italic, bold=self.bold)
        #re-render text after a font change
        self._needSetText=True
        if log and self.autoLog:
            self.win.logOnFlip("Set %s font=%s" %(self.name, self.fontname),
                level=logging.EXP,obj=self)

    def setText(self,text=None, log=True):
        """Set the text to be rendered using the current font
        """
        if text!=None:#make sure we have unicode object to render
            self.text = unicode(text)
        if self._useShaders:
            self._setTextShaders(text)
        else:
            self._setTextNoShaders(text)
        self._needSetText=False
        if log and self.autoLog:
            self.win.logOnFlip("Set %s text=%s" %(self.name, text),
                level=logging.EXP,obj=self)
    def setRGB(self, text, operation='', log=True):
        self._set('rgb', text, operation, log=log)
        if not self._useShaders:
            self._needSetText=True
    def setColor(self, color, colorSpace=None, operation='', log=True):
        """Set the color of the stimulus. See :ref:`colorspaces` for further information
        about the various ways to specify colors and their various implications.

        :Parameters:

        color :
            Can be specified in one of many ways. If a string is given then it
            is interpreted as the name of the color. Any of the standard html/X11
            `color names <http://www.w3schools.com/html/html_colornames.asp>`
            can be used. e.g.::

                myStim.setColor('white')
                myStim.setColor('RoyalBlue')#(the case is actually ignored)

            A hex value can be provided, also formatted as with web colors. This can be
            provided as a string that begins with # (not using python's usual 0x000000 format)::

                myStim.setColor('#DDA0DD')#DDA0DD is hexadecimal for plum

            You can also provide a triplet of values, which refer to the coordinates
            in one of the :ref:`colorspaces`. If no color space is specified then the color
            space most recently used for this stimulus is used again.

                myStim.setColor([1.0,-1.0,-1.0], 'rgb')#a red color in rgb space
                myStim.setColor([0.0,45.0,1.0], 'dkl') #DKL space with elev=0, azimuth=45
                myStim.setColor([0,0,255], 'rgb255') #a blue stimulus using rgb255 space

            Lastly, a single number can be provided, x, which is equivalent to providing
            [x,x,x].

                myStim.setColor(255, 'rgb255') #all guns o max

        colorSpace : string or None

            defining which of the :ref:`colorspaces` to use. For strings and hex
            values this is not needed. If None the default colorSpace for the stimulus is
            used (defined during initialisation).

        operation : one of '+','-','*','/', or '' for no operation (simply replace value)

            for colors specified as a triplet of values (or single intensity value)
            the new value will perform this operation on the previous color

                thisStim.setColor([1,1,1],'rgb255','+')#increment all guns by 1 value
                thisStim.setColor(-1, 'rgb', '*') #multiply the color by -1 (which in this space inverts the contrast)
                thisStim.setColor([10,0,0], 'dkl', '+')#raise the elevation from the isoluminant plane by 10 deg
        """
        #call setColor from super class
        _BaseVisualStim.setColor(self, color, colorSpace=colorSpace,
            operation=operation, log=log)
        #but then update text objects if necess
        if not self._useShaders:
            self._needSetText=True
    def _setTextShaders(self,value=None):
        """Set the text to be rendered using the current font
        """
        if self.win.winType=="pyglet":
            self._pygletTextObj = pyglet.font.Text(self._font, self.text,
                                                       halign=self.alignHoriz, valign=self.alignVert,
                                                       color = (1.0,1.0,1.0, self.opacity),
                                                       width=self._wrapWidthPix)#width of the frame
#            self._pygletTextObj = pyglet.text.Label(self.text,self.fontname, int(self.heightPix),
#                                                       anchor_x=self.alignHoriz, anchor_y=self.alignVert,#the point we rotate around
#                                                       halign=self.alignHoriz,
#                                                       color = (int(127.5*self.rgb[0]+127.5),
#                                                            int(127.5*self.rgb[1]+127.5),
#                                                            int(127.5*self.rgb[2]+127.5),
#                                                            int(255*self.opacity)),
#                                                       multiline=True, width=self._wrapWidthPix)#width of the frame
            self.width, self.height = self._pygletTextObj.width, self._pygletTextObj.height
        else:
            self._surf = self._font.render(value, self.antialias, [255,255,255])
            self.width, self.height = self._surf.get_size()

            if self.antialias: smoothing = GL.GL_LINEAR
            else: smoothing = GL.GL_NEAREST
            #generate the textures from pygame surface
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)#bind that name to the target
            GL.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, 4, self.width,self.height,
                                  GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pygame.image.tostring( self._surf, "RGBA",1))
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,smoothing)    #linear smoothing if texture is stretched?
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,smoothing)    #but nearest pixel value if it's compressed?

        self._needSetText=False
        self.needUpdate = True

    def _updateListShaders(self):
        """
        This is only used with pygame text - pyglet handles all from the draw()
        """
        if self._needSetText:
            self.setText(log=False)
        GL.glNewList(self._listID, GL.GL_COMPILE)
        #GL.glPushMatrix()

        #setup the shaderprogram
        #no need to do texture maths so no need for programs?
        #If we're using pyglet then this list won't be called, and for pygame shaders aren't enabled
        GL.glUseProgram(0)#self.win._progSignedTex)
        #GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTex, "texture"), 0) #set the texture to be texture unit 0

        #coords:
        if self.alignHoriz in ['center', 'centre']: left = -self.width/2.0;    right = self.width/2.0
        elif self.alignHoriz =='right':    left = -self.width;    right = 0.0
        else: left = 0.0; right = self.width
        #how much to move bottom
        if self.alignVert in ['center', 'centre']: bottom=-self.height/2.0; top=self.height/2.0
        elif self.alignVert =='top': bottom=-self.height; top=0
        else: bottom=0.0; top=self.height
        Btex, Ttex, Ltex, Rtex = -0.01, 0.98, 0,1.0#there seems to be a rounding err in pygame font textures

        #unbind the mask texture regardless
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        if self.win.winType=="pyglet":
            #unbind the main texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
#            GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0) #the texture is specified by pyglet.font.GlyphString.draw()
            GL.glEnable(GL.GL_TEXTURE_2D)
        else:
            #bind the appropriate main texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
            GL.glEnable(GL.GL_TEXTURE_2D)

        if self.win.winType=="pyglet":
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            self._pygletTextObj.draw()
        else:
            GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
            # right bottom
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Rtex, Btex)
            GL.glVertex3f(right,bottom,0)
            # left bottom
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Ltex,Btex)
            GL.glVertex3f(left,bottom,0)
            # left top
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Ltex,Ttex)
            GL.glVertex3f(left,top,0)
            # right top
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Rtex,Ttex)
            GL.glVertex3f(right,top,0)
            GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glUseProgram(0)
        #GL.glPopMatrix()

        GL.glEndList()
        self.needUpdate=0

    def _setTextNoShaders(self,value=None):
        """Set the text to be rendered using the current font
        """
        desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)

        if self.win.winType=="pyglet":
            self._pygletTextObj = pyglet.font.Text(self._font, self.text,
                                                       halign=self.alignHoriz, valign=self.alignVert,
                                                       color = (desiredRGB[0],desiredRGB[1], desiredRGB[2], self.opacity),
                                                       width=self._wrapWidthPix,#width of the frame
                                                       )
            self.width, self.height = self._pygletTextObj.width, self._pygletTextObj.height
        else:
            self._surf = self._font.render(value, self.antialias,
                                           [desiredRGB[0]*255,
                                            desiredRGB[1]*255,
                                            desiredRGB[2]*255])
            self.width, self.height = self._surf.get_size()
            if self.antialias: smoothing = GL.GL_LINEAR
            else: smoothing = GL.GL_NEAREST
            #generate the textures from pygame surface
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)#bind that name to the target
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA,
                            self.width,self.height,0,
                            GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pygame.image.tostring( self._surf, "RGBA",1))
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,smoothing)    #linear smoothing if texture is stretched?
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,smoothing)    #but nearest pixel value if it's compressed?
        self.needUpdate = True

    def _updateListNoShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        if self._needSetText:
            self.setText(log=False)
        GL.glNewList(self._listID, GL.GL_COMPILE)

        #coords:
        if self.alignHoriz in ['center', 'centre']: left = -self.width/2.0;    right = self.width/2.0
        elif self.alignHoriz =='right':    left = -self.width;    right = 0.0
        else: left = 0.0; right = self.width
        #how much to move bottom
        if self.alignVert in ['center', 'centre']: bottom=-self.height/2.0; top=self.height/2.0
        elif self.alignVert =='top': bottom=-self.height; top=0
        else: bottom=0.0; top=self.height
        Btex, Ttex, Ltex, Rtex = -0.01, 0.98, 0,1.0#there seems to be a rounding err in pygame font textures
        if self.win.winType=="pyglet":
            #unbind the mask texture
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            #unbind the main texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
        else:
            #bind the appropriate main texture
            GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
            #unbind the mask texture regardless
            GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        if self.win.winType=="pyglet":
            self._pygletTextObj.draw()
        else:
            GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
            # right bottom
            GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Rtex, Btex)
            GL.glVertex2f(right,bottom)
            # left bottom
            GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Ltex,Btex)
            GL.glVertex2f(left,bottom)
            # left top
            GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Ltex,Ttex)
            GL.glVertex2f(left,top)
            # right top
            GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Rtex,Ttex)
            GL.glVertex2f(right,top)
            GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEndList()
        self.needUpdate=0

    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.

        If win is specified then override the normal window of this stimulus.
        """
        #set the window to draw to
        if win==None: win=self.win
        if win.winType=='pyglet': win.winHandle.switch_to()

        GL.glPushMatrix()
        GL.glLoadIdentity()#for PyOpenGL this is necessary despite pop/PushMatrix, (not for pyglet)
        #scale and rotate
        prevScale = win.setScale(self._winScale)#to units for translations
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],0)#NB depth is set already
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        win.setScale('pix', None, prevScale)#back to pixels for drawing surface

        if self._useShaders: #then rgb needs to be set as glColor
            #setup color
            desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
            GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)

            GL.glUseProgram(self.win._progSignedTexFont)#self.win._progSignedTex)
#            GL.glUniform3iv(GL.glGetUniformLocation(self.win._progSignedTexFont, "rgb"), 1,
#                desiredRGB.ctypes.data_as(ctypes.POINTER(ctypes.c_float))) #set the texture to be texture unit 0
            GL.glUniform3f(GL.glGetUniformLocation(self.win._progSignedTexFont, "rgb"), desiredRGB[0],desiredRGB[1],desiredRGB[2])

        else: #color is set in texture, so set glColor to white
            GL.glColor4f(1,1,1,1)

        GL.glDisable(GL.GL_DEPTH_TEST) #should text have a depth or just on top?
        #update list if necss and then call it
        if win.winType=='pyglet':
            if self._needSetText:
                self.setText()
            #and align based on x anchor
            if self.alignHoriz=='right':
                GL.glTranslatef(-self.width,0,0)#NB depth is set already
            if self.alignHoriz in ['center', 'centre']:
                GL.glTranslatef(-self.width/2,0,0)#NB depth is set already

            #unbind the mask texture regardless
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            #unbind the main texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            #then allow pyglet to bind and use texture during drawing

            self._pygletTextObj.draw()
            GL.glDisable(GL.GL_TEXTURE_2D)
        else:
            #for pygame we should (and can) use a drawing list
            if self.needUpdate: self._updateList()
            GL.glCallList(self._listID)
        if self._useShaders: GL.glUseProgram(0)#disable shader (but command isn't available pre-OpenGL2.0)

        #GL.glEnable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
        GL.glPopMatrix()
    def setUseShaders(self, val=True):
        """Set this stimulus to use shaders if possible.
        """
        if val==True and self.win._haveShaders==False:
            logging.warn("Shaders were requested but aren;t available. Shaders need OpenGL 2.0+ drivers")
        if val!=self._useShaders:
            self._useShaders=val
            self._needSetText=True
            self.needUpdate=True
    def overlaps(self, polygon):
        """Not implemented for TextStim
        """
        pass
    def contains(self, polygon):
        """Not implemented for TextStim
        """
        pass

class ShapeStim(_BaseVisualStim):
    """Create geometric (vector) shapes by defining vertex locations.

    Shapes can be outlines or filled, by setting lineRGB and fillRGB to
    rgb triplets, or None. They can also be rotated (stim.setOri(__)) and
    translated (stim.setPos(__)) like any other stimulus.

    NB for now the fill of objects is performed using glBegin(GL_POLYGON)
    and that is limited to convex shapes. With concavities you get unpredictable
    results (e.g. add a fill color to the arrow stim below). To create concavities,
    you can combine multiple shapes, or stick to just outlines. (If anyone wants
    to rewrite ShapeStim to use glu tesselators that would be great!)
    """
    def __init__(self,
                 win,
                 units  ='',
                 lineWidth=1.0,
                 lineColor=(1.0,1.0,1.0),
                 lineColorSpace='rgb',
                 fillColor=None,
                 fillColorSpace='rgb',
                 vertices=((-0.5,0),(0,+0.5),(+0.5,0)),
                 closeShape=True,
                 pos= (0,0),
                 size=1,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth  =0,
                 interpolate=True,
                 lineRGB=None,
                 fillRGB=None,
                 name='', autoLog=True):
        """
        :Parameters:
            win :
                A :class:`~psychopy.visual.Window` object (required)

            units :  **None**, 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window` will be used.
                See :ref:`units` for explanation of other options.

            lineColor :

                Could be a:

                    - web name for a color (e.g. 'FireBrick');
                    - hex value (e.g. '#FF0047');
                    - tuple (1.0,1.0,1.0); list [1.0,1.0, 1.0]; or numpy array.

                If the last three are used then the color space should also be given
                See :ref:`colorspaces`

            lineColorSpace:
                The color space controlling the interpretation of the `lineColor`.
                See :ref:`colorspaces`

            fillColor :

                Could be a:

                    - web name for a color (e.g. 'FireBrick');
                    - hex value (e.g. '#FF0047');
                    - tuple (1.0,1.0,1.0); list [1.0,1.0, 1.0]; or numpy array.

                If the last three are used then the color space should also be given
                See :ref:`colorspaces`

            lineWidth : int (or float?)
                specifying the line width in **pixels**

            vertices : a list of lists or a numpy array (Nx2)
                specifying xy positions of each vertex

            closeShape : True or False
                Do you want the last vertex to be automatically connected to the first?

            pos : tuple, list or 2x1 array
                the position of the anchor for the stimulus (relative to which the vertices are drawn)

            size : float, int, tuple, list or 2x1 array
                Scales the ShapeStim up or down. Size is independent of the units, i.e.
                setting the size to 1.5 will make the stimulus to be 1.5 times it's original size
                as defined by the vertices. Use a 2-tuple to scale asymmetrically.

            ori : float or int
                the shape can be rotated around the anchor

            opacity : float (default= *1.0* )
                1.0 is opaque, 0.0 is transparent

            contrast: float (default= *1.0* )
                How far the stimulus deviates from the middle grey.
                Contrast can vary -1:1 (this is a multiplier for the
                values given in the color description of the stimulus).

            depth:
                The depth argument is deprecated and may be removed in future versions.
                Depth is controlled simply by drawing order.

            interpolate : True or False
                If True the edge of the line will be antialiased.

            name : string
                The name of the object to be using during logged messages about
                this stim
                """


        _BaseVisualStim.__init__(self, win, units=units, name=name, autoLog=autoLog)

        self.contrast = float(contrast)
        self.opacity = float(opacity)
        self.pos = numpy.array(pos, float)
        self.closeShape=closeShape
        self.lineWidth=lineWidth
        self.interpolate=interpolate

        self._useShaders=False#since we don't ned to combine textures with colors
        self.lineColorSpace=lineColorSpace
        if lineRGB!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setLineColor(lineRGB, colorSpace='rgb')
        else:
            self.setLineColor(lineColor, colorSpace=lineColorSpace)

        self.fillColorSpace=fillColorSpace
        if fillRGB!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setFillColor(fillRGB, colorSpace='rgb')
        else:
            self.setFillColor(fillColor, colorSpace=fillColorSpace)

        self.depth=depth
        self.ori = numpy.array(ori,float)
        self.size = numpy.array([0.0,0.0])
        self.setSize(size, log=False)
        self.setVertices(vertices, log=False)
        self._calcVerticesRendered()
    def setColor(self, color, colorSpace=None, operation=''):
        """For ShapeStim use :meth:`~ShapeStim.setLineColor` or
        :meth:`~ShapeStim.setFillColor`
        """
        raise AttributeError, 'ShapeStim does not support setColor method. Please use setFillColor or setLineColor instead'
    def setLineRGB(self, value, operation=''):
        """DEPRECATED since v1.60.05: Please use :meth:`~ShapeStim.setLineColor`
        """
        self._set('lineRGB', value, operation)
    def setFillRGB(self, value, operation=''):
        """DEPRECATED since v1.60.05: Please use :meth:`~ShapeStim.setFillColor`
        """
        self._set('fillRGB', value, operation)
    def setLineColor(self, color, colorSpace=None, operation='', log=True):
        """Sets the color of the shape edge. See :meth:`psychopy.visual.GratingStim.setColor`
        for further details of how to use this function.
        """
        _setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='lineRGB',#the name for this rgb value
                    colorAttrib='lineColor',#the name for this color
                    log=log)
    def setFillColor(self, color, colorSpace=None, operation='', log=True):
        """Sets the color of the shape fill. See :meth:`psychopy.visual.GratingStim.setColor`
        for further details of how to use this function.

        Note that shapes where some vertices point inwards will usually not
        'fill' correctly.
        """
        #run the original setColor, which creates color and
        _setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='fillRGB',#the name for this rgb value
                    colorAttrib='fillColor',#the name for this color
                    log=log)
    def setSize(self, value, operation='', log=True):
        """ Sets the size of the shape.
        Size is independent of the units of shape and will simply scale the shape's vertices by the factor given.
        Use a tuple or list of two values to scale asymmetrically.
        """
        self._set('size', numpy.asarray(value), operation, log=log)
        self.needVertexUpdate=True

    def setVertices(self,value=None, operation='', log=True):
        """Set the xy values of the vertices (relative to the centre of the field).
        Values should be:

            - an array/list of Nx2 coordinates.

        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if not (value.shape==(2,) \
            or (len(value.shape)==2 and value.shape[1]==2)
            ):
                raise ValueError("New value for setXYs should be 2x1 or Nx2")
        if operation=='':
            self.vertices=value
        else: exec('self.vertices'+operation+'=value')
        self.needVertexUpdate=True
        if log and self.autoLog:
            self.win.logOnFlip("Set %s vertices=%s" %(self.name, value),
                level=logging.EXP,obj=self)
    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if self.needVertexUpdate: self._calcVerticesRendered()

        if win==None: win=self.win
        if win.winType=='pyglet': win.winHandle.switch_to()

        nVerts = self.vertices.shape[0]

        #scale the drawing frame etc...
        GL.glPushMatrix()#push before drawing, pop after
        win.setScale(self._winScale)
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],0)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        #load Null textures into multitexteureARB - or they modulate glColor
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        if self.interpolate:
            GL.glEnable(GL.GL_LINE_SMOOTH)
            GL.glEnable(GL.GL_POLYGON_SMOOTH)
        else:
            GL.glDisable(GL.GL_LINE_SMOOTH)
            GL.glDisable(GL.GL_POLYGON_SMOOTH)
        GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self._verticesRendered.ctypes)#.data_as(ctypes.POINTER(ctypes.c_float)))

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        if nVerts>2: #draw a filled polygon first
            if self.fillRGB!=None:
                #convert according to colorSpace
                fillRGB = self._getDesiredRGB(self.fillRGB, self.fillColorSpace, self.contrast)
                #then draw
                GL.glColor4f(fillRGB[0], fillRGB[1], fillRGB[2], self.opacity)
                GL.glDrawArrays(GL.GL_POLYGON, 0, nVerts)
        if self.lineRGB!=None:
            lineRGB = self._getDesiredRGB(self.lineRGB, self.lineColorSpace, self.contrast)
            #then draw
            GL.glLineWidth(self.lineWidth)
            GL.glColor4f(lineRGB[0], lineRGB[1], lineRGB[2], self.opacity)
            if self.closeShape: GL.glDrawArrays(GL.GL_LINE_LOOP, 0, nVerts)
            else: GL.glDrawArrays(GL.GL_LINE_STRIP, 0, nVerts)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glPopMatrix()

    def _calcVerticesRendered(self):
        self.needVertexUpdate=False
        if self.units in ['norm', 'pix', 'height']:
            self._verticesRendered=self.vertices
            self._posRendered=self.pos
        elif self.units in ['deg', 'degs']:
            self._verticesRendered=psychopy.misc.deg2pix(self.vertices, self.win.monitor)
            self._posRendered=psychopy.misc.deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm':
            self._verticesRendered=psychopy.misc.cm2pix(self.vertices, self.win.monitor)
            self._posRendered=psychopy.misc.cm2pix(self.pos, self.win.monitor)
        self._verticesRendered = self._verticesRendered * self.size

class Polygon(ShapeStim):
    """Creates a regular polygon (triangles, pentagrams, ...) as a special case of a :class:`~psychopy.visual.ShapeStim`

    (New in version 1.72.00)
    """
    def __init__(self, win, edges=3, radius=.5, **kwargs):
        """
        Polygon accepts all input parameters that :class:`~psychopy.visual.ShapeStim` accepts, except for vertices and closeShape.

        :Parameters:

            win :
                A :class:`~psychopy.visual.Window` object (required)

            edges : int
                Number of edges of the polygon

            radius : float, int, tuple, list or 2x1 array
                Radius of the Polygon (distance from the center to the corners).
                May be a -2tuple or list to stretch the polygon asymmetrically
        """
        self.edges = edges
        self.radius = numpy.asarray(radius)
        self._calcVertices()
        kwargs['closeShape'] = True # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices
        ShapeStim.__init__(self, win, **kwargs)

    def _calcVertices(self):
        d = numpy.pi*2/ self.edges
        self.vertices = [
            numpy.asarray(
                (numpy.sin(e*d), numpy.cos(e*d))
            ) * self.radius
            for e in xrange(self.edges)
        ]

    def setRadius(self, radius, log=True):
        """Changes the radius of the Polygon. Parameter should be

            - float, int, tuple, list or 2x1 array"""
        self.radius = numpy.asarray(radius)
        self._calcVertices()
        self.setVertices(self.vertices, log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s radius=%s" %(self.name, radius),
                level=logging.EXP,obj=self)
class Circle(Polygon):
    """Creates a Circle with a given radius as a special case of a `~psychopy.visual.ShapeStim`

    (New in version 1.72.00)
    """
    def __init__(self, win, radius=.5, edges=32, **kwargs):
        """
        Circle accepts all input parameters that `~psychopy.visual.ShapeStim` accept, except for vertices and closeShape.

        :Parameters:

            win :
                A :class:`~psychopy.visual.Window` object (required)

            edges : float or int (default=32)
                Specifies the resolution of the polygon that is approximating the
                circle.

            radius : float, int, tuple, list or 2x1 array
                Radius of the Circle (distance from the center to the corners).
                If radius is a 2-tuple or list, the values will be interpreted as semi-major and
                semi-minor radii of an ellipse.
        """
        kwargs['edges'] = edges
        kwargs['radius'] = radius
        Polygon.__init__(self, win, **kwargs)


    def setRadius(self, radius, log=True):
        """Changes the radius of the Polygon. If radius is a 2-tuple or list, the values will be
        interpreted as semi-major and semi-minor radii of an ellipse."""
        self.radius = numpy.asarray(radius)
        self._calcVertices()
        self.setVertices(self.vertices, log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s radius=%s" %(self.name, radius),
                level=logging.EXP,obj=self)

class Rect(ShapeStim):
    """Creates a rectangle of given width and height as a special case of a `~psychopy.visual.ShapeStim`

    (New in version 1.72.00)
    """
    def __init__(self, win, width=.5, height=.5, **kwargs):
        """
        Rect accepts all input parameters, that `~psychopy.visual.ShapeStim` accept, except for vertices and closeShape.

        :Parameters:

            win :
                A :class:`~psychopy.visual.Window` object (required)

            width : int or float
                Width of the Rectangle (in its respective units, if specified)

            height : int or float
                Height of the Rectangle (in its respective units, if specified)

        """
        self.width = width
        self.height = height
        self._calcVertices()
        kwargs['closeShape'] = True # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices

        ShapeStim.__init__(self, win, **kwargs)

    def _calcVertices(self):
        self.vertices = [
            (-self.width*.5,  self.height*.5),
            ( self.width*.5,  self.height*.5),
            ( self.width*.5, -self.height*.5),
            (-self.width*.5, -self.height*.5)
        ]

    def setWidth(self, width, log=True):
        """Changes the width of the Rectangle"""
        self.width = width
        self._calcVertices()
        self.setVertices(self.vertices, log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s width=%s" %(self.name, width),
                level=logging.EXP,obj=self)

    def setHeight(self, height, log=True):
        """Changes the height of the Rectangle """
        self.height = height
        self._calcVertices()
        self.setVertices(self.vertices, log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s height=%s" %(self.name, height),
                level=logging.EXP,obj=self)

class Line(ShapeStim):
    """Creates a Line between two points.

    (New in version 1.72.00)
    """
    def __init__(self, win, start=(-.5, -.5), end=(.5, .5), **kwargs):
        """
        Line accepts all input parameters, that `~psychopy.visual.ShapeStim` accepts, except
        for vertices, closeShape and fillColor.

        The methods `contains` and `overlaps` are inherited from `~psychopy.visual.ShapeStim`,
        but always return False (because a line is not a proper (2D) polygon).

        :Parameters:

            win :
                A :class:`~psychopy.visual.Window` object (required)

            start : tuple, list or 2x1 array
                Specifies the position of the start of the line

            end : tuple, list or 2x1 array
                Specifies the position of the end of the line

        """
        self.start = start
        self.end = end
        self.vertices = [start, end]
        kwargs['closeShape'] = False # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices
        kwargs['fillColor'] = None
        ShapeStim.__init__(self, win, **kwargs)

    def setStart(self, start, log=True):
        """Changes the start point of the line. Argument should be

            - tuple, list or 2x1 array specifying the coordinates of the start point"""
        self.start = start
        self.setVertices([self.start, self.end], log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s start=%s" %(self.name, start),
                level=logging.EXP,obj=self)

    def setEnd(self, end, log=True):
        """Changes the end point of the line. Argument should be a tuple, list
        or 2x1 array specifying the coordinates of the end point"""
        self.end = end
        self.setVertices([self.start, self.end], log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s end=%s" %(self.name, end),
                level=logging.EXP,obj=self)

    def contains(self):
        pass
    def overlaps(self):
        pass

class ImageStim(_BaseVisualStim):
    def __init__(self,
                 win,
                 image     =None,
                 mask    =None,
                 units   ="",
                 pos     =(0.0,0.0),
                 size    =None,
                 ori     =0.0,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=1.0,
                 depth=0,
                 interpolate=False,
                 flipHoriz=False,
                 flipVert=False,
                 texRes=128,
                 name='', autoLog=True,
                 maskParams=None):
        """
        :Parameters:

            win :
                a :class:`~psychopy.visual.Window` object (required)
            image :
                The image file to be presented (most formats supported)
            mask :
                The alpha mask that can be used to control the outer shape of the stimulus

                + **None**, 'circle', 'gauss', 'raisedCos'
                + or the name of an image file (most formats supported)
                + or a numpy array (1xN or NxN) ranging -1:1

            units : **None**, 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window` will be used.
                See :ref:`units` for explanation of other options.

            pos :
                a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y of the centre of the stimulus.
                The origin is the screen centre, the units are determined
                by units (see above). Stimuli can be position beyond the
                window!

            size :
                a tuple (0.5,0.5) or a list [0.5,0.5] for the x and y
                OR a single value (which will be applied to x and y).
                Units are specified by 'units' (see above).
                Sizes can be negative and can extend beyond the window.

                .. note::

                    If the mask is Gaussian ('gauss'), then the 'size' parameter refers to
                    the stimulus at 3 standard deviations on each side of the
                    centre (ie. sd=size/6)

            ori:
                orientation of stimulus in degrees

            color:

                Could be a:

                    - web name for a color (e.g. 'FireBrick');
                    - hex value (e.g. '#FF0047');
                    - tuple (1.0,1.0,1.0); list [1.0,1.0, 1.0]; or numpy array.

                If the last three are used then the color space should also be given
                See :ref:`colorspaces`

            colorSpace:
                the color space controlling the interpretation of the `color`
                See :ref:`colorspaces`

            contrast: float (default= *1.0* )
                How far the stimulus deviates from the middle grey.
                Contrast can vary -1:1 (this is a multiplier for the
                values given in the color description of the stimulus).

            opacity: float (default= *1.0* )
                1.0 is opaque, 0.0 is transparent

            texRes:
                Sets the resolution of the mask (this is independent of the image resolution)

            depth:
                The depth argument is deprecated and may be removed in future versions.
                Depth is controlled simply by drawing order.

            name : string
                The name of the object to be using during logged messages about
                this stim

            maskParams: Various types of input. Default to None.
                This is used to pass additional parameters to the mask if those
                are needed.
                - For the 'raisedCos' mask, pass a dict: {'fringeWidth':0.2},
                where 'fringeWidth' is a parameter (float, 0-1), determining
                the proportion of the patch that will be blurred by the raised
                cosine edge.

        """
        _BaseVisualStim.__init__(self, win, units=units, name=name, autoLog=autoLog)

        if win._haveShaders: self._useShaders=True#by default, this is a good thing
        else: self._useShaders=False

        self.ori = float(ori)
        self.contrast = float(contrast)
        self.opacity = float(opacity)
        self.interpolate=interpolate
        self.flipHoriz = flipHoriz
        self.flipVert = flipVert

        self.origSize=None#if an image texture is loaded this will be updated

        self.colorSpace=colorSpace
        self.setColor(color, colorSpace=colorSpace, log=False)
        self.rgbPedestal=[0,0,0]#does an rgb pedestal make sense for an image?

        #initialise textures for stimulus
        self.texID=GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self.texID))
        self.maskID=GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self.maskID))

        # Set the maskParams (defaults to None):
        self.maskParams= maskParams

        self.texRes=texRes
        self.setImage(image, log=False)
        self.setMask(mask, log=False)

        #size
        self._requestedSize=size
        if size==None:
            self._setSizeToDefault()
        elif type(size) in [tuple,list]:
            self.size = numpy.array(size,float)
        else:
            self.size = numpy.array((size,size),float)#make a square if only given one dimension

        self.pos = numpy.array(pos,float)

        self.depth=depth
        #fix scaling to window coords
        self._calcSizeRendered()
        self._calcPosRendered()

        # _verticesRendered for .contains() and .overlaps()
        v = [(-.5,-.5), (-.5,.5), (.5,.5), (.5,-.5)]
        self._verticesRendered = numpy.array(self._sizeRendered, dtype=float) * v

        #generate a displaylist ID
        self._listID = GL.glGenLists(1)
        self._updateList()#ie refresh display list

    def _updateListShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self.needUpdate=0
        GL.glNewList(self._listID,GL.GL_COMPILE)
        #setup the shaderprogram
        GL.glUseProgram(self.win._progSignedTexMask)
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "texture"), 0) #set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "mask"), 1)  # mask is texture unit 1
        #mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)#implicitly disables 1D

        #main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        flipHoriz = self.flipHoriz*(-2)+1#True=(-1), False->(+1)
        flipVert = self.flipVert*(-2)+1
        #calculate coords in advance:
        L = -self._sizeRendered[0]/2 * flipHoriz#vertices
        R =  self._sizeRendered[0]/2 * flipHoriz
        T =  self._sizeRendered[1]/2 * flipVert
        B = -self._sizeRendered[1]/2 * flipVert

        GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,1,0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,1,0)
        GL.glVertex2f(R,B)
        # left bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,0,0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,0,0)
        GL.glVertex2f(L,B)
        # left top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,0,1)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,0,1)
        GL.glVertex2f(L,T)
        # right top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,1,1)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,1,1)
        GL.glVertex2f(R,T)
        GL.glEnd()

        #unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)#implicitly disables 1D
        #main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glUseProgram(0)

        GL.glEndList()

    #for the sake of older graphics cards------------------------------------
    def _updateListNoShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self.needUpdate=0

        GL.glNewList(self._listID,GL.GL_COMPILE)
        GL.glColor4f(1.0,1.0,1.0,1.0)#glColor can interfere with multitextures
        #mask
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)#implicitly disables 1D
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.maskID)

        #main texture
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)

        flipHoriz = self.flipHoriz*(-2)+1#True=(-1), False->(+1)
        flipVert = self.flipVert*(-2)+1
        #calculate vertices
        L = -self._sizeRendered[0]/2 * flipHoriz
        R =  self._sizeRendered[0]/2 * flipHoriz
        T =  self._sizeRendered[1]/2 * flipVert
        B = -self._sizeRendered[1]/2 * flipVert

        GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,1,0)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,1,0)
        GL.glVertex2f(R,B)
        # left bottom
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,0,0)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,0,0)
        GL.glVertex2f(L,B)
        # left top
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,0,1)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,0,1)
        GL.glVertex2f(L,T)
        # right top
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,1,1)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,1,1)
        GL.glVertex2f(R,T)
        GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEndList()


    def __del__(self):
        self.clearTextures()#remove textures from graphics card to prevent crash

    def contains(self, x, y=None):
        """Determines if a point x,y is on the image (within its boundary).

        See :class:`~psychopy.visual.ShapeStim` `.contains()`.
        """
        if hasattr(x, 'getPos'):
            x,y = x.getPos()
        elif type(x) in [list, tuple, numpy.ndarray]:
            x,y = x[0:2]
        return pointInPolygon(x, y, self)

    def overlaps(self, polygon):
        """Determines if the image overlaps another image or shape (`polygon`).

        See :class:`~psychopy.visual.ShapeStim` `.overlaps()`.
        """
        return polygonsOverlap(self, polygon)

    def clearTextures(self):
        """
        Clear the textures associated with the given stimulus.
        As of v1.61.00 this is called automatically during garbage collection of
        your stimulus, so doesn't need calling explicitly by the user.
        """
        GL.glDeleteTextures(1, self.texID)
        GL.glDeleteTextures(1, self.maskID)
    def draw(self, win=None):
        if win==None: win=self.win
        if win.winType=='pyglet': win.winHandle.switch_to()

        #do scaling
        GL.glPushMatrix()#push before the list, pop after
        win.setScale(self._winScale)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],0)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        #the list just does the texture mapping

        desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
        GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)

        if self.needUpdate: self._updateList()
        GL.glCallList(self._listID)

        #return the view to previous state
        GL.glPopMatrix()
    def setImage(self, value, log=True):
        """Set the image to be used for the stimulus to this new value
        """
        self._imName = value

        createTexture(value, id=self.texID, pixFormat=GL.GL_RGB, stim=self,
            maskParams=self.maskParams, forcePOW2=False)
        #if user requested size=None then update the size for new stim here
        if hasattr(self, '_requestedSize') and self._requestedSize==None:
            self._setSizeToDefault()
        if log and self.autoLog:
            self.win.logOnFlip("Set %s image=%s" %(self.name, value),
                level=logging.EXP,obj=self)
    def setMask(self,value, log=True):
        """Change the image to be used as an alpha-mask for the image
        """
        self._maskName = value
        createTexture(value, id=self.maskID, pixFormat=GL.GL_ALPHA, stim=self,
            res=self.texRes, maskParams=self.maskParams)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s mask=%s" %(self.name, value),
                level=logging.EXP,obj=self)
    def _setSizeToDefault(self):
        """Set the size to default (e.g. to the size of the loaded image etc)
        """
        #calculate new size
        if self.origSize is None:#not an image from a file
            self.size=numpy.array([0.5,0.5])#this was PsychoPy's original default
        else:
            #we have an image - calculate the size in `units` that matches original pixel size
            if self.units=='pix': self.size=numpy.array(self.origSize)
            elif self.units=='deg': self.size= psychopy.misc.pix2deg(numpy.array(self.origSize, float), self.win.monitor)
            elif self.units=='cm': self.size= psychopy.misc.pix2cm(numpy.array(self.origSize, float), self.win.monitor)
            elif self.units=='norm': self.size= 2*numpy.array(self.origSize, float)/self.win.size
            elif self.units=='height': self.size= numpy.array(self.origSize, float)/self.win.size[1]
        #set it
        self._calcSizeRendered()
        self.needUpdate=True
class BufferImageStim(GratingStim):
    """
    Take a "screen-shot" (full or partial), save to a ImageStim()-like RBGA object.

    The class returns a screen-shot, i.e., a single collage image composed of static
    elements, ones that you want to treat as effectively a single stimulus. The
    screen-shot can be of the visible screen (front buffer) or hidden (back buffer).

    BufferImageStim aims to provide fast rendering, while still allowing dynamic
    orientation, position, and opacity. Its fast to draw but slow to init (like
    ImageStim). There is no support for dynamic depth.

    You specify the part of the screen to capture (in norm units), and optionally
    the stimuli themselves (as a list of items to be drawn). You get a screenshot
    of those pixels. If your OpenGL does not support arbitrary sizes, the image
    will be larger, using square powers of two if needed, with the excess image
    being invisible (using alpha). The aim is to preserve the buffer contents as
    rendered.

    Checks for OpenGL 2.1+, or uses square-power-of-2 images.

    Status: seems to work on Mac, but limitations:
    - Screen units are not properly sorted out, would be better to allow pix too
    - Not tested on Windows, Linux, FreeBSD

    **Example**::

        # define lots of stimuli, make a list:
        mySimpleImageStim = ...
        myTextStim = ...
        stimList = [mySimpleImageStim, myTextStim]

        # draw stim list items & capture everything (slow):
        screenshot = visual.BufferImageStim(myWin, stim=stimList)

        # render to screen (fast):
        while <conditions>:
            screenshot.draw()  # fast; can vary .ori, ._position, .opacity
            other_stuff.draw() # dynamic
            myWin.flip()

    See coder Demos > stimuli > bufferImageStim.py for a demo, with timing stats.

    :Author:
        - 2010 Jeremy Gray
    """
    def __init__(self, win, buffer='back', rect=(-1, 1, 1, -1), sqPower2=False,
        stim=(), interpolate=True, vertMirror=False, name='', autoLog=True):
        """
        :Parameters:

            win :
                A :class:`~psychopy.visual.Window` object (required)
            buffer :
                the screen buffer to capture from, default is 'back' (hidden).
                'front' is the buffer in view after win.flip()
            rect :
                a list of edges [left, top, right, bottom] defining a screen rectangle
                which is the area to capture from the screen, given in norm units.
                default is fullscreen: [-1, 1, 1, -1]
            stim :
                a list of item(s) to be drawn to the buffer in order, then captured.
                each item needs to have its own .draw() method, and have the same
                window as win
            interpolate :
                whether to use interpolation (default = True, generally good,
                especially if you change the orientation)
            sqPower2 :
                - False (default) = use rect for size if OpenGL = 2.1+
                - True = use square, power-of-two image sizes
            vertMirror :
                whether to vertically flip (mirror) the captured image; default = False
            name : string
                The name of the object to be using during logged messages about this stim
        """
        # depends on: window._getRegionOfFrame

        if len(list(stim)) > 0: # draw all stim to the back buffer
            win.clearBuffer()
            logging.debug('BufferImageStim.__init__: clearing back buffer')
            buffer = 'back'
            for stimulus in list(stim):
                try:
                    if stimulus.win == win:
                        stimulus.draw()
                    else:
                        logging.warning('BufferImageStim.__init__: user requested "%s" drawn in another window' % repr(stimulus))
                except AttributeError:
                    logging.warning('BufferImageStim.__init__: "%s" failed to draw' % repr(stimulus))

        self.vertMirror = vertMirror # used in .draw()

        # take a screenshot of the buffer using win._getRegionOfFrame():
        glversion = pyglet.gl.gl_info.get_version()
        if glversion >= '2.1' and not sqPower2:
            region = win._getRegionOfFrame(buffer=buffer, rect=rect)
        else:
            if not sqPower2:
                logging.debug('BufferImageStim.__init__: defaulting to square power-of-2 sized image (%s)' % glversion )
            region = win._getRegionOfFrame(buffer=buffer, rect=rect, squarePower2=True)

        # turn the RGBA region into a GratingStim()-like object:
        GratingStim.__init__(self, win, tex=region, units='pix',
                             interpolate=interpolate, name=name, autoLog=autoLog)
        # May 2012: GratingStim is ~3x faster to initialize than ImageStim, looks the same in the demo
        # but subclassing ImageStim seems more intuitive; maybe setTex gets called multiple times?
        #ImageStim.__init__(self, win, image=region, units='pix', interpolate=interpolate, name=name, autoLog=autoLog)

        # to improve drawing speed, move these out of draw:
        self.desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
        self.thisScale = 2.0/numpy.array(self.win.size)

    def setTex(self, tex, interpolate=True, log=True):
        # setTex is called only once
        self._texName = tex
        id = self.texID
        pixFormat = GL.GL_RGB
        useShaders = self._useShaders
        self.interpolate = interpolate

        if self.vertMirror:
            im = tex # looks backwards, but is correct
        else:
            im = tex.transpose(Image.FLIP_TOP_BOTTOM)
        self.origSize=im.size

        #im = im.convert("RGBA") # should be RGBA because win._getRegionOfFrame() returns RGBA
        intensity = numpy.array(im).astype(numpy.float32)*0.0078431372549019607 - 1  # same as *2/255-1, but much faster

        if useShaders:#pixFormat==GL.GL_RGB and not wasLum
            internalFormat = GL.GL_RGB32F_ARB
            dataType = GL.GL_FLOAT
            data = intensity
        else: #pixFormat==GL.GL_RGB:# not wasLum, not useShaders  - an RGB bitmap with no shader options
            internalFormat = GL.GL_RGB
            dataType = GL.GL_UNSIGNED_BYTE
            data = psychopy.misc.float_uint8(intensity)

        pixFormat=GL.GL_RGBA # because win._getRegionOfFrame() returns RGBA
        internalFormat=GL.GL_RGBA32F_ARB

        if self.win.winType=='pygame':
            texture = data.tostring()#serialise
        else:#pyglet on linux needs ctypes instead of string object!?
            texture = data.ctypes#serialise

        #bind the texture in openGL
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, id) #bind that name to the target
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT) #makes the texture map wrap (this is actually default anyway)
        #important if using bits++ because GL_LINEAR
        #sometimes extrapolates to pixel vals outside range
        if interpolate:
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_LINEAR)
            if useShaders:#GL_GENERATE_MIPMAP was only available from OpenGL 1.4
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                    data.shape[1], data.shape[0], 0,
                    pixFormat, dataType, texture)
            else:#use glu
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_NEAREST)
                GL.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, internalFormat,
                    data.shape[1], data.shape[0], pixFormat, dataType, texture)
        else:
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                            data.shape[1], data.shape[0], 0,
                            pixFormat, dataType, texture)

        if log and self.autoLog:
            self.win.logOnFlip("Set %s tex=%s" %(self.name, tex),
                level=logging.EXP,obj=self)
    def draw(self):
        """
        Draws the BufferImage on the screen, similar to :class:`~psychopy.visual.ImageStim` `.draw()`.
        Allows dynamic position, size, rotation, color, and opacity.
        Limitations / bugs: not sure what happens with shaders & self._updateList()
        """
        # this is copy & pasted from old GratingStim, then had stuff taken out for speed

        if self.win.winType=='pyglet':
            self.win.winHandle.switch_to()

        GL.glPushMatrix() # preserve state
        #GL.glLoadIdentity()

        GL.glScalef(self.thisScale[0], self.thisScale[1], 1.0)

        # enable dynamic position, orientation, opacity; depth not working?
        GL.glTranslatef(self._posRendered[0], self._posRendered[1], 0)
        GL.glRotatef(-self.ori, 0.0, 0.0, 1.0)
        GL.glColor4f(self.desiredRGB[0], self.desiredRGB[1], self.desiredRGB[2], self.opacity)

        GL.glCallList(self._listID) # make it happen
        GL.glPopMatrix() #return the view to previous state

class RatingScale:
    """A class for getting numeric or categorical ratings, e.g., a 1-to-7 scale.

    Returns a re-usable rating-scale object having a .draw() method, with a
    customizable visual appearance. Tries to provide useful default values.

    The .draw() method displays the rating scale only (not the item to be rated),
    handles the subject's response, and updates the display. When the subject
    responds, .noResponse goes False (i.e., there is a response). You can then
    call .getRating() to obtain the rating, .getRT() to get the decision time, or
    .reset() to restore the scale (for re-use). The experimenter has to handle
    the item to be rated, i.e., draw() it in the same window each frame. A
    RatingScale instance has no idea what else is on the screen. The subject can
    use the arrow keys (left, right) to move the marker in small increments (e.g.,
    1/100th of a tick-mark if precision = 100).

    Auto-rescaling happens if the low-anchor is 0 and high-anchor is a multiple
    of 10, just to reduce visual clutter.

    **Example 1**:

        The default 7-point scale::

            myItem = <create your text, image, movie, ...>
            myRatingScale = visual.RatingScale(myWin)
            while myRatingScale.noResponse:
                myItem.draw()
                myRatingScale.draw()
                myWin.flip()
            rating = myRatingScale.getRating()
            decisionTime = myRatingScale.getRT()

        You can equivalently specify the while condition using .status::

            while myRatingScale.status != FINISHED:

    **Example 2**:

        Key-board only. Considerable customization is possible. For fMRI, if your
        response box sends keys 1-4, you could specify left, right, and accept
        keys, and no mouse::

            myRatingScale = visual.RatingScale(myWin, markerStart=4,
                leftKeys='1', rightKeys = '2', acceptKeys='4')

    **Example 3**:

        Non-numeric choices (categorical, unordered)::

            myRatingScale = visual.RatingScale(myWin, choices=['agree', 'disagree'])
            myRatingScale = visual.RatingScale(myWin,
                                choices=['cherry', 'apple', True, 3.14, 'pie'])

        str(item) will be displayed, but the value returned by
        getResponse() will be of type you gave it::

            myRatingScale = visual.RatingScale(myWin, choices=[True, False])

        So if you give boolean values and the subject chooses False,
        getResponse() will return False (bool) and not 'False' (str).

    See Coder Demos -> stimuli -> ratingScale.py for examples. As another example,
    fMRI_launchScan.py uses a rating scale for the experimenter to choose between
    two modes (and not for subjects giving ratings).

    The Builder RatingScale component gives a restricted set of options, but also
    allows full control over a RatingScale (via 'customizeEverything').

    :Author:
        2010 Jeremy Gray, with various updates.
    """
    def __init__(self,
                win,
                scale='<default>',
                choices=None,
                low=1,
                high=7,
                lowAnchorText=None,
                highAnchorText=None,
                precision=1,
                textSizeFactor=1.0,
                textColor='LightGray',
                textFont='Helvetica Bold',
                showValue=True,
                showScale=True,
                showAnchors=True,
                showAccept=True,
                acceptKeys='return',
                acceptPreText='key, click',
                acceptText='accept?',
                leftKeys='left',
                rightKeys='right',
                lineColor='White',
                markerStyle='triangle',
                markerColor=None,
                markerStart=False,
                markerExpansion=1,
                customMarker=None,
                escapeKeys=None,
                allowSkip=True,
                skipKeys='tab',
                mouseOnly=False,
                singleClick=False,
                displaySizeFactor=1.0,
                stretchHoriz=1.0,
                pos=None,
                minTime=1.0,
                maxTime=0.0,
                disappear=False,
                name='',
                autoLog=True):
        """
    :Parameters:

        win :
            A :class:`~psychopy.visual.Window` object (required)
        scale :
            string, explanation of the numbers to display to the subject, shown above the line;
            default = '<low>=not at all, <high>=extremely'
            to suppress all text above the line, set `showScale=False`
        choices :
            a list of items which the subject can choose among;
            (takes precedence over `low`, `high`, `lowAnchorText`, `highAnchorText`, `showScale`)
        low :
            lowest numeric rating / low anchor (integer, default = 1)
        high :
            highest numeric rating / high anchor (integer, default = 7; at least low+1)
        lowAnchorText :
            text to dsiplay for the low end of the scale (default = numeric low value)
        highAnchorText :
            text to display for the high end of the scale (default = numeric high value)
        precision :
            portions of a tick to accept as input [1, 10, 100], default = 1 tick (no fractional parts)

            .. note:: `leftKeys` / `rightKeys` will move the marker by one portion of a tick.

        textSizeFactor :
            control the size of text elements of the scale.
            for larger than default text (expand) set > 1; for smaller, set < 1
        textColor :
            color to use for anchor and scale text (assumed to be RGB), default = 'LightGray'
        textFont :
            name of the font to use, default = 'Helvetica Bold'
        showValue :
            show the subject their currently selected number, default = True
        showScale :
            show the `scale` text (the text above the line), default = True
            if False, will not show any text above the line
        showAnchors :
            show the two end points of the scale (low, high), default = True
        showAccept :
            show the button to click to accept the current value by using the mouse, default = True

            .. note::
                If showAccept is False and acceptKeys is empty, acceptKeys is reset to ['return']
                to give the subject a way to respond.

        acceptKeys :
            a key or list of keys that mean "accept the current response", default = ['return']
        acceptPreText :
            text to display before any value has been selected
        acceptText :
            text to display in the 'accept' button after a value has been selected
        leftKeys :
            a key or list of keys that mean "move leftwards", default = ['left']
        rightKeys :
            a key or list of keys that mean "move rightwards", default = ['right']
        lineColor :
            color to use for the scale line, default = 'White'
        markerStyle :
            'triangle' (DarkBlue), 'circle' (DarkRed), or 'glow' (White)
        markerColor :
            None = use defaults; or any legal RGB colorname, e.g., '#123456', 'DarkRed'
        markerStart :
            False, or the value in [low..high] to be pre-selected upon initial display
        markerExpansion :
            how much the glow marker expands when moving to the right; 0=none, negative shrinks; try 10 or -10
        customMarker :
            allows for a user-defined marker; must have a `.draw()` method, such as a
            :class:`~psychopy.visual.TextStim()` or :class:`~psychopy.visual.GratingStim()`
        escapeKeys :
            keys that will quit the experiment, calling `core.quit()`. default = [ ] (none).

            .. note:: in the Builder, the default is ['escape'] (to be consistent with other Builder conventions)

        allowSkip :
            if True, the subject can skip an item by pressing a key in `skipKeys`, default = True
        skipKeys :
            list of keys the subject can use to skip a response, default = ['tab']

            .. note::
                to require a response to every item, use `allowSkip=False`

        mouseOnly :
            require the subject use the mouse only (no keyboard), default = False.
            can be used to avoid competing with other objects for keyboard input.

            .. note::
                `mouseOnly=True` and `showAccept=False` is a bad combination,
                so `showAccept` wins (`mouseOnly` is reset to `False`);
                similarly, `mouseOnly` and `allowSkip` can conflict, because
                skipping an item is done via key press (`mouseOnly` wins)
                `mouseOnly=True` is helpful if there will be something else
                on the screen expecting keyboard input
        singleClick :
            enable a mouse click to both indicate and accept the rating, default = False.
            note that the 'accept' box is visible, but clicking it has no effect,
            its just to display the value. a legal key press will also count as a singleClick.
        pos : tuple (x, y)
            where to position the rating scale (x, y) in terms of the window's units (pix, norm);
            default (0.0, -0.4) in norm units
        displaySizeFactor :
            how much to expand or contract the overall rating scale display
            (not just the line length)
        stretchHoriz:
            multiplicative factor for stretching (or compressing) the scale
            horizontally (3 -> use the whole window);
            like displaySizeFactor, but only in the horizontal direction
        minTime :
            number of seconds that must elapse before a reponse can be accepted,
            default = 1.0s
        maxTime :
            number of seconds after which a reponse cannot be made accepted.
            if `maxTime` <= `minTime`, there's unlimited time.
            default = 0.0s (wait forever)
        disappear :
            if True, the rating scale will be hidden after a value is accepted;
            useful when showing multiple scales. The default is to remain on-screen.

        name : string
            The name of the object to be using during logged messages about
            this stim
        autolog :
            whether logging should be done automatically
        """

        ### MAYBE SOMEDAY ?
        # - radio-button-like display for categorical choices

        logging.exp('RatingScale %s: init()' % name)
        self.win = win
        self.name = name
        self.autoLog = autoLog
        self.disappear = disappear

        # internally work in norm units, restore to orig units at the end of __init__:
        self.savedWinUnits = self.win.units
        self.win.units = 'norm'

        # Generally make things well-behaved if the requested value(s) would be trouble:
        self._initFirst(showAccept, mouseOnly, singleClick, acceptKeys,
                        markerStart, low, high, precision, choices,
                        lowAnchorText, highAnchorText, scale, showScale, showAnchors)
        self._initMisc(minTime, maxTime)

        # Set scale & position, key-bindings:
        self._initPosScale(pos, displaySizeFactor, stretchHoriz)
        self._initKeyBindings(self.acceptKeys, skipKeys, escapeKeys, leftKeys, rightKeys, allowSkip)

        # Construct the visual elements:
        self._initLine(lineColor=lineColor)
        self._initMarker(customMarker, markerExpansion, markerColor, markerStyle, self.tickSize)
        self._initTextElements(win, self.lowAnchorText, self.highAnchorText, self.scale,
                            textColor, textFont, textSizeFactor, showValue)
        self._initAcceptBox(self.showAccept, acceptPreText, acceptText, self.markerColor,
                            self.textSizeSmall, textSizeFactor, self.textFont)

        # List-ify the requested visual elements; self.marker is handled separately
        self.visualDisplayElements = []
        if self.showScale:   self.visualDisplayElements += [self.scaleDescription]
        if self.showAnchors: self.visualDisplayElements += [self.lowAnchor, self.highAnchor]
        if self.showAccept:  self.visualDisplayElements += [self.acceptBox, self.accept]
        self.visualDisplayElements += [self.line] # last b/c win xp had display issues for me in a VM

        # Final touches:
        self.origScaleDescription = self.scaleDescription.text
        self.reset() # sets .status
        self.win.units = self.savedWinUnits # restore

    def _initFirst(self, showAccept, mouseOnly, singleClick, acceptKeys,
                   markerStart, low, high, precision, choices,
                   lowAnchorText, highAnchorText, scale, showScale, showAnchors):
        """some sanity checking; various things are set, especially those that are
        used later; choices, anchors, markerStart settings are handled here
        """
        self.showAccept = bool(showAccept)
        self.mouseOnly = bool(mouseOnly)
        self.singleClick = bool(singleClick)
        self.acceptKeys = acceptKeys
        self.precision = precision
        self.showAnchors = bool(showAnchors)

        if not self.showAccept:
            # the accept button is the mouse-based way to accept the current response
            if len(list(self.acceptKeys)) == 0:
                # make sure there is in fact a way to respond using a key-press:
                self.acceptKeys = ['return']
            if self.mouseOnly and not self.singleClick:
                # then there's no way to respond, so deny mouseOnly / enable using keys:
                self.mouseOnly = False
                logging.warning("RatingScale %s: ignoring mouseOnly (because showAccept and singleClick are False)" % self.name)

        # 'choices' is a list of non-numeric (unordered) alternatives:
        self.scale = scale
        self.showScale = showScale
        self.lowAnchorText = lowAnchorText
        self.highAnchorText = highAnchorText
        if choices and len(list(choices)) < 2:
            logging.warning("RatingScale %s: ignoring choices=[ ]; it requires 2 or more list elements" % self.name)
        if choices and len(list(choices)) >= 2:
            low = 0
            high = len(list(choices)) - 1 # can be modified in anchors; do self.low there
            # anchor text defaults to blank, unless low or highAnchorText is requested explicitly:
            if lowAnchorText is None and highAnchorText is None:
                self.showAnchors = False
            else:
                self.lowAnchorText = unicode(lowAnchorText)
                self.highAnchorText = unicode(highAnchorText)
            self.scale = '  '.join(map(unicode, choices)) # unicode for display
            self.choices = choices
        else:
            self.choices = False

        # Anchors need to be well-behaved [do after choices]:
        try:
            self.low = int(low) # low anchor
        except:
            self.low = 1
        try:
            self.high = int(high) # high anchor
        except:
            self.high = self.low + 1
        if self.high <= self.low:
            self.high = self.low + 1
            self.precision = 100

        # Marker preselected and valid? [do after anchors]
        if ( (type(markerStart) == float and self.precision > 1 or
                type(markerStart) == int) and
                markerStart >= self.low and markerStart <= self.high):
            self.markerStart = markerStart
            self.markerPlacedAt = markerStart
            self.markerPlaced = True
        elif isinstance(markerStart, basestring) and type(self.choices) == list and markerStart in self.choices:
            self.markerStart = self.choices.index(markerStart)
            self.markerPlacedAt = markerStart
            self.markerPlaced = True
        else:
            self.markerStart = None
            self.markerPlaced = False

    def _initMisc(self, minTime, maxTime):
        # precision is the fractional parts of a tick mark to be sensitive to, in [1,10,100]:
        if type(self.precision) != int or self.precision < 10:
            self.precision = 1
            self.fmtStr = "%.0f" # decimal places, purely for display
        elif self.precision < 100:
            self.precision = 10
            self.fmtStr = "%.1f"
        else:
            self.precision = 100
            self.fmtStr = "%.2f"

        self.myClock = core.Clock() # for decision time
        try:
            self.minimumTime = float(minTime)
        except ValueError:
            self.minimumTime = 1.0
        self.minimumTime = max(self.minimumTime, 0.)
        try:
            self.maximumTime = float(maxTime)
        except ValueError:
            self.maximumTime = 0.0
        self.timedOut = False

        self.myMouse = event.Mouse(win=self.win, visible=True)
        # Mouse-click-able 'accept' button pulsates (cycles its brightness over frames):
        frames_per_cycle = 100
        self.pulseColor = [0.6 + 0.22 * float(cos(i/15.65)) for i in range(frames_per_cycle)]

    def _initPosScale(self, pos, displaySizeFactor, stretchHoriz):
        """position (x,y) and magnitification (size) of the rating scale
        """
        # Screen position (translation) of the rating scale as a whole:
        if pos:
            if len(list(pos)) == 2:
                offsetHoriz, offsetVert = pos
            else:
                logging.warning("RatingScale %s: pos expects a tuple (x,y)" % self.name)
        try:
            self.offsetHoriz = float(offsetHoriz)
        except:
            if self.savedWinUnits == 'pix':
                self.offsetHoriz = 0
            else: # default x in norm units:
                self.offsetHoriz = 0.0
        try:
            self.offsetVert = float(offsetVert)
        except:
            if self.savedWinUnits == 'pix':
                self.offsetVert = int(self.win.size[1] / -5.0)
            else: # default y in norm units:
                self.offsetVert = -0.4
        # pos=(x,y) will consider x,y to be in win units, but want norm internally
        if self.savedWinUnits == 'pix':
            self.offsetHoriz = float(self.offsetHoriz) / self.win.size[0] / 0.5
            self.offsetVert = float(self.offsetVert) / self.win.size[1] / 0.5
        self.pos = [self.offsetHoriz, self.offsetVert] # just expose; not used elsewhere yet

        # Scale size (magnification) of the rating scale as a whole:
        try:
            self.stretchHoriz = float(stretchHoriz)
        except:
            self.stretchHoriz = 1.
        try:
            self.displaySizeFactor = float(displaySizeFactor) * 0.6
        except:
            self.displaySizeFactor = 0.6
        if not 0.06 < self.displaySizeFactor < 3:
            logging.warning("RatingScale %s: unusual displaySizeFactor" % self.name)

    def _initKeyBindings(self, acceptKeys, skipKeys, escapeKeys, leftKeys, rightKeys, allowSkip):
        # keys for accepting the currently selected response:
        if self.mouseOnly:
            self.acceptKeys = [ ] # no valid keys, so must use mouse
        else:
            if type(acceptKeys) not in [list, tuple]:
                acceptKeys = [acceptKeys]
            self.acceptKeys = acceptKeys
        self.skipKeys = [ ]
        if allowSkip and not self.mouseOnly:
            if skipKeys is None:
                skipKeys = [ ]
            elif type(skipKeys) not in [list, tuple]:
                skipKeys = [skipKeys]
            self.skipKeys = list(skipKeys)
        if type(escapeKeys) not in [list, tuple]:
            if escapeKeys is None:
                escapeKeys = [ ]
            else:
                escapeKeys = [escapeKeys]
        self.escapeKeys = escapeKeys
        if type(leftKeys) not in [list, tuple]:
            leftKeys = [leftKeys]
        self.leftKeys = leftKeys
        if type(rightKeys) not in [list, tuple]:
            rightKeys = [rightKeys]
        self.rightKeys = rightKeys

        # allow responding via numeric keys if the response range is in 0-9:
        self.respKeys = [ ]
        if (not self.mouseOnly and self.low > -1 and self.high < 10):
            self.respKeys = [str(i) for i in range(self.low, self.high + 1)]
        # but if any digit is used as an action key, that should take precedence
        # so disable using numeric keys:
        if (set(self.respKeys).intersection(self.leftKeys + self.rightKeys +
                                self.acceptKeys + self.skipKeys + self.escapeKeys) == set([]) ):
            self.enableRespKeys = True
        else:
            self.enableRespKeys = False

    def _initLine(self, lineColor='White'):
        """define a ShapeStim to be a graphical line, with tick marks.

        ### Notes (JRG Aug 2010)
        Conceptually, the response line is always -0.5 to +0.5 ("internal" units). This line, of unit length,
        is scaled and translated for display. The line is effectively "center justified", expanding both left
        and right with scaling, with pos[] specifiying the screen coordinate (in window units, norm or pix)
        of the mid-point of the response line. Tick marks are in integer units, internally 0 to (high-low),
        with 0 being the left end and (high-low) being the right end. (Subjects see low to high on the screen.)
        Non-numeric (categorical) choices are selected using tick-marks interpreted as an index, choice[tick].
        Tick units get mapped to "internal" units based on their proportion of the total ticks (--> 0. to 1.).
        The unit-length internal line is expanded / contracted by stretchHoriz and displaySizeFactor, and then
        is translated to position pos (offsetHoriz=pos[0], offsetVert=pos[1]). pos is the name of the arg, and
        its values appear in the code as offsetHoriz and offsetVert only for historical reasons (should be
        refactored for clarity).

        Auto-rescaling reduces the number of tick marks shown on the
        screen by a factor of 10, just for nicer appearance, without affecting the internal representation.

        Thus, the horizontal screen position of the i-th tick mark, where i in [0,n], for n total ticks (n = high-low),
        in screen units ('norm') will be:
          tick-i             == offsetHoriz + (-0.5 + i/n ) * stretchHoriz * displaySizeFactor
        So two special cases are:
          tick-0 (left end)  == offsetHoriz - 0.5 * stretchHoriz * displaySizeFactor
          tick-n (right end) == offsetHoriz + 0.5 * stretchHoriz * displaySizeFactor
        The vertical screen position is just offsetVert (in screen norm units).
        To elaborate: tick-0 is the left-most tick, or "low anchor"; here 0 is internal, the subject sees <low>.
        tick-n is the right-most tick, or "high anchor", or internal-tick-(high-low), and the subject sees <high>.
        Intermediate ticks, i, are located proportionally between -0.5 to + 0.5, based on their proportion
        of the total number of ticks, float(i)/n. The "proportion of total" is used because its a line of unit length,
        i.e., the same length as used to internally represent the scale (-0.5 to +0.5).
        If precision > 1, the user / experimenter is asking for fractional ticks. These map correctly
        onto [0, 1] as well without requiring special handling (just do ensure float() ).

        Another note: -0.5 to +0.5 looked too big to be the default size of the rating line in screen norm units,
        so I set the internal displaySizeFactor = 0.6 to compensate (i.e., making everything smaller). The user can
        adjust the scaling around the default by setting displaySizeFactor, stretchHoriz, or both.
        This means that the user / experimenter can just think of > 1 being expansion (and < 1 == contraction)
        relative to the default (internal) scaling, and not worry about the internal scaling.
        """

        self.lineColor = lineColor
        self.lineColorSpace = 'rgb'
        self.tickMarks = float(self.high - self.low)

        # visually remap 10 ticks onto 1 tick in some conditions (= cosmetic only):
        self.autoRescaleFactor = 1
        if (self.low == 0 and self.tickMarks > 20 and int(self.tickMarks) % 10 == 0):
            self.autoRescaleFactor = 10
            self.tickMarks /= self.autoRescaleFactor
        self.tickSize = 0.04 # vertical height of each tick, norm units

        # ends of the rating line, in norm units:
        self.lineLeftEnd  = self.offsetHoriz - 0.5 * self.stretchHoriz * self.displaySizeFactor
        self.lineRightEnd = self.offsetHoriz + 0.5 * self.stretchHoriz * self.displaySizeFactor

        # space around the line within which to accept mouse input:
        pad = 0.06 * self.displaySizeFactor
        self.nearLine = numpy.asarray([
            (self.lineLeftEnd - pad, -2 * pad + self.offsetVert),
            (self.lineLeftEnd - pad, 2 * pad + self.offsetVert),
            (self.lineRightEnd + pad, 2 * pad + self.offsetVert),
            (self.lineRightEnd + pad, -2 * pad + self.offsetVert) ])

        # vertices for ShapeStim:
        vertices = [[self.lineLeftEnd, self.offsetVert]] # first vertex
        for t in range(int(self.tickMarks) + 1):
            vertices.append([self.offsetHoriz + self.stretchHoriz * self.displaySizeFactor *
                    (-0.5 + t / self.tickMarks), self.tickSize * self.displaySizeFactor + self.offsetVert])
            vertices.append([self.offsetHoriz + self.stretchHoriz * self.displaySizeFactor *
                    (-0.5 + t / self.tickMarks), self.offsetVert])
            if t < self.tickMarks: # extend the line to the next tick mark, t + 1
                vertices.append([self.offsetHoriz + self.stretchHoriz * self.displaySizeFactor *
                                 (-0.5 + (t + 1) / self.tickMarks), self.offsetVert])
        vertices.append([self.lineRightEnd, self.offsetVert])
        vertices.append([self.lineLeftEnd, self.offsetVert])

        # create the line:
        self.line = ShapeStim(win=self.win, units='norm', vertices=vertices, lineWidth=4,
                              lineColor=self.lineColor, lineColorSpace=self.lineColorSpace,
                              name=self.name+'.line')

    def _initMarker(self, customMarker, markerExpansion, markerColor, markerStyle, tickSize):
        """define a GratingStim or ShapeStim to be used as the indicator
        """
        # preparatory stuff:
        self.markerStyle = markerStyle
        if customMarker and not 'draw' in dir(customMarker):
            logging.warning("RatingScale: the requested customMarker has no draw method; reverting to default")
            self.markerStyle = 'triangle'
            customMarker = None

        self.markerSize = 8. * self.displaySizeFactor
        self.markerOffsetVert = 0.
        self.markerExpansion = float(markerExpansion) * 0.6

        self.markerColor = markerColor
        if markerColor and isinstance(markerColor, basestring):
            markerColor = markerColor.replace(' ','')

        # decide how to define self.marker:
        if customMarker:
            self.marker = customMarker
            if markerColor == None:
                if hasattr(customMarker, 'color'):
                    if not customMarker.color: # 0 causes other problems, so ignore it here
                        customMarker.color = 'DarkBlue'
                elif hasattr(customMarker, 'fillColor'):
                    customMarker.color = customMarker.fillColor
                else:
                    customMarker.color = 'DarkBlue'
                markerColor = customMarker.color
                if not hasattr(self.marker, 'name'):
                    self.marker.name = 'customMarker'
        elif self.markerStyle == 'triangle': # and sys.platform in ['linux2', 'darwin']):
            vertices = [[-1 * tickSize * self.displaySizeFactor * 1.8, tickSize * self.displaySizeFactor * 3],
                    [ tickSize * self.displaySizeFactor * 1.8, tickSize * self.displaySizeFactor * 3], [0, -0.005]]
            if markerColor == None:
                markerColor = 'DarkBlue'
            try:
                self.marker = ShapeStim(win=self.win, units='norm', vertices=vertices, lineWidth=0.1,
                                        lineColor=markerColor, fillColor=markerColor, fillColorSpace='rgb',
                                        name=self.name+'.markerTri', autoLog=False)
            except AttributeError: # bad markerColor, presumably
                self.marker = ShapeStim(win=self.win, units='norm', vertices=vertices, lineWidth=0.1,
                                        lineColor='DarkBlue', fillColor='DarkBlue', fillColorSpace='rgb',
                                        name=self.name+'.markerTri', autoLog=False)
                markerColor = 'DarkBlue'
            self.markerExpansion = 0
        elif self.markerStyle == 'glow':
            if markerColor == None:
                markerColor = 'White'
            try:
                self.marker = PatchStim(win=self.win, tex='sin', mask='gauss', color=markerColor,
                                        colorSpace='rgb', opacity = 0.85, autoLog=False,
                                        name=self.name+'.markerGlow')
            except AttributeError: # bad markerColor, presumably
                self.marker = PatchStim(win=self.win, tex='sin', mask='gauss', color='White',
                                        colorSpace='rgb', opacity = 0.85, autoLog=False,
                                        name=self.name+'.markerGlow')
                markerColor = 'White'
            self.markerBaseSize = tickSize * self.markerSize
            self.markerOffsetVert = .02
            if self.markerExpansion == 0:
                self.markerBaseSize *= self.markerSize * 0.7
                if self.markerSize > 1.2:
                    self.markerBaseSize *= .7
                self.marker.setSize(self.markerBaseSize/2.)
        else: # self.markerStyle == 'circle':
            if markerColor == None:
                markerColor = 'DarkRed'
            x,y = self.win.size
            windowRatio = float(y)/x
            self.markerSizeVert = 3.2 * tickSize * self.displaySizeFactor
            size = [3.2 * tickSize * self.displaySizeFactor * windowRatio, self.markerSizeVert]
            self.markerOffsetVert = self.markerSizeVert / 2.
            try:
                self.marker = PatchStim(win=self.win, tex=None, units='norm', size=size,
                                        mask='circle', color=markerColor, colorSpace='rgb',
                                        name=self.name+'.markerCir', autoLog=False)
            except AttributeError: # bad markerColor, presumably
                self.marker = PatchStim(win=self.win, tex=None, units='norm', size=size,
                                        mask='circle', color='DarkRed', colorSpace='rgb',
                                        name=self.name+'.markerCir', autoLog=False)
                markerColor = 'DarkRed'
            self.markerBaseSize = tickSize
        self.markerColor = markerColor

    def _initTextElements(self, win, lowAnchorText, highAnchorText, scale, textColor,
                          textFont, textSizeFactor, showValue):
        """creates TextStim for self.scaleDescription, self.lowAnchor, self.highAnchor
        """
        # text appearance (size, color, font, visibility):
        self.showValue = bool(showValue) # hide if False
        self.textColor = textColor
        self.textColorSpace = 'rgb'
        self.textFont = textFont
        if not type(textSizeFactor) in [float, int]:
            textSizeFactor = 1.0
        self.textSize = 0.2 * textSizeFactor * self.displaySizeFactor
        self.textSizeSmall = self.textSize * 0.6
        self.showValue = bool(showValue)

        if lowAnchorText:
            lowText = unicode(lowAnchorText)
        else:
            lowText = unicode(self.low)
        if highAnchorText:
            highText = unicode(highAnchorText)
        else:
            highText = unicode(self.high)
        self.lowAnchorText = lowText
        self.highAnchorText = highText
        if not scale:
            scale = ' '
        if scale == '<default>': # set the default
            scale = lowText + unicode(' = not at all . . . extremely = ') + highText

        # create the TextStim:
        self.scaleDescription = TextStim(win=self.win, height=self.textSizeSmall,
                                    color=self.textColor, colorSpace=self.textColorSpace,
                                    pos=[self.offsetHoriz, 0.22 * self.displaySizeFactor + self.offsetVert],
                                    name=self.name+'.scale')
        self.scaleDescription.setFont(textFont)
        self.lowAnchor = TextStim(win=self.win,
                            pos=[self.offsetHoriz - 0.5 * self.stretchHoriz * self.displaySizeFactor,
                            -2 * self.textSizeSmall * self.displaySizeFactor + self.offsetVert],
                            height=self.textSizeSmall, color=self.textColor, colorSpace=self.textColorSpace,
                            name=self.name+'.lowAnchor')
        self.lowAnchor.setFont(textFont)
        self.lowAnchor.setText(lowText)
        self.highAnchor = TextStim(win=self.win,
                            pos=[self.offsetHoriz + 0.5 * self.stretchHoriz * self.displaySizeFactor,
                            -2 * self.textSizeSmall * self.displaySizeFactor + self.offsetVert],
                            height=self.textSizeSmall, color=self.textColor, colorSpace=self.textColorSpace,
                            name=self.name+'.highAnchor')
        self.highAnchor.setFont(textFont)
        self.highAnchor.setText(highText)
        self.setDescription(scale) # do after having set the relevant things
    def setDescription(self, scale):
        """Method to set the description that appears above the line, (e.g., "1=not at all...extremely=7")
        The text will not be visible if `showScale` is False. This can be useful
        if re-using the same RatingScale object to get ratings of different dimentions.
        While its possible to just assign to rs.scaleDescription.text, its better
        to do rs.setDescription() which records the appropriate change in the log file.
        """
        self.scaleDescription.setText(scale)
        if self.showScale:
            logging.exp('RatingScale %s: setting scale="%s"' % (self.name, self.scaleDescription.text))
        else:
            logging.exp('RatingScale %s: no scale description; low=%s, high=%s' %
                        (self.name, self.lowAnchor.text, self.highAnchor.text))

    def _initAcceptBox(self, showAccept, acceptPreText, acceptText,
                       markerColor, textSizeSmall, textSizeFactor, textFont):
        """creates a ShapeStim for self.acceptBox (mouse-click-able 'accept'  button)
        and a TextStim for self.accept (container for the text shown inside the box)
        """
        if not showAccept: # then no point creating things that won't be used
            return

        self.acceptLineColor = [-.2, -.2, -.2]
        self.acceptFillColor = [.2, .2, .2]

        # define self.acceptBox:
        self.acceptBoxtop  = acceptBoxtop  = self.offsetVert - 0.2 * self.displaySizeFactor * textSizeFactor
        self.acceptBoxbot  = acceptBoxbot  = self.offsetVert - 0.37 * self.displaySizeFactor * textSizeFactor
        self.acceptBoxleft = acceptBoxleft = self.offsetHoriz - 0.2 * self.displaySizeFactor * textSizeFactor
        self.acceptBoxright = acceptBoxright = self.offsetHoriz + 0.2 * self.displaySizeFactor * textSizeFactor

        # define a rectangle with rounded corners; for square corners, set delta2 to 0
        delta = 0.025 * self.displaySizeFactor
        delta2 = delta / 7
        acceptBoxVertices = [
            [acceptBoxleft,acceptBoxtop-delta], [acceptBoxleft+delta2,acceptBoxtop-3*delta2],
            [acceptBoxleft+3*delta2,acceptBoxtop-delta2], [acceptBoxleft+delta,acceptBoxtop],
            [acceptBoxright-delta,acceptBoxtop], [acceptBoxright-3*delta2,acceptBoxtop-delta2],
            [acceptBoxright-delta2,acceptBoxtop-3*delta2], [acceptBoxright,acceptBoxtop-delta],
            [acceptBoxright,acceptBoxbot+delta],[acceptBoxright-delta2,acceptBoxbot+3*delta2],
            [acceptBoxright-3*delta2,acceptBoxbot+delta2], [acceptBoxright-delta,acceptBoxbot],
            [acceptBoxleft+delta,acceptBoxbot], [acceptBoxleft+3*delta2,acceptBoxbot+delta2],
            [acceptBoxleft+delta2,acceptBoxbot+3*delta2], [acceptBoxleft,acceptBoxbot+delta] ]
        if sys.platform not in ['linux2']:
            self.acceptBox = ShapeStim(win=self.win, vertices=acceptBoxVertices,
                            fillColor=self.acceptFillColor, lineColor=self.acceptLineColor,
                            name=self.name+'.accept')
        else: # interpolation looks bad on linux, as of Aug 2010
            self.acceptBox = ShapeStim(win=self.win, vertices=acceptBoxVertices,
                            fillColor=self.acceptFillColor, lineColor=self.acceptLineColor,
                            interpolate=False, name=self.name+'.accept')

        # text to display inside accept button before a marker has been placed:
        if self.low > 0 and self.high < 10 and not self.mouseOnly:
            self.keyClick = 'key, click'
        else:
            self.keyClick = 'click line'
        if acceptPreText != 'key, click': # non-default
            self.keyClick = unicode(acceptPreText)
        self.acceptText = unicode(acceptText)

        # create the TextStim:
        self.accept = TextStim(win=self.win, text=self.keyClick, font=self.textFont,
                            pos=[self.offsetHoriz, (acceptBoxtop + acceptBoxbot) / 2.],
                            italic=True, height=textSizeSmall, color=self.textColor,
                            colorSpace=self.textColorSpace, autoLog=False)
        self.accept.setFont(textFont)

        self.acceptTextColor = markerColor
        if markerColor in ['White']:
            self.acceptTextColor = 'Black'

    def _getMarkerFromPos(self, mouseX):
        """Convert mouseX into units of tick marks, 0 .. high-low, fractional if precision > 1
        """
        mouseX = min(max(mouseX, self.lineLeftEnd), self.lineRightEnd)
        markerPos = (mouseX - self.offsetHoriz) * self.tickMarks / (self.stretchHoriz *
            self.displaySizeFactor) + self.tickMarks/2. # mouseX==0 -> mid-point of tick scale
        markerPos = (round(markerPos * self.precision * self.autoRescaleFactor) /
            float(self.precision * self.autoRescaleFactor) )  # scale to 0..tickMarks
        return markerPos # 0 .. high-low
    def _getMarkerFromTick(self, value):
        """Convert a requested tick value into a position on the internal scale.
        Accounts for non-zero low end, autoRescale, and precision.
        The return value is assured to be on the scale.
        """
        # on the line:
        value = max(min(self.high, value), self.low)
        # with requested precision:
        value = (round(value * self.precision * self.autoRescaleFactor) /
                    float(self.precision * self.autoRescaleFactor) )
        return (value - self.low) * self.autoRescaleFactor
    def setMarkerPos(self, value):
        """Method to allow the experimenter to set the marker's position on the
        scale (in units of tick marks). This method can also set the index within
        a list of choices (which start at 0). No range checking is done.

        Assuming you have defined rs = RatingScale(...), you can specify a tick
        position directly::
            rs.setMarkerPos(2)
        or do range checking, precision management, and auto-rescaling::
            rs.setMarkerPos(rs._getMarkerFromTick(2))
        To work from a screen coordinate, such as the X position of a mouse click::
            rs.setMarkerPos(rs._getMarkerFromPos(mouseX))
        """
        self.markerPlacedAt = value
        self.markerPlaced = True # only needed first time, which this ensures
    def draw(self):
        """
        Update the visual display, check for response (key, mouse, skip).

        sets response flags as appropriate (`self.noResponse`, `self.timedOut`).
        `draw()` only draws the rating scale, not the item to be rated
        """
        self.win.units = 'norm' # orig = saved during init, restored at end of .draw()
        if self.firstDraw:
            self.firstDraw = False
            self.myClock.reset()
            self.status = STARTED

        # timed out?
        if self.maximumTime > self.minimumTime and self.myClock.getTime() > self.maximumTime:
            self.noResponse = False
            self.timedOut = True
            logging.data('RatingScale %s: rating=%s (no response, timed out after %.3fs)' %
                         (self.name, unicode(self.getRating()), self.maximumTime) )
            logging.data('RatingScale %s: rating RT=%.3fs' % (self.name, self.getRT()) ) # getRT() should not be None here, cuz timedout

        # 'disappear' == draw nothing if subj is done:
        if self.noResponse == False and self.disappear:
            self.win.units = self.savedWinUnits
            return

        # draw everything except the marker:
        for visualElement in self.visualDisplayElements:
            visualElement.draw()

        # if the subject is done but the scale is still being drawn:
        if self.noResponse == False:
            # fix the marker position on the line
            if not self.markerPosFixed:
                self.marker.setPos((0, -.012), '+') # drop it onto the line
                self.markerPosFixed = True # flag to park it there
            self.marker.draw()
            if self.showAccept:
                self.acceptBox.setFillColor(self.acceptFillColor)
                self.acceptBox.setLineColor(self.acceptLineColor)
                self.acceptBox.draw()
            self.win.units = self.savedWinUnits
            return # makes the marker unresponsive

        mouseX, mouseY = self.myMouse.getPos() # norm units

        # draw the marker:
        if self.markerPlaced or self.singleClick:
            # expansion fun & games with 'glow':
            if self.markerStyle == 'glow':
                if self.markerExpansion > 0:
                    self.marker.setSize(self.markerBaseSize + 0.1 * self.markerExpansion *
                                        self.markerPlacedAt / self.tickMarks)
                    self.marker.setOpacity(0.2 + self.markerPlacedAt / self.tickMarks)
                elif self.markerExpansion < 0:
                    self.marker.setSize(self.markerBaseSize - 0.1 * self.markerExpansion *
                                        (self.tickMarks - self.markerPlacedAt) / self.tickMarks)
                    self.marker.setOpacity(1.2 - self.markerPlacedAt / self.tickMarks)
            # update position:
            if self.singleClick and pointInPolygon(mouseX, mouseY, self.nearLine):
                #self.markerPlacedAt = self._getMarkerFromPos(mouseX)
                self.setMarkerPos(self._getMarkerFromPos(mouseX))
            elif not hasattr(self, 'markerPlacedAt'):
                self.markerPlacedAt = False
            # set the marker's screen position based on its tick coordinate (== markerPlacedAt)
            if self.markerPlacedAt is not False:
                self.marker.setPos([self.offsetHoriz + self.displaySizeFactor * self.stretchHoriz *
                                (-0.5 + self.markerPlacedAt / self.tickMarks),
                                self.offsetVert + self.markerOffsetVert])
                self.marker.draw()
            if self.showAccept:
                self.frame = (self.frame + 1) % 100
                self.acceptBox.setFillColor(self.pulseColor[self.frame])
                self.acceptBox.setLineColor(self.pulseColor[self.frame])
                self.accept.setColor(self.acceptTextColor)
                if self.showValue and self.markerPlacedAt is not False:
                    if self.choices:
                        val = unicode(self.choices[int(self.markerPlacedAt)])
                    else:
                        val = self.fmtStr % ((self.markerPlacedAt + self.low) * self.autoRescaleFactor )
                    self.accept.setText(val)
                elif self.markerPlacedAt is not False:
                    self.accept.setText(self.acceptText)

        # handle key responses:
        if not self.mouseOnly:
            for key in event.getKeys():
                if key in self.escapeKeys:
                    core.quit()
                if key in self.skipKeys:
                    self.markerPlacedAt = None
                    self.noResponse = False
                if self.enableRespKeys and key in self.respKeys: # place the marker at the corresponding tick
                    self.markerPlaced = True
                    self.markerPlacedAt = self._getMarkerFromTick(int(key))
                    self.marker.setPos([self.displaySizeFactor *
                                        (-0.5 + self.markerPlacedAt / self.tickMarks), 0])
                    if self.singleClick and self.myClock.getTime() > self.minimumTime:
                        self.noResponse = False
                        self.marker.setPos((0, self.offsetVert), '+')
                        logging.data('RatingScale %s: (key single-click) rating=%s' %
                                     (self.name, unicode(self.getRating())) )
                if key in self.leftKeys:
                    if self.markerPlaced and self.markerPlacedAt > 0:
                        self.markerPlacedAt = max(0, self.markerPlacedAt - 1. / self.autoRescaleFactor / self.precision)
                if key in self.rightKeys:
                    if self.markerPlaced and self.markerPlacedAt < self.tickMarks:
                        self.markerPlacedAt = min(self.tickMarks, self.markerPlacedAt +
                                                  1. / self.autoRescaleFactor / self.precision)
                if (self.markerPlaced and key in self.acceptKeys and self.myClock.getTime() > self.minimumTime):
                    self.noResponse = False
                    logging.data('RatingScale %s: (key response) rating=%s' %
                                     (self.name, unicode(self.getRating())) )

        # handle mouse:
        if self.myMouse.getPressed()[0]: # if mouse (left click) is pressed...
            #mouseX, mouseY = self.myMouse.getPos() # done above
            if pointInPolygon(mouseX, mouseY, self.nearLine): # if near the line, place the marker there:
                self.markerPlaced = True
                self.markerPlacedAt = self._getMarkerFromPos(mouseX)
                if (self.singleClick and self.myClock.getTime() > self.minimumTime):
                    self.noResponse = False
                    logging.data('RatingScale %s: (mouse single-click) rating=%s' %
                                 (self.name, unicode(self.getRating())) )
            # if in accept box, and a value has been selected, and enough time has elapsed:
            if self.showAccept:
                if (self.markerPlaced and self.myClock.getTime() > self.minimumTime and
                        self.acceptBox.contains(mouseX, mouseY)):
                    self.noResponse = False # accept the currently marked value
                    logging.data('RatingScale %s: (mouse response) rating=%s' %
                                (self.name, unicode(self.getRating())) )

        # decision time = time from the first .draw() to when 'accept' was pressed:
        if not self.noResponse and self.decisionTime == 0:
            self.decisionTime = self.myClock.getTime()
            logging.data('RatingScale %s: rating RT=%.3f' % (self.name, self.decisionTime))
            # only set this once: at the time 'accept' is indicated by subject
            # minimum time is enforced during key and mouse handling
            self.status = FINISHED

        # restore user's units:
        self.win.units = self.savedWinUnits

    def reset(self):
        """Restores the rating-scale to its post-creation state, status NOT_STARTED.

        Does not restore the scale text description (such reset is needed between
        items when rating multiple items)
        """
        # only resets things that are likely to have changed when the ratingScale instance is used by a subject
        self.noResponse = True
        self.markerPlaced = False
        self.markerPlacedAt = False
        #NB markerStart could be 0; during __init__, its forced to be numeric and valid, or None (not boolean)
        if self.markerStart != None:
            self.markerPlaced = True
            self.markerPlacedAt = self.markerStart - self.low # __init__ assures this is valid
        self.firstDraw = True # triggers self.myClock.reset() at start of draw()
        self.decisionTime = 0
        self.markerPosFixed = False
        self.frame = 0 # a counter used only to 'pulse' the 'accept' box
        if self.showAccept:
            self.acceptBox.setFillColor(self.acceptFillColor, 'rgb')
            self.acceptBox.setLineColor(self.acceptLineColor, 'rgb')
            self.accept.setColor('#444444','rgb') # greyed out
            self.accept.setText(self.keyClick)
        logging.exp('RatingScale %s: reset()' % self.name)
        self.status = NOT_STARTED

    def getRating(self):
        """Returns the numerical rating.
        None if the subject skipped this item; False if not available.
        """
        if self.noResponse:
            return False
        if not type(self.markerPlacedAt) in [float, int]:
            return None # eg, if skipped a response

        if self.precision == 1: # set type for the response, based on what was wanted
            response = int(self.markerPlacedAt * self.autoRescaleFactor) + self.low
        else:
            response = float(self.markerPlacedAt) * self.autoRescaleFactor + self.low
        if self.choices:
            response = self.choices[response]
            # retains type as given by experimenter, eg, str bool etc
            # boolean False will have an RT value, however
        return response

    def getRT(self):
        """Returns the seconds taken to make the rating (or to indicate skip).
        Returns None if no rating available. or maxTime if the response timed out.
        """
        if self.noResponse:
            if self.timedOut:
                return self.maximumTime
            return None
        return self.decisionTime

class Aperture:
    """Restrict a stimulus visibility area to a basic shape (circle, square, triangle)

    When enabled, any drawing commands will only operate on pixels within the
    Aperture. Once disabled, subsequent draw operations affect the whole screen
    as usual.

    See demos/stimuli/aperture.py for example usage

    :Author:
        2011, Yuri Spitsyn
        2011, Jon Peirce added units options, Jeremy Gray added shape & orientation
    """
    def __init__(self, win, size, pos=(0,0), ori=0, nVert=120, shape='circle', units=None,
            name='', autoLog=True):
        self.win=win
        self.name = name
        self.autoLog=autoLog

        #unit conversions
        if units!=None and len(units): self.units = units
        else: self.units = win.units
        if self.units in ['norm','height']: self._winScale=self.units
        else: self._winScale='pix' #set the window to have pixels coords

        if shape.lower() == 'square':
            ori += 45
            nVert = 4
        elif shape.lower() == 'triangle':
            nVert = 3
        self.ori = ori
        self.nVert = 120
        if type(nVert) == int:
            self.nVert = nVert
        self.quad=GL.gluNewQuadric() #needed for gluDisk
        self.setSize(size, needReset=False)
        self.setPos(pos, needReset=False)
        self._reset()#implicitly runs an self.enable()
    def _reset(self):
        self.enable()
        GL.glClearStencil(0)
        GL.glClear(GL.GL_STENCIL_BUFFER_BIT)

        GL.glPushMatrix()
        self.win.setScale(self._winScale)
        GL.glTranslatef(self._posRendered[0], self._posRendered[1], 0)
        GL.glRotatef(-self.ori, 0.0, 0.0, 1.0)

        GL.glDisable(GL.GL_LIGHTING)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(GL.GL_FALSE)

        GL.glStencilFunc(GL.GL_NEVER, 0, 0)
        GL.glStencilOp(GL.GL_INCR, GL.GL_INCR, GL.GL_INCR)
        GL.glColor3f(0,0,0)
        GL.gluDisk(self.quad, 0, self._sizeRendered/2.0, self.nVert, 2)
        GL.glStencilFunc(GL.GL_EQUAL, 1, 1)
        GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_KEEP)

        GL.glPopMatrix()

    def setSize(self, size, needReset=True, log=True):
        """Set the size (diameter) of the Aperture
        """
        self.size = size
        self._calcSizeRendered()
        if needReset: self._reset()
        if log and self.autoLog:
             self.win.logOnFlip("Set %s size=%s" %(self.name, size),
                 level=logging.EXP,obj=self)
    def setPos(self, pos, needReset=True, log=True):
        """Set the pos (centre) of the Aperture
        """
        self.pos = numpy.array(pos)
        self._calcPosRendered()
        if needReset: self._reset()
        if log and self.autoLog:
             self.win.logOnFlip("Set %s pos=%s" %(self.name, pos),
                 level=logging.EXP,obj=self)
    def _calcSizeRendered(self):
        """Calculate the size of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix', 'height']: self._sizeRendered=self.size
        elif self.units in ['deg', 'degs']: self._sizeRendered=psychopy.misc.deg2pix(self.size, self.win.monitor)
        elif self.units=='cm': self._sizeRendered=psychopy.misc.cm2pix(self.size, self.win.monitor)
        else:
            logging.ERROR("Stimulus units should be 'height', 'norm', 'deg', 'cm' or 'pix', not '%s'" %self.units)
    def _calcPosRendered(self):
        """Calculate the pos of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix', 'height']: self._posRendered=self.pos
        elif self.units in ['deg', 'degs']: self._posRendered=psychopy.misc.deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm': self._posRendered=psychopy.misc.cm2pix(self.pos, self.win.monitor)
    def enable(self):
        """Enable the aperture so that it is used in future drawing operations

        NB. The Aperture is enabled by default, when created.

        """
        GL.glEnable(GL.GL_STENCIL_TEST)
        self.enabled=True#by default
        self.status=STARTED
    def disable(self):
        """Disable the Aperture. Any subsequent drawing operations will not be
        affected by the aperture until re-enabled.
        """
        GL.glDisable(GL.GL_STENCIL_TEST)
        self.enabled=False
        self.status=STOPPED
    def __del__(self):
        self.disable()

class CustomMouse():
    """Class for more control over the mouse, including the pointer graphic and bounding box.

    Seems to work with pyglet or pygame. Not completely tested.

    Known limitations:
    - only norm units are working
    - getRel() always returns [0,0]
    - mouseMoved() is always False; maybe due to self.mouse.visible == False -> held at [0,0]
    - no idea if clickReset() works

    Author: Jeremy Gray, 2011
    """
    def __init__(self, win, newPos=None, visible=True,
                 leftLimit=None, topLimit=None, rightLimit=None, bottomLimit=None,
                 showLimitBox=False, clickOnUp=False,
                 pointer=None):
        """Class for customizing the appearance and behavior of the mouse.

        Use a custom mouse for extra control over the pointer appearance and function.
        Its probably slower to render than the regular system mouse.
        Create your `visual.Window` before creating a CustomMouse.

        :Parameters:
            win : required, `visual.Window`
                the window to which this mouse is attached
            visible : **True** or False
                makes the mouse invisbile if necessary
            newPos : **None** or [x,y]
                gives the mouse a particular starting position (pygame or pyglet)
            leftLimit :
                left edge of a virtual box within which the mouse can move
            topLimit :
                top edge of virtual box
            rightLimit :
                right edge of virtual box
            bottomLimit :
                lower edge of virtual box
            showLimitBox : default is False
                display the boundary of the area within which the mouse can move.
            pointer :
                The visual display item to use as the pointer; must have .draw()
                and setPos() methods. If your item has .setOpacity(), you can
                alter the mouse's opacity.
            clickOnUp : when to count a mouse click as having occured
                default is False, record a click when the mouse is first pressed
                down. True means record a click when the mouse button is released.
        :Note:
            CustomMouse is a new feature, and subject to change. `setPos()` does
            not work yet. `getRel()` returns `[0,0]` and `mouseMoved()` always
            returns `False`. `clickReset()` may not be working.
        """
        self.win = win
        self.mouse = event.Mouse(win=self.win)

        # maybe inheriting from Mouse would be easier? its not that simple
        self.getRel = self.mouse.getRel
        self.getWheelRel = self.mouse.getWheelRel
        self.mouseMoved = self.mouse.mouseMoved  # FAILS
        self.mouseMoveTime = self.mouse.mouseMoveTime
        self.getPressed = self.mouse.getPressed
        self.clickReset = self.mouse.clickReset  # ???
        self._pix2windowUnits = self.mouse._pix2windowUnits
        self._windowUnits2pix = self.mouse._windowUnits2pix

        # the graphic to use as the 'mouse' icon (pointer)
        if pointer:
            self.setPointer(pointer)
        else:
            #self.pointer = TextStim(win, text='+')
            self.pointer = ImageStim(win,
                    image=os.path.join(os.path.split(__file__)[0], 'pointer.png'))
        self.mouse.setVisible(False) # hide the actual (system) mouse
        self.visible = visible # the custom (virtual) mouse

        self.leftLimit = self.rightLimit = None
        self.topLimit = self.bottomLimit = None
        self.setLimit(leftLimit=leftLimit, topLimit=topLimit,
                      rightLimit=rightLimit, bottomLimit=bottomLimit)
        self.showLimitBox = showLimitBox

        self.lastPos = None
        self.prevPos = None
        if newPos is not None:
            self.lastPos = newPos
        else:
            self.lastPos = self.mouse.getPos()

        # for counting clicks:
        self.clickOnUp = clickOnUp
        self.wasDown = False # state of mouse 1 frame prior to current frame, look for changes
        self.clicks = 0 # how many mouse clicks since last reset
        self.clickButton = 0 # which button to count clicks for; 0 = left

    def _setPos(self, pos=None):
        """internal mouse position management. setting a position here leads to
        the virtual mouse being out of alignment with the hardware mouse, which
        leads to an 'invisible wall' effect for the mouse.
        """
        if pos is None:
            pos = self.getPos()
        else:
            self.lastPos = pos
        self.pointer.setPos(pos)
    def setPos(self, pos):
        """Not implemented yet. Place the mouse at a specific position.
        """
        raise NotImplementedError('setPos is not available for custom mouse')
    def getPos(self):
        """Returns the mouse's current position.
        Influenced by changes in .getRel(), constrained to be in its virtual box.
        """
        dx, dy = self.getRel()
        x = min(max(self.lastPos[0] + dx, self.leftLimit), self.rightLimit)
        y = min(max(self.lastPos[1] + dy, self.bottomLimit), self.topLimit)
        self.lastPos = numpy.array([x,y])
        return self.lastPos
    def draw(self):
        """Draw mouse (if its visible), show the limit box, update the click count.
        """
        self._setPos()
        if self.showLimitBox:
            self.box.draw()
        if self.visible:
            self.pointer.draw()
        isDownNow = self.getPressed()[self.clickButton]
        if self.clickOnUp:
            if self.wasDown and not isDownNow: # newly up
                self.clicks += 1
        else:
            if not self.wasDown and isDownNow: # newly down
                self.clicks += 1
        self.wasDown = isDownNow
    def getClicks(self):
        """Return the number of clicks since the last reset"""
        return self.clicks
    def resetClicks(self):
        """Set click count to zero"""
        self.clicks = 0
    def getVisible(self):
        """Return the mouse's visibility state"""
        return self.visible
    def setVisible(self, visible):
        """Make the mouse visible or not (pyglet or pygame)."""
        self.visible = visible
    def setPointer(self, pointer):
        """Set the visual item to be drawn as the mouse pointer."""
        if hasattr(pointer, 'draw') and hasattr(pointer, 'setPos'):
            self.pointer = pointer
        else:
            raise AttributeError, "need .draw() and .setPos() methods in pointer"
    def setLimit(self, leftLimit=None, topLimit=None, rightLimit=None, bottomLimit=None):
        """Set the mouse's bounding box by specifying the edges."""
        if type(leftLimit) in [int,float]:
            self.leftLimit = leftLimit
        elif self.leftLimit is None:
            self.leftLimit = -1
            if self.win.units == 'pix':
                self.leftLimit = self.win.size[0]/-2.
        if type(rightLimit) in [int,float]:
            self.rightLimit = rightLimit
        elif self.rightLimit is None:
            self.rightLimit = .99
            if self.win.units == 'pix':
                self.rightLimit = self.win.size[0]/2. - 5
        if type(topLimit) in [int,float]:
            self.topLimit = topLimit
        elif self.topLimit is None:
            self.topLimit = 1
            if self.win.units == 'pix':
                self.topLimit = self.win.size[1]/2.
        if type(bottomLimit) in [int,float]:
            self.bottomLimit = bottomLimit
        elif self.bottomLimit is None:
            self.bottomLimit = -0.98
            if self.win.units == 'pix':
                self.bottomLimit = self.win.size[1]/-2. + 10

        self.box = psychopy.visual.ShapeStim(self.win,
                    vertices=[[self.leftLimit,self.topLimit],[self.rightLimit,self.topLimit],
                        [self.rightLimit,self.bottomLimit],
                        [self.leftLimit,self.bottomLimit],[self.leftLimit,self.topLimit]],
                    opacity=0.35)

        # avoid accumulated relative-offsets producing a different effective limit:
        self.mouse.setVisible(True)
        self.lastPos = self.mouse.getPos() # hardware mouse's position
        self.mouse.setVisible(False)

def makeRadialMatrix(matrixSize):
    """Generate a square matrix where each element val is
    its distance from the centre of the matrix
    """
    oneStep = 2.0/(matrixSize-1)
    xx,yy = numpy.mgrid[0:2+oneStep:oneStep, 0:2+oneStep:oneStep] -1.0 #NB need to add one step length because
    rad = numpy.sqrt(xx**2 + yy**2)
    return rad

def createTexture(tex, id, pixFormat, stim, res=128, maskParams=None, forcePOW2=True):
    """
    id is the texture ID
    pixFormat = GL.GL_ALPHA, GL.GL_RGB
    useShaders is a bool
    interpolate is a bool (determines whether texture will use GL_LINEAR or GL_NEAREST
    res is the resolution of the texture (unless a bitmap image is used)

    For grating stimuli (anything that needs multiple cycles) forcePOW2 should
    be set to be True. Otherwise the wrapping of the texture will not work.

    """

    """
    Create an intensity texture, ranging -1:1.0
    """
    global _nImageResizes
    notSqr=False #most of the options will be creating a sqr texture
    useShaders = stim._useShaders
    interpolate = stim.interpolate
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
    elif tex == "gauss":
        rad=makeRadialMatrix(res)
        sigma = 1/3.0;
        intensity = numpy.exp( -rad**2.0 / (2.0*sigma**2.0) )*2-1 #3sd.s by the edge of the stimulus
        fromFile=0
    elif tex == "radRamp":#a radial ramp
        rad=makeRadialMatrix(res)
        intensity = 1-2*rad
        intensity = numpy.where(rad<-1, intensity, -1)#clip off the corners (circular)
        fromFile=0

    elif tex == "raisedCos": # A raised cosine
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
        stim.origSize=im.size
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
                elif _nImageResizes==reportNImageResizes:
                    logging.warning("Multiple images have needed resizing - I'll stop bothering you!")
                _nImageResizes+=1
                im=im.resize([powerOf2,powerOf2],Image.BILINEAR)

        #is it Luminance or RGB?
        if im.mode=='L':
            wasLum = True
            intensity= numpy.array(im).astype(numpy.float32)*0.0078431372549019607-1.0 # 2/255-1.0 == get to range -1:1
        elif pixFormat==GL.GL_ALPHA:#we have RGB and need Lum
            wasLum = True
            im = im.convert("L")#force to intensity (in case it was rgb)
            intensity= numpy.array(im).astype(numpy.float32)*0.0078431372549019607-1.0 # much faster to avoid division 2/255
        elif pixFormat==GL.GL_RGB:#we have RGB and keep it that way
            #texture = im.tostring("raw", "RGB", 0, -1)
            im = im.convert("RGBA")#force to rgb (in case it was CMYK or L)
            intensity = numpy.array(im).astype(numpy.float32)*0.0078431372549019607-1
            wasLum=False

    if pixFormat==GL.GL_RGB and wasLum and useShaders:
        #keep as float32 -1:1
        if sys.platform!='darwin' and stim.win.glVendor.startswith('nvidia'):
            #nvidia under win/linux might not support 32bit float
            internalFormat = GL.GL_RGB16F_ARB #could use GL_LUMINANCE32F_ARB here but check shader code?
        else:#we've got a mac or an ATI card and can handle 32bit float textures
            internalFormat = GL.GL_RGB32F_ARB #could use GL_LUMINANCE32F_ARB here but check shader code?
        dataType = GL.GL_FLOAT
        data = numpy.ones((intensity.shape[0],intensity.shape[1],3),numpy.float32)#initialise data array as a float
        data[:,:,0] = intensity#R
        data[:,:,1] = intensity#G
        data[:,:,2] = intensity#B
    elif pixFormat==GL.GL_RGB and wasLum:#and not using shaders
        #scale by rgb and convert to ubyte
        internalFormat = GL.GL_RGB
        dataType = GL.GL_UNSIGNED_BYTE
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
        data = psychopy.misc.float_uint8(stim.contrast*data)
    elif pixFormat==GL.GL_RGB and useShaders:#not wasLum
        internalFormat = GL.GL_RGB32F_ARB
        dataType = GL.GL_FLOAT
        data = intensity
    elif pixFormat==GL.GL_RGB:# not wasLum, not useShaders  - an RGB bitmap with no shader options
        internalFormat = GL.GL_RGB
        dataType = GL.GL_UNSIGNED_BYTE
        data = psychopy.misc.float_uint8(intensity)
    elif pixFormat==GL.GL_ALPHA and useShaders:# a mask with no shader options
        internalFormat = GL.GL_ALPHA
        dataType = GL.GL_UNSIGNED_BYTE
        data = psychopy.misc.float_uint8(intensity)
    elif pixFormat==GL.GL_ALPHA:# not wasLum, not useShaders  - a mask with no shader options
        internalFormat = GL.GL_ALPHA
        dataType = GL.GL_UNSIGNED_BYTE
        #can't use float_uint8 - do it manually
        data = numpy.around(255*stim.opacity*(0.5+0.5*intensity)).astype(numpy.uint8)
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

def pointInPolygon(x, y, poly):
    """Determine if a point (`x`, `y`) is inside a polygon, using the ray casting method.

    `poly` is a list of 3+ vertices as (x,y) pairs.
    If given a `ShapeStim`-based object, will use the
    rendered vertices and position as the polygon.

    Returns True (inside) or False (outside). Used by :class:`~psychopy.visual.ShapeStim` `.contains()`
    """
    # looks powerful but has a C dependency: http://pypi.python.org/pypi/Shapely
    # see also https://github.com/jraedler/Polygon2/

    if hasattr(poly, '_verticesRendered') and hasattr(poly, '_posRendered'):
        poly = poly._verticesRendered + poly._posRendered
    nVert = len(poly)
    if nVert < 3:
        msg = 'pointInPolygon expects a polygon with 3 or more vertices'
        logging.warning(msg)
        return False

    # faster if have matplotlib.nxutils:
    if haveNxutils:
        return bool(nxutils.pnpoly(x, y, poly))

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

    # faster if have matplotlib.nxutils:
    if haveNxutils:
        if any(nxutils.points_inside_poly(poly1, poly2)):
            return True
        return any(nxutils.points_inside_poly(poly2, poly1))

    # fall through to pure python:
    for p1 in poly1:
        if pointInPolygon(p1[0], p1[1], poly2):
            return True
    for p2 in poly2:
        if pointInPolygon(p2[0], p2[1], poly1):
            return True
    return False


def _setTexIfNoShaders(obj):
    """Useful decorator for classes that need to update Texture after other properties
    """
    if hasattr(obj, 'setTex') and hasattr(obj, '_texName') and not obj._useShaders:
        obj.setTex(obj._texName)

def _setColor(self, color, colorSpace=None, operation='',
                rgbAttrib='rgb', #or 'fillRGB' etc
                colorAttrib='color', #or 'fillColor' etc
                colorSpaceAttrib=None, #e.g. 'colorSpace' or 'fillColorSpace'
                log=True):
    """Provides the workings needed by setColor, and can perform this for
    any arbitrary color type (e.g. fillColor,lineColor etc)
    """

    #how this works:
    #rather than using self.rgb=rgb this function uses setattr(self,'rgb',rgb)
    #color represents the color in the native space
    #colorAttrib is the name that color will be assigned using setattr(self,colorAttrib,color)
    #rgb is calculated from converting color
    #rgbAttrib is the attribute name that rgb is stored under, e.g. lineRGB for self.lineRGB
    #colorSpace and takes name from colorAttrib+space e.g. self.lineRGBSpace=colorSpace
    try:
        color=float(color)
        isScalar=True
    except:
        isScalar=False

    if colorSpaceAttrib==None:
        colorSpaceAttrib = colorAttrib+'Space'

    if type(color) in [str, unicode, numpy.string_]:
        if color.lower() in colors.colors255.keys():
            #set rgb, color and colorSpace
            setattr(self,rgbAttrib,numpy.array(colors.colors255[color.lower()], float))
            setattr(self,colorSpaceAttrib,'named')#e.g. self.colorSpace='named'
            setattr(self,colorAttrib,color) #e.g. self.color='red'
            _setTexIfNoShaders(self)
            return
        elif color[0]=='#' or color[0:2]=='0x':
            setattr(self,rgbAttrib,numpy.array(colors.hex2rgb255(color)))#e.g. self.rgb=[0,0,0]
            setattr(self,colorAttrib,color) #e.g. self.color='#000000'
            setattr(self,colorSpaceAttrib,'hex')#e.g. self.colorSpace='hex'
            _setTexIfNoShaders(self)
            return
#                except:
#                    pass#this will be handled with AttributeError below
        #we got a string, but it isn't in the list of named colors and doesn't work as a hex
        raise AttributeError("PsychoPy can't interpret the color string '%s'" %color)
    elif isScalar:
        color = numpy.asarray([color,color,color],float)
    elif type(color) in [tuple,list]:
        color = numpy.asarray(color,float)
    elif type(color) ==numpy.ndarray:
        pass
    elif color==None:
        setattr(self,rgbAttrib,None)#e.g. self.rgb=[0,0,0]
        setattr(self,colorAttrib,None) #e.g. self.color='#000000'
        setattr(self,colorSpaceAttrib,None)#e.g. self.colorSpace='hex'
        _setTexIfNoShaders(self)
    else:
        raise AttributeError("PsychoPy can't interpret the color %s (type=%s)" %(color, type(color)))

    #at this point we have a numpy array of 3 vals (actually we haven't checked that there are 3)
    #check if colorSpace is given and use self.colorSpace if not
    if colorSpace==None: colorSpace=getattr(self,colorSpaceAttrib)
    #check whether combining sensible colorSpaces (e.g. can't add things to hex or named colors)
    if operation!='' and getattr(self,colorSpaceAttrib) in ['named','hex']:
            raise AttributeError("setColor() cannot combine ('%s') colors within 'named' or 'hex' color spaces"\
                %(operation))
    elif operation!='' and colorSpace!=getattr(self,colorSpaceAttrib) :
            raise AttributeError("setColor cannot combine ('%s') colors from different colorSpaces (%s,%s)"\
                %(operation, self.colorSpace, colorSpace))
    else:#OK to update current color
        exec('self.%s %s= color' %(colorAttrib, operation))#if no operation then just assign
    #get window (for color conversions)
    if colorSpace in ['dkl','lms']: #only needed for these spaces
        if hasattr(self,'dkl_rgb'): win=self #self is probably a Window
        elif hasattr(self, 'win'): win=self.win #self is probably a Stimulus
        else:
            win=None
            logging.error("_setColor() is being applied to something that has no known Window object")
    #convert new self.color to rgb space
    newColor=getattr(self, colorAttrib)
    if colorSpace in ['rgb','rgb255']: setattr(self,rgbAttrib, newColor)
    elif colorSpace=='dkl':
        if numpy.all(win.dkl_rgb==numpy.ones([3,3])):dkl_rgb=None
        else: dkl_rgb=win.dkl_rgb
        setattr(self,rgbAttrib, colors.dkl2rgb(numpy.asarray(newColor).transpose(), dkl_rgb) )
    elif colorSpace=='lms':
        logging.error("The automated calibration routine for LMS space in PsychoPy is currently suspect." +\
                      " We would STRONGLY recommend you don't use this space for now (contact Jon for further info)")
        if numpy.all(win.lms_rgb==numpy.ones([3,3])):lms_rgb=None
        else: lms_rgb=win.lms_rgb
        setattr(self,rgbAttrib, colors.lms2rgb(newColor, lms_rgb) )
    elif colorSpace=='hsv':
        setattr(self,rgbAttrib, colors.hsv2rgb(numpy.asarray(newColor)) )
    else: logging.error('Unknown colorSpace: %s' %colorSpace)
    setattr(self,colorSpaceAttrib, colorSpace)#store name of colorSpace for future ref and for drawing
    #if needed, set the texture too
    _setTexIfNoShaders(self)

    if log:
        if hasattr(self,'win'):
            self.win.logOnFlip("Set %s.%s=%s (%s)" %(self.name,colorAttrib,newColor,colorSpace),
                level=logging.EXP,obj=self)
        else:
            self.logOnFlip("Set Window %s=%s (%s)" %(colorAttrib,newColor,colorSpace),
                level=logging.EXP,obj=self)
def getMsPerFrame(myWin, nFrames=60, showVisual=False, msg='', msDelay=0.):
    """Assesses the monitor refresh rate (average, median, SD) under current conditions, over at least 60 frames.

    Records time for each refresh (frame) for n frames (at least 60), while displaying an optional visual.
    The visual is just eye-candy to show that something is happening when assessing many frames. You can
    also give it text to display instead of a visual,
    e.g., msg='(testing refresh rate...)'; setting msg implies showVisual == False.
    To simulate refresh rate under cpu load, you can specify a time to wait within the loop prior to
    doing the win.flip(). If 0 < msDelay < 100, wait for that long in ms.

    Returns timing stats (in ms) of:
    - average time per frame, for all frames
    - standard deviation of all frames
    - median, as the average of 12 frame times around the median (~monitor refresh rate)

    :Author:
        - 2010 written by Jeremy Gray
    """

    #from psychopy import visual # which imports core, so currently need to do here in core.msPerFrame()

    nFrames = max(60, nFrames)  # lower bound of 60 samples--need enough to estimate the SD
    num2avg = 12  # how many to average from around the median
    if len(msg):
        showVisual = False
        showText = True
        myMsg = TextStim(myWin, text=msg, italic=True,
                            color=(.7,.6,.5),colorSpace='rgb', height=0.1)
    else:
        showText = False
    if showVisual:
        x,y = myWin.size
        myStim = GratingStim(myWin, tex='sin', mask='gauss',
            size=[.6*y/float(x),.6], sf=3.0, opacity=.2,
            autoLog=False)
    clockt = [] # clock times
    drawt  = [] # end of drawing time, in clock time units, for testing how long myStim.draw() takes

    if msDelay > 0 and msDelay < 100:
        doWait = True
        delayTime = msDelay/1000. #sec
    else:
        doWait = False

    winUnitsSaved = myWin.units
    myWin.units = 'norm' # norm is required for the visual (or text) display, as coded below

    # accumulate secs per frame (and time-to-draw) for a bunch of frames:
    rush(True)
    for i in range(5): # wake everybody up
        myWin.flip()
    for i in range(nFrames): # ... and go for real this time
        clockt.append(core.getTime())
        if showVisual:
            myStim.setPhase(1.0/nFrames, '+')
            myStim.setSF(3./nFrames, '+')
            myStim.setOri(12./nFrames,'+')
            myStim.setOpacity(.9/nFrames, '+')
            myStim.draw()
        elif showText:
            myMsg.draw()
        if doWait:
            core.wait(delayTime)
        drawt.append(core.getTime())
        myWin.flip()
    rush(False)

    myWin.units = winUnitsSaved # restore

    frameTimes = [(clockt[i] - clockt[i-1]) for i in range(1,len(clockt))]
    drawTimes  = [(drawt[i] - clockt[i]) for i in range(len(clockt))] # == drawing only
    freeTimes = [frameTimes[i] - drawTimes[i] for i in range(len(frameTimes))] # == unused time

    # cast to float so that the resulting type == type(0.123)
    frameTimes.sort() # for median
    msPFmed = 1000. * float(numpy.average(frameTimes[ (nFrames-num2avg)/2 : (nFrames+num2avg)/2 ])) # median-most slice
    msPFavg = 1000. * float(numpy.average(frameTimes))
    msPFstd = 1000. * float(numpy.std(frameTimes))
    msdrawAvg = 1000. * float(numpy.average(drawTimes))
    msdrawSD = 1000. * float(numpy.std(drawTimes))
    msfree = 1000. * float(numpy.average(freeTimes))

    return msPFavg, msPFstd, msPFmed #, msdrawAvg, msdrawSD, msfree




