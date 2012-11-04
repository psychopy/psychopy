#!/usr/bin/env python
import sys, os, copy
from psychopy import visual, misc, monitors, filters, preferences
from psychopy.tests import utils
import numpy
import pytest
prefs = preferences.Preferences()

"""Each test class creates a context subclasses _baseVisualTest to run a series
of tests on a single graphics context (e.g. pyglet with shaders)

To add a new stimulus test use _base so that it gets tested in all contexts

"""

class _baseVisualTest:
    #this class allows others to be created that inherit all the tests for
    #a different window config
    @classmethod
    def setup_class(self):#run once for each test class (window)
        self.win=None
        self.contextName
        raise NotImplementedError
    @classmethod
    def teardown_class(self):#run once for each test class (window)
        self.win.close()#shutil.rmtree(self.temp_dir)
    def setup(self):#this is run for each test individually
        #make sure we start with a clean window
        self.win.flip()
    def test_auto_draw(self):
        win = self.win
        stims=[]
        stims.append(visual.PatchStim(win))
        stims.append(visual.ShapeStim(win))
        stims.append(visual.TextStim(win))
        for stim in stims:
            assert stim.status==visual.NOT_STARTED
            stim.setAutoDraw(True)
            assert stim.status==visual.STARTED
            stim.setAutoDraw(False)
            assert stim.status==visual.FINISHED
            assert stim.status==visual.STOPPED
    def test_gabor(self):
        win = self.win
        #using init
        gabor = visual.PatchStim(win, mask='gauss', ori=-45,
            pos=[0.6*self.scaleFactor, -0.6*self.scaleFactor],
            sf=2.0/self.scaleFactor, size=2*self.scaleFactor,
            interpolate=True)
        gabor.draw()
        utils.compareScreenshot('gabor1_%s.png' %(self.contextName), win)
        win.flip()#AFTER compare screenshot
        
        #using .set()
        gabor.setOri(45)
        gabor.setSize(0.2*self.scaleFactor, '-')
        gabor.setColor([45,30,0.3], colorSpace='dkl')
        gabor.setSF(0.2/self.scaleFactor, '+')
        gabor.setPos([-0.5*self.scaleFactor,0.5*self.scaleFactor],'+')
        gabor.setContrast(0.8)
        gabor.setOpacity(0.8)
        gabor.draw()
        utils.compareScreenshot('gabor2_%s.png' %(self.contextName), win)
    #def testMaskMatrix(self):
    #    #aims to draw the exact same stimulus as in testGabor, but using filters
    #    win=self.win
    #    contextName=self.contextName
    #    #create gabor using filters
    #    size=2*self.scaleFactor#to match Gabor1 above
    #    if win.units in ['norm','height']:
    #        sf=1.0/size
    #    else:
    #        sf=2.0/self.scaleFactor#to match Gabor1 above
    #    cycles=size*sf
    #    grating = filters.makeGrating(256, ori=135, cycles=cycles)
    #    gabor = filters.maskMatrix(grating, shape='gauss')
    #    stim = visual.PatchStim(win, tex=gabor,
    #        pos=[0.6*self.scaleFactor, -0.6*self.scaleFactor],
    #        sf=1.0/size, size=size,
    #        interpolate=True)
    #    stim.draw()
    #    utils.compareScreenshot('gabor1_%s.png' %(contextName), win)
    def test_text(self):
        win = self.win
        #set font
        fontFile = os.path.join(prefs.paths['resources'], 'DejaVuSerif.ttf')
        #using init
        stim = visual.TextStim(win,text=u'\u03A8a', color=[0.5,1.0,1.0], ori=15,
            height=0.8*self.scaleFactor, pos=[0,0], font='DejaVu Serif',
            fontFiles=[fontFile])
        stim.draw()
        #compare with a LIBERAL criterion (fonts do differ)
        utils.compareScreenshot('text1_%s.png' %(self.contextName), win, crit=20)
        win.flip()#AFTER compare screenshot
        #using set
        stim.setText('y')
        if sys.platform=='win32':
            stim.setFont('Courier New')
        else:
            stim.setFont('Courier')
        stim.setOri(-30.5)
        stim.setHeight(1.0*self.scaleFactor)
        stim.setColor([0.1,-1,0.8], colorSpace='rgb')
        stim.setPos([-0.5,0.5],'+')
        stim.setContrast(0.8)
        stim.setOpacity(0.8)
        stim.draw()
        #compare with a LIBERAL criterion (fonts do differ)
        utils.compareScreenshot('text2_%s.png' %(self.contextName), win, crit=20)

    def test_mov(self):
        win = self.win
        if self.win.winType=='pygame':
            pytest.skip("movies only available for pyglet backend")
        win.flip()
        #construct full path to the movie file
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testMovie.mp4')
        #check if present
        if not os.path.isfile(fileName):
            raise IOError('Could not find movie file: %s' % os.path.abspath(fileName))
        #then do actual drawing
        mov = visual.MovieStim(win, fileName)
        for frameN in range(10):
            mov.draw()
            win.flip()

    def test_shape(self):
        win = self.win

        shape = visual.ShapeStim(win, lineColor=[1, 1, 1], lineWidth=1.0,
            fillColor=[0.80000000000000004, 0.80000000000000004, 0.80000000000000004],
            vertices=[[-0.5*self.scaleFactor, 0],[0, 0.5*self.scaleFactor],[0.5*self.scaleFactor, 0]],
            closeShape=True, pos=[0, 0], ori=0.0, opacity=1.0, depth=0, interpolate=True)
        shape.draw()
        #NB shape rendering can differ a little, depending on aliasing
        utils.compareScreenshot('shape1_%s.png' %(self.contextName), win, crit=12.0)
        win.flip()
        
        # Using .set()
        shape.setContrast(0.8)
        shape.setOpacity(0.8)
        shape.draw()
        utils.compareScreenshot('shape2_%s.png' %(self.contextName), win, crit=12.0)
    def test_radial(self):
        win = self.win
        #using init
        wedge = visual.RadialStim(win, tex='sqrXsqr', color=1,size=2*self.scaleFactor,
            visibleWedge=[0, 45], radialCycles=2, angularCycles=2, interpolate=False)
        wedge.draw()
        utils.compareScreenshot('wedge1_%s.png' %(self.contextName), win, crit=10.0)
        win.flip()#AFTER compare screenshot
        
        #using .set()
        wedge.setOri(180)
        wedge.setContrast(0.8)
        wedge.setOpacity(0.8)
        wedge.setRadialPhase(0.1,operation='+')
        wedge.setAngularPhase(0.1)
        wedge.draw()
        utils.compareScreenshot('wedge2_%s.png' %(self.contextName), win, crit=10.0)
    def test_simpleimage(self):
        win = self.win
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testimage.jpg')
        if not os.path.isfile(fileName):
            raise IOError('Could not find image file: %s' % os.path.abspath(fileName))
        image = visual.SimpleImageStim(win, image=fileName, flipHoriz=True, flipVert=True)
        image.draw()
        utils.compareScreenshot('simpleimage1_%s.png' %(self.contextName), win, crit=5.0) # Should be exact replication
    def test_dots(self):
        #NB we can't use screenshots here - just check that no errors are raised
        win = self.win
        #using init
        dots =visual.DotStim(win, color=(1.0,1.0,1.0), dir=270,
            nDots=500, fieldShape='circle', fieldPos=(0.0,0.0),fieldSize=1*self.scaleFactor,
            dotLife=5, #number of frames for each dot to be drawn
            signalDots='same', #are the signal and noise dots 'different' or 'same' popns (see Scase et al)
            noiseDots='direction', #do the noise dots follow random- 'walk', 'direction', or 'position'
            speed=0.01*self.scaleFactor, coherence=0.9)
        dots.draw()
        win.flip()
        
        #using .set() and check the underlying variable changed
        prevDirs = copy.copy(dots._dotsDir)
        prevSignals = copy.copy(dots._signalDots)
        prevPosRend = copy.copy(dots._fieldPosRendered)
        dots.setDir(20)
        dots.setFieldCoherence(0.5)
        dots.setFieldPos([-0.5,0.5])
        dots.setSpeed(0.1*self.scaleFactor)
        dots.setOpacity(0.8)
        dots.setContrast(0.8)
        dots.draw()
        #check that things changed
        assert (prevDirs-dots._dotsDir).sum()!=0, \
            "dots._dotsDir failed to change after dots.setDir()"
        assert prevSignals.sum()!=dots._signalDots.sum(), \
            "dots._signalDots failed to change after dots.setCoherence()"
        assert not numpy.alltrue(prevPosRend==dots._fieldPosRendered), \
            "dots._fieldPosRendered failed to change after dots.setPos()"
    def test_element_array(self):
        win = self.win
        if not win._haveShaders:
            pytest.skip("ElementArray requires shaders, which aren't available")
        #using init
        thetas = numpy.arange(0,360,10)
        N=len(thetas)
        radii = numpy.linspace(0,1.0,N)*self.scaleFactor
        x, y = misc.pol2cart(theta=thetas, radius=radii)
        xys = numpy.array([x,y]).transpose()
        spiral = visual.ElementArrayStim(win, nElements=N,sizes=0.5*self.scaleFactor,
            sfs=3.0, xys=xys, oris=thetas)
        spiral.draw()
        win.flip()
        spiral.draw()
        utils.compareScreenshot('elarray1_%s.png' %(self.contextName), win)
        win.flip()
    def test_aperture(self):
        win = self.win
        if not win.allowStencil:
            pytest.skip("Don't run aperture test when no stencil is available")
        grating = visual.PatchStim(win, mask='gauss',sf=8.0, size=2,color='FireBrick', units='norm')
        aperture = visual.Aperture(win, size=1*self.scaleFactor,pos=[0.8*self.scaleFactor,0])
        aperture.disable()
        grating.draw()
        aperture.enable()
        grating.setOri(90)
        grating.setColor('black')
        grating.draw()
        utils.compareScreenshot('aperture1_%s.png' %(self.contextName), win)
        #aperture should automatically disable on exit
    def test_rating_scale(self):
        # try to avoid text; avoid default / 'triangle' because it does not display on win XP
        win = self.win
        win.flip()
        rs = visual.RatingScale(win, low=0,high=1,precision=100, displaySizeFactor=3, pos=(0,-.4),
                        lowAnchorText=' ', highAnchorText=' ', scale=' ',
                        markerStyle='glow', markerStart=0.7, markerColor='darkBlue')
        rs.draw()
        utils.compareScreenshot('ratingscale1_%s.png' %(self.contextName), win, crit=30.0)
        win.flip()#AFTER compare screenshot
    def test_refresh_rate(self):
        if self.win.winType=='pygame':
            pytest.skip("getMsPerFrame seems to crash the testing of pygame")
        #make sure that we're successfully syncing to the frame rate
        msPFavg, msPFstd, msPFmed = visual.getMsPerFrame(self.win,nFrames=60, showVisual=True)
        assert (1000/150.0 < msPFavg < 1000/40.0), \
            "Your frame period is %.1fms which suggests you aren't syncing to the frame" %msPFavg

