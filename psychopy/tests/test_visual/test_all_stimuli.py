import sys, os, copy
from pathlib import Path

from psychopy import visual, monitors, prefs, constants
from psychopy.visual import filters
from psychopy.tools.coordinatetools import pol2cart
from psychopy.tests import utils
import numpy
import pytest
import shutil
from tempfile import mkdtemp

"""Each test class creates a context subclasses _baseVisualTest to run a series
of tests on a single graphics context (e.g. pyglet with shaders)

To add a new stimulus test use _base so that it gets tested in all contexts

"""

from psychopy.tests import skip_under_vm, requires_plugin
from psychopy.tools import systemtools


class Test_Window():
    """Some tests just for the window - we don't really care about what's drawn inside it
    """
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-test_window')
        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_captureMovieFrames(self):
        stim = visual.GratingStim(self.win, dkl=[0,0,1])
        stim.autoDraw = True
        for frameN in range(3):
            stim.phase += 0.3
            self.win.flip()
            self.win.getMovieFrame()
        self.win.saveMovieFrames(os.path.join(self.temp_dir, 'junkFrames.png'))
        self.win.saveMovieFrames(os.path.join(self.temp_dir, 'junkFrames.gif'))
        region = self.win._getRegionOfFrame()

    def test_multiFlip(self):
        self.win.recordFrameIntervals = False #does a reset
        self.win.recordFrameIntervals = True
        self.win.multiFlip(3)
        self.win.multiFlip(3,clearBuffer=False)
        self.win.saveFrameIntervals(os.path.join(self.temp_dir, 'junkFrameInts'))
        fps = self.win.fps()

    def test_callonFlip(self):
        def assertThisIs2(val):
            assert val==2
        self.win.callOnFlip(assertThisIs2, 2)
        self.win.flip()

    def test_resetViewport(self):
        # Check if the `Window.resetViewport()` method works correctly. Not
        # checking if the OpenGL state is correct here, just if the property
        # setter `Window.viewport` updates accordingly.
        #
        # bugfix: https://github.com/psychopy/psychopy/issues/5135
        #
        viewportOld = self.win.viewport.copy()  # store old viewport value

        # Create a new viewport, ensure that the test value never equals the
        # windows size.
        viewportNew = [0, 0] + [max(int(v / 2.0), 1) for v in viewportOld[2:]]
        self.win.viewport = viewportNew

        # assert that the change has been made correctly after setting
        assert numpy.allclose(self.win.viewport, viewportNew), \
            "Failed to change viewport, expected `{}` got `{}`.".format(
                viewportNew, list(self.win.viewport))  # show as list

        # reset the viewport and check if the value is reset to original
        self.win.resetViewport()

        assert numpy.allclose(self.win.viewport, viewportOld), \
            "Failed to reset viewport, expected `{}` got `{}`.".format(
                viewportOld, list(self.win.viewport))


