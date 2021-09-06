#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyglet.window import key
from psychopy.visual import *
from psychopy.visual.windowwarp import *
from psychopy.visual.windowframepack import *

foregroundColor=[-1,-1,-1]
backgroundColor=[1,1,1]


class ProjectionsLinesAndCircles():
    """
    Test jig for projection warping.
    Switch between warpings by pressing a key 'S'pherical, 'C'ylindrical, 'N'one, warp'F'ile.
    Click the mouse to set the eyepoint X, Y.
    Up / Down arrow or mousewheel to move eyepoint in and out.
    """
    def __init__(self, window, warper):
        self.window = window
        self.warper = warper

        self.stimT = TextStim(self.window, text='Null warper',
                              units = 'pix', pos=(0, -140), height=20)

        self.bl = -window.size / 2.0
        self.tl = (self.bl[0], -self.bl[1])
        self.tr = window.size / 2.0

        self.stims = []
        self.degrees = 120
        nLines = 12
        for x in range(-nLines, nLines+1):
            t = GratingStim(window,tex=None,units='deg',size=[2,window.size[1]],texRes=128,color=foregroundColor, pos=[float(x) / nLines * self.degrees,0])
            self.stims.append (t)

        for y in range(-nLines, nLines+1):
            t = GratingStim(window,tex=None,units='deg',size=[window.size[0],2],texRes=128,color=foregroundColor,pos=[0,float(y)/nLines * self.degrees])
            self.stims.append (t)

        for c in range(1, nLines+1):
            t = Circle(window, radius=c * 10, edges=128, units='deg', lineWidth=4)
            self.stims.append (t)

        self.updateInfo()

        self.keys = key.KeyStateHandler()
        window.winHandle.push_handlers(self.keys)
        self.mouse = event.Mouse(win=self.window)

    def updateFrame(self, i):
        """ Updates frame with any item that is to be modulated per frame. """
        for s in self.stims:
            s.draw()
        self.stimT.draw()

    def update_sweep(self,i):
        """ Update function for sweeps. Input is in domain units. """
        self.updateFrame(i)
        self.check_keys()
        self._handleMouse()
        self.window.flip()

    def updateInfo(self):
        try:
            self.stimT.setText ("%s \n   eyePoint: %.3f, %.3f \n   eyeDistance: %.2f\n\nProjection: [s]pherical, [c]ylindrical, [n]one, warp[f]ile\nFlip: [h]orizontal, [v]ertical\nMouse: wheel = eye distance, click to set eyepoint\n[q]uit" % (
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
                self.window.close()
                sys.exit()
            elif k in ['space']:
                for c in range (1,2):
                    t = Circle(self.window, radius=c)
                    self.stims.append (t)
                #for c in range (1,2):
                #    t = RadialStim(self.window)
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
                    #r'C:\WinPython-64bit-2.7.5.3\python-2.7.5.amd64\Lib\site-packages\aibs\Projector\Calibration\standard_4x3.data',
                    r'C:\Users\jayb\Documents\Stash\aibs\Projector\Calibration\InteriorProject24inDome6inMirrorCenter.meshwarp.data',
                    #r'C:\WinPython-64bit-2.7.5.3\python-2.7.5.amd64\Lib\site-packages\aibs\Projector\Calibration\standard_16x9.data',
                    (0.5,0.5))

            # flip horizontal and vertical
            elif k in ['h']:
                self.warper.changeProjection(self.warper.warp, self.warper.warpfile, flipHorizontal = not self.warper.flipHorizontal)
            elif k in ['v']:
                self.warper.changeProjection(self.warper.warp, self.warper.warpile, flipVertical = not self.warper.flipVertical)

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
        x, y = self.mouse.getWheelRel()
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


def mainProjectionsLinesAndCircles(params=None):
    """
    ProjectionsLinesAndCircles test runner to test projections
    """
    if not params:
        params = {'testlength': 400}
    win = Window(monitor='LightCrafter4500', screen=1, fullscr=True, color='gray', useFBO = True, autoLog=False)
    warper = Warper (win, warp='spherical', warpfile = "", warpGridsize = 128, eyepoint = [0.5, 0.5], flipHorizontal = False, flipVertical = False)

    # frame packer is used with DLP projectors to create 180Hz monochrome stimuli
    #framePacker = ProjectorFramePacker(win)

    g = ProjectionsLinesAndCircles(win, warper)
    for i in range(int(params['testlength'] * 60)):
        g.update_sweep(i)
    win.close()


if __name__ == "__main__":
    mainProjectionsLinesAndCircles()
