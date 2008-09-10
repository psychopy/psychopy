"""To control the screen and visual stimuli for experiments
"""
import psychopy.misc
import psychopy #so we can get the __path__
from psychopy import core, ext, log
import psychopy.event
import monitors
import Image
import sys, os, time, glob, copy
import makeMovies

import numpy
from numpy import sin, cos, pi

#shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
try:
    import ctypes
    import pyglet
    #pyglet.options['debug_gl'] = False#must be done before importing pyglet.gl or pyglet.window
    import pyglet.gl, pyglet.window, pyglet.image, pyglet.font, pyglet.media
    import _shadersPyglet
    havePyglet=True    
except:
    havePyglet=False    

try:
    import pygame
    import OpenGL.GL, OpenGL.GLU, OpenGL.GL.ARB.multitexture
    import _shadersPygame
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
    using either PyGame (python's SDL binding) or GLUT.
    These two types have different structure but can achieve
    similar results. Pygame follows a procedural model, that
    is you specify from line to line what happens next. This
    is usually more intuitive for psychophysics exps. Glut
    uses a callback or event-driven model, where you specify
    functions to be run on certain events (when a button is
    pressed do...).
    """
    def __init__(self,
                 size = (800,600),
                 pos = None,
                 rgb = (0.0,0.0,0.0),
                 dkl=None,
                 lms=None,
                 fullscr = 0,
                 allowGUI=True,
                 monitor=dict([]),
                 bitsMode=None,
                 winType=None,
                 units='norm',
                 gamma = None,
                 blendMode='avg',
                 screen=0):
        """
        **Arguments:**

            - **size** :  size of the window in pixels (X,Y)
            - **rgb** :  background color (R,G,B) from -1.0 to 1.0
            - **fullScr** :  0(in a window), 1(fullscreen) NB Try using fullScr=0, allowGUI=0
            - **allowGUI** :  0,1 If set to 1, window will be drawn with no frame and no buttons to close etc...
            - **winType** :  'pyglet', 'pygame' or 'glut' (if None then PsychoPy will try to use Pyglet, Pygame, GLUT in that order)
            - **monitor** :  the name of your monitor (from MonitorCentre) or an actual ``Monitor`` object
            - **units** :  'norm' (normalised),'deg','cm','pix' Defines the default units of stimuli drawn in the window (can be overridden by each stimulus)
            
        The following args will override **monitor** settings(see above):

            - **gamma** : 1.0, monitor gamma for linearisation (will use Bits++ if possible)
            - **bitsMode** : None, 'fast', ('slow' mode is deprecated). Defines how (and if) the Bits++ box will be used. 'Fast' updates every frame by drawing a hidden line on the top of the screen.

        """
        global haveShaders
        self.size = numpy.array(size, numpy.int)
        self.pos = pos                 
        if type(rgb)==float or type(rgb)==int: #user may give a luminance val
            self.rgb=numpy.array((rgb,rgb,rgb), float)
        else:
            self.rgb = numpy.asarray(rgb, float)
        self._defDepth=0.0

        #settings for the monitor: local settings (if available) override monitor
        #if we have a monitors.Monitor object (psychopy 0.54 onwards)
        #convert to a Monitor object
        if monitor==None:
            monitor = monitors.Monitor('__blank__')
        if type(monitor)==str:
            monitor = monitors.Monitor(monitor)
        elif type(monitor)==dict:
            #convert into a monitor object
            monitor = monitors.Monitor('temp',currentCalib=monitor,verbose=False)
        self.monitor = monitor

        #otherwise monitor will just be a dict
        self.scrWidthCM=monitor.getWidth()
        self.scrDistCM=monitor.getDistance()

        scrSize = monitor.getSizePix()
        if scrSize==None:
            self.scrWidthPIX=None
        else:self.scrWidthPIX=scrSize[0]

        if fullscr: self._isFullScr=1
        else:   self._isFullScr=0
        self.units = units
        self.screen = screen

        if blendMode=='add' and not haveFB:
            log.warning("""User requested a blendmode of "add" but framebuffer objects not available. You need PyOpenGL3.0+ to use this blend mode""")
            self.blendMode='average' #resort to the simpler blending without float rendering
        else: self.blendMode=blendMode

        #setup bits++ if possible
        self.bitsMode = bitsMode #could be [None, 'fast', 'slow']
        if self.bitsMode!=None:
            from psychopy import bits
            self.bits = bits.BitsBox(self)
            self.haveBits = True

        #gamma
        if self.bitsMode!=None and hasattr(monitor, 'lineariseLums'):
            #ideally we use bits++ and provide a complete linearised lookup table
            #using monitor.lineariseLums(lumLevels)
            self.gamma=None
        if gamma != None and (type(gamma) in [float, int]):
            #an integer that needs to be an array
            self.gamma=[gamma,gamma,gamma]
        elif gamma != None:# and (type(gamma) not in [float, int]):
            #an array (hopefully!)
            self.gamma=gamma
        elif type(monitor.getGammaGrid())==numpy.ndarray:
            self.gamma = monitor.getGammaGrid()[1:,2]
        elif monitor.getGamma()!=None:
            self.gamma = monitor.getGamma()
        else: self.gamma = [1.0,1.0,1.0] #gamma wasn't set anywhere
        
        #colour conversions
        dkl_rgb = monitor.getDKL_RGB()
        if dkl_rgb!=None:
            self.dkl_rgb=dkl_rgb
        else: self.dkl_rgb = None
        lms_rgb = monitor.getLMS_RGB()
        if lms_rgb!=None:
            self.lms_rgb=lms_rgb
        else: self.lms_rgb = None

        #setup context and openGL()
        self.allowGUI = allowGUI
        if winType is None:#choose the default windowing
            if havePyglet: winType="pyglet"
            elif havePygame: winType="pygame"
            else: winType='glut'
        if winType is "glut": self._setupGlut()
        elif winType is "pygame": self._setupPygame()
        elif winType is "pyglet": self._setupPyglet()
        self._setupGL()

        self.frameClock = core.Clock()#from psycho/core
        self.frames = 0         #frames since last fps calc
        self.movieFrames=[] #list of captured frames (Image objects)

        self.setGamma(self.gamma)#using either pygame or bits++
        self.lastFrameT = time.time()
        self.update()#do a screen refresh straight away



    def whenIdle(self,func):
        """Defines the function to use during idling (GLUT only)
        """
        GLUT.glutIdleFunc(func)
    def onResize(self, width, height):
        '''A default resize event handler.

        This default handler updates the GL viewport to cover the entire
        window and sets the ``GL_PROJECTION`` matrix to be orthagonal in
        window space.  The bottom-left corner is (0, 0) and the top-right
        corner is the width and height of the window in pixels.

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

        self.frames +=1
        now = core.getTime()
        deltaT = now - self.lastFrameT; self.lastFrameT=now
        if deltaT>1/60.0: log.warning('t of last frame was %.2fms (=1/%i)' %(deltaT*1000, 1/deltaT))

        if haveFB:
            #set rendering back to the framebuffer object
            FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, self.frameBuffer)
            
        #reset returned buffer for next frame
        if clearBuffer: GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        else: GL.glClear(GL.GL_DEPTH_BUFFER_BIT)#always clear the depth bit
        self._defDepth=0.0#gets gradually updated through frame
        
    def update(self):
        """Deprecated: use Window.flip() instead        
        """
        self.flip(clearBuffer=True)#clearBuffer was the original behaviour for win.update()
        
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

    def saveMovieFrames(self, fileName, mpgCodec='mpeg1video'):
        """
        Writes any captured frames to disk. Will write any format
        that is understood by PIL (tif, jpg, bmp, png...)

        Usage:
            - ``myWin.writeMovieFrames('frame.tif')``
                #writes a series of frames as frame001.tif, frame002.tif etc...

        """
        fileRoot, fileExt = os.path.splitext(fileName)
        if len(self.movieFrames)==0:
            log.error('no frames to write - did you forget to update your window?')
            return
        else:
            log.info('writing %i frames' %len(self.movieFrames))
        if fileExt=='.gif': makeMovies.makeAnimatedGIF(fileName, self.movieFrames)
        elif fileExt in ['.mpg', '.mpeg']: makeMovies.makeMPEG(fileName, self.movieFrames, codec=mpgCodec)
        elif len(self.movieFrames)==1:
            self.movieFrames[0].save(fileName)
        else:
            frame_name_format = "%s%%0%dd%s" % (fileRoot, numpy.ceil(numpy.log10(len(self.movieFrames)+1)), fileExt)            for frameN, thisFrame in enumerate(self.movieFrames):               thisFileName = frame_name_format % (frameN+1,)               thisFrame.save(thisFileName) 

    def fullScr(self):
        """Toggles fullscreen mode (GLUT only).

        Fullscreen mode for PyGame contexts must be set during initialisation
        of the Window() class
        """
        if self.winType is 'glut':
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
        if self.winType is 'GLUT':
            GLUT.glutDestroyWindow(self.handle)
        elif self.winType is 'pyglet':
            self.winHandle.close()
        else:
            #pygame.quit()
            pygame.display.quit()
        if self.bitsMode is not None:
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

    def setScale(self, units, font='dummyFont', prevScale=[1.0,1.0]):
        """This method is called from within the draw routine and sets the
        scale of the OpenGL context to map between units. Could potentially be
        called by the user in order to draw OpenGl objects manually
        in each frame.

        The **units** can be 'norm'(normalised),'pix'(pixels),'cm' or
        'stroke_font'. The **font** argument is only used if units='stroke_font'
        """
        if units is "norm":
            thisScale = numpy.array([1.0,1.0])
        elif units in ["pix", "pixels"]:
            thisScale = 2.0/numpy.array(self.size)
        elif units is "cm":
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
        elif units is "stroke_font":
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
            self.bits.setGamma(self.gamma)
        elif self.winType=='pygame':
            pygame.display.set_gamma(self.gamma[0], self.gamma[1], self.gamma[2])
            
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
        self.winType = "pyglet"
        #setup the global use of pyglet.gl
        global GL, GLU, GL_multitexture
        GL = pyglet.gl
        GLU = pyglet.gl
        GL_multitexture = pyglet.gl
        
        config = GL.Config(depth_size=8, double_buffer=True)
        allScrs = pyglet.window.get_platform().get_default_display().get_screens()
        if len(allScrs)>self.screen:
            thisScreen = allScrs[self.screen]
            print 'configured pyglet screen %i' %self.screen
        else: 
            print "Requested an unavailable screen number"
        if self._isFullScr:
            w,h = None,None
        else:
            w,h = self.size
        if self.allowGUI: style=None
        else: style='borderless'
        self.winHandle = pyglet.window.Window(width=w, height=h,
                                              caption="PsychoPy", 
                                              fullscreen=self._isFullScr,
                                              config=config,
                                              screen=thisScreen,
                                              style=style
                                          )
        self.winHandle.set_vsync(True)
        self.winHandle.on_key_press = psychopy.event._onPygletKey
        self.winHandle.on_mouse_press = psychopy.event._onPygletMousePress
        self.winHandle.on_mouse_release = psychopy.event._onPygletMouseRelease
        self.winHandle.on_mouse_scroll = psychopy.event._onPygletMouseWheel
        if not self.allowGUI: 
            #make mouse invisible. Could go further and make it 'exclusive' (but need to alter x,y handling then)
            self.winHandle._mouse_visible=False
        self.winHandle.on_resize = self.onResize
        if self.pos is None:
            #work out where the centre should be
            self.pos = [ (thisScreen.width-self.size[0])/2 , (thisScreen.height-self.size[1])/2 ]
        self.winHandle.set_location(self.pos[0]+thisScreen.x, self.pos[1]+thisScreen.y)#add the necessary amount for second screen
        
        try: #to load an icon for the window
            iconFile = os.path.join(psychopy.__path__[0], 'psychopy.png')
            icon = pyglet.image.load(filename=iconFile)
            self.winHandle.set_icon(icon)
        except: pass#doesn't matter

    def _setupPygame(self):
        self.winType = "pygame"
        
        #setup the global use of PyOpenGL (rather than pyglet.gl)
        global GL, GLU, GL_multitexture
        
        GL = OpenGL.GL
        GLU = OpenGL.GLU
        GL_multitexture = OpenGL.GL.ARB.multitexture
        
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
        elif self.pos is None:
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

        #get screen properties (which pygame has initialised for us)
        #GLUT.glutInitDisplayMode(GLUT.GLUT_RGBA | GLUT.GLUT_DOUBLE | GLUT.GLUT_ALPHA | GLUT.GLUT_DEPTH)
        #if self.scrWidthPIX == 0:
            #self.scrWidthPIX = GLUT.glutGet(GLUT.GLUT_SCREEN_WIDTH)
        #if self.scrWidthCM == 0:
            #self.scrWidthCM = GLUT.glutGet(GLUT.GLUT_SCREEN_WIDTH_MM)/10.0
        #print 'screen width: ', self.scrWidthCM, 'cm, ', self.scrWidthPIX, 'pixels'
    def _setupGL(self):
        global haveShaders, _shaders
        if self.winType=='pyglet': _shaders=_shadersPyglet
        else: _shaders=_shadersPygame
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
        
        try:
            self._progSignedTexMask = _shaders.compileProgram(_shaders.vertSimple, _shaders.fragSignedColorTexMask)#fragSignedColorTexMask
            self._progSignedTex = _shaders.compileProgram(_shaders.vertSimple, _shaders.fragSignedColorTex)
            #print "successfully compiled shaders"
            haveShaders=True 
        except: 
            haveShaders=False #they didn't compile - probably no OpenGL2.0 drivers (but PyOpenGL3 installed)
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
    
#############################################################################
class _BaseVisualStim:
    """A template for a stimulus class, on which PatchStim, TextStim etc... are based.
    Not finished...?
    """
    def __init__(self):
        raise NotImplementedError('abstract')
    def draw(self):
        raise NotImplementedError('abstract')
        
    def setPos(self, newPos, operation=None, units=None):
        self._set('pos', val=newPos, op=operation)
    def setDepth(self,newDepth, operation=None):
        self._set('depth', newDepth, operation)
    def setSize(self, newSize, operation=None, units=None):
        if units==None: units=self.units#need to change this to create several units from one
        self._set('size', newSize, op=operation)
        self.needUpdate=True
    def setOri(self, newOri, operation=None):
        self._set('ori',val=newOri, op=operation)
    def setOpacity(self,newOpacity,operation=None):
        self._set('opacity', newOpacity, operation)
        #opacity is coded by the texture, if not using shaders
        if not self._haveShaders:
            self.setMask(self._maskName)
    def setDKL(self, newDKL, operation=None):
        self._set('dkl', value=newDKL, op=operation)
        self.setRGB(psychopy.misc.dkl2rgb(self.dkl, self.win.dkl_rgb))
    def setLMS(self, newLMS, operation=None):
        self._set('lms', value=newLMS, op=operation)
        self.setRGB(psychopy.misc.lms2rgb(self.lms, self.win.lms_rgb))
    def setRGB(self, newRGB, operation):      
        self._set('rgb', newRGB, operation)
        #if we don't have shaders we need to rebuild the texture
        if not self._haveShaders:
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
        if op is None: op=''
        #format the input value as float vectors
        if type(val) in [tuple,list]:
            val=numpy.asarray(val,float)
        
        if op=='':#this routine can handle single value inputs (e.g. size) for multi out (e.g. h,w)
            exec('self.'+attrib+'*=0') #set all values in array to 0
            exec('self.'+attrib+'+=val') #then add the value to array
        else:
            exec('self.'+attrib+op+'=val')
        
            
class DotStim(_BaseVisualStim):
    """
    This stimulus class defines a field of dots, all with the same speed
    but various directions of motion. A subset of 'coherent' dots have
    the same direction of motion.
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
                 dotLife = 1,
                 dir    =0.0,
                 speed  =0.5,
                 rgb    =[1.0,1.0,1.0],
                 opacity        =1.0,
                 depth  =0,
                 element=None):
        """
        **Arguments:**

            - **win:** a Window() object required - the stimulus must know where to draw itself!

            - **units:**
                + None (use the current units of the Window)
                + **or** 'norm' (normalised: window voes from -1:1 in each direction)
                + **or**  'cm','pix','deg' (but these real-world units need you to give sufficient info about your monitor, see below)

            - **nDots:** number of dots to be generated. For a 'sqr' fieldShape this is exactly the number of dots
                drawn each frame. For other stimuli that use masks (e.g. fieldShape='circle') it is
                the *average* number of dots drawn.

            - **fieldPos:** a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y of the centre of the stimulus.
                The origin is the screen centre, the units are determined
                by units (see above).

            - **fieldSize:** a tuple (0.5,0.5) or a list [0.5,0.5] for the x and y
                OR a single value (which will be applied to x and y).
                Units are specified by 'units' (see above).
                Sizes can be negative and can extend beyond the window.

            - **fieldShape:** *'circle'*,'sqr','gauss' Defines the envelope used to present the dots

            - **dotSize:** *2.0* in specified *units* [overridden if *element* is specified]

            - **dotLife:** Not currently implemented

            - **dir:** direction of the coherent dots (degrees)

            - **speed:** speed of the dots (in *units*/frame)

            - **rgb:** a tuple (1.0,1.0, 1.0) or a list [1.0,1.0, 1.0]
                or a single value (which will be applied to all guns).
                RGB vals are applied to simple textures and to greyscale
                image files but not to RGB images.

                **NB** units range -1:1 (so 0.0 is GREY). Again this is
                unconventional but it's great for vision scientists
                because they usually change things relative to a
                midpoint rather than relative to black.

                    [overridden if *element* is specified]

            - **opacity** 1.0,
                1.0 is opaque, 0.0 is transparent

            - **depth** 0,
                This can be used to choose which
                stimulus overlays which. (more negative values are nearer).
                At present the window does not do perspective rendering
                but could do if that's really useful(?!)

            - **element:** *None*.
                This can be any object that has a ``.draw()`` method and a
                ``.setPos([x,y])`` method (e.g. AlphaStim, TextStim...)!!
                """
        self.win = win
        if len(units): self.units = units
        else: self.units = win.units
        self.nDots = nDots
        self.fieldPos = fieldPos
        self.fieldSize = fieldSize
        self.fieldShape = fieldShape
        self.dotSize = dotSize
        self.dir = dir
        self.speed = speed
        self.opacity = opacity
        self.element = element

        if type(rgb) in [float, int]: #user may give a luminance val
            self.rgb=numpy.array((rgb,rgb,rgb), float)
        else:
            self.rgb = numpy.array(rgb, float)

        self.depth=depth
        #size
        if type(fieldSize) in [tuple,list]:
            self.fieldSize = numpy.array(fieldSize,float)
        else:
            self.fieldSize = numpy.array((fieldSize,fieldSize),float)#make a square if only given one dimension
        """initialise the dots themselves - give them all random dir and then
        fix the first n in the array to have the direction specified"""

        if self.fieldShape=='circle':self._nDotsTotal=int(nDots*4/pi) #control for smaller area of circle
        else: self._nDotsTotal = self.nDots
        self.coherence=round(coherence*self._nDotsTotal)/self._nDotsTotal#store actual coherence

        self._dotsXY = numpy.random.rand(self._nDotsTotal,2)*self.fieldSize - self.fieldSize/2 #initialise a random array of X,Y
        self._dotsDir = numpy.random.rand(self._nDotsTotal)*2*pi
        self._dotsDir[0:int(self.coherence*self._nDotsTotal)] = self.dir
        self._opacity = numpy.ones(self._nDotsTotal,'f')*self.opacity
        self._dotsSpeed = numpy.ones(self._nDotsTotal, 'f')*self.speed#all dots have the same speed
        self._dotsLife = dotLife*numpy.random.rand(self._nDotsTotal)
        self.frameClock = core.Clock()#we'll need a time record

        self._update_dotsXY()

    def _set(self, attrib, val, op=''):
        """Use this to set attributes of your stimulus after initialising it.

        **arguments:**
            - attrib = a string naming any of the attributes of the stimulus (set during init)
            - val = the value to be used in the operation on the attrib
            - op = a string representing the operation to be performed (optional) most maths operators apply ('+','-','*'...)

        **examples:**
            - myStim.set('rgb',0) #will simply set all guns to zero (black)
            - myStim.set('rgb',0.5,'+') #will increment all 3 guns by 0.5
            - myStim.set('rgb',(1.0,0.5,0.5),'*') # will keep the red gun the same and halve the others

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
            if self.fieldShape=='circle': self._nDotsTotal=int(self.nDots*4/pi)
            else: self._nDotsTotal = self.nDots
            self.coherence=round(self.coherence*self._nDotsTotal)/self._nDotsTotal


    def set(self, attrib, val, op=''):
        """DotStim.set() is obselete and may not be supported in future
        versions of PsychoPy. Use the specific method for each parameter instead
        (e.g. setOri(), setSF()...)
        """
        self._set(attrib, val, op)


    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if win==None: win=self.win
        if win.winType=='pyglet': win.winHandle.switch_to()
        
        self._update_dotsXY()
        if self.depth==0:
            thisDepth = self.win._defDepth
            self.win._defDepth += _depthIncrements[self.win.winType]
        else:
            thisDepth=self.depth

        #draw the dots
        if self.element==None:
            #scale the drawing frame etc...
            GL.glPushMatrix()#push before drawing, pop after
            GL.glLoadIdentity()
            self.win.setScale(self.units)
            GL.glTranslatef(self.fieldPos[0],self.fieldPos[1],thisDepth)
            GL.glPointSize(self.dotSize)

            #load Null textures into multitexteureARB - they modulate with glColor
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

            visible = (self._opacity>0)
            visibleXY = self._dotsXY[visible,:]
            if self.win.winType == 'pyglet':
                #visibleXY = numpy.transpose(visibleXY)
                #visibleXY=visibleXY.flat
                GL.glVertexPointer(2, GL.GL_DOUBLE, 0, visibleXY.ctypes)#.data_as(ctypes.POINTER(ctypes.c_float)))
            else:
                GL.glVertexPointerd(visibleXY)

            GL.glColor4f(self.rgb[0], self.rgb[1], self.rgb[2], 1.0)
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDrawArrays(GL.GL_POINTS, 0, len(visibleXY))
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glPopMatrix()
        else:
            #we don't want to do the screen scaling twice so for each dot subtract the screen centre
            initialDepth=self.element.depth
            for pointN in range(0,self._nDotsTotal):
                if self._opacity[pointN]>0.0:
#                    self.element.setDepth(0.0001,'-')# this will be done in the draw routine
                    self.element.setPos(self._dotsXY[pointN,:]-self.fieldPos)
                    self.element.draw()

            self.element.setDepth(initialDepth)#reset depth before going to next frame


    def _update_dotsXY(self):
        """
        The user shouldn't call this - its gets done within draw()
        """
        deltaT = self.frameClock.getTime() #measure time since last frame draw
        self.frameClock.reset()

        self._dotsLife -= deltaT #dots to be reborn will be negative
        deadDots = (self._dotsLife<0.0)
        """XXXX need to give deadDots new XY and direction etc"""
        self._dotsXY[:,0] += self.speed*numpy.reshape(numpy.cos(self._dotsDir),(self._nDotsTotal,))
        self._dotsXY[:,1] += self.speed*numpy.reshape(numpy.sin(self._dotsDir),(self._nDotsTotal,))# 0 radians=East!
        #handle boundaries of the field: square for now - circles not quite working
        if self.fieldShape is 'sqr':
            #gone outside the square
            self._dotsXY[:,0] = ((self._dotsXY[:,0]+self.fieldSize[0]/2) % self.fieldSize[0])-self.fieldSize[0]/2
            self._dotsXY[:,1] = ((self._dotsXY[:,1]+self.fieldSize[1]/2) % self.fieldSize[1])-self.fieldSize[1]/2
        elif self.fieldShape is 'circle':
            #gone outside the square
            self._dotsXY[:,0] = ((self._dotsXY[:,0]+self.fieldSize[0]/2) % self.fieldSize[0])-self.fieldSize[0]/2
            self._dotsXY[:,1] = ((self._dotsXY[:,1]+self.fieldSize[1]/2) % self.fieldSize[1])-self.fieldSize[1]/2
            #use a circular envelope and flips dot to opposite edge if they fall
            #beyond radius.
            #NB always circular - uses fieldSize in X only
            normXY = self._dotsXY/(self.fieldSize/2.0)
            dotDist = numpy.sqrt((normXY[:,0]**2.0 + normXY[:,1]**2.0))
            self._opacity = numpy.where(dotDist<1.0, self.opacity, 0.0)


class PatchStim(_BaseVisualStim):
    """Stimulus object for drawing arbitrary bitmaps, textures and shapes.
    One of the main stimuli for PsychoPy.

    Formally AlphaStim is just a texture behind an optional
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

    At present all these operations are 2D (and stimuli are layered in the order
    they are initialised) but this could all be done in 3D too!
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
                 rgb   =[1.0,1.0,1.0],
                 dkl=None,
                 lms=None,
                 contrast=1.0,
                 opacity=1.0,
                 depth=0,
                 rgbPedestal = [0.0,0.0,0.0],
                 interpolate=False):
        """
        **Arguments:**

            - **win:** 
                a Window() object required - the stimulus must know where to draw itself!

            - **tex** 
                The texture forming the image
                + 'sin','sqr',None
                + **or** the name of an image file (most formats supported)
                + **or** a numpy array (1xN or NxN) ranging -1:1

            - **mask:**
                The alpha mask (forming the shape of the image)
                + None, 'circle', 'gauss'
                + **or** the name of an image file (most formats supported)
                + **or** a numpy array (1xN or NxN) ranging -1:1

            - **units:**
                + None (use the current units of the Window)
                + **or** 'norm' (normalised: window voes from -1:1 in each direction)
                + **or**  'cm','pix','deg' (but these real-world units need you to give sufficient info about your monitor, see below)

            - **pos:** 
                a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y of the centre of the stimulus.
                The origin is the screen centre, the units are determined
                by units (see above). Stimuli can be position beyond the
                window!
            - **size:** 
                a tuple (0.5,0.5) or a list [0.5,0.5] for the x and y
                OR a single value (which will be applied to x and y).
                Units are specified by 'units' (see above).
                Sizes can be negative and can extend beyond the window.
            - **sf:** 
                a tuple (1.0,1.0) or a list [1.0,1.0] for the x and y
                OR a single value (which will be applied to x and y).
                Units are in cycles per 'units' (see above). For *deg*, *cm* and *norm* units th
                default sf=1, for *pix* the default sf=1/size so that one cycle fits on the stim.
            - **ori:** 
                orientation of stimulus in degrees.
            - **phase:** 
                a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y
                OR a single value (which will be applied to x and y).
                Phase of the stimulus in each direction.
                **NB** phase has modulus 1 (rather than 360 or 2*pi)
                This is a little unconventional but has the nice effect
                that setting phase=t*n drifts a stimulus at n Hz

            - **texRes:** 
                resolution of the texture (if not loading from an image file)

            - **rgb:** 
                a tuple (1.0,1.0, 1.0) or a list [1.0,1.0, 1.0]
                or a single value (which will be applied to all guns).
                RGB vals are applied to simple textures and to greyscale
                image files but not to RGB images.

                **NB** units range -1:1 (so 0.0 is GREY). Again this is
                unconventional but it's great for vision scientists
                because they usually change things relative to a
                midpoint rather than relative to black.

            - **dkl:** 
                a tuple (45.0,90.0, 1.0) or a list [45.0,90.0, 1.0]
                specifying the coordinates of the stimuli in cone-opponent
                space (Derrington, Krauskopf, Lennie 1984)
                Triplets represent [elevation, azimuth, magnitude].
                Note that the monitor must be calibrated for this to be
                accurate (if not, example phosphors from a Sony Trinitron
                CRT will be used).

            - **lms:** 
                a tuple (0.5, 1.0, 1.0) or a list [0.5, 1.0, 1.0]
                specifying the coordinates of the stimuli in cone space
                Triplets represent relative modulation of each cone [L, M, S].
                Note that the monitor must be calibrated for this to be
                accurate (if not, example phosphors from a Sony Trinitron
                CRT will be used).

            - **contrast** 1.0,
                How far the stimulus deviates from the middle grey.
                Contrast can vary -1:1 (this is a multiplier for the
                values given in the color description of the stimulus)

            - **opacity** 1.0,
                1.0 is opaque, 0.0 is transparent

            - **depth** 0,
                This can potentially be used (not tested!) to choose which
                stimulus overlays which. (more negative values are nearer).
                At present the window does not do perspective rendering
                but could do if that's really useful(?!)

        """
        global haveShaders
        self._haveShaders=haveShaders
        if not haveShaders:
            self._updateList = self._updateListNoShaders
        
        self.win = win
        assert isinstance(self.win, Window)

        if units in [None, "", []]:
            self.units = win.units
        else:
            self.units = units
        self.ori = float(ori)
        self.texRes = texRes #must be power of 2
        self.contrast = float(contrast)
        self.opacity = opacity
        self.interpolate=interpolate
          
        #for rgb allow user to give a single val and apply to all channels
        if type(rgb)==float or type(rgb)==int: #user may give a luminance val
            self.rgb=numpy.array((rgb,rgb,rgb), float)
        else:
            self.rgb = numpy.asarray(rgb, float)
        if type(rgbPedestal)==float or type(rgbPedestal)==int: #user may give a luminance val
            self.rgbPedestal=numpy.array((rgbPedestal,rgbPedestal,rgbPedestal), float)
        else:
            self.rgbPedestal = numpy.asarray(rgbPedestal, float)

        if dkl is not None:
            self.dkl = dkl
            self.rgb = psychopy.misc.dkl2rgb(dkl, win.dkl_rgb)
        elif lms is not None:
            self.lms = lms
            #log.warning('LMS-to-RGB conversion is not properly tested yet - it should NOT be used for proper research!')
            self.rgb = psychopy.misc.lms2rgb(lms, win.lms_rgb)

        #phase (ranging 0:1)
        if type(phase) in [tuple,list]:
            self.phase = numpy.array(phase)
        else:
            self.phase = numpy.array((phase,0),float)

        #size
        if type(size) in [tuple,list]:
            self.size = numpy.array(size,float)
        else:
            self.size = numpy.array((size,size),float)#make a square if only given one dimension

        #sf
        if units=='pix' and sf==(1,1): #if using pix and sf wasn't given
            sf = 1.0/self.size#so that exactly
        if type(sf) in [float, int] or len(sf)==1:
            self.sf = numpy.array((sf,sf),float)
        else:
            self.sf = numpy.array(sf,float)

        self.pos = numpy.array(pos)

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
        #generate a displaylist ID
        self._listID = GL.glGenLists(1)
        self._updateList()#ie refresh display list


    def setSF(self,value,operation=None):
        self._set('sf', value, operation)
        self.needUpdate = 1
    def setPhase(self,value, operation=None):
        self._set('phase', value, operation)
        self.needUpdate = 1
    def setContrast(self,value,operation=None):
        self._set('contrast', value, operation)
        #if we don't have shaders we need to rebuild the texture
        if not self._haveShaders:
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
            self.win._defDepth += _depthIncrements[self.win.winType]
        else:
            thisDepth=self.depth

        #do scaling
        GL.glPushMatrix()#push before the list, pop after
        #GL.glLoadIdentity() #implicitly done by push/pop?
        #scale the viewport to the appropriate size
        self.win.setScale(self.units)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self.pos[0],self.pos[1],thisDepth)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        #the list just does the texture mapping

        desiredRGB = (self.rgb*self.contrast+1)/2.0#RGB in range 0:1 and scaled for contrast
        if numpy.any(desiredRGB**2.0>1.0):
            desiredRGB=[0.6,0.6,0.4]
        GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)

        if self.needUpdate: self._updateList()
        GL.glCallList(self._listID)

        #return the view to previous state
        GL.glPopMatrix()

    def _updateList(self):
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
        L = -self.size[0]/2#vertices
        R =      self.size[0]/2
        T =      self.size[1]/2
        B = -self.size[1]/2
        #depth = self.depth
        if self.units=='norm':#sf is dependent on size (openGL default)
            Ltex = -self.sf[0]/2 - self.phase[0]+0.5
            Rtex = +self.sf[0]/2 - self.phase[0]+0.5
            Ttex = +self.sf[1]/2 - self.phase[1]+0.5
            Btex = -self.sf[1]/2 - self.phase[1]+0.5
        else: #we should scale to become independent of size
            Ltex = -self.sf[0]*self.size[0]/2 - self.phase[0]+0.5
            Rtex = +self.sf[0]*self.size[0]/2 - self.phase[0]+0.5
            Ttex = +self.sf[1]*self.size[1]/2 - self.phase[1]+0.5
            Btex = -self.sf[1]*self.size[1]/2 - self.phase[1]+0.5
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
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)#implicitly disables 1D
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.maskID)

        #main texture
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)
        #calculate coords in advance:
        L = -self.size[0]/2#vertices
        R =      self.size[0]/2
        T =      self.size[1]/2
        B = -self.size[1]/2
        #depth = self.depth
        if self.units=='norm':#sf is dependent on size (openGL default)
            Ltex = -self.sf[0]/2 - self.phase[0]+0.5
            Rtex = +self.sf[0]/2 - self.phase[0]+0.5
            Ttex = +self.sf[1]/2 - self.phase[1]+0.5
            Btex = -self.sf[1]/2 - self.phase[1]+0.5
        else: #we should scale to become independent of size
            Ltex = -self.sf[0]*self.size[0]/2 - self.phase[0]+0.5
            Rtex = +self.sf[0]*self.size[0]/2 - self.phase[0]+0.5
            Ttex = +self.sf[1]*self.size[1]/2 - self.phase[1]+0.5
            Btex = -self.sf[1]*self.size[1]/2 - self.phase[1]+0.5
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



    def clearTextures(self):
        """
        Clear the textures associated with the given stimulus. You should call this before
        de-referencing your stimulus or the textures associated with it will be kept in memory.
        
        For example, the following will eventually crash::
        
            from psychopy import visual
            win = visual.Window([400,400])
            for frameN in range(3000):
                #creating a new stimulus every time
                stim = visual.PatchStim(win, texRes=512)
                stim.draw()
                win.flip()
                
        Whereas this will not, because it removes uneeded textures from memory::
        
            from psychopy import visual
            win = visual.Window([400,400])
            for frameN in range(3000):
                #creating a new stimulus every time
                stim = visual.PatchStim(win, texRes=512)
                stim.draw()
                stim.clearTextures()
                win.flip()         
        """
        #only needed for pyglet
        if self.win.winType=='pyglet':
            GL.glDeleteTextures(1, self.texID)
            GL.glDeleteTextures(1, self.maskID)