#create different subclasses for each context/backend
class TestPygletNorm(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], winType='pyglet', pos=[50,50], allowStencil=True)
        self.contextName='norm'
        self.scaleFactor=1#applied to size/pos values
class TestPygletHeight(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,64], winType='pyglet', pos=[50,50], allowStencil=False)
        self.contextName='height'
        self.scaleFactor=1#applied to size/pos values
class TestPygletNormNoShaders(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], monitor='testMonitor', winType='pyglet', pos=[50,50], allowStencil=True)
        self.win._haveShaders=False
        self.contextName='normNoShade'
        self.scaleFactor=1#applied to size/pos values
class TestPygletNormStencil(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], monitor='testMonitor', winType='pyglet', pos=[50,50], allowStencil=True)
        self.contextName='stencil'
        self.scaleFactor=1#applied to size/pos values
class TestPygletPix(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(57)
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], monitor=mon, winType='pyglet', pos=[50,50], allowStencil=True,
            units='pix')
        self.contextName='pix'
        self.scaleFactor=60#applied to size/pos values
class TestPygletCm(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(57.0)
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], monitor=mon, winType='pyglet', pos=[50,50], allowStencil=False,
            units='cm')
        self.contextName='cm'
        self.scaleFactor=2#applied to size/pos values
class TestPygletDeg(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(57.0)
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], monitor=mon, winType='pyglet', pos=[50,50], allowStencil=True,
            units='deg')
        self.contextName='deg'
        self.scaleFactor=2#applied to size/pos values
