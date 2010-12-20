#openGL testbed
import scipy
from OpenGL import GL, GLU, GLUT
import OpenGL.GL.ARB.multitexture as GL_multitexture
import sys

# Some api in the chain is translating the keystrokes to this octal string
# so instead of saying: ESCAPE = 27, we use the following.
ESCAPE = '\033'

# Number of the glut window.
window = 0

# Rotation angle for the triangle. 
rtri = 0.0

# Rotation angle for the quadrilateral.
rquad = 0.0
lutAsString='dummy'

# A general OpenGL initialization function.  Sets all of the initial parameters. 
def InitGL(Width, Height):				# We call this right after our OpenGL window is created.
	GL.glClearColor(0.0, 0.0, 0.0, 0.0)	# This Will Clear The Background Color To Black
	GL.glClearDepth(1.0)					# Enables Clearing Of The Depth Buffer
	GL.glDepthFunc(GL.GL_LESS)				# The Type Of Depth Test To Do
	GL.glDisable(GL.GL_DEPTH_TEST)				# Enables Depth Testing
	GL.glShadeModel(GL.GL_SMOOTH)				# Enables Smooth Color Shading
		
	GL.glMatrixMode(GL.GL_PROJECTION)
	GL.glLoadIdentity()					# Reset The Projection Matrix
	# Calculate The Aspect Ratio Of The Window
	GLU.gluPerspective(45.0, float(Width)/float(Height), 0.1, 100.0)

	GL.glMatrixMode(GL.GL_MODELVIEW)
	GL.glLoadIdentity()					# Reset The Model Matrix
	setOrthoMode()
# The function called when our window is resized (which shouldn't happen if you enable fullscreen, below)
def ReSizeGLScene(Width, Height):
	if Height == 0:						# Prevent A Divide By Zero If The Window Is Too Small 
			Height = 1

	GL.glViewport(0, 0, Width, Height)		# Reset The Current Viewport And Perspective Transformation

# The main drawing function. 
def drawRotatingObjects():
		global rtri, rquad
		GL.glLoadIdentity()					# Reset The View 

		# Move Left 1.5 units and into the screen 6.0 units.
		GL.glTranslatef(-1.5, 0.0, -6.0)

		# We have smooth color mode on, this will blend across the vertices.
		# Draw a triangle rotated on the Y axis. 
		GL.glRotatef(rtri, 0.0, 1.0, 0.0)      # Rotate
		GL.glBegin(GL.GL_POLYGON)                 # Start drawing a polygon
		GL.glColor3f(1.0, 0.0, 0.0)            # Red
		GL.glVertex3f(0.0, 1.0, 0.0)           # Top
		GL.glColor3f(0.0, 1.0, 0.0)            # Green
		GL.glVertex3f(1.0, -1.0, 0.0)          # Bottom Right
		GL.glColor3f(0.0, 0.0, 1.0)            # Blue
		GL.glVertex3f(-1.0, -1.0, 0.0)         # Bottom Left
		GL.glEnd()                             # We are done with the polygon

		# draw a quad
		GL.glLoadIdentity()
		
		# Move Right 1.5 units and into the screen 6.0 units.
		GL.glTranslatef(1.5, 0.0, -6.0)

		# Draw a square (quadrilateral) rotated on the X axis.
		GL.glRotatef(rquad, 1.0, 0.0, 0.0)		# Rotate 
		GL.glColor3f(0.3, 0.5, 1.0)            # Bluish shade
		GL.glBegin(GL.GL_QUADS)                   # Start drawing a 4 sided polygon
		GL.glVertex3f(-1.0, 1.0, 0.0)          # Top Left
		GL.glVertex3f(1.0, 1.0, 0.0)           # Top Right
		GL.glVertex3f(1.0, -1.0, 0.0)          # Bottom Right
		GL.glVertex3f(-1.0, -1.0, 0.0)         # Bottom Left
		GL.glEnd()                             # We are done with the polygon

		rtri  = rtri + 1.0                  # Increase The Rotation Variable For The Triangle
		rquad = rquad - 1.0                 # Decrease The Rotation Variable For The Quad
def DrawGLScene():
	GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
	#drawRotatingObjects()
	
	#setOrthoMode()
	drawBitsLUT()
	#setPerspectiveMode()
	
	GLUT.glutSwapBuffers()

# The function called whenever a key is pressed. Note the use of Python tuples to pass in: (key, x, y)  
def keyPressed(*args):
		# If escape is pressed, kill everything.
	if args[0] == ESCAPE:
			GLUT.glutDestroyWindow(window)
			sys.exit()

