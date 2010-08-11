"""To control the screen and visual stimuli for experiments
"""
# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy #so we can get the __path__
from psychopy import core, ext, log, preferences, monitors, event
import colors
import psychopy.event
#misc must only be imported *after* event or MovieStim breaks on win32 (JWP has no idea why!)
import psychopy.misc
import Image
import sys, os, platform, time, glob, copy
import makeMovies

import numpy
from numpy import sin, cos, pi

from psychopy.ext import rush as rush

prefs = preferences.Preferences()#load the site/user config files

#shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
try:
    import ctypes
    import pyglet
    #pyglet.options['debug_gl'] = False#must be done before importing pyglet.gl or pyglet.window
    import pyglet.gl, pyglet.window, pyglet.image, pyglet.font, pyglet.media, pyglet.event
    import _shadersPyglet
    import gamma
    havePyglet=True
except:
    havePyglet=False
    
#import _shadersPygame
try:
    import OpenGL.GL, OpenGL.GL.ARB.multitexture, OpenGL.GLU
    import pygame
    havePygame=True
    if OpenGL.__version__ > '3':
        cTypesOpenGL = True
    else:
        cTypesOpenGL = False
except:
    havePygame=False

global GL, GLU, GL_multitexture, _shaders#will use these later to assign the pyglet or pyopengl equivs

#check for advanced drawing abilities
#actually FBO isn't working yet so disable
try:
    import OpenGL.GL.EXT.framebuffer_object as FB
    haveFB=False
except:
    haveFB=False


#try to get GLUT
try:
    from OpenGL import GLUT
    haveGLUT=True
except:
    log.warning('GLUT not available - is the GLUT library installed on the path?')
    haveGLUT=False

global DEBUG; DEBUG=False

