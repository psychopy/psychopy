from psychopy import visual,event, core
import pyglet.font, numpy
import pyglet.gl as GL
symbolSet=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','1','2','3','4','5','6','7','8','9','_']

_depthIncrements = {'pyglet':+0.001, 'pygame':-0.001, 'glut':-0.001}
class FasterText(visual.TextStim):
    def __init__(self, *args, **kwargs):
        visual.TextStim.__init__(self, *args, **kwargs)
        font = pyglet.font.load('Arial', 14, bold=True, italic=False)
        self.glyphStr = pyglet.font.GlyphString(self.text, font.get_glyphs(self.text))
    def draw(self, win=None):
        
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
        prevScale = self.win.setScale(self._winScale)
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],thisDepth)#NB depth is set already
        GL.glRotatef(self.ori,0.0,0.0,1.0)
        self.win.setScale('pix',None, prevScale)
        
        if self._useShaders: #then rgb needs to be set as glColor
            #setup color
            desiredRGB = (self.rgb*self.contrast+1)/2.0#RGB in range 0:1 and scaled for contrast
            if numpy.any(desiredRGB**2.0>1.0):
                desiredRGB=[0.6,0.6,0.4]
            GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)
        else: #color is set in texture, so set glColor to white
            GL.glColor4f(1,1,1,1)

        GL.glDisable(GL.GL_DEPTH_TEST) #should text have a depth or just on top?
        #update list if necss and then call it
        if self.win.winType=='pyglet':
            
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
            
            self.glyphStr.draw()            
            GL.glDisable(GL.GL_TEXTURE_2D) 
        else: 
            #for pygame we should (and can) use a drawing list   
            if self.needUpdate: self._updateList()
            GL.glCallList(self._listID)
        GL.glEnable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
        GL.glPopMatrix()
        
myWin = visual.Window((800,600), winType='pyglet')
myWin.setRecordFrameIntervals()
off_symbolArray=[]
colCount=1
rowCount=1

x_offset=100
y_offset=100

x_origin=-1*1680/2
y_origin=1050/2

for symbol in symbolSet:
        off_symbolArray.append(FasterText(myWin,
            units='pix',height = 100,
            pos=(x_origin+(colCount*x_offset),y_origin-(rowCount*y_offset)),
            text=symbol,rgb=[+1,-1,-1]) )
        colCount=colCount+1
        if colCount>6:
                colCount=1
                rowCount=rowCount+1

on_symbolArray=[]
colCount=1
rowCount=1

switch=0
for frameN in range(300):
        for symbols in off_symbolArray:
                symbols.draw()
        myWin.flip() 
        
print myWin.fps()
