import sys
from pyglet.window import key
from psychopy.visual import Window, TextStim, GratingStim, Circle
from psychopy.visual.windowwarp import Warper
from psychopy import event
import pytest, copy

"""define WindowWarp configurations, test the logic

    test:
    cd psychopy/psychopy/
    py.test -k projections --cov-report term-missing --cov visual/windowwarp.py
"""

foregroundColor = [-1, -1, -1]
backgroundColor = [1, 1, 1]


class ProjectionsLinesAndCircles:
    """
    Test jig for projection warping.
    Switch between warpings by pressing a key 'S'pherical, 'C'ylindrical, 'N'one, warp'F'ile.
    Click the mouse to set the eyepoint X, Y.
    Up / Down arrow or mousewheel to move eyepoint in and out.
    """
    def __init__(self, win, warper):

        self.win = win
        self.warper = warper

        self.stimT = TextStim(self.win, text='Null warper', units = 'pix',
                              pos=(0, -140), height=20)

        self.bl = -win.size / 2.0
        self.tl = (self.bl[0], -self.bl[1])
        self.tr = win.size / 2.0

        self.stims = []
        self.degrees = 120
        nLines = 12
        for x in range(-nLines, nLines+1):
            t = GratingStim(win, tex=None, units='deg', size=[2, win.size[1]],
                            texRes=128, color=foregroundColor,
                            pos=[float(x) / nLines * self.degrees, 0])
            self.stims.append (t)

        for y in range (-nLines, nLines+1):
            t = GratingStim(win, tex=None, units='deg', size=[win.size[0], 2],
                            texRes=128, color=foregroundColor,
                            pos=[0, float(y)/nLines * self.degrees])
            self.stims.append(t)

        for c in range (1, nLines+1):
            t = Circle (win, radius=c * 10, edges=128, units='deg', lineWidth=4)
            self.stims.append(t)

        self.updateInfo()

        self.keys = key.KeyStateHandler()
        win.winHandle.push_handlers(self.keys)
        self.mouse = event.Mouse(win=self.win)

    def updateFrame(self):
        """ Updates frame with any item that is to be modulated per frame. """
        for s in self.stims:
            s.draw()
        self.stimT.draw()

    def update_sweep(self):
        """ Update function for sweeps. Input is in domain units. """
        self.updateFrame()
        self.check_keys()
        self._handleMouse()
        self.win.flip()

    def updateInfo(self):
        try:
            self.stimT.setText(
                "%s \n   eyePoint: %.3f, %.3f \n   eyeDistance: %.2f\n\n"
                "Projection: [s]pherical, [c]ylindrical, [n]one, warp[f]ile\n"
                "Flip: [h]orizontal, [v]ertical\n"
                "Mouse: wheel = eye distance, click to set eyepoint\n"
                "[q]uit" % (
                self.warper.warp,
                self.warper.eyepoint[0], self.warper.eyepoint[1],
                self.warper.dist_cm))
        except Exception:
            pass

    def check_keys(self):
        """Checks key input"""
        for keys in event.getKeys(timeStamped=True):
            k = keys[0]
            if k in ['escape', 'q']:
                self.win.close()
                sys.exit()
            elif k in ['space']:
                for c in range (1,2):
                    t = Circle(self.win, radius=c)
                    self.stims.append (t)
                #for c in range (1,2):
                #    t = RadialStim(self.win)
                #    self.stims.append(t)

            # handle projections
            elif k in ['s']:
                self.warper.changeProjection ('spherical', None, (0.5,0.5))
            elif k in ['c']:
                self.warper.changeProjection ('cylindrical', None, (0.5,0.5))
            elif k in ['n']:
                self.warper.changeProjection (None, None, (0.5,0.5))
            elif k in ['f']:
                self.warper.changeProjection ('warpfile',
                    r'..\data\sample.meshwarp.data',
                     (0.5,0.5))

            # flip horizontal and vertical
            elif k in ['h']:
                self.warper.changeProjection(self.warper.warp, self.warper.warpfile, flipHorizontal = not self.warper.flipHorizontal)
            elif k in ['v']:
                self.warper.changeProjection(self.warper.warp, self.warper.warpfile, flipVertical = not self.warper.flipVertical)

            # move eyepoint
            elif k in ['down']:
                if (self.warper.dist_cm > 1):
                    self.warper.dist_cm -= 1
                    self.warper.changeProjection (self.warper.warp, None, self.warper.eyepoint)
            elif k in ['up']:
                if (self.warper.dist_cm < 200):
                    self.warper.dist_cm += 1
                    self.warper.changeProjection (self.warper.warp, None, self.warper.eyepoint)
            elif k in ['right']:
                if (self.warper.eyepoint[0] < 0.9):
                    self.warper.eyepoint = (self.warper.eyepoint[0] + 0.1, self.warper.eyepoint[1])
                    self.warper.changeProjection (self.warper.warp, None, self.warper.eyepoint)
            elif k in ['left']:
                if (self.warper.eyepoint[0] > 0.1):
                    self.warper.eyepoint = (self.warper.eyepoint[0] - 0.1, self.warper.eyepoint[1])
                    self.warper.changeProjection (self.warper.warp, None, self.warper.eyepoint)

            self.updateInfo()

    def _handleMouse(self):
        x,y = self.mouse.getWheelRel()
        if y != 0:
            self.warper.dist_cm += y
            self.warper.dist_cm = max (1, min (200, self.warper.dist_cm))
            self.warper.changeProjection (self.warper.warp, self.warper.warpfile, self.warper.eyepoint)
            self.updateInfo()

        pos = (self.mouse.getPos() + 1) / 2
        leftDown = self.mouse.getPressed()[0]
        if leftDown:
            self.warper.changeProjection (self.warper.warp, self.warper.warpfile, pos)
            self.updateInfo()


