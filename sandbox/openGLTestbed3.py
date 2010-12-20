#openGL testbed
import pygame, time, scipy
from OpenGL import GL, GLUT
import OpenGL.GL.ARB.multitexture as GL_multitexture
from psychopy import visual, misc, core
import monitors
winSize=[600,600]
sqrSize = 1.0
class Window:
    """
    Used to set up a context in which to draw objects,
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
	winType="pygame",
	units='norm',
	gamma = None):
	"""
	**Arguments:**

	    - **size** :  size of the window in pixels (X,Y)
	    - **rgb** :	 background color (R,G,B) from -1.0 to 1.0
	    - **fullScr** :  0(in a window), 1(fullscreen) NB Try using fullScr=0, allowGUI=0
	    - **allowGUI** :  0,1 If set to 1, window will be drawn with no frame and no buttons to close etc...
	    - **winType** :  'pygame' or 'glut' (pygame is strongly recommended)
	    - **monitor** :  the name of your monitor (from MonitorCentre) or an actual ``Monitor`` object
	    - **units** :  'norm' (normalised),'deg','cm','pix' Defines the default units of stimuli drawn in the window (can be overridden by each stimulus)

	The following args will override **monitor** settings(see above):

	    - **gamma** : 1.0, monitor gamma for linearisation (will use Bits++ if possible)
	    - **bitsMode** : None, 'fast', ('slow' mode is deprecated). Defines how (and if) the Bits++ box will be used. 'Fast' updates every frame by drawing a hidden line on the top of the screen.

	"""
	self.size = scipy.array(size, scipy.uint16)
	self.pos = pos
	if type(rgb)==float or type(rgb)==int: #user may give a luminance val
	    self.rgb=scipy.array((rgb,rgb,rgb), scipy.Float)
	else:
	    self.rgb = scipy.asarray(rgb, scipy.Float)
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

	#setup context and openGL()
	self.allowGUI = allowGUI
	if winType is "glut":		self._setupGlut()
	elif winType is "pygame":	self._setupPygame()
	self._setupGL()
	#setupGL()
	self.update()#do a screen refresh straight away

    def update(self):
	"""Do a screen refresh (after drawing each frame)
	"""
	pygame.display.flip()
	pygame.event.pump()#keeps us in synch with system event queue

	#reset returned buffer for next frame
	GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
	self._defDepth=0.0

    def setScale(self, units, font='dummyFont', prevScale=[1.0,1.0]):
	"""This method is called from within the draw routine and sets the
	scale of the OpenGL context to map between units. Could potentially be
	called by the user in order to draw OpenGl objects manually
	in each frame.

	The **units** can be 'norm'(normalised),'pix'(pixels),'cm' or
	'stroke_font'. The **font** argument is only used if units='stroke_font'
	"""
	if units is "norm":
	    thisScale = scipy.array([1.0,1.0])
	elif units in ["pix", "pixels"]:
	    thisScale = 2.0/scipy.array(self.size)
	elif units is "cm":
	    #windowPerCM = windowPerPIX / CMperPIX
	    #			= (window	/winPIX)	/ (scrCm				/scrPIX)
	    if (self.scrWidthCM in [0,None]) or (self.scrWidthPIX in [0, None]):
		print 'you didnt give me the width of the screen (pixels and cm)'
		core.wait(1.0); core.quit()
	    thisScale = (scipy.array([2.0,2.0])/self.size)/(float(self.scrWidthCM)/float(self.scrWidthPIX))
	elif units in ["deg", "degs"]:
	    #windowPerDeg = winPerCM*CMperDEG
	    #		= winPerCM		* tan(scipy.pi/180) * distance
	    if (self.scrWidthCM in [0,None]) or (self.scrWidthPIX in [0, None]):
		print 'you didnt give me the width of the screen (pixels and cm)'
		core.wait(1.0); core.quit()
	    cmScale = (scipy.array([2.0,2.0])/self.size)/(float(self.scrWidthCM)/float(self.scrWidthPIX))
	    thisScale = cmScale * 0.017455 * self.scrDistCM
	elif units is "stroke_font":
	    thisScale = scipy.array([2*font.letterWidth,2*font.letterWidth]/self.size/38.0)
	#actually set the scale as appropriate
	thisScale = thisScale/scipy.asarray(prevScale)#allows undoing of a previous scaling procedure
	print 'scale %f %f' %(thisScale[0], thisScale[1])
	GL.glScalef(float(thisScale[0]), float(thisScale[1]), 1.0)
	return thisScale #just in case the user wants to know?!

    def _setupPygame(self):
	self.winType = "pygame"
	pygame.init()

	winSettings = pygame.OPENGL|pygame.DOUBLEBUF#|pygame.OPENGLBLIT #these are ints stored in pygame.locals
	
	self.winHandle = pygame.display.set_mode(self.size.astype('i'),winSettings)
	pygame.display.set_gamma(1.0) #this will be set appropriately later

    def _setupGL(self):
	#do settings for openGL
	GL.glViewport(0, 0, (self.size[0]), self.size[1]);
	#GL.glViewport(0, 0, float(self.size[0]), float(self.size[1]));
	print self.size[0], self.size[1]
	GL.glClearColor((self.rgb[0]+1.0)/2.0, (self.rgb[1]+1.0)/2.0, (self.rgb[2]+1.0)/2.0, 1.0)	# This Will Clear The Background Color To Black
	GL.glClearDepth(1.0)
	
	GL.glEnable(GL.GL_DEPTH_TEST)			# Enables Depth Testing
	GL.glEnable(GL.GL_BLEND)
	GL.glEnable(GL.GL_TEXTURE_1D)
	GL.glEnable(GL.GL_TEXTURE_2D)

	GL.glShadeModel(GL.GL_SMOOTH)			# Color Shading (FLAT or SMOOTH)
	GL.glEnable(GL.GL_POINT_SMOOTH)
	#GL.glEnable(GL.GL_LINE_SMOOTH)
	#GL.glEnable(GL.GL_POLYGON_SMOOTH)

	GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
	GL.glDepthFunc(GL.GL_LESS)			# The Type Of Depth Test To Do
	GL.glClear(GL.GL_COLOR_BUFFER_BIT|GL.GL_DEPTH_BUFFER_BIT)
	if not GL_multitexture.glInitMultitextureARB():#try initialising multitexture
	    print 'GL_ARB_multitexture not supported!'
	    sys.exit(1)
	#if sys.platform=='darwin':
	    #ext.darwin.syncSwapBuffers(1)

class PatchStim:
    def __init__(self,
	win,
	tex	="sin",
	mask	="none",
	units	="",
	pos	=(0.0,0.0),
	size	=(0.5,0.5),
	sf	=(1.0,1.0),
	ori	=0.0,
	phase	=(0.0,0.0),
	texRes =128,
	rgb   =[1.0,1.0,1.0],
	dkl=None,
	lms=None,
	contrast=1.0,
	opacity=1.0,
	depth=0,
	rgbPedestal = [0.0,0.0,0.0],
	interpolate=False):
	
	self.win = win
	if len(units): self.units = units
	else: self.units = win.units
	self.ori = float(ori)
	self.texRes = texRes #must be power of 2
	self.contrast = float(contrast)
	self.opacity = opacity

	#for rgb allow user to give a single val and apply to all channels
	if type(rgb)==float or type(rgb)==int: #user may give a luminance val
	    self.rgb=scipy.array((rgb,rgb,rgb), scipy.Float)
	else:
	    self.rgb = scipy.asarray(rgb, scipy.Float)
	if type(rgbPedestal)==float or type(rgbPedestal)==int: #user may give a luminance val
	    self.rgbPedestal=scipy.array((rgbPedestal,rgbPedestal,rgbPedestal), scipy.Float)
	else:
	    self.rgbPedestal = scipy.asarray(rgbPedestal, scipy.Float)

	if dkl:
	    self.dkl = dkl
	    self.rgb = misc.dkl2rgb(dkl, win.dkl_rgb)
	elif lms:
	    self.lms = lms
	    warn('LMS-to-RGB conversion is not properly tested yet - it should NOT be used for proper research!')
	    self.rgb = misc.lms2rgb(lms, win.lms_rgb)

	#phase (ranging 0:1)
	if type(phase) in [tuple,list]:
	    self.phase = scipy.array(phase)
	else:
	    self.phase = scipy.array((phase,0),scipy.Float)

	#sf
	if type(sf) in [tuple,list]:
	    self.sf = scipy.array(sf,scipy.Float)
	else:
	    self.sf = scipy.array((sf,sf),scipy.Float)
	self.pos = scipy.array(pos)

	if depth==0:
	    self.depth = win._defDepth
	    win._defDepth -= 0.0001# -ve depth means closer to viewer
	else:
	    self.depth=depth

	#size
	if type(size) in [tuple,list]:
	    self.size = scipy.array(size,scipy.Float)
	else:
	    self.size = scipy.array((size,size),scipy.Float)#make a square if only given one dimension
	#initialise textures for stimulus
	(self.texID, self.maskID) = GL.glGenTextures(2)
	self._setTex(tex)
	self._setMask(mask)
	#generate a displaylist ID
	self._listID = GL.glGenLists(1)
	self._updateList()#ie refresh display list

    def set(self, attrib, val, op=''):
	"""PatchStim.set() is obselete and may not be supported in future
	versions of PsychoPy. Use the specific method for each parameter instead
	(e.g. setOri(), setSF()...)
	"""
	self._set(attrib, val, op)

    def setOri(self,value,operation=None):
	self._set('ori', value, operation)
    def setSF(self,value,operation=None):
	self._set('sf', value, operation)
    def setSize(self,value,operation=None):
	self._set('size', value, operation)
    def setPhase(self,value, operation=None):
	self._set('phase', value, operation)
    def setPos(self,value,operation=None):
	self._set('pos', value, operation)

    def setContrast(self,value,operation=None):
	self.set('contrast', value, operation)
    def setDepth(self,value, operation=None):
	self._set('depth', value, operation)

    def draw(self):
	"""
	Draw the stimulus in its relevant window. You must call
	this method after every MyWin.update() if you want the
	stimulus to appear on that frame and then update the screen
	again.
	"""
	#do scaling
	GL.glPushMatrix()#push before the list, pop after
	#GL.glLoadIdentity() #implicitly done by push/pop?
	#scale the viewport to the appropriate size
	#self.win.setScale(self.units)
	#move to centre of stimulus and rotate
	GL.glTranslatef(self.pos[0],self.pos[1],self.depth)
	GL.glRotatef(-self.ori,0.0,0.0,1.0)

	#the list just does the texture mapping
	if self.needUpdate: self._updateList()
	GL.glCallList(self._listID)

	#return the view to previous state
	GL.glPopMatrix()

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
	if op is None: op=''
	#format the input value as float vectors
	if type(val) in [tuple,list]:
	    val=scipy.asarray(val,scipy.Float)
	#handle special cases for texture/mask alterations
	if attrib in ['contrast' , 'rgb' , 'tex']:#we will need to update the texture
	    exec('self.'+attrib+op+'=val')
	    self._setTex(self._texName)
	elif attrib in ['mask' , 'opacity']:#we'll need to update the mask
	    exec('self.'+attrib+op+'=val')
	    self._setMask(self.__maskName)
	else:#just change the setting
	    if op=='':#this routine can handle single value inputs (e.g. size) for multi out (e.g. h,w)
		exec('self.'+attrib+'*=0') #set all values in array to 0
		exec('self.'+attrib+'+=val') #then add the value to array
	    else:
		exec('self.'+attrib+op+'=val')
	#flag the update
	if attrib in ['phase', 'sf', 'size']:
	    #these all need an update of the drawing list
	    #(not needed for pos or ori, which are determined during draw)
	    self.needUpdate = 1

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
	GL.glColor4f(1.0,1.0,1.0,1.0)#glColor can interfere with multitextures
	
	#calculate coords in advance:
	L = -self.size[0]/2#vertices
	R =	 self.size[0]/2
	T =	 self.size[1]/2
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

	GL.glBegin(GL.GL_QUADS)			 # draw a 4 sided polygon
	# right bottom
	GL.glVertex3f(R,B,0)
	# left bottom
	GL.glVertex3f(L,B, 0)
	# left top
	GL.glVertex3f(L,T,0)
	# right top
	GL.glVertex3f(R,T,0)
	GL.glEnd()
   
	GL.glDisable(GL.GL_TEXTURE_2D)
	GL.glEndList()



    def _setTex(self, texName):
	"""
	Users shouldn't use this method
	"""
	self._texName = texName
	res = self.texRes
	#create some helper variables
	onePeriodY = scipy.outerproduct(scipy.arange(0,2*scipy.pi,2*scipy.pi/res), scipy.ones((1,res)))#equivalent to matlab meshgrid
	onePeriodX = scipy.outerproduct(scipy.ones((1,res)), scipy.arange(0,2*scipy.pi,2*scipy.pi/res))
	if type(texName) == scipy.ArrayType:
	    #handle a numpy array
	    intensity = texName.astype(scipy.Float)
	    wasLum = True
	    #is it 1D?
	    if texName.shape[0]==1:
		self._tex1D=True
		res=im.shape[1]
	    elif len(texName.shape)==1 or texName.shape[1]==1:
		self._tex1D=True
		res=texName.shape[0]
	    else:
		self._tex1D=False
		if texName.shape[0]!=texName.shape[1]: raise StandardError, "numpy array for texture was not square"
		res=texName.shape[0]
	elif texName in [None,"none", "None"]:
	    res=4 #4x4 (2x2 is SUPPOSED to be fine but generates wierd colours!)
	    intensity = scipy.ones(res,scipy.Float)
	    wasLum = True
	    self._tex1D=True

	if wasLum and self._tex1D:
	    #for a luminance image, scale RGB channels according to color
	    data = scipy.ones((res,3),scipy.Float)#initialise data array as a float
	    data[:,0] = intensity.flat*self.rgb[0] + self.rgbPedestal[0]#R
	    data[:,1] = intensity.flat*self.rgb[1] + self.rgbPedestal[1]#G
	    data[:,2] = intensity.flat*self.rgb[2] + self.rgbPedestal[2]#B
	    data = misc.float_uint8(self.contrast*data)#data range -1:1 -> 0:255
	    texture = data.tostring()#serialise

	elif wasLum:
	    #for a luminance image, scale RGB channels according to color
	    data = scipy.ones((res,res,3),scipy.Float)#initialise data array as a float
	    data[:,:,0] = intensity*self.rgb[0]	 + self.rgbPedestal[0]#R
	    data[:,:,1] = intensity*self.rgb[1]	 + self.rgbPedestal[1]#G
	    data[:,:,2] = intensity*self.rgb[2]	 + self.rgbPedestal[2]#B
	    data = misc.float_uint8(self.contrast*data)#data range -1:1 -> 0:255
	    texture = data.tostring()#serialise

	#bind the texture in openGL
	if self._tex1D:
	    GL.glEnable(GL.GL_TEXTURE_1D)
	    GL.glBindTexture(GL.GL_TEXTURE_1D, self.texID)#bind that name to the target
	    GL.glTexImage1D(GL.GL_TEXTURE_1D,#target
		0,				#mipmap level
		GL.GL_RGB,	#internal format
		res,			#width
		0,				#border
		GL.GL_RGB, #target format
		GL.GL_UNSIGNED_BYTE, #target data type
		texture)		#the data
	    GL.glTexParameteri(GL.GL_TEXTURE_1D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT)	#makes the texture map wrap (this is actually default anyway)
	    #interpolate with NEAREST NEIGHBOUR. Important if using bits++ because GL_LINEAR
	    #sometimes extrapolates to pixel vals outside range
	    GL.glTexParameteri(GL.GL_TEXTURE_1D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST)
	    GL.glTexParameteri(GL.GL_TEXTURE_1D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
	else:
	    GL.glEnable(GL.GL_TEXTURE_2D)
	    GL.glBindTexture(GL.GL_TEXTURE_2D, self.texID)#bind that name to the target
	    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB,
		res,res, 0,
		GL.GL_RGB, GL.GL_UNSIGNED_BYTE, texture)
	    GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT)	#makes the texture map wrap (this is actually default anyway)
	    #important if using bits++ because GL_LINEAR
	    #sometimes extrapolates to pixel vals outside range
	    GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST) #linear smoothing if texture is stretched?
	    GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST) #but nearest pixel value if it's compressed?
	GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)#?? do we need this - think not!


    def _setMask(self, maskName):
	"""Users shouldn't use this method
	"""
	self.__maskName = maskName
	res = self.texRes#resolution of texture - 128 is bearable
	rad = misc.makeRadialMatrix(res)
	if type(maskName) == scipy.ArrayType:
	    #handle a numpy array
	    intensity = 255*maskName.astype(scipy.Float)
	    fromFile=0
	elif maskName is "circle":
	    intensity = 255.0*(rad<=1)
	    fromFile=0
	elif maskName is "gauss":
	    sigma = 1/3.0;
	    intensity = 255.0*scipy.exp( -rad**2.0 / (2.0*sigma**2.0) )#3sd.s by the edge of the stimulus
	    fromFile=0
	elif maskName is "radRamp":#a radial ramp
	    intensity = 255.0-255.0*rad
	    intensity = scipy.where(rad<1, intensity, 0)#half wave rectify
	    fromFile=0
	elif maskName in [None,"none"]:
	    res=4
	    intensity = 255.0*scipy.ones((res,res),scipy.Float)
	    fromFile=0
	else:#might be a filename of a tiff
	    try:
		im = Image.open(maskName)
	    except IOError, (details):
		print "couldn't load mask...",maskName,':',details
		return
	    res = im.size[0]
	    im = im.convert("L")#force to intensity (in case it was rgb)
	    intensity = misc.image2array(im)

	#cast into ubyte when done
	data = intensity*self.opacity
	#NB now byintensity already ranges 0:255 - just needs type conv.

	data = data.astype(scipy.UnsignedInt8)
	mask = data.tostring()#serialise

	#do the openGL binding
	GL.glBindTexture(GL.GL_TEXTURE_2D, self.maskID)
	GL.glEnable(GL.GL_TEXTURE_2D)
	GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_ALPHA,
	    res,res, 0,
	    GL.GL_ALPHA, GL.GL_UNSIGNED_BYTE, mask)
	GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT)	#makes the texture map wrap (this is actually default anyway)
	GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_LINEAR)	#linear smoothing if texture is stretched
	GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
	GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)






def setupGL():
    #setup pygame
    pygame.init()
    winHandle = pygame.display.set_mode(winSize,pygame.OPENGL|pygame.DOUBLEBUF)
    
    #setup opengl
    GL.glClearColor(0,0,0, 1.0)	# This Will Clear The Background Color To Black
    GL.glClearDepth(1.0)
    GL.glViewport(0, 0, winSize[0], winSize[1]);
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()			# Reset The Projection Matrix
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    
    GL.glClear(GL.GL_COLOR_BUFFER_BIT|GL.GL_DEPTH_BUFFER_BIT)         
    GL.glEnable(GL.GL_DEPTH_TEST)			# Enables Depth Testing
    GL.glEnable(GL.GL_BLEND)
    GL.glEnable(GL.GL_TEXTURE_1D)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glShadeModel(GL.GL_SMOOTH)			# Color Shading (FLAT or SMOOTH)
    GL.glEnable(GL.GL_POINT_SMOOTH)


#setupGL()
win = Window(winSize)

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
stim = PatchStim(win='junk', size=0.1,pos=[-0.6,-0.6], units='norm', depth = 0.1, tex=None)
stim.draw()

pygame.display.flip()
time.sleep(5)