class _baseVisualTest():
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

    def setup_method(self):#this is run for each test individually
        #make sure we start with a clean window
        self.win.flip()

    def test_imageAndGauss(self):
        win = self.win
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testimage.jpg')
        #use image stim
        size = numpy.array([2.0,2.0])*self.scaleFactor
        image = visual.ImageStim(win, image=fileName, mask='gauss',
                                 size=size, flipHoriz=True, flipVert=True)
        image.draw()
        utils.compareScreenshot('imageAndGauss_%s.png' %(self.contextName), win)
        win.flip()

    def test_gratingImageAndGauss(self):
        win = self.win
        size = numpy.array([2.0,2.0])*self.scaleFactor
        #generate identical image as test_imageAndGauss but using GratingStim
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testimage.jpg')
        if win.units in ['norm','height']:
            sf = -1.0
        else:
            sf = -1.0 / size  # this will do the flipping and get exactly one cycle
        image = visual.GratingStim(win, tex=fileName, size=size, sf=sf, mask='gauss')
        image.draw()
        utils.compareScreenshot('imageAndGauss_%s.png' %(self.contextName), win)
        win.flip()

    def test_numpyFilterMask(self):
        """if the mask is passed in as a numpy array it goes through a different
        set of rules when turned into a texture. But the outcome should be as above
        """
        win = self.win
        from psychopy.visual import filters
        gaussMask = filters.makeMask(128, 'gauss')
        size = numpy.array([2.0,2.0])*self.scaleFactor
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testimage.jpg')
        image = visual.ImageStim(win, image=fileName, mask=gaussMask,
                                 size=size, flipHoriz=True, flipVert=True)
        image.draw()
        utils.compareScreenshot('imageAndGauss_%s.png' %(self.contextName), win)
        win.flip()

    def test_greyscaleImage(self):
        win = self.win
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'greyscale.jpg')
        imageStim = visual.ImageStim(win, fileName)
        imageStim.draw()
        utils.compareScreenshot('greyscale_%s.png' %(self.contextName), win)
        "{}".format(imageStim) #check that str(xxx) is working
        win.flip()
        imageStim.color = [0.1,0.1,0.1]
        imageStim.draw()
        utils.compareScreenshot('greyscaleLowContr_%s.png' %(self.contextName), win)
        win.flip()
        imageStim.color = 1
        imageStim.contrast = 0.1#should have identical effect to color=0.1
        imageStim.draw()
        utils.compareScreenshot('greyscaleLowContr_%s.png' %(self.contextName), win)
        win.flip()
        imageStim.contrast = 1.0
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'greyscale2.png')
        imageStim.image = fileName
        imageStim.size *= 3
        imageStim.draw()
        utils.compareScreenshot('greyscale2_%s.png' %(self.contextName), win)
        win.flip()

    def test_numpyTexture(self):
        win = self.win
        grating = filters.makeGrating(res=64, ori=20.0,
                                     cycles=3.0, phase=0.5,
                                     gratType='sqr', contr=1.0)
        imageStim = visual.ImageStim(win, image=grating,
                                     size = 3*self.scaleFactor,
                                     interpolate=True)
        imageStim.draw()

        utils.compareScreenshot('numpyImage_%s.png' %(self.contextName), win)
        "{}".format(imageStim) #check that str(xxx) is working
        win.flip()
        #set lowcontrast using color
        imageStim.color = [0.1,0.1,0.1]
        imageStim.draw()
        utils.compareScreenshot('numpyLowContr_%s.png' %(self.contextName), win)
        win.flip()
        #now try low contrast using contr
        imageStim.color = 1
        imageStim.contrast = 0.1#should have identical effect to color=0.1
        imageStim.draw()
        utils.compareScreenshot('numpyLowContr_%s.png' %(self.contextName), win)
        win.flip()

    def test_hexColors(self):
        win = self.win
        circle = visual.Circle(win, fillColor='#0000FF',
                               lineColor=None,
                               size=2* self.scaleFactor)
        circle.draw()
        grat = visual.GratingStim(win, ori=20, color='#00AAFF',
            pos=[0.6 * self.scaleFactor, -0.6 * self.scaleFactor],
            sf=3.0 / self.scaleFactor, size=2 * self.scaleFactor,
            interpolate=True)
        grat.draw()
        utils.compareScreenshot('circleHex_%s.png' %(self.contextName), win)
        win.flip()

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
        fontFile = str(utils.TESTS_FONT)
        #using init
        stim = visual.TextStim(win,text=u'\u03A8a', color=[0.5, 1.0, 1.0], ori=15,
            height=0.8*self.scaleFactor, pos=[0,0], font='DejaVu Serif',
            fontFiles=[fontFile])
        stim.draw()
        if self.win.winType != 'pygame':
            #compare with a LIBERAL criterion (fonts do differ)
            utils.compareScreenshot('text1_%s.png' %(self.contextName), win, crit=20)
        win.flip()  # AFTER compare screenshot
        #using set
        stim.text = 'y'
        if sys.platform=='win32':
            stim.font = 'Courier New'
        else:
            stim.font = 'Courier'
        stim.ori = -30.5
        stim.height = 1.0 * self.scaleFactor
        stim.setColor([0.1, -1, 0.8], colorSpace='rgb')
        stim.pos += [-0.5, 0.5]
        stim.contrast = 0.8
        stim.opacity = 0.8
        stim.draw()
        "{}".format(stim) #check that str(xxx) is working
        if self.win.winType != 'pygame':
            #compare with a LIBERAL criterion (fonts do differ)
            utils.compareScreenshot('text2_%s.png' %self.contextName,
                                    win, crit=20)

    def test_text_with_add(self):
        # pyglet text will reset the blendMode to 'avg' so check that we are
        # getting back to 'add' if we want it
        win = self.win
        text = visual.TextStim(win, pos=[0, 0.9])
        grat1 = visual.GratingStim(win, size=2*self.scaleFactor,
                                   opacity=0.5,
                                   pos=[0.3,0.0], ori=45, sf=2*self.scaleFactor)
        grat2 = visual.GratingStim(win, size=2 * self.scaleFactor,
                                   opacity=0.5,
                                   pos=[-0.3, 0.0], ori=-45,
                                   sf=2*self.scaleFactor)

        text.draw()
        grat1.draw()
        grat2.draw()
        if systemtools.isVM_CI():
            pytest.skip("Blendmode='add' doesn't work under a virtual machine for some reason")
        if self.win.winType != 'pygame':
            utils.compareScreenshot('blend_add_%s.png' %self.contextName,
                                    win, crit=20)

    def test_rect(self):
        win = self.win
        rect = visual.Rect(win)
        rect.draw()
        rect.lineColor = 'blue'
        rect.pos = [1, 1]
        rect.ori = 30
        rect.fillColor = 'pink'
        rect.draw()
        "{}".format(rect) #check that str(xxx) is working
        rect.width = 1
        rect.height = 1

    def test_circle(self):
        win = self.win
        circle = visual.Circle(win)
        circle.fillColor = 'red'
        circle.draw()
        circle.lineColor = 'blue'
        circle.fillColor = None
        circle.pos = [0.5, -0.5]
        circle.ori = 30
        circle.draw()
        "{}".format(circle) #check that str(xxx) is working

    def test_line(self):
        win = self.win
        line = visual.Line(win)
        line.start = (0, 0)
        line.end = (0.1, 0.1)
        line.draw()
        win.flip()
        "{}".format(line)  # check that str(xxx) is working

    def test_Polygon(self):
        win = self.win
        cols = ['red','green','purple','orange','blue']
        for n, col in enumerate(cols):
            poly = visual.Polygon(win, edges=n + 5, lineColor=col)
            poly.draw()
        win.flip()
        "{}".format(poly) #check that str(xxx) is working
        poly.edges = 3
        poly.radius = 1

    def test_shape(self):
        win = self.win
        arrow = [(-0.4,0.05), (-0.4,-0.05), (-.2,-0.05), (-.2,-0.1), (0,0), (-.2,0.1), (-.2,0.05)]
        shape = visual.ShapeStim(win, lineColor='white', lineWidth=1.0,
            fillColor='red', vertices=arrow, pos=[0, 0],
            ori=0.0, opacity=1.0, depth=0, interpolate=True)
        shape.draw()
        #NB shape rendering can differ a little, depending on aliasing
        utils.compareScreenshot('shape2_1_%s.png' %(self.contextName), win, crit=12.5)
        win.flip()

        # Using .set()
        shape.contrast = 0.8
        shape.opacity = 0.8
        shape.ori = 90
        shape.draw()
        assert 'Shape' in "{}".format(shape)  # check that str(xxx) is working
        utils.compareScreenshot('shape2_2_%s.png' %(self.contextName), win, crit=12.5)

    def test_simpleimage(self):
        win = self.win
        if win.useRetina:
            pytest.skip("Rendering pixel-for-pixel is not identical on retina")
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testimage.jpg')
        if not os.path.isfile(fileName):
            raise IOError('Could not find image file: %s' % os.path.abspath(fileName))
        image = visual.SimpleImageStim(win, image=fileName, flipHoriz=True, flipVert=True)
        "{}".format(image) #check that str(xxx) is working
        image.draw()
        utils.compareScreenshot('simpleimage1_%s.png' %(self.contextName), win, crit=5.0) # Should be exact replication

    def test_dotsUnits(self):
        #to test this create a small dense circle of dots and check the circle
        #has correct dimensions
        fieldSize = numpy.array([1.0,1.0])
        pos = numpy.array([0.5,0])*fieldSize
        dots = visual.DotStim(self.win, color=[-1.0,0.0,0.5], dotSize=5,
                              nDots=1000, fieldShape='circle', fieldPos=pos)
        dots.draw()
        utils.compareScreenshot('dots_%s.png' %(self.contextName), self.win, crit=20)
        self.win.flip()

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
        "{}".format(dots) #check that str(xxx) is working

        #using .set() and check the underlying variable changed
        prevDirs = copy.copy(dots._dotsDir)
        prevSignals = copy.copy(dots._signalDots)
        prevVerticesPix = copy.copy(dots.verticesPix)
        dots.dir = 20
        dots.coherence = 0.5
        dots.fieldPos = [-0.5, 0.5]
        dots.speed = 0.1 * self.scaleFactor
        dots.opacity = 0.8
        dots.contrast = 0.8
        dots.draw()
        #check that things changed
        assert (prevDirs-dots._dotsDir).sum()!=0, \
            "dots._dotsDir failed to change after dots.setDir()"
        assert prevSignals.sum()!=dots._signalDots.sum(), \
            "dots._signalDots failed to change after dots.setCoherence()"
        assert not numpy.all(prevVerticesPix==dots.verticesPix), \
            "dots.verticesPix failed to change after dots.setPos()"

    def test_element_array(self):
        win = self.win
        if not win._haveShaders:
            pytest.skip("ElementArray requires shaders, which aren't available")
        #using init
        thetas = numpy.arange(0,360,10)
        N=len(thetas)

        radii = numpy.linspace(0,1.0,N)*self.scaleFactor
        x, y = pol2cart(theta=thetas, radius=radii)
        xys = numpy.array([x,y]).transpose()
        spiral = visual.ElementArrayStim(
                win, opacities = 0, nElements=N, sizes=0.5*self.scaleFactor,
                sfs=1.0, xys=xys, oris=-thetas)
        spiral.draw()
        #check that the update function is working by changing vals after first draw() call
        spiral.opacities = 1.0
        spiral.sfs = 3.0
        spiral.draw()
        "{}".format(spiral) #check that str(xxx) is working
        win.flip()
        spiral.draw()
        utils.compareScreenshot('elarray1_%s.png' %(self.contextName), win)
        win.flip()

    def test_aperture(self):
        win = self.win
        if not win.allowStencil:
            pytest.skip("Don't run aperture test when no stencil is available")
        grating = visual.GratingStim(
                win, mask='gauss',sf=8.0, size=2,color='FireBrick',
                units='norm')
        aperture = visual.Aperture(win, size=1*self.scaleFactor,
                                   pos=[0.8*self.scaleFactor,0])
        aperture.enabled = False
        grating.draw()
        aperture.enabled = True
        "{}".format(aperture) #check that str(xxx) is working
        grating.ori = 90
        grating.color = 'black'
        grating.draw()
        utils.compareScreenshot('aperture1_%s.png' %(self.contextName), win)
        #aperture should automatically disable on exit
        for shape, nVert, pos in [(None, 4, (0,0)), ('circle', 72, (.2, -.7)),
                                  ('square', 4, (-.5,-.5)), ('triangle', 3, (1,1))]:
            aperture = visual.Aperture(win, pos=pos, shape=shape, nVert=nVert)
            assert len(aperture.vertices) == nVert  # true for BaseShapeStim; expect (nVert-2)*3 if tesselated
            assert aperture.contains(pos)

    def test_aperture_image(self):
        win = self.win
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testwedges.png')
        if not win.allowStencil:
            pytest.skip("Don't run aperture test when no stencil is available")
        grating = visual.GratingStim(win, mask='gauss',sf=8.0, size=2,
                                     color='FireBrick', units='norm')
        aperture = visual.Aperture(win, size=1*self.scaleFactor,
                                   pos=[0.8*self.scaleFactor,0], shape=fileName)
        aperture.enabled = False
        grating.draw()
        aperture.enabled = True
        "{}".format(aperture) #check that str(xxx) is working
        grating.ori = 90
        grating.color = 'black'
        grating.draw()
        utils.compareScreenshot('aperture2_%s.png' %(self.contextName),
                                win, crit=30)
        #aperture should automatically disable on exit

    @skip_under_vm
    def test_refresh_rate(self):
        if self.win.winType=='pygame':
            pytest.skip("getMsPerFrame seems to crash the testing of pygame")
        #make sure that we're successfully syncing to the frame rate
        msPFavg, msPFstd, msPFmed = visual.getMsPerFrame(self.win, nFrames=60, showVisual=True)
        assert (1000/150.0) < msPFavg < (1000/40.0), \
            "Your frame period is %.1fms which suggests you aren't syncing to the frame" %msPFavg


