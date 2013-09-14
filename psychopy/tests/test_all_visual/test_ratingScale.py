import sys, os, copy
from psychopy import visual, prefs, event
from psychopy.tests import utils
from psychopy.constants import *
import numpy
import pytest
import shutil
from tempfile import mkdtemp

"""define various RatingScale instances, aiming for complete code coverage
"""

class Test_class_RatingScale:
    """RatingScale internal logic, no check that its drawn correctly
    """
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-test_window')
        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False)

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_init_scales(self):
        # give non-default values for all params

        r = visual.RatingScale(self.win)
        r = visual.RatingScale(self.win, low=0, high=1000)
        r = visual.RatingScale(self.win, scale='scale')
        r = visual.RatingScale(self.win, choices=['a', 'b'])
        r = visual.RatingScale(self.win, lowAnchorText=1, highAnchorText='a lot')
        r = visual.RatingScale(self.win, tickMarks=[1,2,3])
        r = visual.RatingScale(self.win, labels=['a', 'b'])
        for i in [0, 1, 10, 100, 1000, 0.3]:
            r = visual.RatingScale(self.win, precision=i)
        r = visual.RatingScale(self.win, textSizeFactor=3, textColor=0.3)
        r = visual.RatingScale(self.win, textFont='Helvetica')
        r = visual.RatingScale(self.win, showValue=False)
        r = visual.RatingScale(self.win, showScale=False)
        r = visual.RatingScale(self.win, showAnchors=False)
        r = visual.RatingScale(self.win, showAccept=False)
        r = visual.RatingScale(self.win, acceptKeys='a')
        r = visual.RatingScale(self.win, acceptKeys=['a','b'])
        r = visual.RatingScale(self.win, acceptPreText='a')
        r = visual.RatingScale(self.win, acceptText='a')
        r = visual.RatingScale(self.win, acceptSize=2.1)

        r = visual.RatingScale(self.win, leftKeys=['a'])
        r = visual.RatingScale(self.win, rightKeys=['a'])
        r = visual.RatingScale(self.win, respKeys=['a'])
        r = visual.RatingScale(self.win, lineColor='Black')

        r = visual.RatingScale(self.win, ticksAboveLine=False)
        r = visual.RatingScale(self.win, markerStart=3)
        r = visual.RatingScale(self.win, markerExpansion=10)
        r = visual.RatingScale(self.win, markerStyle='glow', markerExpansion=0, displaySizeFactor=2)
        r.markerPlaced = True
        r.markerExpansion = 10
        r.draw()

        r = visual.RatingScale(self.win, customMarker=visual.Circle(self.win))
        for marker in ['triangle', 'glow', 'slider', 'circle']:
            r = visual.RatingScale(self.win, markerStyle=marker)

        r = visual.RatingScale(self.win, escapeKeys=['space'])
        r = visual.RatingScale(self.win, allowSkip=False)
        r = visual.RatingScale(self.win, mouseOnly=True, singleClick=True)
        r = visual.RatingScale(self.win, displaySizeFactor=.2, stretchHoriz=2)
        r = visual.RatingScale(self.win, pos=(0,.5), skipKeys='space')
        r = visual.RatingScale(self.win, minTime=0.001, maxTime=1)
        r = visual.RatingScale(self.win, name='name', autoLog=False)

    def test_ratingscale_misc(self):
        r = visual.RatingScale(self.win)
        r._getMarkerFromPos(.2)
        r._getMarkerFromTick(0)

    def test_draw_conditionals(self):
        r = visual.RatingScale(self.win)

        # 934-40, 944-45 if self.allowTimeOut ....:
        r.allowTimeOut = True
        r.timedOut = False
        r.maxTime = -1
        r.noResponse = False
        r.disappear = True
        r.draw()

        # 1049-1061  if self.myMouse.getPressed()[0]:

        # 1066-1072  if not self.noResponse and self.decisionTime == 0:
        r = visual.RatingScale(self.win)
        r.beyondMinTime = True
        r.showAccept = True
        r.noResponse = False
        r.decisionTime = 0
        r.draw()

    def test_key_presses(self):
        r = visual.RatingScale(self.win)
        r.markerPlaced = True
        r.allKeys = ['s']
        r.markerPlacedAt = 2

        # 1014-1042
        r.mouseOnly = False
        r.skipKeys = ['s']
        event._onPygletKey(symbol='s', modifiers=None, emulated=True)
        r.draw()
        r.skipKeys = []

        r.respKeys = ['s']
        r.enableRespKeys = True
        event._onPygletKey(symbol='s', modifiers=None, emulated=True)
        r.draw()
        r.respKeys = []

        r = visual.RatingScale(self.win)
        r.markerPlaced = True
        r.allKeys = ['s']
        r.markerPlacedAt = 2
        r.leftKeys = ['s']
        event._onPygletKey(symbol='s', modifiers=None, emulated=True)
        r.draw()
        r.leftKeys = []

        r.rightKeys = ['s']
        event._onPygletKey(symbol='s', modifiers=None, emulated=True)
        r.draw()
        r.rightKeys = []

        r.acceptKeys = ['s']
        r.beyondMinTime = True
        event._onPygletKey(symbol='s', modifiers=None, emulated=True)
        r.draw()

    def test_1019_1029(self):
        # 1019-1029
        r = visual.RatingScale(self.win)
        r.skipKeys = []
        r.mouseOnly = False
        r.enableRespKeys = True
        r.respKeys = ['s']
        r.allKeys = ['s']
        r.tickFromKeyPress = {u's': 1}
        event._onPygletKey(symbol='s', modifiers=None, emulated=True)
        r.singleClick = True
        r.beyondMinTime = True
        r.draw()

        r.leftKeys = ['s']
        r.draw()
        r.leftKeys = []
        r.rightKeys = ['s']
        r.draw()
        r.rightKeys = []

        # 1139-43
        r.status = FINISHED
        for r.noResponse in [True, False]:
            for r.timedOut in [True, False]:
                r.getRT()

        # getRating coverage
        r.noResponse =True
        r.status = FINISHED
        r.getRating()

    def test_labels_False(self):
        # 386-92
        for anc in [None, 'a']:
            r = visual.RatingScale(self.win, choices=['1', '2', '3'], labels=False,
                               lowAnchorText=anc, highAnchorText=anc)
