#openGL testbed
import pygame, time, scipy, Image
from OpenGL import GL, GLU
import OpenGL.GL.ARB.multitexture as GL_multitexture
import OpenGL.GL.EXT.framebuffer_object as FB
from psychopy import visual, misc
winSize=[512,512]
sqrSize =1
    
def setupPygame():
    #setup pygame
    pygame.init()
    winHandle = pygame.display.set_mode(winSize,pygame.OPENGL|pygame.DOUBLEBUF)
def setupOpenGL():
    #setup opengl
    GL.glClearColor(0,0,0, 1.0)     # This Will Clear The Background Color To Black
    GL.glClearDepth(1.0)
    GL.glViewport(0, 0, winSize[0], winSize[1]);
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()                     # Reset The Projection Matrix
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

    GL.glClear(GL.GL_COLOR_BUFFER_BIT|GL.GL_DEPTH_BUFFER_BIT)         
    GL.glEnable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
    GL.glEnable(GL.GL_BLEND)
    GL.glShadeModel(GL.GL_SMOOTH)                   # Color Shading (FLAT or SMOOTH)
    GL.glEnable(GL.GL_POINT_SMOOTH)

def createFBO(size=None):
    """ Offscreen rendering
    
    Save an offscreen rendering of size (w,h) to filename.
    """
    def round2 (n):
        """ Get nearest power of two superior to n """
        f = 1
        while f<n:
            f*= 2
        return f

    if size == None:
        size = (512,512)
    w = round2 (size[0])
    h = round2 (size[1])

    # Setup framebuffer
    frameBuffer = FB.glGenFramebuffersEXT(1)
    FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, frameBuffer)
    
    # Setup depthbuffer
    depthBuffer = FB.glGenRenderbuffersEXT(1)
    FB.glBindRenderbufferEXT (FB.GL_RENDERBUFFER_EXT,depthBuffer)
    FB.glRenderbufferStorageEXT (FB.GL_RENDERBUFFER_EXT, GL.GL_DEPTH_COMPONENT, w, h)
        
    # Create texture to render to
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
    GL.glDisable(GL.GL_TEXTURE_2D);
    return frameBuffer, texture, depthBuffer
        
def flip():
    global frameTexture
    FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, 0)
    
    #before flipping need to copy the renderBuffer to the frameBuffer
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, frameTexture)
    GL.glBegin( GL.GL_QUADS )
    GL.glTexCoord2f( 0.0, 0.0 ) ; GL.glVertex2f( -1.0,-1.0 )
    GL.glTexCoord2f( 0.0, 1.0 ) ; GL.glVertex2f( -1.0, 1.0 )
    GL.glTexCoord2f( 1.0, 1.0 ) ; GL.glVertex2f( 1.0,   1.0 )
    GL.glTexCoord2f( 1.0, 0.0 ) ; GL.glVertex2f( 1.0,   -1.0 )
    GL.glEnd()
#    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    pygame.display.flip()
    GL.glDisable(GL.GL_TEXTURE_2D);
    
    FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, frameBuffer)
        
def drawScene(frameBuffer, frameTexture):
    FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, frameBuffer)
    
    GL.glClear(GL.GL_COLOR_BUFFER_BIT|GL.GL_DEPTH_BUFFER_BIT)   
    #GL.glPushAttrib(GL.GL_VIEWPORT_BIT);
    GL.glPushMatrix()
    #GL.glViewport(0,0,512,512);
    
#    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT);
    GL.glLoadIdentity()                     # Reset The Projection Matrix
    
    #GL.glDisable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
    GL.glBegin(GL.GL_POLYGON)                 # Start drawing a polygon
    GL.glColor3f(1.0, 0.0, 0.0)            # Red
    GL.glVertex2f(-sqrSize*0.5, sqrSize*0.5)           # Top left
    GL.glColor3f(1.0, 1.0, 1.0)            # White
    GL.glVertex2f(sqrSize*0.5, sqrSize*0.5)         # Top right
    GL.glColor3f(0.0, 1.0, 0.0)            # Green
    GL.glVertex2f(sqrSize*0.5, -sqrSize*0.5)          # Bottom Right
    GL.glColor3f(0.0, 0.0, 1.0)            # Blue
    GL.glVertex2f(-sqrSize*0.5, -sqrSize*0.5)         # Bottom Left
    GL.glEnd()      

    GL.glColor3f(1.0, 1.0, 1.0) 
    #GL.glPopAttrib()
    GL.glPopMatrix()
    FB.glBindFramebufferEXT(FB.GL_FRAMEBUFFER_EXT, 0)

#run a frame
setupPygame()
setupOpenGL()
frameBuffer, frameTexture, depthBuffer = createFBO(size=[512,512])
drawScene(frameBuffer, frameTexture)
flip()
time.sleep(1)