class AlphaStim(PatchStim):
    """DEPRECATED. Use PatchStim instead/n/n"""
    def __init__(self, *arguments, **keywords):
        PatchStim.__init__(self, *arguments, **keywords)
        
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
                 visibleWedge=[0, 360],
                 rgb   =[1.0,1.0,1.0],
                 dkl=None,
                 lms=None,
                 contrast=1.0,
                 opacity=1.0,
                 depth=0,
                 rgbPedestal = [0.0,0.0,0.0],
                 interpolate=False):
        """
        **Arguments:**

            - **win:**
                a Window() object required - the stimulus must know where to draw itself!

            - **tex**
                The texture forming the image
                + 'sqrXsqr', 'sinXsin', 'sin','sqr',None
                + **or** the name of an image file (most formats supported)
                + **or** a numpy array (1xN or NxN) ranging -1:1

            - **mask:**
                Unlike the mask in the AlphaStim, this is a 1-D mask dictating the behaviour
                from the centre of the stimulus to the surround.

            - **units:**
                + None (use the current units of the Window)
                + **or** 'norm' (normalised: window goes from -1:1 in each direction)
                + **or**  'cm','pix','deg' (but these real-world units need you to give sufficient info about your monitor, see below)

            - **pos:**
                    a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y of the centre of the stimulus.
                    The origin is the screen centre, the units are determined
                    by units (see above). Stimuli can be position beyond the
                    window!

            - **size:**
                    a tuple (0.5,0.5) or a list [0.5,0.5] for the x and y
                    OR a single value (which will be applied to x and y).
                    Units are specified by 'units' (see above).

                    Sizes can be negative and can extend beyond the window.

            - **sf:**
                    + a tuple (1.0,1.0) or a list [1.0,1.0] for the x and y
                    + OR a single value (which will be applied to x and y).

                    Units are in cycles per 'units' (see above)

            - **ori:** orientation of stimulus in degrees.

            - **texRes:** 128, resolution of the texture (if not loading from an image file)

            - **angularRes:** 100, the number of triangles used to make the stim

            - **radialPhase:**
                    the phase of the texture from the centre to the perimeter
                    of the stimulus

            - **angularPhase:** the phase of the texture around the stimulus

            - **rgb:**
                    a tuple (1.0,1.0, 1.0) or a list [1.0,1.0, 1.0]
                    or a single value (which will be applied to all guns).
                    RGB vals are applied to simple textures and to greyscale
                    image files but not to RGB images.

                    **NB** units range -1:1 (so 0.0 is GREY). This might seem
                    strange but it's great for vision scientists
                    because they usually change things relative to a
                    midpoint rather than relative to black.

            - **dkl:** a tuple (45.0,90.0, 1.0) or a list [45.0,90.0, 1.0]
                    specifying the coordinates of the stimuli in cone-opponent
                    space (Derrington, Krauskopf, Lennie 1984)
                    Triplets represent [elevation, azimuth, magnitude].
                    Note that the monitor must be calibrated for this to be
                    accurate (if not, example phosphors from a Sony Trinitron
                    CRT will be used).

            - **lms:** a tuple (0.5, 1.0, 1.0) or a list [0.5, 1.0, 1.0]
                    specifying the coordinates of the stimuli in cone space
                    Triplets represent relative modulation of each cone [L, M, S].
                    Note that the monitor must be calibrated for this to be
                    accurate (if not, example phosphors from a Sony Trinitron
                    CRT will be used).

            - **contrast** 1.0,
                    How far the stimulus deviates from the middle grey.
                    Contrast can vary -1:1 (this is a multiplier for the
                    values given in the color description of the stimulus)

            - **opacity** 1.0,
                    1.0 is opaque, 0.0 is transparent

            - **depth** 0,
                    This can potentially be used (not tested!) to choose which
                    stimulus overlays which. (more negative values are nearer).
                    At present the window does not do perspective rendering
                    but could do if that's really useful(?!)

        """
        self.win = win
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
        self.pos = numpy.array(pos)
        self.interpolate=interpolate

        #these are defined by the AlphaStim but will just cause confusion here!
        self.setSF = None
        self.setPhase = None
        self.setSF = None

        #use different functions on systems without OpenGL2.0
        global haveShaders
        self._haveShaders=haveShaders
        if not haveShaders: 
            self._updateList = self._updateListNoShaders

        #for rgb allow user to give a single val and apply to all channels
        if type(rgb)==float or type(rgb)==int: #user may give a luminance val
            self.rgb=numpy.array((rgb,rgb,rgb), float)
        else:
            self.rgb = numpy.asarray(rgb, float)
        if type(rgbPedestal)==float or type(rgbPedestal)==int: #user may give a luminance val
            self.rgbPedestal=numpy.array((rgbPedestal,rgbPedestal,rgbPedestal), float)
        else:
            self.rgbPedestal = numpy.asarray(rgbPedestal, float)

        if dkl:
            self.dkl = dkl
            self.rgb = psychopy.misc.dkl2rgb(dkl, win.dkl_rgb)
        elif lms:
            self.lms = lms
            #warn('LMS-to-RGB conversion is not properly tested yet - it should NOT be used for proper research!')
            self.rgb = psychopy.misc.lms2rgb(lms, win.lms_rgb)

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

        self._updateTextureCoords()
        self._updateMaskCoords()
        self._updateXY()
        self._updateList()#ie refresh display list

    def setSize(self, value, operation=None):
        exec('self.size' + operation+ '=value')
        self._updateXY()
        self.needUpdate=True
    def setAngularCycles(self,value,operation=None):
        """set the number of cycles going around the stimulus"""
        exec('self.angularCycles' + operation+ '=value')
        self._updateTextureCoords()
        self.needUpdate=True
    def setRadialCycles(self,value,operation=None):
        """set the number of texture cycles from centre to periphery"""
        exec('self.radialCycles' + operation+ '=value')
        self._updateTextureCoords()
        self.needUpdate=True
    def setAngularPhase(self,value, operation=None):
        """set the angular phase of the texture"""
        exec('self.angularPhase' + operation+ '=value')
        self._updateTextureCoords()
        self.needUpdate=True
    def setRadialPhase(self,value, operation=None):
        """set the radial phase of the texture"""
        self._updateTextureCoords()
        exec('self.radialPhase' + operation+ '=value')
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
        #GL.glLoadIdentity() #implicitly done by push/pop?
        #scale the viewport to the appropriate size
        win.setScale(self.units)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self.pos[0],self.pos[1],thisDepth)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)

        #setup color
        desiredRGB = (self.rgb*self.contrast+1)/2.0#RGB in range 0:1 and scaled for contrast
        if numpy.any(desiredRGB**2.0>1.0):
            desiredRGB=[0.6,0.6,0.4]
        GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)

        #the list does the texture mapping
        if self.needUpdate: self._updateList()
        GL.glCallList(self._listID)

        #return the view to previous state
        GL.glPopMatrix()

    def _updateXY(self):
        """Update if the SIZE changes"""
        #triangles = [trisX100, verticesX3, xyX2]
        self._XY = numpy.zeros([self.angularRes, 3, 2])
        self._XY[:,1,0] = numpy.sin(self._angles)*self.size[0]/2 #x position of 1st outer vertex
        self._XY[:,1,1] = numpy.cos(self._angles)*self.size[1]/2#y position of 1st outer vertex
        self._XY[:,2,0] = numpy.sin(self._angles+self._triangleWidth)*self.size[0]/2#x position of 2nd outer vertex
        self._XY[:,2,1] = numpy.cos(self._angles+self._triangleWidth)*self.size[1]/2#y position of 2nd outer vertex

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
        self._maskCoords = numpy.zeros([self.angularRes, 3, 2]) + self.maskRadialPhase
        self._maskCoords[:,1:3,:] = 1 + self.maskRadialPhase#all outer points have mask value of 1
        self._visibleMask = self._maskCoords[self._visible,:,:].reshape(self._nVisible,2)


    def _updateList(self):
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
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTex, "texture"), 0) #set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTex, "mask"), 1)  # mask is texture unit 1

        #assign vertex array
        if self.win.winType=='pyglet':
            arrPointer = self._visibleXY.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            GL.glVertexPointer(2, GL.GL_FLOAT, 0, arrPointer) 
        else:
            GL.glVertexPointerd(self._visibleXY)#must be reshaped in to Nx2 coordinates
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)

        #bind and enable textures
        #main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        #mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        #set pointers to visible textures
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        if self.win.winType=='pyglet':
            arrPointer = self._visibleTexture.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, arrPointer) 
        else:
            GL.glTexCoordPointerd(self._visibleTexture)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        #mask
        GL.glClientActiveTexture(GL.GL_TEXTURE1)
        if self.win.winType=='pyglet':
            arrPointer = self._visibleMask.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, arrPointer) 
        else:
            GL.glTexCoordPointerd(self._visibleMask)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        #do the drawing
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible)

        #disable set states
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisable(GL.GL_TEXTURE_2D)

        #setup the shaderprogram
        GL.glUseProgram(0)
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
        """Users shouldn't use this method
        """
        self._maskName = value
        res = self.texRes#resolution of texture - 128 is bearable
        step = 1.0/res
        rad = numpy.arange(0,1+step,step)
        if type(self._maskName) == numpy.ndarray:
            #handle a numpy array
            intensity = 255*maskName.astype(float)
            res = len(intensity)
            fromFile=0
        elif type(self._maskName) == list:
            #handle a numpy array
            intensity = 255*numpy.array(maskName, 'f')
            res = len(intensity)
            fromFile=0
        elif self._maskName is "circle":
            intensity = 255.0*(rad<=1)
            fromFile=0
        elif self._maskName is "gauss":
            sigma = 1/3.0;
            intensity = 255.0*numpy.exp( -rad**2.0 / (2.0*sigma**2.0) )#3sd.s by the edge of the stimulus
            fromFile=0
        elif self._maskName is "radRamp":#a radial ramp
            intensity = 255.0-255.0*rad
            intensity = numpy.where(rad<1, intensity, 0)#half wave rectify
            fromFile=0
        elif self._maskName in [None,"none"]:
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
        