#create different subclasses for each context/backend
class TestPygletNorm(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], winType='pyglet', pos=[50,50],
                                 allowStencil=True, autoLog=False)
        self.contextName='norm'
        self.scaleFactor=1#applied to size/pos values

class TestPygletHexColor(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], winType='pyglet', pos=[50,50],
                                 color="#FF0099",
                                 allowStencil=True, autoLog=False)
        self.contextName='normHexbackground'
        self.scaleFactor=1#applied to size/pos values

if not systemtools.isVM_CI():
    class TestPygletBlendAdd(_baseVisualTest):
        @classmethod
        def setup_class(self):
            self.win = visual.Window([128,128], winType='pyglet', pos=[50,50],
                                     blendMode='add', useFBO=True)
            self.contextName='normAddBlend'
            self.scaleFactor=1#applied to size/pos values


class TestPygletNormFBO(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], units="norm", winType='pyglet', pos=[50,50],
                                 allowStencil=True, autoLog=False, useFBO=True)
        self.contextName='norm'
        self.scaleFactor=1#applied to size/pos values


class TestPygletHeight(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,64], units="height", winType='pyglet', pos=[50,50],
                                 allowStencil=False, autoLog=False)
        self.contextName='height'
        self.scaleFactor=1#applied to size/pos values


