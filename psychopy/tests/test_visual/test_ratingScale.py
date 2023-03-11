from psychopy.colors import Color
from psychopy.visual import RatingScale, Window, shape, TextStim
from psychopy import event, core
from psychopy.constants import (NOT_STARTED, FINISHED)
from psychopy.tools import systemtools
import pytest, copy

"""define RatingScale configurations, test the logic

    .draw() is to pick up coverage, not do a visual test (see test_all_visual).
    ~93% coverage; miss code that is conditional on mouse events

    test:
    cd psychopy/psychopy/
    py.test -k ratingscale --cov-report term-missing --cov visual/ratingscale.py
"""


@pytest.mark.ratingscale
class Test_class_RatingScale:
    """RatingScale internal logic, no check that its drawn correctly
    """
    def setup_class(self):
        self.win = Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        self.winpix = Window([128,128], pos=[50,50], allowGUI=False, units='pix', autoLog=False)
        self.r = RatingScale(self.win, autoLog=False)

    def teardown_class(self):
        pass

    def test_init_scales(self):
        # ideally: give default, non-default, and bad values for all params

        # defaults: ---------
        r = copy.copy(self.r)
        assert (r.low, r.high, r.precision) == (1, 7, 1)
        assert (r.markerStyle, r.markerStart, r.markerPlaced) == ('triangle', None, False)

        # non-defaults and some bad: ---------
        r = RatingScale(self.win, low=-10., high=10., autoLog=False)
        assert (r.low, r.high) == (-10, 10)
        assert (type(r.low), type(r.high)) == (int, int)
        r = RatingScale(self.win, low='a', high='s', autoLog=False)  # bad vals
        assert (r.low, r.high) == (1, 2)
        r = RatingScale(self.win, low=10, high=2, autoLog=False)
        assert r.high == r.low + 1 == 11
        assert r.precision == 100

        ch = ['a', 'b']
        r = RatingScale(self.win, choices=ch, precision=10, autoLog=False)
        assert r.precision == 1  # because choices
        assert r.respKeys == list(map(str, list(range(len(ch)))))
        r = RatingScale(self.win, choices=['a'], autoLog=False)

        r = RatingScale(self.win, tickMarks=[1,2,3], labels=['a','b'], autoLog=False)

        for i in [-1, 0.3, 1.2, 9, 12, 100, 1000]:
            r = RatingScale(self.win, precision=i, autoLog=False)
            assert r.precision in [1, 10, 100]
        r = RatingScale(self.win, textSize=3, textColor=0.3, autoLog=False)

        #r = RatingScale(self.win, textFont=utils.TESTS_FONT, autoLog=False)
        #assert r.accept.font == r.scaleDescription.font == utils.TESTS_FONT

        r = RatingScale(self.win, showValue=False, showAccept=False, acceptKeys=[], autoLog=False)
        r = RatingScale(self.win, showAccept=False, mouseOnly=True, singleClick=False, autoLog=False)
        assert r.mouseOnly == False

        r = RatingScale(self.win, acceptKeys='a', autoLog=False)
        r = RatingScale(self.win, acceptKeys=['a','b'], autoLog=False)
        r = RatingScale(self.win, acceptPreText='a', acceptText='a', acceptSize=2.1, autoLog=False)

        r = RatingScale(self.win, leftKeys=['a'], rightKeys=['a'], autoLog=False)
        assert r.respKeys == list(map(str, list(range(1,8))))
        r = RatingScale(self.win, respKeys=['a'], acceptKeys=['a'], autoLog=False)
        r = RatingScale(self.win, acceptKeys=['1'], autoLog=False)
        r = RatingScale(self.win, tickHeight=-1, autoLog=False)

        r = RatingScale(self.win, markerStart=3, tickHeight=False, autoLog=False)
        r = RatingScale(self.win, markerStart='a', choices=['a','b'], autoLog=False)
        assert r.choices == ['a', 'b']
        r = RatingScale(self.win, markerColor='dark red', lineColor='Black', autoLog=False)
        assert r.marker._fillColor == r.marker._borderColor == Color('darkred')
        assert r.line._borderColor == Color('Black')
        r = RatingScale(self.win, marker='glow', markerExpansion=0, autoLog=False)
        r.markerPlaced = True
        r.draw()
        r.markerExpansion = 10
        r.draw()

        r = RatingScale(self.win, skipKeys=None, mouseOnly=True, singleClick=True, autoLog=False)
        r = RatingScale(self.win, pos=(0,.5), skipKeys='space', autoLog=False)
        r = RatingScale(self.winpix, pos=[1], autoLog=False)
        r = RatingScale(self.winpix, pos=['a','x'], autoLog=False)
        assert r.pos == [0.0, (-50.0 / r.win.size[1])]
        x, y = -3, 17
        r = RatingScale(self.winpix, pos=(x, y), size=.2, stretch=2, autoLog=False)
        assert r.offsetHoriz == 2. * x / r.win.size[0]
        assert r.offsetVert == 2. * y / r.win.size[1]
        assert r.stretch == 2
        assert r.size == 0.2 * 0.6  # internal rescaling by 0.6

        r = RatingScale(self.win, stretch='foo', size='foo', autoLog=False)
        assert r.stretch == 1
        assert r.size == 0.6
        r = RatingScale(self.win, size=5, autoLog=False)
        assert r.size == 3

        r = RatingScale(self.win, minTime=0.001, maxTime=1, autoLog=False)
        assert r.minTime == 0.001 and r.maxTime == 1
        r = RatingScale(self.win, minTime='x', maxTime='s', name='name', autoLog=False)
        assert r.minTime == 1.0 and r.maxTime == 0.
        assert r.name == 'name' and r.autoLog == False

    def test_markers(self):
        for marker in ['triangle', 'glow', 'slider', 'circle', 'hover', None]:
            r = RatingScale(self.win, choices=['0', '1'], marker=marker, autoLog=False)
            r.draw()
        with pytest.raises(SystemExit):
            r = RatingScale(self.win, marker='hover', autoLog=False)  # needs choices

        cm = TextStim(self.win, text='|')
        r = RatingScale(self.win, marker=cm, autoLog=False)
        r.noResponse = False
        r.markerPosFixed = False
        r.draw()

        class bad_customMarker():
            def __init__(self): pass
        r = RatingScale(self.win, marker=bad_customMarker(), autoLog=False)
        assert type(r.marker) == shape.ShapeStim

    def test_ratingscale_misc(self):
        r = copy.copy(self.r)
        assert r._getMarkerFromPos(0.2) == 5
        assert r._getMarkerFromTick(0) == 0
        r.setMarkerPos(2)
        assert r.markerPlacedAt == 2
        r.setDescription()
        assert r.flipVert == False  # 'needed to test'
        r.setFlipVert(True)

        # test reset()
        r = RatingScale(self.win, markerStart=2)
        assert r.noResponse == True
        assert r.markerPlaced == True
        assert r.markerPlacedBySubject == False
        assert r.markerPlacedAt == r.markerStart - r.low
        assert r.firstDraw == True
        assert r.decisionTime == 0
        assert r.markerPosFixed == False
        assert r.frame == 0
        assert r.status == NOT_STARTED
        assert r.history is None

        assert r.autoRescaleFactor == 1
        r = RatingScale(self.win, low=0, high=30)
        assert r.autoRescaleFactor == 10

    def test_draw_conditionals(self):
        r = copy.copy(self.r)

        r.allowTimeOut = True
        r.timedOut = False
        r.maxTime = -1
        r.noResponse = False
        r.disappear = True
        r.draw()

        # miss lines: if self.myMouse.getPressed()[0]:

        r = copy.copy(self.r)
        r.beyondMinTime = True
        r.showAccept = True
        r.noResponse = False
        r.decisionTime = 0
        r.draw()

        r = RatingScale(self.win, singleClick=True, markerStart=1, marker='glow', markerExpansion=-10, autoLog=False)
        r.draw()

        r = RatingScale(self.win, singleClick=True, markerStart=-1, autoLog=False)
        r.draw()

        r = RatingScale(self.win, showAccept=True, choices=['a', 'b'], autoLog=False)
        r.showValue = True
        r.markerPlacedAt = 1
        r.markerPlaced = True
        r.draw()
        r.showvalue = False
        r.draw()

        r = RatingScale(self.win, labels=['a', 'b', 'c'], autoLog=False)
        r = RatingScale(self.win, tickMarks=[1,2,3], labels=None, autoLog=False)
        r = RatingScale(self.win, leftKeys=['s'], autoLog=False)
        r.markerPlaced = False
        event._onPygletKey(symbol='s', modifiers=0, emulated=True)
        r.draw()

    def test_obsolete_args(self):
        with pytest.raises(SystemExit):
            r = RatingScale(self.win, showScale=True, autoLog=False)
        with pytest.raises(SystemExit):
            r = RatingScale(self.win, ZZZshowScale=True, autoLog=False)

    def test_key_presses(self):
        # simulated keys are not being picked up in draw:

        r = copy.copy(self.r)
        r.markerPlaced = True

        r.mouseOnly = False
        event._onPygletKey(symbol='tab', modifiers=0, emulated=True)
        r.draw()

        r.respKeys = ['s']
        r.enableRespKeys = True
        event._onPygletKey(symbol='s', modifiers=0, emulated=True)
        r.draw()

        # test move left, move right:
        r = RatingScale(self.win, markerStart=3, autoLog=False)
        assert r.markerPlacedAt == 2
        event._onPygletKey(symbol='left', modifiers=0, emulated=True)
        r.draw()
        assert r.markerPlaced  # and r.markerPlacedBySubject
        #assert r.markerPlacedAt == 1
        event._onPygletKey(symbol='right', modifiers=0, emulated=True)
        r.draw()
        #assert r.markerPlacedAt == 2

        r.acceptKeys = ['s']
        r.beyondMinTime = True
        event._onPygletKey(symbol='s', modifiers=0, emulated=True)
        r.draw()

    def test_somelines(self):
        r = copy.copy(self.r)
        r.skipKeys = []
        r.mouseOnly = False
        r.enableRespKeys = True
        r.respKeys = ['s']
        r.allKeys = ['s']
        r.tickFromKeyPress = {u's': 1}
        event._onPygletKey(symbol='s', modifiers=0, emulated=True)
        r.singleClick = True
        r.beyondMinTime = True
        r.draw()

        r.leftKeys = ['s']
        r.draw()
        r.leftKeys = []
        r.rightKeys = ['s']
        r.draw()
        r.rightKeys = []

    def test_getRating_RT_history(self):
        # 1139-43
        r = copy.copy(self.r)
        r.status = FINISHED
        r.noResponse = True
        r.timedOut = True
        assert r.getRT() == r.maxTime
        r.timedOut = False
        assert r.getRT() is None
        r.noResponse = False
        assert r.getRT() == r.decisionTime

        r.reset()  # ---------------
        r.noResponse = True
        r.markerPlacedAt = 0
        r.status = FINISHED
        assert r.getRating() is None

        r.status = FINISHED + 1
        assert r.getRating() == 1

        r.precision = 1
        r.choices = ['a', 'b']
        assert r.getRating() == 'b'

        r = RatingScale(self.win, singleClick=True, autoLog=False)
        r.draw()
        core.wait(.001, 0)
        r.acceptKeys = r.allKeys = ['1']
        r.beyondMinTime = True
        event._onPygletKey(symbol='1', modifiers=0, emulated=True)
        r.draw()
        h = r.getHistory()
        assert h[0] == (None, 0)
        assert h[-1][0] == 1
        if systemtools.isVM_CI():
            assert 0.001 < h[-1][1] < 0.1  # virtual machines not usually great
        else:
            assert 0.001 < h[-1][1] < 0.03

    def test_labels_False(self):
        for anchor in [None, 'a']:
            r = RatingScale(self.win, labels=[anchor, anchor], autoLog=False)