class MovieStim:
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
                 flipHoriz = False):
        """
        **Arguments:**

            - **win:** a Window() object required - the stimulus must know where to draw itself

            - **filename:**
                a string giving the relative or absolute path to the movie. Can be any movie that 
                AVbin can read (e.g. mpeg, DivX)
                
            - **units:**
                + None (use 'pix')
                + **or** 'norm' (normalised: window goes from -1:1)
                + **or**  'cm','pix','deg' (but these real-world units need you to give sufficient info about your monitor, see below)
                
            - **pos**:
                position of the centre of the movie, given in the units specified
                
            - **flipVert**:
                bool (True/False or 1/-1) if True then the movie will be top-bottom flipped
                
            - **flipHoriz**:
                bool (True/False or 1/-1) if True then the movie will be right-left flipped
            
            - **ori**:
                orientation of the stimulus in degrees
                
            - **size**:
                size of the stimulus in units given. If not specified then the movie will take its
                original dimensions. Thes can be interrogated by 
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
        self.pos = numpy.asarray(pos)
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.playing=0
        
        #size
        if size == None: self.size= numpy.array([self.format.width, self.format.height] , float)
        elif type(size) in [tuple,list]: self.size = numpy.array(size,float)
        else: self.size = numpy.array((size,size),float)
        
        self.ori = ori
        if units in [None, "", []]:
            self.units = win.units
        else:
            self.units = units
            
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

        #do scaling
        #scale the viewport to the appropriate size
        self.win.setScale(self.units)
        
        frameTexture = self._player.get_texture()
        
        GL.glPushMatrix()
        #move to centre of stimulus and rotate
        GL.glTranslatef(self.pos[0],self.pos[1],thisDepth)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        flipBitX = 1-self.flipHoriz*2
        flipBitY = 1-self.flipVert*2
        frameTexture.blit(
                -self.size[0]/2.0*flipBitX, 
                -self.size[1]/2.0*flipBitY, 
                width=self.size[0]*flipBitX, 
                height=self.size[1]*flipBitY,
                z=thisDepth)        
        GL.glPopMatrix()
    def _onEOS(self):
        #not called, for some reason?!
        self.playing=-1
        print 'movie finished'
class TextStimGLUT:
    """Class of text stimuli to be displayed in a **Window()**

    **Written:**
            - jwp, 2003
    """
    def __init__(self,win,
                 text="Hello World",
                 font="GLUT_BITMAP_TIMES_ROMAN_24",
                 pos=(0.0,0.0),
                 depth=0,
                 rgb=(1.0,1.0,1.0),
                 opacity=1.0,
                 units="",
                 ori=0.0,
                 letterWidth=10.0,
                 lineWidth=1.0,
                 alignHoriz='center',
                 alignVert='center'):
        self.win = win
        global haveShaders
        if len(units): self.units = units
        else: self.units = win.units
        self.pos= numpy.array(pos)
        if type(font)==str:
            self.fontName=font
            exec('self.font=GLUT.'+font)
        else:#presumably was an actual GLUT font enumerator
            self.font = font
        if self.font in [GLUT.GLUT_STROKE_ROMAN, GLUT.GLUT_STROKE_MONO_ROMAN]:
            self.strokeFont=1
        else: self.strokeFont=0
        self.text='' #just a placeholder set below
        self.setText(text) #some additional things get set with text
        self.needUpdate =1
        self.opacity= opacity
        self.contrast= 1.0
        self.alignHoriz = alignHoriz
        self.alignVert = alignVert

        if not haveShaders:
            self._updateList = self._updateListNoShaders

        if type(rgb) in [float, int]: #user may give a luminance val
            self.rgb=numpy.asarray((rgb,rgb,rgb), float)
        else:
            self.rgb = numpy.asarray(rgb, float)

        self.depth=depth

        self._listID = GL.glGenLists(1)
        #initialise textures for stimulus
        if self.win.winType=="pyglet":
            self.texID=GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(self.texID))
        else:
            self._texID = GL.glGenTextures(1)
        #self._setColorTex()

        self.ori=ori
        self.lineWidth=lineWidth
        self.letterWidth=letterWidth#width of each character in pix
        GL.glEnable(GL.GL_LINE_SMOOTH)#nicer for stroke fonts

    def _set(self,attrib,val,op=''):
        #can handle single value in -> multi out (e.g. size->h,w)
        if op=='' or op==None:
            exec('self.'+attrib+'*=0') #set all values in array to 0
            exec('self.'+attrib+'+=val') #then add the value to array
        else:
            exec('self.'+attrib+op+'=val')
        self.needUpdate =1

    def set(self, attrib, val, op=''):
        """DEPRECATED
        TextStim.set() is obselete and may not be supported in future
        versions of PsychoPy. Use the specific method for each parameter instead
        (e.g. setOri(), setText()...)
        """
        self._set(attrib, val, op)

    def setOri(self,value,operation=None):
        self._set('ori', value, operation)
    def setPos(self,value,operation=None):
        self._set('pos', value, operation)
    def setRGB(self,value, operation=None):
        self._set('rgb', value, operation)
    def setOpacity(self,value,operation=None):
        self._set('opacity', value, operation)
    def setText(self,value,operation=None):
        self._set('text', value, operation)
        #also update the current length and height
        if self.strokeFont:
            if len(self.text)==1:
                self.length = GLUT.glutStrokeWidth(self.font, ord(self.text))
            else: self.length = GLUT.glutStrokeLength(self.font, self.text)
            self.height = 100.0 #roughly!
        else:
            if len(self.text)==1:
                self.length = GLUT.glutBitmapWidth(self.font, ord(self.text))
            else: self.length = GLUT.glutBitmapLength(self.font, self.text)
            if self.fontName:
                #final two digits of name give height (but overestimated!)
                self.height=float(self.fontName[-2:])-1
            else: self.height = 23.0 #(if the default 24pt font was used)
    def setDepth(self,value, operation=None):
        self._set('depth', value, operation)

    def _updateList(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        GL.glNewList(self._listID, GL.GL_COMPILE)
        GL.glPushMatrix()

        #load Null textures into multitexteureARB - they interfere with glColor
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        GL.glColor4f(self.rgb[0]/2.0+0.5, self.rgb[1]/2.0+0.5, self.rgb[2]/2.0+0.5, self.opacity)

        unitScale = self.win.setScale(self.units)
        GL.glTranslatef(self.pos[0],self.pos[1],0)#NB depth is set already
        if self.strokeFont:#draw stroke font stims
            GL.glLineWidth(self.lineWidth)
            GL.glPopMatrix()#get rid of the scaling matrix for positioning
            GL.glPushMatrix()#and make a new one for drawing the characters
            #NB:scaling stroke_fonts requires that we move to the right position
            #to start drawing (setScale above) and then change the scale again
            #so that the letters are spaced correctly
            #alignment
            self.win.setScale('stroke_font', self) #special usage of setScale
            if self.alignHoriz =='center':
                #self.win.setScale('pix')
                GL.glTranslatef(-self.length/2, -self.height/2, 0.0)
            elif self.alignHoriz =='right':
                GL.glTranslatef(-self.length, -self.height, 0.0)
            else:#no need to change
                pass
            #stroke fonts rotate
            GL.glRotatef(self.ori,0.0,0.0,1.0)

            for characters in self.text:
                GLUT.glutStrokeCharacter(self.font,ord(characters))
        else:#draw bitmap font stims
            self.win.setScale('pix', self, prevScale=unitScale)
            #how much to move left
            if self.alignHoriz =='center': left = -self.length/2.0
            elif self.alignHoriz =='right':left = -self.length
            else: left = 0.0
            #how much to move bottom
            if self.alignVert =='center': bottom = -self.height/2.0
            elif self.alignVert =='top': bottom = -self.height
            else: bottom = 0.0
            #do the actual move
            GL.glRasterPos3f(left,bottom,0)

            for characters in self.text:
                GLUT.glutBitmapCharacter(self.font,ord(characters))

        GL.glPopMatrix()

        GL.glEndList()
        self.needUpdate=0

    def _updateListNoShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        GL.glNewList(self._listID, GL.GL_COMPILE)
        GL.glPushMatrix()

        #load Null textures into multitexteureARB - they interfere with glColor
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        GL.glColor4f(self.rgb[0]/2.0+0.5, self.rgb[1]/2.0+0.5, self.rgb[2]/2.0+0.5, self.opacity)

        unitScale = self.win.setScale(self.units)
        GL.glTranslatef(self.pos[0],self.pos[1],0)#NB depth is set already
        if self.strokeFont:#draw stroke font stims
            GL.glLineWidth(self.lineWidth)
            GL.glPopMatrix()#get rid of the scaling matrix for positioning
            GL.glPushMatrix()#and make a new one for drawing the characters
            #NB:scaling stroke_fonts requires that we move to the right position
            #to start drawing (setScale above) and then change the scale again
            #so that the letters are spaced correctly
            #alignment
            self.win.setScale('stroke_font', self) #special usage of setScale
            if self.alignHoriz =='center':
                #self.win.setScale('pix')
                GL.glTranslatef(-self.length/2, -self.height/2, 0.0)
            elif self.alignHoriz =='right':
                GL.glTranslatef(-self.length, -self.height, 0.0)
            else:#no need to change
                pass
            #stroke fonts rotate
            GL.glRotatef(self.ori,0.0,0.0,1.0)

            for characters in self.text:
                GLUT.glutStrokeCharacter(self.font,ord(characters))
        else:#draw bitmap font stims
            self.win.setScale('pix', self, prevScale=unitScale)
            #how much to move left
            if self.alignHoriz =='center': left = -self.length/2.0
            elif self.alignHoriz =='right':left = -self.length
            else: left = 0.0
            #how much to move bottom
            if self.alignVert =='center': bottom = -self.height/2.0
            elif self.alignVert =='top': bottom = -self.height
            else: bottom = 0.0
            #do the actual move
            GL.glRasterPos3f(left,bottom,0)

            for characters in self.text:
                GLUT.glutBitmapCharacter(self.font,ord(characters))

        GL.glPopMatrix()

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

        GL.glPushMatrix()#push before the list, pop after
        if self.needUpdate: self._updateList()
        GL.glCallList(self._listID)
        GL.glPopMatrix()#push before the list, pop after

class TextStim(_BaseVisualStim):
    """Class of text stimuli to be displayed in a **Window()**

    **Written:**
            - jwp, 2003
            - jwp, 2007 added support for pygame fonts (any TT font and UNICODE support)
            - jwp, 2008 added support for pyglet back-end (including ttf and Unicode support)

            On windows fonts can be given as concatenated names all in lower case. e.g. 'arial', 'monotypecorsiva', 'rockwellextra'...
            If no font name is given, a default font will be used.
    """
    def __init__(self, win,
                 text="Hello World",
                 font="",
                 pos=(0.0,0.0),
                 depth=0,
                 rgb=(1.0,1.0,1.0),
                 opacity=1.0,
                 units="",
                 ori=0.0,
                 height=None,
                 antialias=True,
                 bold=False,
                 italic=False,
                 alignHoriz='center',
                 alignVert='center',
                 fontFiles=[]):
        """
            **Arguments:**
        
                - **win:**
                    a Window() object required - the stimulus must know where to draw itself!
        
                - **text**
                    The text to be rendered
        
                - **pos**
                    Position on the screen
                    
                - **depth**
                    Depth on the screen (if None it will be defined on .draw() to be in front of the last object drawn)
                    
                - **rgb**
                    The color of the text (ranging [-1,-1,-1] to [1,1,1])
                    
                - **opacity**
                    How transparent the object will be (0 for transparent, 1 for opaque)
        
                - **units**
                    "pix", "norm", "cm", "deg" only if you want to override the Window's default
                    
                - **ori**
                    Orientation of the text
                    
                - **height**
                    Height of the characters (including the ascent of the letter and the descent)
                    
                - **antialias**
                    boolean to allow (or not) antialiasing the text
                    
                - **bold**
                    Make the text bold (better to use a bold font name)
                    
                - **italic**
                    Make the text italic (better to use an actual italic font)
                    
                - **alignHoriz**
                    The horizontal alignment ('left', 'right' or 'center')
                    
                - **alignVert**
                    The vertical alignment ('top', 'bottom' or 'center')
                    
                - **fontFiles**
                    A list of additional files if the font is not in the standard system location (include the full path)
        """
        global haveShaders
        self._haveShaders=haveShaders
        self.win = win
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
        self._pygletTextObj=None
        
        if not haveShaders:
            self._updateList = self._updateListNoShaders
            self.setText = self.setTextNoShaders

        if len(units): self.units = units
        else: self.units = win.units
        self.pos= numpy.array(pos)

        #height in pix (needs to be done after units)
        if self.units=='cm':
            if height: self.height = height
            else: self.height = 1.0#default text height
            self.heightPix = psychopy.misc.cm2pix(self.height, win.monitor)
        elif self.units=='deg':
            if height: self.height = height
            else: self.height = 1.0#default text height
            self.heightPix = psychopy.misc.deg2pix(self.height, win.monitor)
        elif self.units=='norm':
            if height: self.height = height
            else: self.height = 0.1#default text height
            self.heightPix = self.height*win.size[1]/2
        else: #treat units as pix
            if height: self.height = height
            else: self.height = 20#default text height
            self.heightPix = self.height
        
        for thisFont in fontFiles:
            pyglet.font.add_file(thisFont)
        self.setFont(font)

        if type(rgb) in [float, int]: #user may give a luminance val
            self.rgb=numpy.asarray((rgb,rgb,rgb), float)
        else:
            self.rgb = numpy.asarray(rgb, float)

        #generate the texture and list holders
        self._listID = GL.glGenLists(1)
        if not self.win.winType=="pyglet":
            self._texID = GL.glGenTextures(1)
        #render the text surfaces and build drawing list
        self.setText(text) #some additional things get set with text

        self.needUpdate=True

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
                        log.warn("Found %s but it doesn't end .ttf. Using default font." %fontFilenames[0])
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

    def setText(self,value):
        """Set the text to be rendered using the current font
        """
        self.text = value
        
        if self.win.winType=="pyglet":
            if self._pygletTextObj==None: 
                self._pygletTextObj = pyglet.font.Text(self._font, self.text,
                                                       halign=self.alignHoriz, valign=self.alignVert,
                                                       color = (self.rgb[0],self.rgb[1], self.rgb[2], self.opacity)
                                                       )#width of the frame
            else: self._pygletTextObj.text= self.text
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
            #GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT) #makes the texture map wrap (this is actually default anyway)
            ##important if using bits++ because GL_LINEAR
            ##sometimes extrapolates to pixel vals outside range
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,smoothing)    #linear smoothing if texture is stretched?
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,smoothing)    #but nearest pixel value if it's compressed?

        self.needUpdate = True

    def _updateList(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        GL.glNewList(self._listID, GL.GL_COMPILE)
        GL.glPushMatrix()

        #setup the shaderprogram
        #no need to do texture maths so no need for programs?
        GL.glUseProgram(0)#self.win._progSignedTex)
        #GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTex, "texture"), 0) #set the texture to be texture unit 0
        
        #coords:
        if self.alignHoriz =='center': left = -self.width/2.0;    right = self.width/2.0
        elif self.alignHoriz =='right':    left = -self.width;    right = 0.0
        else: left = 0.0; right = self.width
        #how much to move bottom
        if self.alignVert =='center': bottom=-self.height/2.0; top=self.height/2.0
        elif self.alignVert =='top': bottom=-self.height; top=0
        else: bottom=0.0; top=self.height
        Btex, Ttex, Ltex, Rtex = 0, 1.0, 0, 1.0
        
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
        GL.glPopMatrix()

        GL.glEndList()
        self.needUpdate=0

    def setTextNoShaders(self,value,operation=None):
        """Set the text to be rendered using the current font
        """
        self.text = value
        
        if self.win.winType=="pyglet":
            if self._pygletTextObj==None: 
                self._pygletTextObj = pyglet.font.Text(self._font, self.text,
                                                       halign=self.alignHoriz, valign=self.alignVert,
                                                       color = (self.rgb[0],self.rgb[1], self.rgb[2], self.opacity)
                                                       )
            self._pygletTextObj.text=self.text
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
            GLU.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, 4, self.width,self.height,
                                  GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pygame.image.tostring( self._surf, "RGBA",1))
            #GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT) #makes the texture map wrap (this is actually default anyway)
            ##important if using bits++ because GL_LINEAR
            ##sometimes extrapolates to pixel vals outside range
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
        GL.glPushMatrix()

        #coords:
        if self.alignHoriz =='center': left = -self.width/2.0;    right = self.width/2.0
        elif self.alignHoriz =='right':    left = -self.width;    right = 0.0
        else: left = 0.0; right = self.width
        #how much to move bottom
        if self.alignVert =='center': bottom=-self.height/2.0; top=self.height/2.0
        elif self.alignVert =='top': bottom=-self.height; top=0
        else: bottom=0.0; top=self.height
        Btex, Ttex, Ltex, Rtex = 0, 1.0, 0, 1.0

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
            GL.glVertex3f(right,bottom,0)
            # left bottom
            GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Ltex,Btex)
            GL.glVertex3f(left,bottom,0)
            # left top
            GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Ltex,Ttex)
            GL.glVertex3f(left,top,0)
            # right top
            GL_multitexture.glMultiTexCoord2fARB(GL_multitexture.GL_TEXTURE0_ARB,Rtex,Ttex)
            GL.glVertex3f(right,top,0)
            GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glPopMatrix()

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

        #scale and rotate
        unitScale = self.win.setScale(self.units)
        GL.glTranslatef(self.pos[0],self.pos[1],thisDepth)#NB depth is set already
        GL.glRotatef(self.ori,0.0,0.0,1.0)
        #then scale back to pixels
        self.win.setScale('pix', None, unitScale)

        if haveShaders: #then rgb needs to be set as glColor
            #setup color
            desiredRGB = (self.rgb*self.contrast+1)/2.0#RGB in range 0:1 and scaled for contrast
            if numpy.any(desiredRGB**2.0>1.0):
                desiredRGB=[0.6,0.6,0.4]
            GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)
        else: #color is set in texture, so set glColor to white
            GL.glColor4f(1,1,1,1)

        #update list if necss and then call it
        if self.needUpdate: self._updateList()
        GL.glDisable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
        #GL.glDisable(GL.xxx
        GL.glCallList(self._listID)
        GL.glEnable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
        GL.glPopMatrix()

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
    useShaders = stim._haveShaders
    interpolate = stim.interpolate
    
    if type(tex) == numpy.ndarray:
        #handle a numpy array
        #for now this needs to be an NxN intensity array        
        intensity = tex.astype(numpy.float32)
        if intensity.max()>1 or intensity.min()<-1:
            log.error('numpy arrays used as textures should be in the range -1(black):1(white)')
        wasLum = True
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
        res=1 #4x4 (2x2 is SUPPOSED to be fine but generates wierd colours!)
        intensity = numpy.ones([res,res],numpy.float32)
        wasLum = True
    elif tex == "sin":
        onePeriodX, onePeriodY = numpy.mgrid[0:2*pi:2*pi/res, 0:2*pi:2*pi/res]
        intensity = numpy.sin(onePeriodY-pi/2)
        wasLum = True
    elif tex == "sqr":#square wave (symmetric duty cycle)
        onePeriodX, onePeriodY = numpy.mgrid[0:2*pi:2*pi/res, 0:2*pi:2*pi/res]
        sinusoid = numpy.sin(onePeriodY-pi/2)
        intensity = numpy.where(sinusoid>0, 1, -1)
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
    elif tex is "circle":
        rad=makeRadialMatrix(res)
        intensity = (rad<=1)*2-1 
        fromFile=0
    elif tex is "gauss":
        rad=makeRadialMatrix(res)
        sigma = 1/3.0;
        intensity = numpy.exp( -rad**2.0 / (2.0*sigma**2.0) )*2-1 #3sd.s by the edge of the stimulus
        fromFile=0
    elif tex is "radRamp":#a radial ramp
        rad=makeRadialMatrix(res)
        intensity = 1-2*rad
        intensity = numpy.where(rad<-1, intensity, -1)#clip off the corners (circular)
        fromFile=0
    else:#might be a filename of an image
        try:
            im = Image.open(tex)
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        except:
            log.error("couldn't load tex...%s" %(tex))
            core.quit()
            raise #so that we quit

        #is it 1D?
        if im.size[0]==1 or im.size[1]==1:
            log.error("Only 2D textures are supported at the moment")
        else:
            maxDim = max(im.size)
            powerOf2 = 2**numpy.ceil(numpy.log2(maxDim))
            if im.size[0]!=powerOf2 or im.size[1]!=powerOf2:
                log.warning("Image '%s' was not a square power-of-two image. Linearly interpolating to be %ix%i" %(tex, powerOf2, powerOf2))
                im.resize([powerOf2,powerOf2],Image.BILINEAR)                    

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
    elif pixFormat==GL.GL_RGB and wasLum:
        #scale by rgb and convert to ubyte
        internalFormat = GL.GL_RGB
        dataType = GL.GL_UNSIGNED_BYTE
        data = numpy.ones((intensity.shape[0],intensity.shape[1],3),numpy.float32)#initialise data array as a float
        data[:,:,0] = intensity*stim.rgb[0]  + stim.rgbPedestal[0]#R
        data[:,:,1] = intensity*stim.rgb[1]  + stim.rgbPedestal[1]#G
        data[:,:,2] = intensity*stim.rgb[2]  + stim.rgbPedestal[2]#B
        #convert to ubyte
        data = psychopy.misc.float_uint8(stim.contrast*data)
    elif pixFormat==GL.GL_RGB and useShaders:
        internalFormat = GL.GL_RGB32F_ARB
        dataType = GL.GL_FLOAT
        data = intensity
    elif pixFormat==GL.GL_RGB:
        internalFormat = GL.GL_RGB
        dataType = GL.GL_UNSIGNED_BYTE
        data = psychopy.misc.float_uint8(intensity)
    elif pixFormat==GL.GL_ALPHA and useShaders:
        internalFormat = GL.GL_ALPHA
        dataType = GL.GL_UNSIGNED_BYTE
        data = psychopy.misc.float_uint8(intensity)    
    elif pixFormat==GL.GL_ALPHA:
        internalFormat = GL.GL_ALPHA
        dataType = GL.GL_UNSIGNED_BYTE
        #can't use float_uint8 - do it manually
        data = numpy.around(255*stim.opacity*(0.5+0.5*intensity)).astype(numpy.uint8)
    texture = data.tostring()#serialise

    if interpolate: smoothing=GL.GL_LINEAR
    else: smoothing=GL.GL_NEAREST

    #bind the texture in openGL
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, id)#bind that name to the target
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                    data.shape[0],data.shape[1], 0,
                    pixFormat, dataType, texture)
    GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT) #makes the texture map wrap (this is actually default anyway)
    #important if using bits++ because GL_LINEAR
    #sometimes extrapolates to pixel vals outside range
    GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,smoothing)    #linear smoothing if texture is stretched?
    GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,smoothing)    #but nearest pixel value if it's compressed?
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)#?? do we need this - think not!