_depthIncrements = {'pyglet':+0.001, 'pygame':-0.001, 'glut':-0.001}

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
                 waitBlanking=True):
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
            units :  *None*, 'norm' (normalised),'deg','cm','pix'
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
            gamma : 1.0, 
                Monitor gamma for linearisation (will use Bits++ if possible). Overrides monitor settings
            bitsMode : None, 'fast', ('slow' mode is deprecated). 
                Defines how (and if) the Bits++ box will be used. 'fast' updates every frame by drawing a hidden line on the top of the screen.
            
            :note: Preferences. Some parameters (e.g. units) can now be given default values in the user/site preferences and these will be used if None is given here. If you do specify a value here it will take precedence over preferences.
        
        """
        self.size = numpy.array(size, numpy.int)
        self.pos = pos    
        self.winHandle=None#this will get overridden once the window is created
        
        self.colorSpace=colorSpace
        if rgb!=None:
            log.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb')
        elif dkl!=None:
            log.warning("Use of dkl arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(dkl, colorSpace='dkl')
        elif lms!=None:
            log.warning("Use of lms arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(lms, colorSpace='lms')
        else:
            self.setColor(color, colorSpace=colorSpace)
            
        self._defDepth=0.0
        
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
        
        #color conversions
        dkl_rgb = self.monitor.getDKL_RGB()
        if dkl_rgb!=None:
            self.dkl_rgb=dkl_rgb
        else: self.dkl_rgb = None
        lms_rgb = self.monitor.getLMS_RGB()
        if lms_rgb!=None:
            self.lms_rgb=lms_rgb
        else: self.lms_rgb = None
        
        #check whether FBOs are supported
        if blendMode=='add' and not haveFB:
            log.warning("""User requested a blendmode of "add" but framebuffer objects not available. You need PyOpenGL3.0+ to use this blend mode""")
            self.blendMode='average' #resort to the simpler blending without float rendering
        else: self.blendMode=blendMode
        
        #setup context and openGL()
        if winType==None:#choose the default windowing
            self.winType=prefs.general['winType']
        else:
            self.winType = winType
        if self.winType=='pyglet' and not havePyglet:
            log.warning("Requested pyglet backend but pyglet is not installed or not fully working")
            self.winType='pygame'
        if self.winType=='pygame' and not havePygame:
            log.warning("Requested pygame backend but pygame (or PyOpenGL) is not installed or not fully working")
            self.winType='pyglet'
        #setup the context
        if self.winType == "glut": self._setupGlut()
        elif self.winType == "pygame": self._setupPygame()
        elif self.winType == "pyglet": 
            self._setupPyglet()
        
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
        self.frameIntervals=[]
        
        self._refreshThreshold=1/50.0
        
        if self.useNativeGamma:
            log.info('Using gamma table of operating system')
        else:
            log.info('Using gamma: self.gamma' + str(self.gamma))
            self.setGamma(self.gamma)#using either pygame or bits++
        self.lastFrameT = core.getTime()
        
        if self.units=='norm':  self.setScale('norm')
        else: self.setScale('pix')
        
        self.waitBlanking = waitBlanking
        #but override if not possible:
        if sys.platform not in ['darwin','win32']:
            self.waitBlanking=False
        if sys.platform=='darwin' and platform.mac_ver()[0]>='10.6':
            self.waitBlanking=False#Snow leopard doesn't support this?
        self.flip()#do a screen refresh straight away

    def setRecordFrameIntervals(self, value=True):
        """To provide accurate measures of frame intervals, to determine whether frames
        are being dropped. Set this to False while the screen is not being updated
        e.g. during event.waitkeys() and set to True during critical parts of the script
        
        see also:
            Window.saveFrameIntervals()
        """
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
    def whenIdle(self,func):
        """Defines the function to use during idling (GLUT only)
        """
        GLUT.glutIdleFunc(func)
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
    
    def flip(self, clearBuffer=True):
        """Flip the front and back buffers after drawing everything for your frame.
        (This replaces the win.update() method, better reflecting what is happening underneath).
        
        win.flip(clearBuffer=True)#results in a clear screen after flipping        
        win.flip(clearBuffer=False)#the screen is not cleared (so represent the previous screen)
        """
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
        if self.bitsMode == 'fast':
            self.bits._drawLUTtoScreen()

        if self.winType == "glut": GLUT.glutSwapBuffers()
        elif self.winType =="pyglet":
            #print "updating pyglet"
            #make sure this is current context            
            self.winHandle.switch_to()
            
            GL.glTranslatef(0.0,0.0,-5.0)

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
                
        if self.recordFrameIntervals:
            self.frames +=1
            now = core.getTime()
            deltaT = now - self.lastFrameT; self.lastFrameT=now                
            self.frameIntervals.append(deltaT)
            
            if deltaT>self._refreshThreshold \
                and (numpy.average(self.frameIntervals[-2:]))>self._refreshThreshold : #often a long frame is making up for a short frame
                    log.warning('t of last frame was %.2fms (=1/%i)' %(deltaT*1000, 1/deltaT))
                    
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
        
        if self.waitBlanking:
            ext.waitForVBL()

    def update(self):
        """Deprecated: use Window.flip() instead        
        """
        self.flip(clearBuffer=True)#clearBuffer was the original behaviour for win.update()

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
        #GL.glLoadIdentity()
        #do the reading of the pixels
        if buffer=='back':
            GL.glReadBuffer(GL.GL_BACK)            
        else:
            GL.glReadBuffer(GL.GL_FRONT)
        
            #fetch the data with glReadPixels
        if self.winType=='pyglet':
            #pyglet.gl stores the data in a ctypes buffer
            bufferDat = (GL.GLubyte * (4 * self.size[0] * self.size[1]))()
            GL.glReadPixels(0,0,self.size[0],self.size[1], GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,bufferDat)
            im = Image.fromstring(mode='RGBA',size=self.size, data=bufferDat)
        else:
            #pyopengl returns the data
            im = Image.fromstring(mode='RGBA',size=self.size,
                              data=GL.glReadPixels(0,0,self.size[0],self.size[1], GL.GL_RGBA,GL.GL_UNSIGNED_BYTE),
                          )
            
        im=im.transpose(Image.FLIP_TOP_BOTTOM)            
        im=im.convert('RGB')
        self.movieFrames.append(im)

    def saveMovieFrames(self, fileName, mpgCodec='mpeg1video',
        fps=30):
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
            
        Examples::
            myWin.saveMovieFrames('frame.tif')#writes a series of static frames as frame001.tif, frame002.tif etc...
            myWin.saveMovieFrames('stimuli.mov', fps=25)#on OS X only
            myWin.saveMovieFrames('stimuli.gif')#but not great quality
            myWin.saveMovieFrames('stimuli.mpg')#not on OS X
            
        """
        fileRoot, fileExt = os.path.splitext(fileName)
        if len(self.movieFrames)==0:
            log.error('no frames to write - did you forget to update your window?')
            return
        else:
            log.info('writing %i frames' %len(self.movieFrames))
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
                mov.addFrame(frame, frameDuration)
        elif len(self.movieFrames)==1:
            self.movieFrames[0].save(fileName)
        else:
            frame_name_format = "%s%%0%dd%s" % (fileRoot, numpy.ceil(numpy.log10(len(self.movieFrames)+1)), fileExt)
            for frameN, thisFrame in enumerate(self.movieFrames):
               thisFileName = frame_name_format % (frameN+1,)
               thisFrame.save(thisFileName) 

    def fullScr(self):
        """Toggles fullscreen mode (GLUT only).

        Fullscreen mode for PyGame contexts must be set during initialisation
        of the :class:`~psychopy.visual.Window`
        """
        if self.winType=='glut':
            if self._isFullScr:
                GLUT.glutReshapeWindow(int(self.size[0]), int(self.size[1]))
                self._isFullScr=0
            else:
                GLUT.glutFullScreen()
                self._isFullScr=1
        else:
            log.warning('fullscreen toggling is only available to glut contexts')

    def close(self):
        """Close the window (and reset the Bits++ if necess)."""
        self.setMouseVisible(True)
        if self.winType=='GLUT':
            GLUT.glutDestroyWindow(self.handle)
        elif self.winType=='pyglet':
            self.winHandle.close()
        else:
            #pygame.quit()
            pygame.display.quit()
        if self.bitsMode!=None:
            self.bits.reset()
        
    def go(self):
        """start the display loop (GLUT only)"""
        self.frameClock.reset()
        GLUT.glutMainLoop()

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
        visible (the first uses the color to create the new screen the second presents
        that screen to the viewer).  
        
        See `colorSpaces`_ for further information about the ways to specify colors and their various implications.
        
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
            in one of the `colorSpaces`_. If no color space is specified then the color 
            space most recently used for this stimulus is used again.
            
                myStim.setColor([1.0,-1.0,-1.0], 'rgb')#a red color in rgb space
                myStim.setColor([0.0,45.0,1.0], 'dkl') #DKL space with elev=0, azimuth=45
                myStim.setColor([0,0,255], 'rgb255') #a blue stimulus using rgb255 space
            
            Lastly, a single number can be provided, x, which is equivalent to providing
            [x,x,x]. 
            
                myStim.setColor(255, 'rgb255') #all guns o max
            
        colorSpace : string or None
        
            defining which of the `colorSpaces`_ to use. For strings and hex
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
                    
        if self.winHandle!=None:#if it is None then this will be done during window setup
            if self.winType=='pyglet': self.winHandle.switch_to()
            GL.glClearColor((self.rgb[0]+1.0)/2.0, (self.rgb[1]+1.0)/2.0, (self.rgb[2]+1.0)/2.0, 1.0)
        
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

        The `units` can be 'norm'(normalised),'pix'(pixels),'cm' or
        'stroke_font'. The `font` parameter is only used if units='stroke_font'
        """
        if units=="norm":
            thisScale = numpy.array([1.0,1.0])
        elif units in ["pix", "pixels"]:
            thisScale = 2.0/numpy.array(self.size)
        elif units=="cm":
            #windowPerCM = windowPerPIX / CMperPIX
            #                       = (window      /winPIX)        / (scrCm                               /scrPIX)
            if (self.scrWidthCM in [0,None]) or (self.scrWidthPIX in [0, None]):
                log.error('you didnt give me the width of the screen (pixels and cm). Check settings in MonitorCentre.')
                core.wait(1.0); core.quit()
            thisScale = (numpy.array([2.0,2.0])/self.size)/(float(self.scrWidthCM)/float(self.scrWidthPIX))
        elif units in ["deg", "degs"]:
            #windowPerDeg = winPerCM*CMperDEG
            #               = winPerCM              * tan(pi/180) * distance
            if (self.scrWidthCM in [0,None]) or (self.scrWidthPIX in [0, None]):
                log.error('you didnt give me the width of the screen (pixels and cm). Check settings in MonitorCentre.')
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
            
    def _setupGlut(self):
        self.winType="glut"
        #initialise a window
        GLUT.glutInit(sys.argv)
        iconFile = os.path.join(psychopy.__path__[0], 'psychopy.gif')
        GLUT.glutSetIconTitle(iconFile)
        GLUT.glutInitDisplayMode(GLUT.GLUT_RGBA | GLUT.GLUT_DOUBLE | GLUT.GLUT_ALPHA | GLUT.GLUT_DEPTH)
        self.handle = GLUT.glutCreateWindow('PsychoPy')

        if self._isFullScr:      GLUT.glutFullScreen()
        else:  GLUT.glutReshapeWindow(int(self.size[0]), int(self.size[1]))
        #set the redisplay callback
        GLUT.glutDisplayFunc(self.update)
    def _setupPyglet(self):        
        global GL, GLU, GL_multitexture, _shaders#will use these later to assign the pyglet or pyopengl equivs
        self.winType = "pyglet"
        #setup the global use of pyglet.gl
        GL = pyglet.gl
        GLU = pyglet.gl
        GL_multitexture = pyglet.gl
        
        config = GL.Config(depth_size=8, double_buffer=True)
        allScrs = pyglet.window.get_platform().get_default_display().get_screens()
        if len(allScrs)>self.screen:
            thisScreen = allScrs[self.screen]
            log.info('configured pyglet screen %i' %self.screen)
        else: 
            log.error("Requested an unavailable screen number")
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
        #add these methods to the pyglet window                                  
        self.winHandle.setGamma = gamma.setGamma
        self.winHandle.setGammaRamp = gamma.setGammaRamp
        self.winHandle.getGammaRamp = gamma.getGammaRamp        
        self.winHandle.set_vsync(True)
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
            iconFile = os.path.join(psychopy.__path__[0], 'psychopy.png')
            icon = pyglet.image.load(filename=iconFile)
            self.winHandle.set_icon(icon)
        except: pass#doesn't matter
    def _checkMatchingSizes(self, requested,actual):
        """Checks whether the requested and actual screen sizes differ. If not
        then a warning is output and the window size is set to actual
        """  
        if list(requested)!=list(actual):
            log.warning("User requested fullscreen with size %s, but screen is actually %s. Using actual size" \
                %(requested, actual))
            self.size=numpy.array(actual)            
    def _setupPygame(self):
        self.winType = "pygame"
        global GL, GLU, GL_multitexture, _shaders#will use these later to assign the pyglet or pyopengl equivs
        
        #setup the global use of PyOpenGL (rather than pyglet.gl)
        GL = OpenGL.GL     
        GL_multitexture = OpenGL.GL.ARB.multitexture
        GLU = OpenGL.GLU
        #pygame.mixer.pre_init(22050,16,2)#set the values to initialise sound system if it gets used
        pygame.init()
            
        try: #to load an icon for the window
            iconFile = os.path.join(psychopy.__path__[0], 'psychopy.png')
            icon = pygame.image.load(iconFile)
            pygame.display.set_icon(icon)
        except: pass#doesn't matter

        winSettings = pygame.OPENGL|pygame.DOUBLEBUF#|pygame.OPENGLBLIT #these are ints stored in pygame.locals
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
        if self.winType=='pyglet': _shaders=_shadersPyglet
#        else: _shaders=_shadersPygame
        
        #do settings for openGL
        GL.glClearColor((self.rgb[0]+1.0)/2.0, (self.rgb[1]+1.0)/2.0, (self.rgb[2]+1.0)/2.0, 1.0)       # This Will Clear The Background Color To Black
        GL.glClearDepth(1.0)

        GL.glViewport(0, 0, int(self.size[0]), int(self.size[1]));

        GL.glMatrixMode(GL.GL_PROJECTION) # Reset The Projection Matrix
        GL.glLoadIdentity()                    
        if self.winType=='pyglet': GL.gluOrtho2D(-1,1,-1,1) 

        GL.glMatrixMode(GL.GL_MODELVIEW)# Reset The Projection Matrix
        GL.glLoadIdentity()                     
        
        GL.glEnable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
        GL.glDepthFunc(GL.GL_LESS)                      # The Type Of Depth Test To Do
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        
        GL.glShadeModel(GL.GL_SMOOTH)                   # Color Shading (FLAT or SMOOTH)
        GL.glEnable(GL.GL_POINT_SMOOTH)

        if self.winType!='pyglet':
            GL_multitexture.glInitMultitextureARB()
        else:
            #check for GL_ARB_texture_float (which is needed for shaders to be useful)
            #this needs to be done AFTER the context has been created
            if not pyglet.gl.gl_info.have_extension('GL_ARB_texture_float'):
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

        if sys.platform=='darwin':
            ext.darwin.syncSwapBuffers(1)

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
                                      GL.GL_TEXTURE_2D, self.frameTexture, 0);
        FB.glFramebufferRenderbufferEXT(FB.GL_FRAMEBUFFER_EXT, GL.GL_DEPTH_ATTACHMENT_EXT,
                                        FB.GL_RENDERBUFFER_EXT, self.depthBuffer);

        status = FB.glCheckFramebufferStatusEXT (FB.GL_FRAMEBUFFER_EXT);
        if status != FB.GL_FRAMEBUFFER_COMPLETE_EXT:
            print "Error in framebuffer activation"
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

class _BaseVisualStim:
    """A template for a stimulus class, on which PatchStim, TextStim etc... are based.
    Not finished...?
    """
    def __init__(self):
        raise NotImplementedError('Stimulus classes must overide _BaseVisualStim.__init__')
    def draw(self):
        raise NotImplementedError('Stimulus classes must overide _BaseVisualStim.draw')
    def setPos(self, newPos, operation='', units=None):
        """Set the stimulus position in the specified (or inheritted) `units`
        """
        self._set('pos', val=newPos, op=operation)
        self._calcPosRendered()
    def setDepth(self,newDepth, operation=''):
        self._set('depth', newDepth, operation)
    def setSize(self, newSize, operation='', units=None):
        """Set the stimulus size [X,Y] in the specified (or inheritted) `units`
        """
        if units==None: units=self.units#need to change this to create several units from one
        self._set('size', newSize, op=operation)
        self._calcSizeRendered()
        self.needUpdate=True
    def setOri(self, newOri, operation=''):
        """Set the stimulus orientation in degrees
        """
        self._set('ori',val=newOri, op=operation)
    def setOpacity(self,newOpacity,operation=''):
        self._set('opacity', newOpacity, operation)
        #opacity is coded by the texture, if not using shaders
        if not self._useShaders:
            self.setMask(self._maskName)
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

    def setColor(self, color, colorSpace=None, operation=''):
        """Set the color of the stimulus. See `colorSpaces`_ for further information
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
            in one of the `colorSpaces`_. If no color space is specified then the color 
            space most recently used for this stimulus is used again.
            
                myStim.setColor([1.0,-1.0,-1.0], 'rgb')#a red color in rgb space
                myStim.setColor([0.0,45.0,1.0], 'dkl') #DKL space with elev=0, azimuth=45
                myStim.setColor([0,0,255], 'rgb255') #a blue stimulus using rgb255 space
            
            Lastly, a single number can be provided, x, which is equivalent to providing
            [x,x,x]. 
            
                myStim.setColor(255, 'rgb255') #all guns o max
            
        colorSpace : string or None
        
            defining which of the `colorSpaces`_ to use. For strings and hex
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
                    rgbAttrib='rgb', #or 'fillRGB' etc
                    colorAttrib='color')
    def setContr(self, newContr, operation=''):
        """Set the contrast of the stimulus
        """
        self._set('contr', newContr, operation)
        #if we don't have shaders we need to rebuild the texture
        if not self._useShaders:
            self.setTex(self._texName)
    def _set(self, attrib, val, op=''):
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
    def setUseShaders(self, val=True):
        """Set this stimulus to use shaders if possible.
        """
        #NB TextStim overrides this function, so changes here may need changing there too
        if val==True and self.win._haveShaders==False:
            log.error("Shaders were requested for PatchStim but aren't available. Shaders need OpenGL 2.0+ drivers")
        if val!=self._useShaders:
            self._useShaders=val
            self.setTex(self._texName)
            self.setMask(self._maskName)
            self.needUpdate=True
            
    def _updateList(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() 
        Chooses between using and not using shaders each call.
        """
        if self._useShaders:
            self._updateListShaders()
        else: self._updateListNoShaders()  
    def _calcSizeRendered(self):
        """Calculate the size of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix']: self._sizeRendered=self.size
        elif self.units in ['deg', 'degs']: self._sizeRendered=psychopy.misc.deg2pix(self.size, self.win.monitor)
        elif self.units=='cm': self._sizeRendered=psychopy.misc.cm2pix(self.size, self.win.monitor)
        else:
            log.ERROR("Stimulus units should be 'norm', 'deg', 'cm' or 'pix', not '%s'" %self.units)
    def _calcPosRendered(self):
        """Calculate the pos of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix']: self._posRendered=self.pos
        elif self.units in ['deg', 'degs']: self._posRendered=psychopy.misc.deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm': self._posRendered=psychopy.misc.cm2pix(self.pos, self.win.monitor)
        
        
class DotStim(_BaseVisualStim):
    """
    This stimulus class defines a field of dots with an update rule that determines how they change
    on every call to the .draw() method.
    
    This standard class can be used to generate a wide variety of dot motion types. For a review of
    possible types and their pros and cons see Scase, Braddick & Raymond (1996). All six possible 
    motions they describe can be generated with appropriate choices of the signalDots (which
    determines whether signal dots are the 'same' or 'different' from frame to frame), noiseDots
    (which determines the locations of the noise dots on each frame) and the dotLife (which 
    determines for how many frames the dot will continue before being regenerated).
    
    'Movshon'-type noise uses a random position, rather than random direction, for the noise dots 
    and the signal dots are distinct (noiseDots='different'). This has the disadvantage that the
    noise dots not only have a random direction but also a random speed (so differ in two ways
    from the signal dots). The default option for DotStim is that the dots follow a random walk,
    with the dot and noise elements being randomised each frame. This provides greater certainty 
    that individual dots cannot be used to determine the motion direction.
    
    When dots go out of bounds or reach the end of their life they are given a new random position.
    As a result, to prevent inhomogeneities arising in the dots distribution across the field, a 
    limitted lifetime dot is strongly recommended.
    
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
                 opacity =1.0,
                 depth  =0,
                 element=None,
                 signalDots='different',
                 noiseDots='position'):
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
            fieldSize : a single value, specifying the diameter of the field
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
            signalDots : 'same' or 'different'
                If 'same' then the chosen signal dots remain the same on each frame.
                If 'different' they are randomly chosen each frame. This paramater
                corresponds to Scase et al's (1996) categories of RDK.            
            noiseDots : 'position','direction' or 'walk'
                Determines the behaviour of the noise dots, taken directly from 
                Scase et al's (1996) categories. For 'position', noise dots take a
                random position every frame. For 'direction' noise dots follow a 
                random, but constant direction. For 'walk' noise dots vary their
                direction every frame, but keep a constant speed.                            
            rgb : (r,g,b) or [r,g,b] or a single intensity value 
                or a single value (which will be applied to all guns).
                RGB vals are applied to simple textures and to greyscale
                image files but not to RGB images.
                **NB** units range -1:1 (so 0.0 is GREY). See :ref:`rgb` for further info.
            opacity : float
                1.0 is opaque, 0.0 is transparent
            depth : 0,
                This can be used to choose which
                stimulus overlays which. (more negative values are nearer).
                At present the window does not do perspective rendering
                but could do if that's really useful(?!)
            element : *None* or a visual stimulus object
                This can be any object that has a ``.draw()`` method and a
                ``.setPos([x,y])`` method (e.g. a PatchStim, TextStim...)!!
                See `ElementArrayStim` for a faster implementation of this idea.
            """
        self.win = win
        
        self.nDots = nDots
        #size
        if type(fieldPos) in [tuple,list]:
            self.fieldPos = numpy.array(fieldPos,float)
        else: self.fieldPos=fieldPos
        if type(fieldSize) in [tuple,list]:        
            self.fieldSize = numpy.array(fieldSize)
        else:self.fieldSize=fieldSize        
        if type(dotSize) in [tuple,list]:        
            self.dotSize = numpy.array(dotSize)
        else:self.dotSize=dotSize
        self.fieldShape = fieldShape
        self.dir = dir
        self.speed = speed
        self.opacity = opacity
        self.element = element
        self.dotLife = dotLife
        self.signalDots = signalDots
        self.noiseDots = noiseDots
        
        #unit conversions
        if len(units): self.units = units
        else: self.units = win.units
        if self.units=='norm': self._winScale='norm'
        else: self._winScale='pix' #set the window to have pixels coords
        #'rendered' coordinates represent the stimuli in the scaled coords of the window
        #(i.e. norm for units==norm, but pix for all other units)
        self._dotSizeRendered=None
        self._speedRendered=None
        self._fieldSizeRendered=None
        self._fieldPosRendered=None        
        
        self._useShaders=False#not needed for dots?
        self.colorSpace=colorSpace
        if rgb!=None:
            log.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb')
        else:
            self.setColor(color)

        self.depth=depth
        """initialise the dots themselves - give them all random dir and then
        fix the first n in the array to have the direction specified"""

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

    def _set(self, attrib, val, op=''):
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


    def set(self, attrib, val, op=''):
        """DotStim.set() is obselete and may not be supported in future
        versions of PsychoPy. Use the specific method for each parameter instead
        (e.g. setFieldPos(), setCoherence()...)
        """
        self._set(attrib, val, op)
    def setPos(self, newPos=None, operation='', units=None):
        """Obselete - users should use setFieldPos or instead of setPos
        """
        log.error("User called DotStim.setPos(pos). Use DotStim.SetFieldPos(pos) instead.")        
    def setFieldPos(self,val, op=''):
        self._set('fieldPos', val, op)
        self._calcFieldCoordsRendered()
    def setFieldCoherence(self,val, op=''):
        """Change the coherence (%) of the DotStim. This will be rounded according 
        to the number of dots in the stimulus.
        """
        self._set('coherence', val, op)
        self.coherence=round(self.coherence*self.nDots)/self.nDots#store actual coherence rounded by nDots
        self._signalDots = numpy.zeros(self.nDots, dtype=bool)
        self._signalDots[0:int(self.coherence*self.nDots)]=True
        #for 'direction' method we need to update the direction of the number 
        #of signal dots immediately, but for other methods it will be done during updateXY
        if self.noiseDots == 'direction': 
            self._dotsDir=numpy.random.rand(self.nDots)*2*pi
            self._dotsDir[self._signalDots]=self.dir*pi/180
    def setDir(self,val, op=''):
        """Change the direction of the signal dots (units in degrees)
        """
        #check which dots are signal
        signalDots = self._dotsDir==(self.dir*pi/180)        
        self._set('dir', val, op)
        #dots currently moving in the signal direction also need to update their direction
        self._dotsDir[signalDots] = self.dir*pi/180
    def setSpeed(self,val, op=''):
        """Change the speed of the dots (in stimulus `units` per second)
        """
        self._set('speed', val, op)
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
        if self.depth==0:
            thisDepth = self.win._defDepth
            win._defDepth += _depthIncrements[win.winType]
        else:
            thisDepth=self.depth
        
        #draw the dots
        if self.element==None:
            win.setScale(self._winScale) 
            #scale the drawing frame etc...
            GL.glTranslatef(self._fieldPosRendered[0],self._fieldPosRendered[1],thisDepth)
            GL.glPointSize(self.dotSize)
            
            #load Null textures into multitexteureARB - they modulate with glColor
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            
            if self.win.winType == 'pyglet':
                GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self._dotsXYRendered.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
            else:
                GL.glVertexPointerd(self._dotsXYRendered)
            if self.colorSpace in ['rgb','dkl','lms']:
                GL.glColor4f(self.rgb[0]/2.0+0.5, self.rgb[1]/2.0+0.5, self.rgb[2]/2.0+0.5, 1.0)
            else:
                GL.glColor4f(self.rgb[0]/255.0, self.rgb[1]/255.0, self.rgb[2]/255.0, 1.0)
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
        if self.signalDots =='same':
            #noise and signal dots change identity constantly
            #easiest way to keep _signalDots and _dotsDir in sync is to shuffle _dotsDir
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
        if self.fieldShape in  ['square', 'sqr']:
            dead = dead+ (numpy.abs(self._dotsXY[:,0])>self.fieldSize[0]/2.0) + (numpy.abs(self._dotsXY[:,1])>self.fieldSize[1]/2.0)
        elif self.fieldShape == 'circle':
            #transform to a normalised circle (radius = 1 all around) then to polar coords to check 
            normXY = self._dotsXY/(self.fieldSize/2.0)#the normalised XY position (where radius should be <1)
            dead = dead + (numpy.hypot(normXY[:,0],normXY[:,1])>1) #add out-of-bounds to those that need replacing

#        update any dead dots
        if sum(dead):
            self._dotsXY[dead,:] = self._newDotsXY(sum(dead))
            
        #update the pixel XY coordinates    
        self._calcDotsXYRendered()
        
    def _calcDotsXYRendered(self):
        if self.units in ['norm','pix']: self._dotsXYRendered=self._dotsXY
        elif self.units in ['deg','degs']: self._dotsXYRendered=psychopy.misc.deg2pix(self._dotsXY, self.win.monitor)
        elif self.units=='cm': self._dotsXYRendered=psychopy.misc.cm2pix(self._dotsXY, self.win.monitor)
    def _calcFieldCoordsRendered(self):
        if self.units in ['norm', 'pix']: 
            self._fieldSizeRendered=self.fieldSize
            self._fieldPosRendered=self.fieldPos
        elif self.units in ['deg', 'degs']:
            self._fieldSizeRendered=psychopy.misc.deg2pix(self.fieldSize, self.win.monitor)
            self._fieldPosRendered=psychopy.misc.deg2pix(self.fieldPos, self.win.monitor)
        elif self.units=='cm': 
            self._fieldSizeRendered=psychopy.misc.cm2pix(self.fieldSize, self.win.monitor)
            self._fieldPosRendered=psychopy.misc.cm2pix(self.fieldPos, self.win.monitor)

class SimpleImageStim(_BaseVisualStim):
    """A simple stimulus for loading images from a file and presenting at exactly
    the resolution and color in the file (subject to gamma correction if set).
    
    Unlike the PatchStim, this type of stimulus cannot be rescaled, rotated or 
    masked (although flipping horizontally or vertically is possible). Drawing will
    also tend to be marginally slower, because the image isn't preloaded to the 
    gfx card. The advantage, however is that the stimulus will always be in its
    original aspect ratio, with no interplotation or other transformation. It is always 
    
    SimpleImageStim does not support a depth parameter (the OpenGL method
    that draws the pixels does not support it). Simple images will obscure any other 
    stimulus type.
    
    Also, unlike the PatchStim (whose textures should be square and power-of-two
    in size, there is no restriction on the size of images for the SimpleImageStim 
    
    
    """
    def __init__(self,
                 win,
                 image     ="",
                 units   ="",
                 pos     =(0.0,0.0),
                 contrast=1.0,
                 opacity=1.0,
                 flipHoriz=False,
                 flipVert=False):
        """
        :Parameters:

            
            win :
                a :class:`~psychopy.visual.Window` object (required)
            image :
                The filename, including relative or absolute path. The image
                can be any format that the Python Imagin Library can import
                (which is almost all).
            units : **None**, 'norm', 'cm', 'deg' or 'pix'  
                If None then the current units of the :class:`~psychopy.visual.Window` will be used. 
                See :ref:`units` for explanation of other options. 
            pos : 
                a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y of the centre of the stimulus.
                The origin is the screen centre, the units are determined
                by units (see above). Stimuli can be position beyond the
                window!
            contrast :
                How far the stimulus deviates from the middle grey.
                Contrast can vary -1:1 (this is a multiplier for the
                values given in the color description of the stimulus)
            opacity :
                1.0 is opaque, 0.0 is transparent
                
        """
        
        self.win = win
        if win._haveShaders: self._useShaders=True#by default, this is a good thing
        else: self._useShaders=False
        
        if units in [None, "", []]:
            self.units = win.units
        else:self.units = units
        
        self.contrast = float(contrast)
        self.opacity = opacity
        self.pos = numpy.array(pos, float)
        self.setImage(image)
        #flip if necess
        self.flipHoriz=False#initially it is false, then so the flip according to arg above
        self.setFlipHoriz(flipHoriz)
        self.flipVert=False#initially it is false, then so the flip according to arg above
        self.setFlipVert(flipVert)
        #fix scaling to window coords
        if self.units=='norm': self._winScale='norm'
        else: self._winScale='pix' #set the window to have pixels coords
        self._calcPosRendered()
    def setFlipHoriz(self,newVal=True):
        """If set to True then the image will be flipped horiztonally (left-to-right).
        Note that this is relative to the original image, not relative to the current state.
        """
        if newVal!=self.flipHoriz: #we need to make the flip
            self.imArray = numpy.flipud(self.imArray)#numpy and pyglet disagree about ori so ud<=>lr
        self.flipHoriz=newVal
        self._needStrUpdate=True
    def setFlipVert(self,newVal=True):
        """If set to True then the image will be flipped vertically (top-to-bottom).
        Note that this is relative to the original image, not relative to the current state.
        """
        if newVal!=self.flipVert: #we need to make the flip
            self.imArray = numpy.fliplr(self.imArray)#numpy and pyglet disagree about ori so ud<=>lr
        self.flipVert=newVal
        self._needStrUpdate=True
    def setUseShaders(self, val=True):
        """Set this stimulus to use shaders if possible.
        """
        #NB TextStim overrides this function, so changes here may need changing there too
        if val==True and self.win._haveShaders==False:
            log.error("Shaders were requested for PatchStim but aren't available. Shaders need OpenGL 2.0+ drivers")
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
        GL.glOrtho( 0, self.win.size[0],0, self.win.size[1], 0, 1 )	#this also sets the 0,0 to be top-left
        #but return to modelview for rendering
        GL.glMatrixMode(GL.GL_MODELVIEW)							
        GL.glLoadIdentity()
        
        if self._needStrUpdate: self._updateImageStr()
        #unbind any textures
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE1_ARB)
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
    def setPos(self, newPos, operation='', units=None):
        self._set('pos', val=newPos, op=operation)
        self._calcPosRendered()
    def setDepth(self,newDepth, operation=''):
        self._set('depth', newDepth, operation)    
    def _calcPosRendered(self):
        """Calculate the pos of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['pix', 'pixels']: self._posRendered=self.pos
        elif self.units=='norm': self._posRendered=self.pos
        elif self.units in ['deg', 'degs']: self._posRendered=psychopy.misc.deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm': self._posRendered=psychopy.misc.cm2pix(self.pos, self.win.monitor)
    def setImage(self,filename=None):
        if filename!=None:
            self.filename=filename
        if os.path.isfile(self.filename):
            im = Image.open(self.filename)
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        else:
            log.error("couldn't find image...%s" %(filename))
            core.quit()
            raise #so thatensure we quit
        self.size=im.size
        #set correct formats for bytes/floats
        self.imArray = numpy.array(im.convert("RGB")).astype(numpy.float32)/255
        self.internalFormat = GL.GL_RGB      
        if self._useShaders:            
            self.dataType = GL.GL_FLOAT
        else:
            self.dataType = GL.GL_UNSIGNED_BYTE
            self.imArray = psychopy.misc.float_uint8(self.imArray*2-1)
        self._needStrUpdate=True
class PatchStim(_BaseVisualStim):
    """Stimulus object for drawing arbitrary bitmaps, textures and shapes.
    One of the main stimuli for PsychoPy.

    Formally PatchStim is just a texture behind an optional
    transparency mask (an 'alpha mask'). Both the texture and mask can be
    arbitrary bitmaps and their combination allows an enormous variety of
    stimuli to be drawn in realtime.

    **Examples**::

        myGrat = PatchStim(tex='sin',mask='circle') #gives a circular patch of grating
        myGabor = PatchStim(tex='sin',mask='gauss') #gives a 'Gabor' patchgrating
        myImage = PatchStim(tex='face.jpg',mask=None) #simply draws the image face.jpg
    
    An PatchStim can be rotated scaled and shifted in position, its texture can
    be drifted in X and/or Y and it can have a spatial frequency in X and/or Y
    (for an image file that simply draws multiple copies in the patch).

    Also since transparency can be controlled two PatchStims can combine e.g.
    to form a plaid.    

    **Using Patchstim with images from disk (jpg, tif, pgn...)**
    
    Ideally images to be rendered should be square with 'power-of-2' dimensions 
    e.g. 16x16, 128x128. Any image that is not will be upscaled (with linear interp)
    to the nearest such texture by PsychoPy. The size of the stimulus should be 
    specified in the normal way using the appropriate units (deg, pix, cm...). Be 
    sure to get the aspect ration the same as the image (if you don't want it 
    stretched!).

    **Why can't I have a normal image, drawn pixel-by-pixel?** PatchStims are 
    rendered using OpenGL textures. This is more powerful than using simple screen 
    blitting - it allows the rotation, masking, transparency to work. It is still 
    necessary to have power-of-2 textures on most graphics cards.
    """
    def __init__(self,
                 win,
                 tex     ="sin",
                 mask    ="none",
                 units   ="",
                 pos     =(0.0,0.0),
                 size    =(0.5,0.5),
                 sf      =(1.0,1.0),
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
                 interpolate=False):
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
                              
                + **None**, 'circle', 'gauss'
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
            sf:
                a tuple (1.0,1.0) or a list [1.0,1.0] for the x and y
                OR a single value (which will be applied to x and y).
                Where `units` == 'deg' or 'cm' units are in cycles per deg/cm. 
                If `units` == 'norm' then sf units are in cycles per stimulus (so scale with stimulus size).
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
                Could be a the web name for a color (e.g. 'FireBrick');
                a hex value (e.g. '#FF0047');
                a tuple (1.0,1.0,1.0); a list [1.0,1.0, 1.0]; or numpy array.
                If the last three are used then the color space should also be given
                See :ref:`colorspaces`
            colorSpace:
                the color space controlling the interpretation of the `color`
                See :ref:`colorspaces`
            contrast:
                How far the stimulus deviates from the middle grey.
                Contrast can vary -1:1 (this is a multiplier for the
                values given in the color description of the stimulus).
            opacity:
                1.0 is opaque, 0.0 is transparent
            depth:
                This can potentially be used (not tested!) to choose which
                stimulus overlays which. (more negative values are nearer).
                At present the window does not do perspective rendering
                but could do if that's really useful(?!)
                
        """
        
        self.win = win
        if win._haveShaders: self._useShaders=True#by default, this is a good thing
        else: self._useShaders=False
        
        if units in [None, "", []]:
            self.units = win.units
        else:self.units = units
        
        self.ori = float(ori)
        self.texRes = texRes #must be power of 2
        self.contrast = float(contrast)
        self.opacity = opacity
        self.interpolate=interpolate
        
        self.colorSpace=colorSpace
        if rgb!=None:
            log.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb')
        elif dkl!=None:
            log.warning("Use of dkl arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(dkl, colorSpace='dkl')
        elif lms!=None:
            log.warning("Use of lms arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(lms, colorSpace='lms')
        else:
            self.setColor(color, colorSpace=colorSpace)
            
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

        #size
        if type(size) in [tuple,list]:
            self.size = numpy.array(size,float)
        else:
            self.size = numpy.array((size,size),float)#make a square if only given one dimension

        #sf
        if units in ['pix', 'pixels'] and sf==(1,1): #if using pix and sf wasn't given
            sf = 1.0/self.size#so that exactly
        if type(sf) in [float, int] or len(sf)==1:
            self.sf = numpy.array((sf,sf),float)
        else:
            self.sf = numpy.array(sf,float)

        self.pos = numpy.array(pos, float)

        self.depth=depth

        #initialise textures for stimulus
        if self.win.winType=="pyglet":
            self.texID=GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(self.texID))
            self.maskID=GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(self.maskID))
        elif cTypesOpenGL:
            (tID, mID) = GL.glGenTextures(2)
            self.texID = GL.GLuint(int(tID))#need to convert to GLUint (via ints!!)
            self.maskID = GL.GLuint(int(mID))
        else:
            (self.texID, self.maskID) = GL.glGenTextures(2)
        self.setTex(tex)
        self.setMask(mask)
        
        #fix scaling to window coords
        if self.units=='norm': self._winScale='norm'
        else: self._winScale='pix' #set the window to have pixels coords
        self._calcCyclesPerStim()
        self._calcPosRendered()
        self._calcSizeRendered()
        
        #generate a displaylist ID
        self._listID = GL.glGenLists(1)
        self._updateList()#ie refresh display list

    def setSF(self,value,operation=''):
        self._set('sf', value, operation)
        self.needUpdate = 1
        self._calcCyclesPerStim()
    def setPhase(self,value, operation=''):
        self._set('phase', value, operation)
        self.needUpdate = 1
    def setContrast(self,value,operation=''):
        self._set('contrast', value, operation)
        #if we don't have shaders we need to rebuild the texture
        if not self._useShaders:
            self.setTex(self._texName)
    def setTex(self,value):
        self._texName = value
        createTexture(value, id=self.texID, pixFormat=GL.GL_RGB, stim=self, res=self.texRes)
    def setMask(self,value):        
        self._maskName = value
        createTexture(value, id=self.maskID, pixFormat=GL.GL_ALPHA, stim=self, res=self.texRes)
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
        
        #work out next default depth
        if self.depth==0:
            thisDepth = self.win._defDepth
            win._defDepth += _depthIncrements[win.winType]
        else:
            thisDepth=self.depth

        #do scaling
        GL.glPushMatrix()#push before the list, pop after
        win.setScale(self._winScale)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],thisDepth)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        #the list just does the texture mapping
        
        if self.colorSpace in ['rgb','dkl','lms']: #these spaces are 0-centred
            desiredRGB = (self.rgb*self.contrast+1)/2.0#RGB in range 0:1 and scaled for contrast
            if numpy.any(desiredRGB**2.0>1.0):
                desiredRGB=[0.6,0.6,0.4]
            GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)
        else:
            desiredRGB = (self.rgb*self.contrast)/255.0
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
        #print 'updating Shaders list'
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
        #print 'updating No Shaders list'
        self.needUpdate=0

        GL.glNewList(self._listID,GL.GL_COMPILE)
        GL.glColor4f(1.0,1.0,1.0,1.0)#glColor can interfere with multitextures
        #mask
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)#implicitly disables 1D
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.maskID)

        #main texture
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE0_ARB)
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
        GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Rtex, Btex)
        GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE1_ARB,Rmask,Bmask)
        GL.glVertex2f(R,B)
        # left bottom
        GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Ltex,Btex)
        GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE1_ARB,Lmask,Bmask)
        GL.glVertex2f(L,B)
        # left top
        GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Ltex,Ttex)
        GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE1_ARB,Lmask,Tmask)
        GL.glVertex2f(L,T)
        # right top
        GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Rtex,Ttex)
        GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE1_ARB,Rmask,Tmask)
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
        #only needed for pyglet
        if self.win.winType=='pyglet':
            GL.glDeleteTextures(1, self.texID)
            GL.glDeleteTextures(1, self.maskID)
            
    def _calcCyclesPerStim(self):
        if self.units=='norm': self._cycles=self.sf#this is the only form of sf that is not size dependent
        else: self._cycles=self.sf*self.size
        
class RadialStim(PatchStim):
    """Stimulus object for drawing radial stimuli, like an annulus, a rotating wedge,
    a checkerboard etc...

    Ideal for fMRI retinotopy stimuli!

    Many of the capabilities are built on top of the PatchStim.

    This stimulus is still relatively new and I'm finding occasional gliches. it also takes longer to draw
    than a typical PatchStim, so not recommended for tasks where high frame rates are needed.
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
                 interpolate=False):
        """
        :Parameters:

            win :
                a :class:`~psychopy.visual.Window` object (required)
            tex :
                The texture forming the image
                
                - 'sqrXsqr', 'sinXsin', 'sin','sqr',None
                - or the name of an image file (most formats supported)
                - or a numpy array (1xN or NxN) ranging -1:1
                
            mask :
                Unlike the mask in the PatchStim, this is a 1-D mask dictating the behaviour
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
                of the stimulus
            angularPhase : 
                the phase of the texture around the stimulus
            rgb :
                a tuple (1.0,1.0, 1.0) or a list [1.0,1.0, 1.0]
                or a single value (which will be applied to all guns).
                RGB vals are applied to simple textures and to greyscale
                image files but not to RGB images.

                **NB** units range -1:1 (so 0.0 is GREY). See :ref:`rgb` for further info.

            dkl : a tuple (45.0,90.0, 1.0) or a list [45.0,90.0, 1.0]
                specifying the coordinates of the stimuli in cone-opponent
                space (Derrington, Krauskopf, Lennie 1984). See :ref:`dkl` for further info.
                Triplets represent [elevation, azimuth, magnitude].
                Note that the monitor must be calibrated for this to be
                accurate (if not, example phosphors from a Sony Trinitron
                CRT will be used).
            lms : a tuple (0.5, 1.0, 1.0) or a list [0.5, 1.0, 1.0]
                specifying the coordinates of the stimuli in cone space
                Triplets represent relative modulation of each cone [L, M, S].
                See :ref:`lms` for further info.
                Note that the monitor must be calibrated for this to be
                accurate (if not, example phosphors from a Sony Trinitron
                CRT will be used).
            contrast : (default= *1.0* )
                How far the stimulus deviates from the middle grey.
                Contrast can vary -1:1 (this is a multiplier for the
                values given in the color description of the stimulus)
            opacity :
                1.0 is opaque, 0.0 is transparent
            depth :
                This can potentially be used (not tested!) to choose which
                stimulus overlays which. (more negative values are nearer).
                At present the window does not do perspective rendering
                but could do if that's really useful(?!)

        """
        self.win = win
        if win._haveShaders: self._useShaders=True#by default, this is a good thing
        else: self._useShaders=False
        if len(units): self.units = units
        else: self.units = win.units
        
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
        self.opacity = opacity
        self.pos = numpy.array(pos, float)
        self.interpolate=interpolate

        #these are defined by the PatchStim but will just cause confusion here!
        self.setSF = None
        self.setPhase = None
        self.setSF = None

        self.colorSpace=colorSpace
        if rgb!=None:
            log.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb')
        elif dkl!=None:
            log.warning("Use of dkl arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(dkl, colorSpace='dkl')
        elif lms!=None:
            log.warning("Use of lms arguments to stimuli are deprecated. Please use color and colorSpace args instead")
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
        if self.win.winType=="pyglet":
            self.texID=GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(self.texID))
            self.maskID=GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(self.maskID))
        else:
            (self.texID, self.maskID) = GL.glGenTextures(2)
        self.setTex(tex)
        self.setMask(mask)
        
        #generate a displaylist ID
        self._listID = GL.glGenLists(1)

        #
        self._triangleWidth = pi*2/self.angularRes
        self._angles = numpy.arange(0,pi*2, self._triangleWidth, dtype='float64')
        #which vertices are visible?
        self._visible = (self._angles>=(self.visibleWedge[0]*pi/180))#first edge of wedge
        self._visible[(self._angles+self._triangleWidth)*180/pi>(self.visibleWedge[1])] = False#second edge of wedge
        self._nVisible = numpy.sum(self._visible)*3

        
        #do the scaling to the window coordinate system (norm or pix coords)
        if self.units=='norm': self._winScale='norm'
        else: self._winScale='pix' #set the window to have pixels coords
        self._calcPosRendered()
        self._calcSizeRendered()#must be done BEFORE _updateXY
        
        self._updateTextureCoords()
        self._updateMaskCoords()
        self._updateXY()
        self._updateList()#ie refresh display list

    def setSize(self, value, operation=''):
        self._set('size', value, operation)
        self._calcSizeRendered()
        self._updateXY()
        self.needUpdate=True
    def setAngularCycles(self,value,operation=''):
        """set the number of cycles going around the stimulus"""
        self._set('angularCycles', value, operation)
        self._updateTextureCoords()
        self.needUpdate=True
    def setRadialCycles(self,value,operation=''):
        """set the number of texture cycles from centre to periphery"""
        self._set('radialCycles', value, operation)
        self._updateTextureCoords()
        self.needUpdate=True
    def setAngularPhase(self,value, operation=''):
        """set the angular phase of the texture"""
        self._set('angularPhase', value, operation)
        self._updateTextureCoords()
        self.needUpdate=True
    def setRadialPhase(self,value, operation=''):
        """set the radial phase of the texture"""
        self._set('radialPhase', value, operation)
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

        #work out next default depth
        if self.depth==0:
            thisDepth = self.win._defDepth
            self.win._defDepth += _depthIncrements[self.win.winType]
        else:
            thisDepth=self.depth

        #do scaling
        GL.glPushMatrix()#push before the list, pop after
        #scale the viewport to the appropriate size
        self.win.setScale(self._winScale)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],thisDepth)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)

        if self._useShaders:
            #setup color
            desiredRGB = (self.rgb*self.contrast+1)/2.0#RGB in range 0:1 and scaled for contrast
            if numpy.any(desiredRGB**2.0>1.0):
                desiredRGB=[0.6,0.6,0.4]
            GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)
            
            #assign vertex array
            if self.win.winType=='pyglet':
                arrPointer = self._visibleXY.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                GL.glVertexPointer(2, GL.GL_DOUBLE, 0, arrPointer) 
            else:
                GL.glVertexPointerd(self._visibleXY)#must be reshaped in to Nx2 coordinates

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
            if self.win.winType=='pyglet':
                arrPointer = self._visibleTexture.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, arrPointer) 
            else:
                GL.glTexCoordPointerd(self._visibleTexture)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            
            #mask
            GL.glClientActiveTexture(GL.GL_TEXTURE1)
            if self.win.winType=='pyglet':
                arrPointer = self._visibleMask.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                GL.glTexCoordPointer(1, GL.GL_DOUBLE, 0, arrPointer) 
            else:
                GL.glTexCoordPointerd(self._visibleMask)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)                    
            
            #do the drawing
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible)
            #disable set states
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glDisable(GL.GL_TEXTURE_2D)
            
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
        self._textureCoords[:,0,1] = -self.radialPhase #y position of inner vertex
        self._textureCoords[:,1,0] = (self._angles)*self.angularCycles/(2*pi)+self.angularPhase #x position of 1st outer vertex
        self._textureCoords[:,1,1] = self.radialCycles-self.radialPhase#y position of 1st outer vertex
        self._textureCoords[:,2,0] = (self._angles+self._triangleWidth)*self.angularCycles/(2*pi)+self.angularPhase#x position of 2nd outer vertex
        self._textureCoords[:,2,1] = self.radialCycles-self.radialPhase#y position of 2nd outer vertex
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
        if self.win.winType=='pyglet':
            arrPointer = self._visibleXY.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            GL.glVertexPointer(2, GL.GL_FLOAT, 0, arrPointer) 
        else:
            GL.glVertexPointerd(self._visibleXY)#must be reshaped in to Nx2 coordinates

        #setup the shaderprogram
        GL.glUseProgram(self.win._progSignedTexMask1D)
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask1D, "texture"), 0) #set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask1D, "mask"), 1)  # mask is texture unit 1 
        
        #set pointers to visible textures
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        if self.win.winType=='pyglet':
            arrPointer = self._visibleTexture.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, arrPointer) 
        else:
            GL.glTexCoordPointerd(self._visibleTexture)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        #then bind main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)
        GL.glEnable(GL.GL_TEXTURE_2D)    
        
        #mask
        GL.glClientActiveTexture(GL.GL_TEXTURE1)
        if self.win.winType=='pyglet':
            arrPointer = self._visibleMask.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            GL.glTexCoordPointer(1, GL.GL_FLOAT, 0, arrPointer) 
        else:
            GL.glTexCoordPointerd(self._visibleMask)
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
        GL.glColor4f(1.0,1.0,1.0,1.0)#glColor can interfere with multitextures

        #assign vertex array
        if self.win.winType=='pyglet':
            arrPointer = self._visibleXY.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, arrPointer) 
        else:
            GL.glVertexPointerd(self._visibleXY)#must be reshaped in to Nx2 coordinates
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)

        #bind and enable textures
        #main texture
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE0_ARB)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        #mask
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE1_ARB)
        GL.glBindTexture(GL.GL_TEXTURE_1D, self.maskID)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_TEXTURE_1D)

        #set pointers to visible textures
        GL_multitexture.glClientActiveTextureARB(GL_multitexture.GL_TEXTURE0_ARB)
        if self.win.winType=='pyglet':
            arrPointer = self._visibleTexture.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
            GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, arrPointer) 
        else:
            GL.glTexCoordPointerd(self._visibleTexture)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        #mask
        GL_multitexture.glClientActiveTextureARB(GL_multitexture.GL_TEXTURE1_ARB)
        if self.win.winType=='pyglet':
            arrPointer = self._visibleMask.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
            GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, arrPointer) 
        else:
            GL.glTexCoordPointerd(self._visibleMask)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        #do the drawing
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible)

        #disable set states
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glEndList()

    def setTex(self,value):
        self._texName = value
        createTexture(value, id=self.texID, pixFormat=GL.GL_RGB, stim=self, res=self.texRes)
    def setMask(self,value):        
        """
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
                log.error("couldn't load mask...%s: %s" %(value,details))
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
        
    def __del__(self):
        self.clearTextures()#remove textures from graphics card to prevent crash
        
    def clearTextures(self):
        """
        Clear the textures associated with the given stimulus. 
        As of v1.61.00 this is called automatically during garbage collection of
        your stimulus, so doesn't need calling explicitly by the user.
        """
        #only needed for pyglet
        if self.win.winType=='pyglet':
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
                 rgbs = (1.0,1.0,1.0),
                 opacities = 1.0,
                 depths = 0,
                 fieldDepth = 0,
                 oris = 0,
                 sfs=1.0,
                 contrs = 1,
                 phases=0,
                 elementTex='sin',
                 elementMask='gauss',
                 texRes=48):
        
        """
        :Parameters:
        
            win :
                a :class:`~psychopy.visual.Window` object (required)
                                 
            units : **None**, 'norm', 'cm', 'deg' or 'pix'  
                If None then the current units of the :class:`~psychopy.visual.Window` will be used. 
                See :ref:`units` for explanation of other options.
            
            fieldPos : 
                The centre of the array of elements
                                
            fieldSize : 
                The size of the array of elements (this will be overridden by setting explicit xy positions for the elements)
            
            fieldShape : 
                The shape of the array ('circle' or 'sqr')        
            
            nElements : 
                number of elements in the array     
               
            sizes : 
                an array of sizes Nx1, Nx2 or a single value      
              
            xys : 
                the xy positions of the elements, relative to the field centre (fieldPos)   
                 
            rgbs : 
                specifying the color(s) of the elements. 
                Should be Nx1 (different greys), Nx3 (different colors) or 1x3 (for a single color)
            
            opacities : 
                the opacity of each element (Nx1 or a single value)
            
            depths : 
                the depths of the elements (Nx1), relative the overall depth of the field (fieldDepth)
            
            fieldDepth : 
                the depth of the field (will be added to the depths of the elements)
            
            oris : 
                the orientations of the elements (Nx1 or a single value)
            
            sfs : 
                the spatial frequencies of the elements (Nx1, Nx2 or a single value)
            
            contrs : 
                the contrasts of the elements, ranging -1 to +1 (Nx1 or a single value)
            
            phases : 
                the spatial phase of the texture on the stimulus (Nx1 or a single value)
            
            elementTex : 
                the texture, to be used by all elements (e.g. 'sin', 'sqr',.. , 'myTexture.tif', numpy.ones([48,48]))
            
            elementMask : 
                the mask, to be used by all elements (e.g. 'circle', 'gauss',.. , 'myTexture.tif', numpy.ones([48,48]))
            
            texRes : 
                the number of pixels in the textures (overridden if an array or image is provided)                       
        
        """
        self.win = win        
        if units in [None, "", []]:
            self.units = win.units
        else: self.units = units
        
        self.fieldPos = fieldPos
        self.fieldSize = fieldSize
        self.fieldShape = fieldShape
        self.nElements = nElements
        #info for each element
        self.sizes = sizes
        self.rgbs=rgbs
        self.xys= xys
        self.opacities = opacities
        self.oris = oris
        self.contrs = contrs
        self.phases = phases
        self.needVertexUpdate=True
        self.needColorUpdate=True
        self._useShaders=True
        self.interpolate=True
        self.fieldDepth=fieldDepth
        if depths==0:
            self.depths=numpy.arange(0,_depthIncrements[self.win.winType]*self.nElements,_depthIncrements[self.win.winType]).repeat(4).reshape(self.nElements, 4)
        else:
            self.depths=depths
        if self.win.winType != 'pyglet':
            raise TypeError('ElementArray requires a pyglet context')
                
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
        self.setMask(elementMask)
        self.setTex(elementTex)
        
        #set units for rendering (pix or norm)
        if self.units=='norm': self._winScale='norm'
        else: self._winScale='pix' #set the window to have pixels coords
        
        self.setContrs(contrs)
        self.setRgbs(rgbs)
        self.setOpacities(opacities)#opacities is used by setRgbs, so this needs to be early
        self.setXYs(xys)
        self.setOris(oris)  
        self.setSizes(sizes) #set sizes before sfs (sfs may need it formatted)
        self.setSfs(sfs)
        self.setPhases(phases)
        
        self._calcFieldCoordsRendered()
        self._calcSizesRendered()
        self._calcXYsRendered()
        
                
    def setXYs(self,value=None, operation=''):
        """Set the xy values of the element centres (relative to the centre of the field).
        Values should be:            
            
            - None
            - an array/list of Nx2 coordinates.
            
        If value is None then the xy positions will be generated automatically, based
        on the fieldSize and fieldPos. In this case opacity will also be overridden
        by this function (it is used to make elements outside the field invisible.
        """
        if value==None:
            if self.fieldShape is 'sqr':
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
            
    def setOris(self,value,operation=''):
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
    #----------------------------------------------------------------------
    def setSfs(self, value,operation=''):
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
        if value.shape in [(),(1,)]:
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
                        
    def setOpacities(self,value,operation=''):
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
        
    def setSizes(self,value,operation=''):
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
        if value.shape in [(),(1,)]:
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
        self.needVertexUpdate=True    
        
    def setPhases(self,value,operation=''):
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
        if value.shape in [(),(1,)]:
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
        
    def setRgbs(self,value,operation=''):
        """Set the rgb for each element. 
        Should either be:
        
          - a single value 
          - an Nx1 array/list 
          - an Nx3 array/list
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if value.shape in [(), (1,),(3,)]:
            value = numpy.resize(value, [self.nElements,3])
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            value.shape=(self.nElements,1)#set to be 2D
            value = value.repeat(3,1) #repeat once on dim 1
        elif value.shape == (self.nElements,3):
            pass#all is good
        else:
            raise ValueError("New value for setRgbs should be either Nx1, Nx3 or a single value")
        if operation=='':
            self.rgbs=value    
        else: exec('self.rgbs'+operation+'=value')
        
        self.needColorUpdate=True 
    def setContrs(self,value,operation=''):
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
    def setFieldPos(self,value,operation=''):
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
    def setPos(self, newPos=None, operation='', units=None):
        """Obselete - users should use setFieldPos or instead of setPos
        """
        log.error("User called ElementArrayStim.setPos(pos). Use ElementArrayStim.SetFieldPos(pos) instead.")
        
    def setFieldSize(self,value,operation=''):
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
        self.setXYs()#to reflect new settings, overriding individual xys 
        
    def draw(self):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.update() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """        
        if self.needVertexUpdate: 
            self.updateElementVertices()
        if self.needColorUpdate:
            self.updataElementColors()
        if self.needTexCoordUpdate:
            self.updataTextureCoords()
            
        #scale the drawing frame and get to centre of field
        GL.glPushMatrix()#push before drawing, pop after        
        GL.glPushClientAttrib(GL.GL_CLIENT_ALL_ATTRIB_BITS)#push the data for client attributes
        
        GL.glLoadIdentity()
        self.win.setScale(self._winScale)
        if self.fieldDepth==0:
            thisDepth=self.win._defDepth
            self.win._defDepth += _depthIncrements[self.win.winType]
        GL.glTranslatef(self._fieldPosRendered[0],self._fieldPosRendered[1],0.0)
               
        GL.glColorPointer(4, GL.GL_DOUBLE, 0, self._RGBAs.ctypes)
        GL.glVertexPointer(3, GL.GL_DOUBLE, 0, self._visXYZvertices.ctypes)#.data_as(ctypes.POINTER(ctypes.c_float)))

        #setup the shaderprogram        
        GL.glUseProgram(self.win._progSignedTexMask)
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "texture"), 0) #set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "mask"), 1)  # mask is texture unit 1
        
        #setup client texture coordinates first
        GL.glClientActiveTexture (GL.GL_TEXTURE0)   
        GL.glTexCoordPointer (2, GL.GL_DOUBLE, 0, self._texCoords.ctypes)  
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)    
        GL.glClientActiveTexture (GL.GL_TEXTURE1)   
        GL.glTexCoordPointer (2, GL.GL_DOUBLE, 0, self._maskCoords.ctypes)  
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)    
        #then bind textures
        GL.glActiveTexture (GL.GL_TEXTURE1)     
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture (GL.GL_TEXTURE_2D, self.maskID)
        GL.glActiveTexture (GL.GL_TEXTURE0)     
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture (GL.GL_TEXTURE_2D, self.texID)
        
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glDrawArrays(GL.GL_QUADS, 0, self._visXYZvertices.shape[0]*4)
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        
        GL.glPopClientAttrib()
        GL.glPopMatrix()
        
    def _calcSizesRendered(self):
        if self.units in ['norm','pix']: self._sizesRendered=self.sizes
        elif self.units in ['deg', 'degs']: self._sizesRendered=psychopy.misc.deg2pix(self.sizes, self.win.monitor)
        elif self.units=='cm': self._sizesRendered=psychopy.misc.cm2pix(self.sizes, self.win.monitor)
    def _calcXYsRendered(self):
        if self.units in ['norm','pix']: self._XYsRendered=self.xys
        elif self.units in ['deg', 'degs']: self._XYsRendered=psychopy.misc.deg2pix(self.xys, self.win.monitor)
        elif self.units=='cm': self._XYsRendered=psychopy.misc.cm2pix(self.xys, self.win.monitor)
    def _calcFieldCoordsRendered(self):
        if self.units in ['norm', 'pix']: 
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
        self._visXYZvertices[:,:,2] = self.depths
            
        self.needVertexUpdate=False
        
    #----------------------------------------------------------------------
    def updataElementColors(self):
        """Create a new array of self._RGBAs"""
        
        N=self.nElements
        self._RGBAs=numpy.zeros([N,4],'d')
        self._RGBAs[:,0:3] = self.rgbs[:,:] * self.contrs[:].reshape([N,1]).repeat(3,1)/2+0.5
        self._RGBAs[:,-1] = self.opacities.reshape([N,])
        self._RGBAs=self._RGBAs.reshape([N,1,4]).repeat(4,1)#repeat for the 4 vertices in the grid
        self.needColorUpdate=False
    def updataTextureCoords(self):
        """Create a new array of self._maskCoords"""
        
        N=self.nElements
        self._maskCoords=numpy.array([[0,1],[1,1],[1,0],[0,0]],'d').reshape([1,4,2])
        self._maskCoords = self._maskCoords.repeat(N,0)        
        
        #for the main texture
        if self.units in ['norm', 'pix']:#sf is dependent on size (openGL default)
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
        
    def setTex(self,value):
        """Change the texture (all elements have the same base texture). Avoid this 
        during time-critical points in your script. Uploading new textures to the 
        graphics card can be time-consuming.
        """
        self._texName = value
        createTexture(value, id=self.texID, pixFormat=GL.GL_RGB, stim=self, res=self.texRes)
    def setMask(self,value):    
        """Change the mask (all elements have the same mask). Avoid doing this 
        during time-critical points in your script. Uploading new textures to the 
        graphics card can be time-consuming."""    
        self._maskName = value
        createTexture(value, id=self.maskID, pixFormat=GL.GL_ALPHA, stim=self, res=self.texRes)        
    def __del__(self):
        self.clearTextures()#remove textures from graphics card to prevent crash        
    def clearTextures(self):
        """
        Clear the textures associated with the given stimulus. 
        As of v1.61.00 this is called automatically during garbage collection of
        your stimulus, so doesn't need calling explicitly by the user.
        """
        #only needed for pyglet
        if self.win.winType=='pyglet':
            GL.glDeleteTextures(1, self.texID)
            GL.glDeleteTextures(1, self.maskID)
            
class MovieStim(_BaseVisualStim):
    """A stimulus class for playing movies (mpeg, avi, etc...) in 
    PsychoPy. 
    
    **examples**::
    
        mov = visual.MovieStim(myWin, 'testmovie.mpg', fliVert=False)
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
                 opacity=1.0):
        """
        :Parameters:

            win :
                a :class:`~psychopy.visual.Window` object (required)
            filename :
                a string giving the relative or absolute path to the movie. Can be any movie that 
                AVbin can read (e.g. mpeg, DivX)
            units : **None**, 'norm', 'cm', 'deg' or 'pix'  
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
            opacity :
                the movie can be made transparent by reducing this
        """
        self.win = win 
        
        self._movie=None # the actual pyglet media object
        self._player=pyglet.media.ManagedSoundPlayer()
        self.filename=filename
        self.duration=None
        self.loadMovie( self.filename )
        self.format=self._movie.video_format        
        self.pos=pos
        self.depth=0        
        self.pos = numpy.asarray(pos, float)
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.opacity = opacity
        self.playing=0
        #size
        if size == None: self.size= numpy.array([self.format.width, self.format.height] , float)
        elif type(size) in [tuple,list]: self.size = numpy.array(size,float)
        else: self.size = numpy.array((size,size),float)
        
        self.ori = ori
        if units in [None, "", []]: self.units = win.units
        else: self.units = units
        #fix scaling to window coords
        if self.units=='norm': self._winScale='norm'
        else: self._winScale='pix' #set the window to have pixels coords
        self._calcPosRendered()
        self._calcSizeRendered()
        
        #check for pyglet
        if win.winType!='pyglet': 
            log.Error('Movie stimuli can only be used with a pyglet window')
            core.quit()
                    
    def loadMovie(self, filename):
        
        self._movie = pyglet.media.load( filename, streaming=True)
        self._player.queue(self._movie)
        self.duration = self._movie.duration
        #self._player.on_eos=self.onEOS #doesn't seem to work
        
    def draw(self, win=None):
        """Draw the current frame to a particular visual.Window (or to the
        default win for this object if not specified). The current position in the
        movie will be determined automatically.
        
        This method should be called on every frame that the movie is meant to appear"""
        if not self._player.playing:
            self._player.play()
            self.playing=1
        #set the window to draw to
        if win==None: win=self.win
        win.winHandle.switch_to()
        
        #work out next default depth
        if self.depth==0:
            thisDepth = self.win._defDepth
            self.win._defDepth += _depthIncrements[self.win.winType]
        else:
            thisDepth=self.depth
        
        #make sure that textures are on and GL_TEXTURE0 is active
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        
        frameTexture = self._player.get_texture()
        GL.glColor4f(1,1,1,self.opacity)
        GL.glPushMatrix()
        #do scaling
        #scale the viewport to the appropriate size
        self.win.setScale(self._winScale)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],thisDepth)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        flipBitX = 1-self.flipHoriz*2
        flipBitY = 1-self.flipVert*2
        frameTexture.blit(
                -self._sizeRendered[0]/2.0*flipBitX, 
                -self._sizeRendered[1]/2.0*flipBitY, 
                width=self._sizeRendered[0]*flipBitX, 
                height=self._sizeRendered[1]*flipBitY,
                z=thisDepth)        
        GL.glPopMatrix()
        
    def _onEOS(self):
        #not called, for some reason?!
        self.playing=-1

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
                 units="",
                 ori=0.0,
                 height=None,
                 antialias=True,
                 bold=False,
                 italic=False,
                 alignHoriz='center',
                 alignVert='center',
                 fontFiles=[],
                 wrapWidth=None):
        """
        :Parameters:        
            win: A :class:`Window` object. 
                Required - the stimulus must know where to draw itself
            text: 
                The text to be rendered
            pos: 
                Position on the screen            
            depth: 
                Depth on the screen (if None it will be defined on .draw() to be in front of the last object drawn)
            color: 
                The color of the text (ranging [-1,-1,-1] to [1,1,1])
                NB: parameter rgb=() is deprecated.  
            colorSpace: 'rgb'
                The color-space to use.
            opacity: 
                How transparent the object will be (0 for transparent, 1 for opaque)
            units : **None**, 'norm', 'cm', 'deg' or 'pix'  
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
        """
        self.win = win
        if win._haveShaders: self._useShaders=True
        else: self._useShaders=False
        self.needUpdate =1
        self.opacity= opacity
        self.contrast= 1.0
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

        if len(units): self.units = units
        else: self.units = win.units
        if self.units=='norm': self._winScale='norm'
        else: self._winScale='pix' #set the window to have pixels coords
        
        self.pos= numpy.array(pos, float)
        
        #height in pix (needs to be done after units)
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
        else: #treat units as pix
            if height==None: self.height = 20
            else: self.height = height
            self.heightPix = self.height
        
        if self.wrapWidth ==None:
            if self.units=='norm': self.wrapWidth=1
            elif self.units in ['deg', 'degs']: self.wrapWidth=15
            elif self.units=='cm': self.wrapWidth=15
            elif self.units in ['pix', 'pixels']: self.wrapWidth=500
        if self.units=='norm': self._wrapWidthPix= self.wrapWidth*win.size[0]/2
        elif self.units in ['deg', 'degs']: self._wrapWidthPix= psychopy.misc.deg2pix(self.wrapWidth, win.monitor)
        elif self.units=='cm': self._wrapWidthPix= psychopy.misc.cm2pix(self.wrapWidth, win.monitor)
        elif self.units in ['pix', 'pixels']: self._wrapWidthPix=self.wrapWidth
                
        for thisFont in fontFiles:
            pyglet.font.add_file(thisFont)
        self.setFont(font)

        #generate the texture and list holders
        self._listID = GL.glGenLists(1)
        if not self.win.winType=="pyglet":
            self._texID = GL.glGenTextures(1)
        #render the text surfaces and build drawing list
        
        self.colorSpace=colorSpace
        if rgb!=None:
            log.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb')
        else:
            self.setColor(color)
            
        self._calcPosRendered()
        self.setText(text) #self.width and self.height get set with text and calcSizeRednered is called
        
        self.needUpdate=True
    def setHeight(self,height):
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
        else: #treat units as pix
            if height==None: self.height = 20
            else: self.height = height
            self.heightPix = self.height            
        #need to update the font to reflect the change
        self.setFont(self.fontname)    
        self.setText(self.text)
    def setFont(self, font):
        """Set the font to be used for text rendering.
        font should be a string specifying the name of the font (in system resources)
        """
        self.fontname=None
        
        if self.win.winType=="pyglet":
            self._font = pyglet.font.load(font, int(self.heightPix), dpi=72, italic=self.italic, bold=self.bold)
            
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
                        log.warning("Found %s but it doesn't end .ttf. Using default font." %fontFilenames[0])
                        self.fontname = pygame.font.get_default_font()

            if self.fontname is not None and os.path.isfile(self.fontname):
                self._font = pygame.font.Font(self.fontname, int(self.heightPix), italic=self.italic, bold=self.bold)
            else:
                try:
                    self._font = pygame.font.SysFont(self.fontname, int(self.heightPix), italic=self.italic, bold=self.bold)
                    self.fontname = font
                    log.info('using sysFont ' + str(font))
                except:
                    self.fontname = pygame.font.get_default_font()
                    log.error("Couldn't find font %s on the system. Using %s instead!\n \
                              Font names should be written as concatenated names all in lower case.\n \
                              e.g. 'arial', 'monotypecorsiva', 'rockwellextra'..." %(font, self.fontname))
                    self._font = pygame.font.SysFont(self.fontname, int(self.heightPix), italic=self.italic, bold=self.bold)
        self.needUpdate = True

    def setText(self,value=None):
        """Set the text to be rendered using the current font
        """
        value = unicode(value)
        if self._useShaders:
            self._setTextShaders(value)
        else:
            self._setTextNoShaders(value)
    def setRGB(self,value, operation=''):
        self._set('rgb', value, operation)
        if not self._useShaders:
            self.setText(self.text)#need to render the text again to a texture
    def setColor(self, color, colorSpace=None, operation=''):
        """Set the color of the stimulus. See `colorSpaces`_ for further information
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
            in one of the `colorSpaces`_. If no color space is specified then the color 
            space most recently used for this stimulus is used again.
            
                myStim.setColor([1.0,-1.0,-1.0], 'rgb')#a red color in rgb space
                myStim.setColor([0.0,45.0,1.0], 'dkl') #DKL space with elev=0, azimuth=45
                myStim.setColor([0,0,255], 'rgb255') #a blue stimulus using rgb255 space
            
            Lastly, a single number can be provided, x, which is equivalent to providing
            [x,x,x]. 
            
                myStim.setColor(255, 'rgb255') #all guns o max
            
        colorSpace : string or None
        
            defining which of the `colorSpaces`_ to use. For strings and hex
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
        _BaseVisualStim.setColor(self, color, colorSpace=colorSpace, operation=operation)
        #but then update text objects if necess
        if not self._useShaders:
            self.setText(self.text)#need to render the text again to a texture
    def _setTextShaders(self,value=None):
        """Set the text to be rendered using the current font
        """
        if value!=None:            
            self.text = value
        
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
            GLU.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, 4, self.width,self.height,
                                  GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pygame.image.tostring( self._surf, "RGBA",1))
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,smoothing)    #linear smoothing if texture is stretched?
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,smoothing)    #but nearest pixel value if it's compressed?

        self.needUpdate = True

    def _updateListShaders(self):
        """
        This is only used with pygame text - pyglet handles all from the draw()
        """
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
#            GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE0_ARB)
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
        self.text = value
        
        if self.win.winType=="pyglet":
            self._pygletTextObj = pyglet.font.Text(self._font, self.text,
                                                       halign=self.alignHoriz, valign=self.alignVert,
                                                       color = (self.rgb[0],self.rgb[1], self.rgb[2], self.opacity),
                                                       width=self._wrapWidthPix,#width of the frame  
                                                       )
            self.width, self.height = self._pygletTextObj.width, self._pygletTextObj.height
        else:   
            self._surf = self._font.render(value, self.antialias,
                                           [self.rgb[0]*127.5+127.5,
                                            self.rgb[1]*127.5+127.5,
                                            self.rgb[2]*127.5+127.5])
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
            GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE0_ARB)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
            #unbind the mask texture regardless
            GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE1_ARB)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            
        if self.win.winType=="pyglet":
            self._pygletTextObj.draw()
        else:             
            GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
            # right bottom
            GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Rtex, Btex)
            GL.glVertex2f(right,bottom)
            # left bottom
            GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Ltex,Btex)
            GL.glVertex2f(left,bottom)
            # left top
            GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Ltex,Ttex)
            GL.glVertex2f(left,top)
            # right top
            GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Rtex,Ttex)
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
        
        #work out next default depth
        if self.depth==0:
            thisDepth = self.win._defDepth
            self.win._defDepth += _depthIncrements[self.win.winType]
        else:
            thisDepth=self.depth

        GL.glPushMatrix()
        GL.glLoadIdentity()#for PyOpenGL this is necessary despite pop/PushMatrix, (not for pyglet)
        #scale and rotate
        prevScale = win.setScale(self._winScale)#to units for translations
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],thisDepth)#NB depth is set already
        GL.glRotatef(self.ori,0.0,0.0,1.0)
        win.setScale('pix', None, prevScale)#back to pixels for drawing surface
        
        if self._useShaders: #then rgb needs to be set as glColor
            #setup color
            if self.colorSpace in ['rgb','dkl','lms']: #these spaces are 0-centred
                desiredRGB = (self.rgb*self.contrast+1)/2.0#RGB in range 0:1 and scaled for contrast
                if numpy.any(desiredRGB**2.0>1.0):
                    desiredRGB=[0.6,0.6,0.4]
                GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)
            else:
                desiredRGB = (self.rgb*self.contrast)/255.0
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

        GL.glEnable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
        GL.glPopMatrix()
    def setUseShaders(self, val=True):
        """Set this stimulus to use shaders if possible.
        """
        if val==True and self.win._haveShaders==False:
            log.warn("Shaders were requested for PatchStim but aren;t available. Shaders need OpenGL 2.0+ drivers")
        if val!=self._useShaders:
            self._useShaders=val
            self.setText(self.text)  
            self.needUpdate=True            
            
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
                 fillColor=(0.0,0.0,0.0),
                 fillColorSpace='rgb',
                 vertices=((-0.5,0),(0,+0.5),(+0.5,0)),
                 closeShape=True,
                 pos= (0,0),
                 ori=0.0,
                 opacity=1.0,
                 depth  =0,
                 interpolate=True,
                 lineRGB=None,
                 fillRGB=None):
        """
        :Parameters:
            win :
                A :class:`~psychopy.visual.Window` object (required)
                
            units :  **None**, 'norm', 'cm', 'deg' or 'pix'  
                If None then the current units of the :class:`~psychopy.visual.Window` will be used. 
                See :ref:`units` for explanation of other options.
                
            lineRGB :
             
                - (r,g,b) or [r,g,b] 
                - or a single intensity value (which will be applied to all guns).
                
                **NB** units range -1:1 (so 0.0 is GREY). See :ref:`rgb` for details.
                
            fillRGB : 
            
                - (r,g,b) or [r,g,b] 
                - or a single intensity value (which will be applied to all guns).
                
                **NB** units range -1:1 (so 0.0 is GREY). See :ref:`rgb` for details.
                
            lineWidth : int (or float?) 
                specifying the line width in **pixels**
                
            vertices : a list of lists or a numpy array (Nx2) 
                specifying xy positions of each vertex
                
            closeShape : True or False
                Do you want the last vertex to be automatically connected to the first?
                
            pos : tuple, list or 2x1 array
                the position of the anchor for the stimulus (relative to which the vertices are drawn)
                
            ori : float or int
                the shape can be rotated around the anchor
                
            opacity : float
                1.0 is opaque, 0.0 is transparent
                
            depth : 0
                This can be used to choose which
                stimulus overlays which. (more negative values are nearer).
                At present the window does not do perspective rendering
                but could do if that's really useful(?!)
                
            interpolate : True or False
                If True the edge of the line will be antialiased.
                
                """
        
        
        self.win = win
        self.opacity = opacity
        self.pos = numpy.array(pos, float)
        self.closeShape=closeShape
        self.lineWidth=lineWidth
        self.interpolate=interpolate
        
        #unit conversions
        if len(units): self.units = units
        else: self.units = win.units
        if self.units=='norm': self._winScale='norm'
        else: self._winScale='pix' #set the window to have pixels coords
        #'rendered' coordinates represent the stimuli in the scaled coords of the window
        #(i.e. norm for units==norm, but pix for all other units)  
        
        self._useShaders=False#since we don't ned to combine textures with colors
        self.lineColorSpace=lineColorSpace
        if lineRGB!=None:
            log.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setLineColor(lineRGB, colorSpace='rgb')
        else:
            self.setLineColor(lineColor, colorSpace=lineColorSpace)
            
        self.fillColorSpace=fillColorSpace
        if fillRGB!=None:
            log.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setFillColor(fillRGB, colorSpace='rgb')
        else:
            self.setFillColor(fillColor, colorSpace=fillColorSpace)
                    
        self.depth=depth
        self.ori = numpy.array(ori,float)
        self.setVertices(vertices)
        self._calcVerticesRendered()
    
    def setLineRGB(self, value, operation=''):
        """DEPRECATED since v1.60.05: Please use setLineColor
        """
        self._set('lineRGB', value, operation)
    def setFillRGB(self, value, operation=''):
        """DEPRECATED since v1.60.05: Please use setFillColor
        """
        self._set('fillRGB', value, operation)
    def setLineColor(self, color, colorSpace=None, operation=''):
        #run the original setColor, which creates color and 
        _setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='lineRGB',#the name for this rgb value
                    colorAttrib='lineColor')#the name for this color
    def setFillColor(self, color, colorSpace=None, operation=''):
        #run the original setColor, which creates color and 
        _setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='fillRGB',#the name for this rgb value
                    colorAttrib='fillColor')#the name for this color
        
    def setVertices(self,value=None, operation=''):
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
        
        if self.depth==0:
            thisDepth = self.win._defDepth
            win._defDepth += _depthIncrements[win.winType]
        else:
            thisDepth=self.depth
        nVerts = self.vertices.shape[0]
        
        #scale the drawing frame etc...
        GL.glPushMatrix()#push before drawing, pop after
        win.setScale(self._winScale)
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],thisDepth)
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
        if self.win.winType == 'pyglet':
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self._verticesRendered.ctypes)#.data_as(ctypes.POINTER(ctypes.c_float)))
        else:
            GL.glVertexPointerd(self._verticesRendered)
                
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        if nVerts>2: #draw a filled polygon first       
            if self.fillRGB!=None:
                #convert according to colorSpace
                if self.fillColorSpace in ['rgb','dkl','lms']: #these spaces are 0-centred
                    fillRGB = (self.fillRGB+1)/2.0#RGB in range 0:1 and scaled for contrast
                else:fillRGB = self.fillRGB/255.0
                #then draw
                GL.glColor4f(fillRGB[0], fillRGB[1], fillRGB[2], self.opacity)
                GL.glDrawArrays(GL.GL_POLYGON, 0, nVerts)
        if self.lineRGB!=None:
                #convert according to colorSpace
            if self.lineColorSpace in ['rgb','dkl','lms']: #these spaces are 0-centred
                lineRGB = (self.lineRGB+1)/2.0#RGB in range 0:1 and scaled for contrast
            else:lineRGB = self.lineRGB/255.0
            #then draw
            GL.glLineWidth(self.lineWidth)
            GL.glTranslatef(0,0,_depthIncrements[win.winType]/2.0)
            GL.glColor4f(lineRGB[0], lineRGB[1], lineRGB[2], self.opacity)
            if self.closeShape: GL.glDrawArrays(GL.GL_LINE_LOOP, 0, nVerts)        
            else: GL.glDrawArrays(GL.GL_LINE_STRIP, 0, nVerts)       
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glPopMatrix()
        

    def _calcVerticesRendered(self):
        self.needVertexUpdate=False
        if self.units in ['norm', 'pix']: 
            self._verticesRendered=self.vertices
            self._posRendered=self.pos
        elif self.units in ['deg', 'degs']:
            self._verticesRendered=psychopy.misc.deg2pix(self.vertices, self.win.monitor)
            self._posRendered=psychopy.misc.deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm': 
            self._verticesRendered=psychopy.misc.cm2pix(self.vertices, self.win.monitor)
            self._posRendered=psychopy.misc.cm2pix(self.pos, self.win.monitor)

def makeRadialMatrix(matrixSize):
    """Generate a square matrix where each element val is
    its distance from the centre of the matrix
    """
    oneStep = 2.0/(matrixSize-1)
    xx,yy = numpy.mgrid[0:2+oneStep:oneStep, 0:2+oneStep:oneStep] -1.0 #NB need to add one step length because
    rad = numpy.sqrt(xx**2 + yy**2)
    return rad

def createTexture(tex, id, pixFormat, stim, res=128):
    """
    id is the texture ID
    pixFormat = GL.GL_ALPHA, GL.GL_RGB
    useShaders is a bool
    interpolate is a bool (determines whether texture will use GL_LINEAR or GL_NEAREST
    res is the resolution of the texture (unless a bitmap image is used)
    """
    
    """
    Create an intensity texture, ranging -1:1.0
    """
    useShaders = stim._useShaders
    interpolate = stim.interpolate
    if type(tex) == numpy.ndarray:
        #handle a numpy array
        #for now this needs to be an NxN intensity array        
        intensity = tex.astype(numpy.float32)
        if intensity.max()>1 or intensity.min()<-1:
            log.error('numpy arrays used as textures should be in the range -1(black):1(white)')
        if len(tex.shape)==3:
            wasLum=False
        else: wasLum = True
        ##is it 1D?
        if tex.shape[0]==1:
            stim._tex1D=True
            res=im.shape[1]
        elif len(tex.shape)==1 or tex.shape[1]==1:
            stim._tex1D=True
            res=tex.shape[0]
        else:
            stim._tex1D=False
            #check if it's a square power of two
            maxDim = max(tex.shape)
            powerOf2 = 2**numpy.ceil(numpy.log2(maxDim))
            if tex.shape[0]!=powerOf2 or tex.shape[1]!=powerOf2:
                log.error("Numpy array textures must be square and must be power of two (e.g. 16x16, 256x256)")      
                core.quit()
            res=tex.shape[0]
    elif tex in [None,"none", "None"]:
        res=1 #4x4 (2x2 is SUPPOSED to be fine but generates wierd colors!)
        intensity = numpy.ones([res,res],numpy.float32)
        wasLum = True
    elif tex == "sin":
        onePeriodX, onePeriodY = numpy.mgrid[0:res, 0:2*pi:2*pi/res]
        intensity = numpy.sin(onePeriodY-pi/2)
        wasLum = True
    elif tex == "sqr":#square wave (symmetric duty cycle)
        onePeriodX, onePeriodY = numpy.mgrid[0:res, 0:2*pi:2*pi/res]
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
        onePeriodX, onePeriodY = numpy.mgrid[0:2*pi:2*pi/res, 0:2*pi:2*pi/res]
        intensity = numpy.sin(onePeriodX-pi/2)*numpy.sin(onePeriodY-pi/2)
        wasLum = True
    elif tex == "sqrXsqr":
        onePeriodX, onePeriodY = numpy.mgrid[0:2*pi:2*pi/res, 0:2*pi:2*pi/res]
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
    else:#might be a filename of an image
        if os.path.isfile(tex):
            im = Image.open(tex)
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        else:
            log.error("couldn't find tex...%s" %(tex))
            core.quit()
            raise #so thatensure we quit

        #is it 1D?
        if im.size[0]==1 or im.size[1]==1:
            log.error("Only 2D textures are supported at the moment")
        else:
            maxDim = max(im.size)
            powerOf2 = int(2**numpy.ceil(numpy.log2(maxDim)))
            if im.size[0]!=powerOf2 or im.size[1]!=powerOf2:
                log.warning("Image '%s' was not a square power-of-two image. Linearly interpolating to be %ix%i" %(tex, powerOf2, powerOf2))
                im=im.resize([powerOf2,powerOf2],Image.BILINEAR)      
                
        #is it Luminance or RGB?
        if im.mode=='L':
            wasLum = True
            intensity= numpy.array(im).astype(numpy.float32)*2/255-1.0 #get to range -1:1
        elif pixFormat==GL.GL_ALPHA:#we have RGB and need Lum
            wasLum = True
            im = im.convert("L")#force to intensity (in case it was rgb)
            intensity= numpy.array(im).astype(numpy.float32)*2/255-1.0 #get to range -1:1            
        elif pixFormat==GL.GL_RGB:#we have RGB and keep it that way
            #texture = im.tostring("raw", "RGB", 0, -1)
            im = im.convert("RGBA")#force to rgb (in case it was CMYK or L)
            intensity = numpy.array(im).astype(numpy.float32)*2/255-1
            wasLum=False
            
    if pixFormat==GL.GL_RGB and wasLum and useShaders:
        #keep as float32 -1:1
        internalFormat = GL.GL_RGB32F_ARB
        dataType = GL.GL_FLOAT
        data = numpy.ones((intensity.shape[0],intensity.shape[1],3),numpy.float32)#initialise data array as a float
        data[:,:,0] = intensity#R
        data[:,:,1] = intensity#G
        data[:,:,2] = intensity#B
    elif pixFormat==GL.GL_RGB and wasLum:#and not using shaders
        #scale by rgb and convert to ubyte
        internalFormat = GL.GL_RGB
        dataType = GL.GL_UNSIGNED_BYTE
        data = numpy.ones((intensity.shape[0],intensity.shape[1],3),numpy.float32)#initialise data array as a float
        data[:,:,0] = intensity*stim.rgb[0]  + stim.rgbPedestal[0]#R
        data[:,:,1] = intensity*stim.rgb[1]  + stim.rgbPedestal[1]#G
        data[:,:,2] = intensity*stim.rgb[2]  + stim.rgbPedestal[2]#B
        #convert to ubyte
        if stim.colorSpace=='rgb':#scale up to 255 for non-shaders ubyte data
            data = psychopy.misc.float_uint8(stim.contrast*data)
        else:#just convert data type
            data = (stim.contrast*data).astype(numpy.ubyte)
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
    
    if stim.win.winType=='pygame':
        texture = data.tostring()#serialise
    else:#pyglet on linux needs ctypes instead of string object!?
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
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_NEAREST)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                data.shape[0],data.shape[1], 0,
                pixFormat, dataType, texture)
        else:#use glu
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_NEAREST)  
            GLU.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, internalFormat,
                data.shape[0],data.shape[1], pixFormat, dataType, texture)          
    else:
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST) 
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST) 
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                        data.shape[0],data.shape[1], 0,
                        pixFormat, dataType, texture)
        
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)#?? do we need this - think not!

def _setTexIfNoShaders(obj):
    """Useful decorator for classes that need to update Texture after other properties
    """
    if hasattr(obj, 'setTex') and hasattr(obj, '_texName') and not obj._useShaders: 
        obj.setTex(obj._texName)
        
def _setColor(self, color, colorSpace=None, operation='',
                rgbAttrib='rgb', #or 'fillRGB' etc
                colorAttrib='color'):#or 'fillColor' etc
    """Provides the workings needed by setColor, and can perform this for
    any arbitrary color type (e.g. fillColor,lineColor etc)  
    """
    
    #ho this works:
    #rather than using self.rgb=rgb this function uses setattr(self,'rgb',rgb)
    #color represents the color in the native space
    #colorAttrib is the name that color will be assigned using setattr(self,colorAttrib,color)
    #rgb is calculated from converting color
    #rgbAttrib is the attribute name that rgb is stored under, e.g. lineRGB for self.lineRGB
    #colorSpace and takes name from colorAttrib+space e.g. self.lineRGBSpace=colorSpace
    
    if type(color) in [str, unicode]:
        if color.lower() in colors.colors255.keys():
            #set rgb, color and colorSpace
            setattr(self,rgbAttrib,numpy.array(colors.colors255[color.lower()], float))
            setattr(self,colorAttrib+'Space','named')#e.g. self.colorSpace='named'
            setattr(self,colorAttrib,color) #e.g. self.color='red'
            _setTexIfNoShaders(self)
            return
        elif color[0]=='#' or color[0:2]=='0x':
            setattr(self,rgbAttrib,numpy.array(colors.hex2rgb255(color)))#e.g. self.rgb=[0,0,0]
            setattr(self,colorAttrib,color) #e.g. self.color='#000000'
            setattr(self,colorAttrib+'Space','hex')#e.g. self.colorSpace='hex'
            _setTexIfNoShaders(self)
            return
#                except:
#                    pass#this will be handled with AttributeError below
        #we got a string, but it isn't in the list of named colors and doesn't work as a hex
        raise AttributeError("PsychoPy can't interpret the color string '%s'" %color)
    elif type(color) in [float, int]:
        color = numpy.asarray([color,color,color],float)
    elif type(color) in [tuple,list]:
        color = numpy.asarray(color,float)
    elif type(color) ==numpy.ndarray:
        pass
    elif color==None:
        setattr(self,rgbAttrib,None)#e.g. self.rgb=[0,0,0]
        setattr(self,colorAttrib,None) #e.g. self.color='#000000'
        setattr(self,colorAttrib+'Space',None)#e.g. self.colorSpace='hex'
        _setTexIfNoShaders(self)
    else:
        raise AttributeError("PsychoPy can't interpret the color %s (type=%s)" %(color, type(color)))
    
    #at this point we have a numpy array of 3 vals (actually we haven't checked that there are 3)
    #check if colorSpace is given and use self.colorSpace if not
    if colorSpace==None: colorSpace=getattr(self,colorAttrib+'Space')
    #check whether combining sensible colorSpaces (e.g. can't add things to hex or named colors)
    if getattr(self,colorAttrib+'Space') in ['named','hex']:
            raise AttributeError("setColor() cannot combine ('%s') colors within 'named' or 'hex' color spaces"\
                %(operation))
    if operation!='' and colorSpace!=getattr(self,colorAttrib+'Space') :
            raise AttributeError("setColor cannot combine ('%s') colors from different colorSpaces (%s,%s)"\
                %(operation, self.colorSpace, colorSpace))
    else:#OK to update current color
        exec('self.%s %s= color' %(colorAttrib, operation))#if no operation then just assign
    #convert new self.color to rgb space
    newColor=getattr(self, colorAttrib)
    if colorSpace in ['rgb','rgb255']: setattr(self,rgbAttrib, newColor)
    elif colorSpace=='dkl':
        if numpy.all(self.win.dkl_rgb==numpy.ones([3,3])):dkl_rgb=None
        else: dkl_rgb=self.win.dkl_rgb
        setattr(self,rgbAttrib, colors.dkl2rgb(numpy.asarray(newColor).transpose(), dkl_rgb) )
    elif colorSpace=='lms': 
        if numpy.all(self.win.lms_rgb==numpy.ones([3,3])):lms_rgb=None
        else: lms_rgb=self.win.lms_rgb
        setattr(self,rgbAttrib, colors.lms2rgb(newColor, lms_rgb) )
    else: log.error('Unknown colorSpace: %s' %colorSpace)
    setattr(self,colorAttrib+'Space', colorSpace)#store name of colorSpace for future ref and for drawing
    #if needed, set the texture too
    _setTexIfNoShaders(self)
    
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
        myStim = PatchStim(myWin, tex='sin', mask='gauss', size=[.6*y/float(x),.6], sf=3.0, opacity=.2)
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
            wait(delayTime)
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
    #print "draw=%.1fms free=%.1fms pad=%.1fms" % (msdrawAvg,msfree,msDelay)
    
    return msPFavg, msPFstd, msPFmed #, msdrawAvg, msdrawSD, msfree


class RatingScale():
    """Returns a rating-scale object, with display parameters defined during init(). To get a rating,
    call rate(item-string). This will display the scale + item, get the subject's response, and
    return the response info (rating, decision time, scale-info-list). If item is an image file name,
    the image will be displayed. Otherwise, a text string is displayed.
    
    Example: see PsychoPy Coder demo 'ratingScale.py'
    
    Status: coding is in-progress; needs more documentation, esp of the logic & internal representation
        and would benefit from being cleaned up and tightened up.
    
    Auto-rescaling happens if the low-anchor is 0 and high-low is a multiple of 10 (see ratingScale.py demo, example 2).
    
    :Author:
        - 2010 Jeremy Gray
    """
    def __init__(self, win, scale=None, low=1, high=7, precision=1, showValue=True, 
                markerStyle='triangle', markerColor=None, markerExpansion=1, markerStart=False, lowLine=False):
        """
        :Parameters:
            win :
                A :class:`~psychopy.visual.Window` object (required)
            scale :
                string, explanation of the numbers to display to the subject; *None* -> <low>=not at all, <high>=extremely
            low :
                low anchor (integer, default = 1)
            high :
                high anchor (integer, default = 7; reset to low+1 if <= low)
            precision :
                portions of a tick to accept as input [1,10,100], default = 1 tick (no fractional part)
            showValue :
                True, show the currently selected number
            markerStyle :
                *'triangle'* (DarkBlue default), 'circle' (Black default), or 'glow' (White default)
            markerColor :
                *None* = use defaults; or any legal RGB colorname, e.g., '#123456', 'DarkRed'
            markerExpansion :
                how much the glow marker expands when moving to the right; 0=none, negative shrinks; try 10 or -10
            markerStart :
                *False*, or the value [low..high] to be pre-selected upon initial display
            lowLine :
                *False*, whether to shift the rating line low on the screen (eg, to leave more of the screen for images)
        """
        self.win = win
        self.savedWinUnits = self.win.units
        self.win.units = 'norm'
        
        # tick mark stuff; only draw a tick at integer spacing
        self.high = int(high) # high anchor of scale
        self.low = int(low) # low anchor
        self.precision = precision
        if self.high <= self.low:
            self.high = self.low + 1
            self.precision = 100
        self.tickMarks = self.high - self.low
        # ticks are the units the scale uses internally: 0..(high-low)
        # the screen position for a given tickMark == screenLeftEnd + tickMark * screenSpaceBetweenTicks
        # and finally allow for global size changes: multiply the above by displaySizeFactor
        
        # remap 10 ticks onto 1 tick in some conditions:
        self.autoRescaleFactor = 1 
        if self.low == 0 and self.tickMarks > 20 and self.tickMarks % 10 == 0:
            self.autoRescaleFactor = 10
            self.tickMarks /= self.autoRescaleFactor 
            self.precision = min(100, self.precision * self.autoRescaleFactor)
        tickSize = 0.04 # vertical height of each tick, norm units
        self.leftEnd = -0.5 # and possibly resized by displaySizeFactor
        
        if markerStart and markerStart >= self.low and markerStart <= self.high:
            self.markerStart = markerStart
            self.markerPlacedAt = markerStart
            self.markerPlaced = True
        else:
            self.markerStart = None
            self.markerPlaced = False
        
        self.showValue = showValue
        self.markerColor = markerColor
        self.markerStyle = markerStyle
        
        self.padSize = 0.05 # space above/below the line within which to accept mouse input, 1x above, 2x below
        self.offsetVert = -0.3 # shift everything up/down by this amount; -0.7 is good for images
        if lowLine: self.offsetVert = -0.7
        self.offsetHoriz = 0.0 # horiz offset not implemented; everything happens at horiz center of screen
        
        self.minimumTime = 1 # seconds until a response can be accepted
        
        displaySizeFactor = 1 # placeholder to enable resizing the display to free up more of the screen for presenting an image
        if self.precision not in [1, 10, 100]:
            self.precision = 1
        self.snapToTick = self.precision
        self.textSize = 0.12 * displaySizeFactor # for large text, needed
        textSizeSmall = self.textSize * 0.6 # ratio of small text to large text
        self.showValue = showValue in [True, 1]
        
        self.displaySizeFactor = 0.6 * displaySizeFactor
        self.markerSize = 5.0 * displaySizeFactor
        self.markerExpansion = float(markerExpansion) * 0.6
        self.offsetVert = self.offsetVert/displaySizeFactor
        
        self.respKeys = [] # what keyboard keys are accepted for selecting a response
        if self.low > 0 and self.high < 10: # allow responding via numeric keys if the only options are in 1-9
            self.respKeys = [str(i) for i in range(low, high + 1)]
        self.acceptKeys = ['return'] # what keys are allow for accepting the currently selected response
        self.escapeKeys = [] #['escape'] # return None, None, None
        
        # define vertices for making a ShapeStim line with tick marks:
        vertices = [[self.leftEnd * self.displaySizeFactor, self.offsetVert]] # first vertex
        if self.tickMarks:
            for t in range(self.tickMarks + 1):
                vertices.append([self.displaySizeFactor * (self.leftEnd + t / float(self.tickMarks)),
                                 tickSize * self.displaySizeFactor + self.offsetVert])
                vertices.append([self.displaySizeFactor * (self.leftEnd + t / float(self.tickMarks)),
                                 self.offsetVert])
                if t < self.tickMarks: 
                    vertices.append([self.displaySizeFactor * (self.leftEnd + (t + 1) / float(self.tickMarks)),
                                self.offsetVert])
        else:
            self.tickMarks = 1 
        vertices.append([-1 * self.leftEnd * self.displaySizeFactor, self.offsetVert])
        vertices.append([self.leftEnd * self.displaySizeFactor, self.offsetVert])
        self.line = ShapeStim(win=self.win, units='norm', vertices=vertices, lineWidth=4,
                              lineColor='White', lineColorSpace='rgb')
        
        # define the marker:
        if markerColor and type(markerColor) == type('abc'):
            markerColor = markerColor.replace(' ','')
        if self.markerStyle == 'triangle':
            vertices = [[-1 * tickSize * self.displaySizeFactor * 1.8, tickSize * self.displaySizeFactor * 3],
                    [ tickSize * self.displaySizeFactor * 1.8, tickSize * self.displaySizeFactor * 3], [0, -0.005]]
            if markerColor == None:
                markerColor = 'DarkBlue'
            try:
                self.marker = ShapeStim(win=self.win, units='norm', vertices=vertices, lineWidth=0.1,
                                        lineColor=markerColor, fillColor=markerColor, fillColorSpace='rgb')
            except:
                self.marker = ShapeStim(win=self.win, units='norm', vertices=vertices, lineWidth=0.1,
                                        lineColor=markerColor, fillColor='DarkBlue', fillColorSpace='rgb')
            self.markerExpansion = 0
        elif self.markerStyle in ['glow']:
            if markerColor == None:
                markerColor = 'White'
            try:
                self.marker = PatchStim(win=self.win, tex='sin', mask='gauss', color=markerColor,
                                        colorSpace='rgb', opacity = 0.85)
            except: # bad markerColor, presumably:
                self.marker = PatchStim(win=self.win, tex='sin', mask='gauss', color='White',
                                        colorSpace='rgb', opacity = 0.85) 
            self.markerBaseSize = tickSize * self.markerSize
            if self.markerExpansion == 0:
                self.markerBaseSize *= self.markerSize * self.displaySizeFactor
        elif self.markerStyle == 'circle':
            if markerColor == None:
                markerColor = 'Black'
            x,y = self.win.size
            size = [3.2 * tickSize * self.displaySizeFactor * float(y)/x, 3.2 * tickSize * self.displaySizeFactor]
            try:
                self.marker = PatchStim(win=self.win, tex=None, units='norm', size=size,
                                        mask='circle', color=markerColor, colorSpace='rgb')
            except: # user gave a bad markerColor, presumably:
                self.marker = PatchStim(win=self.win, tex=None, units='norm', size=size,
                                        mask='circle', color='Black', colorSpace='rgb') 
            self.markerBaseSize = tickSize
        else:
            raise # need to use markerStyle in ['triangle','glow','circle']
        
        # define the 'accept' box:
        acceptBoxtop = self.offsetVert - 0.12
        acceptBoxbot = self.offsetVert - 0.22
        acceptBoxleft = self.offsetHoriz - 0.12  # offsetHoriz is not fully implemented, merely set to 0
        acceptBoxright = self.offsetHoriz + 0.12
        if self.low > 0 and self.high < 10:
            self.keyClick = 'key, click' # text to display inside accept box before a marker has been placed
        else:
            self.keyClick = 'click line'
        self.accept = TextStim(win=self.win, text=self.keyClick, font='Helvetica', pos=[0, (acceptBoxtop + acceptBoxbot) / 2.],
                          italic=True, height=textSizeSmall, color='#444444', colorSpace='rgb')
        delta = 0.02
        delta2 = delta / 7 
        acceptBoxVertices = [ # a rectangle with rounded corners; for square corners, set delta2 to 0
            [acceptBoxleft,acceptBoxtop-delta], [acceptBoxleft+delta2,acceptBoxtop-3*delta2],
            [acceptBoxleft+3*delta2,acceptBoxtop-delta2], [acceptBoxleft+delta,acceptBoxtop],   
            [acceptBoxright-delta,acceptBoxtop], [acceptBoxright-3*delta2,acceptBoxtop-delta2],
            [acceptBoxright-delta2,acceptBoxtop-3*delta2], [acceptBoxright,acceptBoxtop-delta],  
            [acceptBoxright,acceptBoxbot+delta],[acceptBoxright-delta2,acceptBoxbot+3*delta2],
            [acceptBoxright-3*delta2,acceptBoxbot+delta2], [acceptBoxright-delta,acceptBoxbot],
            [acceptBoxleft+delta,acceptBoxbot], [acceptBoxleft+3*delta2,acceptBoxbot+delta2],
            [acceptBoxleft+delta2,acceptBoxbot+3*delta2], [acceptBoxleft,acceptBoxbot+delta] ]
        self.acceptBox = ShapeStim(win=self.win, vertices=acceptBoxVertices,
                                   fillColor=[.2,.2,.2], lineColor=[-.2,-.2,-.2])
        self.acceptBoxtop = acceptBoxtop
        self.acceptBoxbot = acceptBoxbot
        self.acceptBoxleft = acceptBoxleft
        self.acceptBoxright = acceptBoxright
        if markerColor.lower() in ['white', 'gold']: # ideally, catch any very light color
            self.acceptTextColor = '#444444'
        else:
            self.acceptTextColor = markerColor
        
        # text elements:
        if not scale: # set the default
            scale = str(self.low) + ' = not at all  . . .  ' + str(self.high) + ' = extremely'
        scale = unicode(scale)
        self.psyScaleDescription = TextStim(win=self.win, text=scale, height=textSizeSmall,
                                            color='LightGray', colorSpace='rgb', pos=[0, 0.15 + self.offsetVert])
        self.lowAnchor = TextStim(win=self.win, text=str(self.low), pos=[self.leftEnd * self.displaySizeFactor,
                        -2 * textSizeSmall * self.displaySizeFactor + self.offsetVert], height=textSizeSmall,
                        color='LightGray', colorSpace='rgb')
        self.highAnchor = TextStim(win=self.win, text=str(self.high), pos=[-1 * self.leftEnd * self.displaySizeFactor,
                        -2 * textSizeSmall * self.displaySizeFactor + self.offsetVert], height=textSizeSmall,
                        color='LightGray', colorSpace='rgb')
        
        decPts = int(numpy.log10(self.precision))
        self.fmtStr = "%." + str(decPts) + "f"
        self.accept.setFont('Helvetica Bold')
        
        self.myMouse = event.Mouse(win=self.win, visible=True)
        
        # visual elements, in their drawing order. line would disappear for winXP if it came first
        self.visualDisplayElements = [self.psyScaleDescription, self.lowAnchor, self.highAnchor,
                                      self.acceptBox, self.accept, self.line]
        
        self.win.units = self.savedWinUnits
            
    def rate(self, item, color=None):
        """Obtain a self-reported rating for an item, using this RatingScale.
        
        Shows the item (unicode), optional color, along with visual display elements that were set at object creation.
        Returns the rating, the seconds taken, and info about the scale in a list [low, high, precision, item, scale-description]
        """
        self.savedWinUnits = self.win.units 
        self.win.units = 'norm'
        item = unicode(item)
        try:
            img = Image.open(item) # check if its an image, no performance hit just to open
            x,y = self.win.size
            #targetItem = PatchStim(win=self.win, tex=item, units='pix', size=img.size, pos=[0, y/5.5]) # takes longer, warns about interpolating
            targetItem = SimpleImageStim(win=self.win, image=item, units='pix', pos=[0, y/7])
        except IOError: # its not an image file
            targetItem = TextStim(win=self.win, text=item, height=self.textSize, pos=[0, 0.4 + self.offsetVert],
                   color='LightGray', colorSpace='rgb')
            if not color:
                color = 'White'
            try:
                targetItem.setColor(color, 'rbg')
            except:
                targetItem.setColor('White', 'rbg')
        
        self.markerPlaced = bool(self.markerStart not in [None, False]) # do allow 0 as a legal pre-placement
        if self.markerPlaced:
            markerPlacedAt = self.markerStart - self.low
        self.acceptBox.setFillColor([.2,.2,.2], 'rgb')
        self.acceptBox.setLineColor([-.2,-.2,-.2], 'rgb')
        self.accept.setColor('#444444','rgb')
        self.accept.setText(self.keyClick)
        
        event.clearEvents()
        myClock = core.Clock()
        acceptResponse = False
        frame = 0 # only used to pulse the 'accept' box
        pulse = 0.25 # larger is more salient
        framesPerCycle = 16.
        
        while not acceptResponse:
            # draw everything except the marker:
            for stim in [targetItem] + self.visualDisplayElements:
                stim.draw() 
            # if the marker has been placed on the line, update its position and draw it:
            if self.markerPlaced: # markerPlaced means that a provisional value has been indicated
                frame += 1
                # set 'accept' box pulsing & display text:
                pulseColor = 0.6 + pulse * float(cos(frame / float(framesPerCycle))) # cast to float to avoid numpy_type from cos
                self.acceptBox.setFillColor(pulseColor, 'rgb')
                self.acceptBox.setLineColor(pulseColor, 'rgb')
                self.accept.setColor(self.acceptTextColor, 'rgb')
                if self.showValue:
                    self.accept.setText(self.fmtStr % ((markerPlacedAt + self.low) * self.autoRescaleFactor ))    
                else:
                    self.accept.setText("accept?")
                
                # set the marker's screen position based on its tick coordinate (== markerPlacedAt)
                self.marker.setPos([self.displaySizeFactor * (self.leftEnd + markerPlacedAt / float(self.tickMarks)), self.offsetVert])
                # expansion fun & games with 'glow':
                if self.markerStyle == 'glow':
                    if self.markerExpansion > 0: 
                        self.marker.setSize(self.markerBaseSize + 0.1 * self.markerExpansion * float(markerPlacedAt) / self.tickMarks)
                        self.marker.setOpacity(0.2 + float(markerPlacedAt) / self.tickMarks)
                    elif self.markerExpansion < 0:
                        self.marker.setSize(self.markerBaseSize - 0.1 * self.markerExpansion * float(self.tickMarks - markerPlacedAt) / self.tickMarks)
                        self.marker.setOpacity(0.2 + 1 - float(markerPlacedAt) / self.tickMarks)
                    else: # and markerExpansion == 0:
                        self.marker.setSize(self.markerBaseSize)
                
                self.marker.draw()
            
            # handle key responses:
            for key in event.getKeys(): # almost certainly only 1 key
                if key in self.escapeKeys: # to enable this, set escapeKeys = ['escape'] or whatever in __init__()
                    self.win.units = self.savedWinUnits
                    return None, None, None
                if key in self.respKeys: # place the marker at that tick
                    self.markerPlaced = True
                    markerPlacedAt = (int(key) - self.low) * self.autoRescaleFactor # 0..tickMarks in tick units, rescaled
                    self.marker.setPos([self.displaySizeFactor * (self.leftEnd + markerPlacedAt / float(self.tickMarks)), 0])
                if key in ['left']:
                    if self.markerPlaced and markerPlacedAt > 0:
                        markerPlacedAt = max(0, markerPlacedAt - 1)
                if key in ['right']:
                    if self.markerPlaced and markerPlacedAt < self.tickMarks:
                        markerPlacedAt = min(self.tickMarks, markerPlacedAt + 1)
                if self.markerPlaced and key in self.acceptKeys and myClock.getTime() > self.minimumTime:
                    acceptResponse = True # which ends the loop
                    
            # handle mouse:
            mouse1, m2, m3 = self.myMouse.getPressed()
            if mouse1:
                # set marker based on mouse? if mouse is pressed and its near the line, set the marker to mouseX:
                mouseX, mouseY = self.myMouse.getPos()
                if mouseY > -2 * self.padSize + self.offsetVert and \
                        mouseY < self.padSize + self.offsetVert and \
                        mouseX > self.leftEnd * self.displaySizeFactor - self.padSize and \
                        mouseX < -1 * self.leftEnd * self.displaySizeFactor + self.padSize:
                    mouseX = max(mouseX, self.leftEnd * self.displaySizeFactor)
                    mouseX = min(mouseX, -1 * self.leftEnd * self.displaySizeFactor)
                    self.markerPlaced = True
                    markerPos = mouseX * self.tickMarks / self.displaySizeFactor + self.tickMarks/2. # mouseX==0 -> mid-point of tick scale
                    if markerPos < 0: markerPos = 0
                    if self.snapToTick == 1:
                        markerPlacedAt = int(markerPos+.5) # round to nearest tick; scale to 0..tickMarks, quantized
                    else:
                        markerPlacedAt = int(self.snapToTick * float(markerPos)) / float(self.snapToTick)  # scale to 0..tickMarks
                # accept marker?
                if self.markerPlaced and myClock.getTime() > self.minimumTime and mouseY > self.acceptBoxbot and \
                        mouseY < self.acceptBoxtop and mouseX > self.acceptBoxleft and mouseX < self.acceptBoxright:
                    acceptResponse = True # which ends the loop
            
            event.clearEvents()
            self.win.flip()
            
        self.win.units = self.savedWinUnits
        decisionTime = myClock.getTime()
        if self.precision == 1: # set type for the response, based on what was wanted
            response = int(markerPlacedAt) * self.autoRescaleFactor 
        else:
            response = float(markerPlacedAt) * self.autoRescaleFactor 

        return (response + self.low), decisionTime, [self.low, self.high, self.precision, item, self.psyScaleDescription.text]
    
    def rateDimensions(self, item, dimensions, color=None):
        """rate a single item on each of several dimensions (given as a list of strings).
        
        each string will be displayed as a description of the numeric scale, instead of the scale defined at __init__()
        """
        data = []
        for d in dimensions:
            self.psyScaleDescription.setText(d)
            data.append(self.rate(item, color=color))
        return data