class Test_class_WindowWarp():
    def setup_class(self):
        self.win = Window(monitor='testMonitor', screen=1, fullscr=True, color='gray', useFBO = True, autoLog=False)
        self.warper = Warper(self.win, warp='spherical', warpfile="", warpGridsize=128, eyepoint=[0.5, 0.5],
                             flipHorizontal=False, flipVertical=False)
        self.warper.dist_cm = 15
        self.g = ProjectionsLinesAndCircles(self.win, self.warper)

    def teardown_class(self):
        self.win.close()

    def draw_projection (self, frames=120):
        self.g.updateInfo()
        for i in range(frames):
            self.g.update_sweep()

    def test_spherical(self):
        self.warper.changeProjection('spherical')
        self.draw_projection()

    def test_cylindrical(self):
        self.warper.changeProjection('cylindrical')
        self.draw_projection()

    def test_warpfile(self):
        self.warper.changeProjection('warpfile', warpfile="") #jayb todo
        self.draw_projection()

    def test_distance(self):
        self.test_spherical()
        for i in range (1, 50, 2):
            self.warper.dist_cm = i
            self.warper.changeProjection(self.warper.warp)
            self.g.updateInfo()
            self.g.update_sweep()

        self.test_cylindrical()
        for i in range (1, 50, 2):
            self.warper.dist_cm = i
            self.warper.changeProjection(self.warper.warp)
            self.g.updateInfo()
            self.g.update_sweep()

    def test_flipHorizontal(self):
        self.warper.changeProjection(self.warper.warp, self.warper.warpfile, flipHorizontal = not self.warper.flipHorizontal)
        self.draw_projection()

    def test_flipVertical(self):
        self.warper.changeProjection(self.warper.warp, self.warper.warpfile, flipVertical = not self.warper.flipVertical)
        self.draw_projection()

if __name__ == '__main__':
        # running interactive
        cls = Test_class_WindowWarp()
        cls.setup_class()
        for i in range(2 * 60 * 60):
            cls.g.update_sweep()
        cls.win.close()
