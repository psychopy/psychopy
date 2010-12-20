#openGL testbed
import pygame, time, scipy
from OpenGL import GL
import OpenGL.GL.ARB.multitexture as GL_multitexture
from psychopy import visual, misc
winSize=[600,600]
sqrSize = 1.0

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
    GL.glEnable(GL.GL_TEXTURE_1D)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glShadeModel(GL.GL_SMOOTH)                   # Color Shading (FLAT or SMOOTH)
    GL.glEnable(GL.GL_POINT_SMOOTH)

def drawScene():
    GL.glDisable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
    GL.glPushMatrix()
    GL.glScalef(1.0,1.0,1.0)

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
    GL.glPopMatrix()


#run a frame
setupPygame()
setupOpenGL()
drawScene()
pygame.display.flip()
time.sleep(2)
