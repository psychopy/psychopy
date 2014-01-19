
from psychopy.visual import RatingScale, Window, shape
from psychopy import event, core
from psychopy.constants import *
from psychopy.tests import utils
import pytest

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
        #self.temp_dir = mkdtemp(prefix='psychopy-tests-test_window')
        self.win = Window([128,128], pos=[50,50], allowGUI=False)
        self.winpix = Window([128,128], pos=[50,50], allowGUI=False, units='pix')

    def teardown_class(self):
        pass  #shutil.rmtree(self.temp_dir)

    def test_init_scales(self):
        # ideally: give default, non-default, and bad values for all params

        # defaults: ---------
        r = RatingScale(self.win)
        assert (r.low, r.high, r.precision) == (1, 7, 1)
        assert (r.markerStyle, r.markerStart, r.markerPlaced) == ('triangle', None, False)

        # non-defaults and some bad: ---------
        r = RatingScale(self.win, low=-10., high=10.)
        assert (r.low, r.high) == (-10, 10)
        assert (type(r.low), type(r.high)) == (int, int)
        r = RatingScale(self.win, low='a', high='s')  # bad vals
        assert (r.low, r.high) == (1, 2)
        r = RatingScale(self.win, low=10, high=2)
        assert r.high == r.low + 1 == 11
        assert r.precision == 100

        ch = ['a', 'b']
        r = RatingScale(self.win, choices=ch, precision=10)
        assert r.precision == 1  # because choices
        assert r.respKeys == map(str, range(len(ch)))
        r = RatingScale(self.win, choices=['a'])

        r = RatingScale(self.win, tickMarks=[1,2,3], labels=['a','b'])

        for i in [-1, 0.3, 1.2, 9, 12, 100, 1000]:
            r = RatingScale(self.win, precision=i)
            assert r.precision in [1, 10, 100]
        r = RatingScale(self.win, textSize=3, textColor=0.3)

        r = RatingScale(self.win, textFont=utils.TESTS_FONT)
        assert r.accept.fontname == r.scaleDescription.fontname == utils.TESTS_FONT

        r = RatingScale(self.win, showValue=False, showAccept=False, acceptKeys=[])
        r = RatingScale(self.win, showAccept=False, mouseOnly=True, singleClick=False)
        assert r.mouseOnly == False

        r = RatingScale(self.win, acceptKeys='a')
        r = RatingScale(self.win, acceptKeys=['a','b'])
        r = RatingScale(self.win, acceptPreText='a', acceptText='a', acceptSize=2.1)

        r = RatingScale(self.win, leftKeys=['a'], rightKeys=['a'])
        assert r.respKeys == map(str, range(1,8))
        r = RatingScale(self.win, respKeys=['a'], acceptKeys=['a'])
        r = RatingScale(self.win, acceptKeys=['1'])

        r = RatingScale(self.win, tickHeight=-1)

        r = RatingScale(self.win, markerStart=3, tickHeight=False)
        r = RatingScale(self.win, markerStart='a', choices=['a','b'])
        assert r.choices == ['a', 'b']
        r = RatingScale(self.win, markerColor='dark red', lineColor='Black')
        assert r.marker.fillColor == r.marker.lineColor == 'darkred'
        assert r.line.lineColor == 'Black'
        r = RatingScale(self.win, marker='glow', markerExpansion=0)
        r.markerPlaced = True
        r.draw()
        r.markerExpansion = 10
        r.draw()

        r = RatingScale(self.win, skipKeys=None, mouseOnly=True, singleClick=True)
        r = RatingScale(self.win, pos=(0,.5), skipKeys='space')
        r = RatingScale(self.winpix, pos=[1])
        r = RatingScale(self.winpix, pos=['a','x'])
        assert r.pos == [0.0, -50.0 / r.win.size[1]]
        x, y = -3, 17
        r = RatingScale(self.winpix, pos=(x, y), size=.2, stretch=2)
        assert r.offsetHoriz == 2. * x / r.win.size[0]
        assert r.offsetVert == 2. * y / r.win.size[1]
        assert r.stretch == 2
        assert r.size == 0.2 * 0.6  # internal rescaling by 0.6

        r = RatingScale(self.win, stretch='foo', size='foo')
        assert r.stretch == 1
        assert r.size == 0.6
        r = RatingScale(self.win, size=5)
        assert r.size == 3

        r = RatingScale(self.win, minTime=0.001, maxTime=1)
        assert r.minTime == 0.001 and r.maxTime == 1
        r = RatingScale(self.win, minTime='x', maxTime='s', name='name', autoLog=False)
        assert r.minTime == 1.0 and r.maxTime == 0.
        assert r.name == 'name' and r.autoLog == False

    def test_markers(self):
        for marker in ['triangle', 'glow', 'slider', 'circle', 'hover', None]:
            r = RatingScale(self.win, choices=['0', '1'], marker=marker)
            r.draw()
        with pytest.raises(SystemExit):
            r = RatingScale(self.win, marker='hover')  # needs choices

        class good_customMarker(object):
            def __init__(self):
                self.color = None
                self.fillColor = 1
            def draw(self): pass
            def setPos(self, *args, **kwargs): pass
        cm = good_customMarker()
        r = RatingScale(self.win, marker=cm)
        r.noResponse = False
        r.markerPosFixed = False
        r.draw()

        # then delete parts to see how its handled / get coverage
        del cm.color
        r = RatingScale(self.win, marker=cm)
        assert hasattr(r.marker, 'color')
        del cm.fillColor
        r = RatingScale(self.win, marker=cm)

        class bad_customMarker(object):
            def __init__(self): pass
        r = RatingScale(self.win, marker=bad_customMarker())
        assert type(r.marker) == shape.ShapeStim

    def test_ratingscale_misc(self):
        r = RatingScale(self.win, markerStart=1)
        assert r._getMarkerFromPos(0.2) == 5
        assert r._getMarkerFromTick(0) == 0
        r.setMarkerPos(2)
        assert r.markerPlacedAt == 2
        r.setDescription()
        assert r.flipVert == False  # 'needed to test'
        r.setFlipVert(True)

        # test reset()
        r.reset()
        assert r.noResponse == True
        assert r.markerPlaced == True
        assert r.markerPlacedBySubject == False
        assert r.markerPlacedAt == r.markerStart - r.low
        assert r.firstDraw == True
        assert r.decisionTime == 0
        assert r.markerPosFixed == False
        assert r.frame == 0
        assert r.status == NOT_STARTED
        assert r.history == None

    def test_draw_conditionals(self):
        r = RatingScale(self.win)

        r.allowTimeOut = True
        r.timedOut = False
        r.maxTime = -1
        r.noResponse = False
        r.disappear = True
        r.draw()

        # miss lines: if self.myMouse.getPressed()[0]:

        r.reset() # = RatingScale(self.win)
        r.beyondMinTime = True
        r.showAccept = True
        r.noResponse = False
        r.decisionTime = 0
        r.draw()

        r = RatingScale(self.win, singleClick=True, markerStart=1, marker='glow', markerExpansion=-10)
        r.draw()

        r = RatingScale(self.win, singleClick=True, markerStart=-1)
        r.draw()

        r = RatingScale(self.win, showAccept=True, choices=['a', 'b'])
        r.showValue = True
        r.markerPlacedAt = 1
        r.markerPlaced = True
        r.draw()
        r.showvalue = False
        r.draw()

        r = RatingScale(self.win, labels=['a', 'b', 'c'])
        r = RatingScale(self.win, tickMarks=[1,2,3], labels=None)

        #r.draw()

        r = RatingScale(self.win, leftKeys=['s'])
        r.markerPlaced = False
        event._onPygletKey(symbol='s', modifiers=None, emulated=True)
        r.draw()

    def test_obsolete_args(self):
        with pytest.raises(SystemExit):
            r = RatingScale(self.win, showScale=True)
        with pytest.raises(SystemExit):
            r = RatingScale(self.win, ZZZshowScale=True)

    def test_key_presses(self):
        r = RatingScale(self.win)
        r.markerPlaced = True
        r.allKeys = ['s']
        r.markerPlacedAt = 2

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

        r.reset() # = RatingScale(self.win)
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

    def test_somelines(self):
        r = RatingScale(self.win)
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

    def test_getRating_RT_history(self):
        # 1139-43
        r = RatingScale(self.win)
        r.status = FINISHED
        r.noResponse = True
        r.timedOut = True
        assert r.getRT() == r.maxTime
        r.timedOut = False
        assert r.getRT() == None
        r.noResponse = False
        assert r.getRT() == r.decisionTime

        r.reset()  # ---------------
        r.noResponse = True
        r.markerPlacedAt = 0
        r.status = FINISHED
        assert r.getRating() == None

        r.status = FINISHED + 1
        assert r.getRating() == 1

        r.precision = 1
        r.choices = ['a', 'b']
        assert r.getRating() == 'b'

        r = RatingScale(self.win, singleClick=True)
        r.draw()
        core.wait(.001, 0)
        r.acceptKeys = r.allKeys = ['1']
        r.beyondMinTime = True
        event._onPygletKey(symbol='1', modifiers=None, emulated=True)
        r.draw()
        h = r.getHistory()
        assert h[0] == (None, 0)
        assert h[-1][0] == 1
        assert 0.001 < h[-1][1] < 0.03

    def test_labels_False(self):
        for anchor in [None, 'a']:
            r = RatingScale(self.win, labels=[anchor, anchor])