#class TestPygameNorm(_baseVisualTest):
#    @classmethod
#    def setup_class(self):
#        self.win = visual.Window([128,128], winType='pygame', allowStencil=True)
#        self.contextName='norm'
#        self.scaleFactor=1#applied to size/pos values
#class TestPygamePix(_baseVisualTest):
#    @classmethod
#    def setup_class(self):
#        mon = monitors.Monitor('testMonitor')
#        mon.setDistance(57.0)
#        mon.setWidth(40.0)
#        mon.setSizePix([1024,768])
#        self.win = visual.Window([128,128], monitor=mon, winType='pygame', allowStencil=True,
#            units='pix')
#        self.contextName='pix'
#        self.scaleFactor=60#applied to size/pos values
#class TestPygameCm(_baseVisualTest):
#    @classmethod
#    def setup_class(self):
#        mon = monitors.Monitor('testMonitor')
#        mon.setDistance(57.0)
#        mon.setWidth(40.0)
#        mon.setSizePix([1024,768])
#        self.win = visual.Window([128,128], monitor=mon, winType='pygame', allowStencil=False,
#            units='cm')
#        self.contextName='cm'
#        self.scaleFactor=2#applied to size/pos values
#class TestPygameDeg(_baseVisualTest):
#    @classmethod
#    def setup_class(self):
#        mon = monitors.Monitor('testMonitor')
#        mon.setDistance(57.0)
#        mon.setWidth(40.0)
#        mon.setSizePix([1024,768])
#        self.win = visual.Window([128,128], monitor=mon, winType='pygame', allowStencil=True,
#            units='deg')
#        self.contextName='deg'
#        self.scaleFactor=2#applied to size/pos values