def main():
		global window
		# For now we just pass glutInit one empty argument. I wasn't sure what should or could be passed in (tuple, list, ...)
		# Once I find out the right stuff based on reading the PyOpenGL source, I'll address this.
		lutAsString = buildBitsLUT()
		GLUT.glutInit([])
		GLUT.glutInitDisplayMode(GLUT.GLUT_RGBA | GLUT.GLUT_DOUBLE | GLUT.GLUT_ALPHA | GLUT.GLUT_DEPTH)
		
		# get a 640 x 480 window 
		GLUT.glutInitWindowSize(800, 600)
		
		# the window starts at the upper left corner of the screen 
		GLUT.glutInitWindowPosition(0, 0)
		
		window = GLUT.glutCreateWindow("Jeff Molofee's GL Code Tutorial ... NeHe '99")
		# glutFullScreen()
		#register callbacks
		GLUT.glutIdleFunc(DrawGLScene)		
		GLUT.glutReshapeFunc(ReSizeGLScene)
		GLUT.glutKeyboardFunc(keyPressed)
		GLUT.glutDisplayFunc(DrawGLScene)		

		InitGL(800, 600)

		GLUT.glutMainLoop()

def drawBitsLUT():
	global lutAsString
	x1,y1=800,600
	#GL.glRasterPos2f(0.5,0.5)
	#GL.glDrawPixels(10,10,GL.GL_RGB,GL.GL_UNSIGNED_BYTE,lutAsString) #ub is unsigned byte (ie uint8)
	
	GL.glLoadIdentity()					# Reset The View 

	# Move Left 1.5 units and into the screen 6.0 units.
	GL.glTranslatef(-1.5, 0.0,-0.5)

	# We have smooth color mode on, this will blend across the vertices.
	# Draw a triangle rotated on the Y axis. 
	GL.glBegin(GL.GL_POLYGON)                 # Start drawing a polygon
	GL.glColor3f(1.0, 0.0, 0.0)            # Red
	GL.glVertex2f(0.0, 0.5)           # Top
	GL.glColor3f(0.0, 1.0, 0.0)            # Green
	GL.glVertex2f(0.5, -0.5)          # Bottom Right
	GL.glColor3f(0.0, 0.0, 1.0)            # Blue
	GL.glVertex2f(-0.5, -0.5)         # Bottom Left
	GL.glEnd()                             # We are done with the polygon

def setOrthoMode():
	#switch (and leave in 2D orthographic mode)
	GL.glMatrixMode(GL.GL_PROJECTION)						
	GL.glPushMatrix()									
	GL.glLoadIdentity()								
	GL.glOrtho( 0, 800, 0, 600, 0, 1 )	
	GL.glMatrixMode(GL.GL_MODELVIEW) #for actual rendering								
	GL.glLoadIdentity()
	GL.glDisable(GL.GL_DEPTH_TEST)

def setPerspectiveMode():
	#just getting back out of orthographic mode
	GL.glMatrixMode(GL.GL_PROJECTION)
	GL.glPopMatrix()
	GL.glMatrixMode( GL.GL_MODELVIEW )
	GL.glLoadIdentity()
	GL.glEnable(GL.GL_DEPTH_TEST)
	
def buildBitsLUT():
	global lutAsString
	nEntries=256
	contrast=0.5
	gamma=1.0
	ramp = scipy.arange(-1.0,1.0,2.0/nEntries)
	ramp = (ramp*contrast+1.0)/2.0 #get into range 0:1
	ramp = (ramp**gamma) * 2**16
	ramp = ramp.astype(scipy.UnsignedInt16)
	RGB = scipy.ones((1,nEntries*2,3),scipy.UnsignedInt8)
	RGB[:, 0::2, 0] = 1#byteMS(ramp)#R
	RGB[:, 1::2, 0] = 0# byteLS(ramp)
	RGB[:, 0::2, 1] = 1#byteMS(ramp)#G
	RGB[:, 1::2, 1] = 0#byteLS(ramp)
	RGB[:, 0::2, 2] = 1#byteMS(ramp)#B
	RGB[:, 1::2, 2] = 0#byteLS(ramp)

	#prepend the bits++ header (precedes LUT)
	#and create a string version ready for drawing
	head = scipy.ones((1,12,3),scipy.UnsignedInt8)
	head[:,:,0] = [ 36, 63, 8, 211, 3, 112, 56, 34,0,0,0,0]#R
	head[:,:,1] = [ 106, 136, 19, 25, 115, 68, 41, 159,0,0,0,0]#G
	head[:,:,2] = [ 133, 163, 138, 46, 164, 9, 49, 208,0,0,0,0]#B
	head[:,:,0] = [ 0, 63, 8, 211, 3, 112, 56, 34,0,0,0,0]#R
	head[:,:,1] = [ 0, 136, 19, 25, 115, 68, 41, 159,0,0,0,0]#G
	head[:,:,2] = [ 0, 163, 138, 46, 164, 9, 49, 208,0,0,0,0]#B
	#head[:,:,0] = [ 255, 255, 0, 0, 0, 0, 56, 34,0,0,0,0]#R
	#head[:,:,1] = [ 0, 0, 255, 255, 0, 0, 41, 159,0,0,0,0]#G
	#head[:,:,2] = [ 0, 0, 0, 0, 255, 255, 49, 208,0,0,0,0]#B
	asArr = scipy.concatenate((head,RGB),1)
	lutAsString = asArr.tostring()
		
# Print message to console, and kick off the main to get it rolling.
print "Hit ESC key to quit."
main()
			
