#!/usr/bin/env python
import nose, sys, os
from psychopy import visual
from psychopy.tests import utils

#def testMany():
#    win = visual.Window([600,600])
#    text = visual.TextStim(win, text='hello', pos=[-0.9, -0.9])
#    gabor = visual.PatchStim(win, mask='gauss', pos=[0.9, -0.9])
#    shape = visual.ShapeStim(win, lineRGB=[1, 1, 1], lineWidth=1.0, 
#        fillRGB=[0.80000000000000004, 0.80000000000000004, 0.80000000000000004], 
#        vertices=[[-0.5, 0],[0, 0.5],[0.5, 0]], 
#        closeShape=True, pos=[0, 0], ori=0.0, opacity=1.0, depth=0, interpolate=True)
#    mov = visual.MovieStim(win, 'testMovie.mp4')
#    for frameN in range(10):
#        shape.draw()
#        text.draw()
#        gabor.draw()
#        mov.draw()
#        win.flip()
#    win.close()

class _baseVisualTest:
    #this class allows others to be created that inherit all the tests for
    #a different window config
    def setUp(self):
        #Implement this to create self.win on each use
        self.win=None
        self.contextName
        raise NotImplementedError        
    def tearDown(self):
        self.win.close()#shutil.rmtree(self.temp_dir)
    def testGabor(self):
        _drawGabors(self.win, contextName=self.contextName)
    def testText(self):
        _drawText(self.win, contextName=self.contextName)
        
class TestPygletNorm(_baseVisualTest):
    def setUp(self):
        self.win = visual.Window([48,48], winType='pyglet')
        self.contextName='norm'
        
class TestPygameNorm(_baseVisualTest):
    def setUp(self):
        self.win = visual.Window([48,48], winType='pygame')
        self.contextName='norm'
        
def _drawGabors(win, contextName=""):
    #using init
    gabor = visual.PatchStim(win, mask='gauss', pos=[0.6, -0.6], sf=2, size=2)
    gabor.draw()
    win.flip()
    utils.compareScreenshot('data/gabor1_%s.png' %(contextName), win)
    #using .set()
    gabor.setOri(45)
    gabor.setSize(0.2, '-')
    gabor.setColor([45,30,0.3], colorSpace='dkl')
    gabor.setSF(0.2, '+')
    gabor.setPos([-0.5,0.5],'+')
    gabor.draw()
    win.flip()
    utils.compareScreenshot('data/gabor2_%s.png' %(contextName), win)
    
def _drawText(win, contextName=""):
    if win.winType=='pygame':
        if sys.platform=='win32': font = 'times'
        else:font = '/Library/Fonts/Times New Roman.ttf'
    else: font = 'Times New Roman'
    #using init
    stim = visual.TextStim(win,text=u'\u03A8a', color=[0.5,1.0,1.0], ori=15,
        height=0.8, pos=[0,0], font=font) 
    stim.draw()
    win.flip()
    #compare with a LIBERAL criterion (fonts do differ) 
    utils.compareScreenshot('data/gabor1_%s.png' %(contextName), win, crit=30)
    #using set
    stim.setText('y')
    stim.setFont(font)
    stim.setOri(-30.5)
#    stim.setHeight(1.0)
    stim.setColor([0.1,-1,0.8], colorSpace='rgb')
    stim.setPos([-0.5,0.5],'+')
    stim.draw()
    win.flip()
    #compare with a LIBERAL criterion (fonts do differ)
    utils.compareScreenshot('data/text2_%s.png' %(contextName), win, crit=30)
    


if __name__ == "__main__":
    nose.run(argv=argv)