class TestPygletNormStencil(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], units="norm", monitor='testMonitor',
                                 winType='pyglet', pos=[50,50],
                                 allowStencil=True, autoLog=False)
        self.contextName='stencil'
        self.scaleFactor=1#applied to size/pos values


class TestPygletPix(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(57)
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], units="pix", monitor=mon,
                                 winType='pyglet', pos=[50, 50],
                                 allowStencil=True, autoLog=False)
        self.contextName='pix'
        self.scaleFactor=60#applied to size/pos values


class TestPygletCm(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(57.0)
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], units="cm", monitor=mon,
                                 winType='pyglet', pos=[50,50],
                                 allowStencil=False, autoLog=False)
        self.contextName='cm'
        self.scaleFactor=2#applied to size/pos values


class TestPygletDeg(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(57.0)
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], units="deg", monitor=mon,
                                 winType='pyglet', pos=[50,50], allowStencil=True,
                                 autoLog=False)
        self.contextName='deg'
        self.scaleFactor=2#applied to size/pos values


class TestPygletDegFlat(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(10.0) #exaggerate the effect of flatness by setting the monitor close
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], units="degFlat", monitor=mon,
                                 winType='pyglet', pos=[50,50],
                                 allowStencil=True, autoLog=False)
        self.contextName='degFlat'
        self.scaleFactor=4#applied to size/pos values


class TestPygletDegFlatPos(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(10.0) #exaggerate the effect of flatness by setting the monitor close
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], units='degFlatPos', monitor=mon,
                                 winType='pyglet', pos=[50,50],
                                 allowStencil=True, autoLog=False)
        self.contextName='degFlatPos'
        self.scaleFactor=4#applied to size/pos values

# @pytest.mark.needs_pygame
# class TestPygameNorm(_baseVisualTest):
#    @classmethod
#    def setup_class(self):
#        self.win = visual.Window([128,128], winType='pygame', allowStencil=True, autoLog=False)
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
#            units='pix', autoLog=False)
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
#


if __name__ == '__main__':
    cls = TestPygletDegFlatPos()
    cls.setup_class()
    cls.test_radial()
    cls.teardown_class()
