import pygame, time, numpy, Image
from numpy import pi, sin, cos

#opengl
import OpenGL
from OpenGL import GL, GLU
import OpenGL.GL.ARB.multitexture as GL_multitexture
if OpenGL.__version__>="3.0":
    import OpenGL.GL.EXT.framebuffer_object as FB

from psychopy import visual, misc, event, _shaders
winSize=[800,600]
sqrSize =1
texID = GL.glGenTextures(1)
useFBO = True

def float_uint8(inarray):
    """Converts arrays, lists, tuples and floats ranging -1:1
    into an array of Uint8s ranging 0:255
    """
    retVal = numpy.around(255*(0.5+0.5*numpy.asarray(inarray)))
    return retVal.astype(numpy.uint8)
def setupPygame():
    #setup pygame
    pygame.init()
    winHandle = pygame.display.set_mode(winSize,pygame.OPENGL|pygame.DOUBLEBUF)
def setupOpenGL():
    #setup opengl
    GL.glClearColor(0.5,0.5,0.5, 1.0)     # This Will Clear The Background Color
    GL.glClearDepth(1.0)
    GL.glViewport(0, 0, winSize[0], winSize[1]);
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()                     # Reset The Projection Matrix
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

    GL.glClear(GL.GL_COLOR_BUFFER_BIT|GL.GL_DEPTH_BUFFER_BIT)         
    GL.glEnable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
    GL.glEnable(GL.GL_BLEND)
    GL.glEnable(GL.GL_TEXTURE_1D)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glShadeModel(GL.GL_SMOOTH)                   # Color Shading (FLAT or SMOOTH)
    GL.glEnable(GL.GL_POINT_SMOOTH)
    #GL_multitexture.glInitMultitextureARB()

def createFBO(size):
    """ Offscreen rendering
    """
    w =  size[0]
    h = size[1]

    # Setup framebuffer
    frameBuffer = FB.glGenFramebuffersEXT(1)
    FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, frameBuffer)
    
    # Setup depthbuffer
    depthBuffer = FB.glGenRenderbuffersEXT(1)
    FB.glBindRenderbufferEXT (FB.GL_RENDERBUFFER_EXT,depthBuffer)
    FB.glRenderbufferStorageEXT (FB.GL_RENDERBUFFER_EXT, GL.GL_DEPTH_COMPONENT, w, h)
        
    # Create texture to render to
    GL.glEnable(GL.GL_TEXTURE_2D)
    texture = GL.glGenTextures (1)
    GL.glBindTexture (GL.GL_TEXTURE_2D, texture)
    GL.glTexParameteri (GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri (GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexImage2D (GL.GL_TEXTURE_2D, 0, GL.GL_RGBA32F_ARB, w, h, 0,
                    GL.GL_RGBA, GL.GL_FLOAT, None)
    
    #attach texture to the frame buffer
    FB.glFramebufferTexture2DEXT (FB.GL_FRAMEBUFFER_EXT, GL.GL_COLOR_ATTACHMENT0_EXT,
                               GL.GL_TEXTURE_2D, texture, 0);
    FB.glFramebufferRenderbufferEXT(FB.GL_FRAMEBUFFER_EXT, GL.GL_DEPTH_ATTACHMENT_EXT, 
                                 FB.GL_RENDERBUFFER_EXT, depthBuffer);
                                
    status = FB.glCheckFramebufferStatusEXT (FB.GL_FRAMEBUFFER_EXT);
    if status != FB.GL_FRAMEBUFFER_COMPLETE_EXT:
        print "Error in framebuffer activation"
        return    
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)#unbind that name to the target
    GL.glDisable(GL.GL_TEXTURE_2D)
    return frameBuffer, texture, depthBuffer
        
def flip():
    global frameTexture
    
    if useFBO: 
        FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, 0)
        
        GL.glDisable(GL.GL_BLEND)
        #GL.glBlendEquation(GL.GL_FUNC_ADD)
        #GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        #GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_DST_ALPHA)
        
        #before flipping need to copy the renderBuffer to the frameBuffer
        GL.glColor4f(1,1,1,1)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, frameTexture)
        GL.glBegin( GL.GL_QUADS )
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 0.0 ) 
        GL.glVertex2f( -1.0,-1.0 )
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 1.0 ) 
        GL.glVertex2f( -1.0, 1.0 )
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,1.0, 1.0 ) 
        GL.glVertex2f( 1.0,   1.0 )
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 0.0 ) 
        GL.glVertex2f( 1.0,   -1.0 )
        GL.glEnd()
    pygame.display.flip()
    
    if useFBO: 
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)
        
        FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, frameBuffer)
def makeGrating():
    res=128
    #make basic texture
    onePeriodX, onePeriodY = numpy.mgrid[0:2*pi:2*pi/res, 0:2*pi:2*pi/res]
    intensity = numpy.sin(onePeriodX-pi/2)#*numpy.sin(onePeriodY-pi/2)
    #paste into rgb
    data = numpy.ones((res,res,4),numpy.float32)#initialise data array as a float
    data[:,:,0] = intensity
    data[:,:,1] = intensity
    data[:,:,2] = intensity
    data[:,:,3] = 1.0
    #data = float_uint8(data)#data range -1:1 -> 0:255
    texture = data.tostring()#serialise
    print 'texID', texID
    #upload texture
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texID)#bind that name to the target
    GL.glTexImage2D(GL.GL_TEXTURE_2D,#target
                    0,                              #mipmap level
                    GL.GL_RGBA32F_ARB,      #internal format
                    res,                    #width
                    res,
                    0,                       #border
                    GL.GL_RGBA, #target format
                    GL.GL_FLOAT, #target data type
                    texture)                #the data
    GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT)  #makes the texture map wrap (this is actually default anyway)
    #interpolate with NEAREST NEIGHBOUR. Important if using bits++ because GL_LINEAR
    #sometimes extrapolates to pixel vals outside range
    GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST)
    GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)#bind that name to the target
    GL.glDisable(GL.GL_TEXTURE_2D)
                
def drawScene():
    
    GL.glClear(GL.GL_COLOR_BUFFER_BIT|GL.GL_DEPTH_BUFFER_BIT)   
    GL.glPushMatrix()
    
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texID)#bind that name to the target
    
    #first square
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glColor4f(1,0,1,0.5) 
    GL.glBegin(GL.GL_POLYGON)                 # Start drawing a polygon
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0,0.0,2.0)
    GL.glVertex3f(0, sqrSize*0.8,-.8)           # Top left
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0,2.0,2.0)
    GL.glVertex3f(sqrSize*0.8, sqrSize*0.8,-.80)         # Top right
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0,2.0,0.0)
    GL.glVertex3f(sqrSize*0.8, 0,-.8)          # Bottom Right
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0,0.0,0.0)
    GL.glVertex3f(0, 0,-.8)         # Bottom Left
    try:
        GL.glEnd()    
    except:
        print GL.GLerror, 1
    alpha = 0.5
    
    #2nd square
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glRotatef(45,0.0,0.0,1.0)
    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glColor4f(0.5,0.5,0.5,alpha) 
    GL.glBegin(GL.GL_POLYGON)                 # Start drawing a polygon
    GL.glVertex3f(0, sqrSize*0.8,-.7)           # Top left
    GL.glVertex3f(sqrSize*0.8, sqrSize*0.8,-.70)         # Top right
    GL.glVertex3f(sqrSize*0.8, 0,-.7)          # Bottom Right
    GL.glVertex3f(0, 0,-.7)         # Bottom Left
    GL.glEnd()        
    GL.glEnable(GL.GL_TEXTURE_2D)
    
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glColor4f(1,0,1,alpha) 
    GL.glBegin(GL.GL_POLYGON)                 # Start drawing a polygon
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0,0.0,2.0)
    GL.glVertex3f(0, sqrSize*0.8,-.8)           # Top left
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0,2.0,2.0)
    GL.glVertex3f(sqrSize*0.8, sqrSize*0.8,-.80)         # Top right
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0,2.0,0.0)
    GL.glVertex3f(sqrSize*0.8, 0,-.8)          # Bottom Right
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0,0.0,0.0)
    GL.glVertex3f(0, 0,-.8)         # Bottom Left
    try:
        GL.glEnd()    
    except:
        print GL.GLerror.message, 2
    
    GL.glPopMatrix()

#run a frame
setupPygame()
setupOpenGL()
if useFBO: frameBuffer, frameTexture, depthBuffer = createFBO(size=winSize)
makeGrating()
drawScene()
flip()
event.waitKeys()
