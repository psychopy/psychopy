#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

from psychopy.tests import utils
from psychopy.tests.test_visual.test_basevisual import _TestColorMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin
from psychopy.visual.window import Window
from psychopy.visual.slider import Slider
from psychopy.visual.elementarray import ElementArrayStim
from psychopy.visual.shape import ShapeStim
from psychopy.visual.rect import Rect
from psychopy import constants
from numpy import array_equal
import random


class Test_Slider(_TestColorMixin, _TestBoilerplateMixin):
    def setup_class(self):
        self.win = Window([128,128], pos=[50,50], monitor="testMonitor", allowGUI=False,
                          autoLog=False)
        self.obj = Slider(self.win, units="height", size=(1, 0.1), pos=(0, 0.5), style='radio')
        self.obj.markerPos = 1

        # Pixel which is the border color
        self.borderPoint = (0, 127)
        self.borderUsed = True
        # Pixel which is the fill color
        self.fillPoint = (0, 0)
        self.fillUsed = True
        # Pixel which is the fore color
        self.forePoint = (0, 0)
        self.foreUsed = False

    def teardown_class(self):
        self.win.close()

    def test_horiz(self):
        # Define cases
        exemplars = [
            {'size': (1, 0.2), 'ori': 0, 'horiz': True, 'tag': 'horiz'},  # Wide slider, no rotation
            {'size': (0.2, 1), 'ori': 0, 'horiz': False, 'tag': 'vert'},  # Tall slider, no rotation
            {'size': (1, 0.2), 'ori': 90, 'horiz': False, 'tag': 'vert'},  # Wide slider, 90deg rotation
            {'size': (0.2, 1), 'ori': 90, 'horiz': True, 'tag': 'horiz'},  # Tall slider, 90deg rotation
        ]
        tykes = [
            {'size': (1, 0.2), 'ori': 25, 'horiz': True, 'tag': 'accute_horiz'},  # Wide slider, accute rotation
            {'size': (0.2, 1), 'ori': 25, 'horiz': False, 'tag': 'accute_vert'},  # Tall slider, accute rotation
            {'size': (1, 0.2), 'ori': 115, 'horiz': False, 'tag': 'obtuse_horiz'},  # Wide slider, obtuse rotation
            {'size': (0.2, 1), 'ori': 115, 'horiz': True, 'tag': 'obtuse_vert'},  # Tall slider, obtuse rotation
        ]
        # Try each case
        self.win.flip()
        for case in exemplars + tykes:
            # Make sure horiz is set as intended
            obj = Slider(self.win,
                         labels=["a", "b", "c", "d"], ticks=[1, 2, 3, 4],
                         labelHeight=0.2, labelColor='red',
                         size=case['size'], ori=case['ori'])
            assert obj.horiz == case['horiz']
            # Make sure slider looks as intended
            obj.draw()
            filename = f"test_slider_horiz_{case['tag']}.png"
            # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
            utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win, crit=10)
            self.win.flip()

    def test_reset(self):
        s = Slider(self.win, size=(1, 0.1))
        s.markerPos = 1
        s.history = [1]
        s.rating = 1
        s.rt = 1
        s.status = constants.STARTED
        s.reset()
        assert s.markerPos == None
        assert s.history == []
        assert s.rating == None
        assert s.rt == None
        assert s.status == constants.NOT_STARTED

    def test_elements(self):
        s = Slider(self.win, size=(1, 0.1))
        assert type(s.line) == type(Rect(self.win))
        assert type(s.tickLines) == type(ElementArrayStim(self.win))
        assert type(s.marker) == type(ShapeStim(self.win))
        assert type(s.validArea) == type(Rect(self.win))
        
    def test_pos(self):
        s = Slider(self.win, size=(1, 0.1))
        positions = [(.05, .05),(0.2, .2)]
        for newPos in positions:
            s.pos = newPos
            assert array_equal(s.pos, newPos)
        
    def test_ratingToPos(self):
        s = Slider(self.win, size=(1, 0.1), )
        assert s._ratingToPos(3)[0] == 0
        assert s._ratingToPos(1)[0] == -.5
        assert s._ratingToPos(5)[0] == .5

    def test_posToRatingToPos(self):
        s = Slider(self.win, size=(1, 0.1), )
        assert s._posToRating((0, 0)) == 3
        assert s._posToRating((-.5, 0)) == 1
        assert s._posToRating((.5, 0)) == 5

    def test_tick_and_label_locs(self):
        exemplars = [
            {'ticks': [1, 2, 3, 4, 5], 'labels': ["a", "b", "c", "d", "e"], 'tag': "simple"},
            {'ticks': [1, 2, 3, 9, 10], 'labels': ["a", "b", "c", "d", "e"], 'tag': "clustered"},
            {'ticks': [1, 2, 3, 4, 5], 'labels': ["", "b", "c", "d", ""], 'tag': "blanks"},
            {'ticks': None, 'labels': ["a", "b", "c", "d", "e"], 'tag': "noticks"},
            {'ticks': [1, 2, 3, 4, 5], 'labels': None, 'tag': "nolabels"},
        ]
        tykes = [
            {'ticks': [1, 2, 3], 'labels': ["a", "b", "c", "d", "e"], 'tag': "morelabels"},
            {'ticks': [1, 2, 3, 4, 5], 'labels': ["a", "b", "c"], 'tag': "moreticks"},
            {'ticks': [1, 9, 10], 'labels': ["a", "b", "c", "d", "e"], 'tag': "morelabelsclustered"},
            {'ticks': [1, 7, 8, 9, 10], 'labels': ["a", "b", "c", "d"], 'tag': "moreticksclustered"},
        ]
        # Test all cases
        self.win.flip()
        for case in exemplars + tykes:
            # Make vertical slider
            vert = Slider(self.win, size=(0.1, 0.5), pos=(-0.25, 0), units="height",
                          labels=case['labels'], ticks=case['ticks'])
            vert.draw()
            # Make horizontal slider
            horiz = Slider(self.win, size=(0.5, 0.1), pos=(0.2, 0), units="height",
                           labels=case['labels'], ticks=case['ticks'])
            horiz.draw()
            # Compare screenshot
            filename = "test_slider_ticklabelloc_%(tag)s.png" % case
            #self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
            utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win)
            self.win.flip()

    def test_granularity(self):
        s = Slider(self.win, size=(1, 0.1), granularity=1)
        minRating, maxRating = 1, 5

        assert s.granularity == 1
        assert s._granularRating(1) == minRating
        assert s._granularRating(5) == maxRating
        assert s._granularRating(0) == minRating
        assert s._granularRating(6) == maxRating

    def test_rating(self):
        s = Slider(self.win, size=(1, 0.1))
        minRating, maxRating = 1, 5

        s.rating = 1
        assert s.rating == minRating
        s.rating = 5
        assert s.rating == maxRating
        s.rating = 0
        assert s.rating == minRating
        s.rating = 6
        assert s.rating == maxRating

    def test_markerPos(self):
        s = Slider(self.win, size=(1, 0.1))
        s._updateMarkerPos = False
        minPos, maxPos = 1, 5

        assert s._updateMarkerPos != True
        s.markerPos = 1
        assert s.markerPos == minPos
        s.markerPos = 5
        assert s.markerPos == maxPos
        s.markerPos = 0
        assert s.markerPos == minPos
        s.markerPos = 6
        assert s.markerPos == maxPos
        assert s._updateMarkerPos == True

    def test_recordRating(self):
        s = Slider(self.win, size=(1, 0.1))
        minRating, maxRating = 1, 5

        counter = 0
        for rates in range(0,7):
            s.recordRating(rates, random.random())
            counter +=1

        ratings = [rating[0] for rating in s.history]
        RT = [rt[1] for rt in s.history]

        assert len(s.history) == counter
        assert len(ratings) == counter
        assert min(ratings) == minRating
        assert max(ratings) == maxRating
        assert len(RT) == counter
        assert max(RT) <= 1
        assert min(RT) >= 0

    def test_getRating(self):
        s = Slider(self.win, size=(1, 0.1))
        minRating, maxRating = 1, 5
        s.rating = 1
        assert s.getRating() == minRating
        s.rating = 5
        assert s.getRating() == maxRating
        s.rating = 0
        assert s.getRating() == minRating
        s.rating = 6
        assert s.getRating() == maxRating

    def test_getRT(self):
        s = Slider(self.win, size=(1, 0.1))
        testRT = .89
        s.recordRating(2, testRT)
        assert s.history[-1][1] == s.getRT()
        assert type(s.getRT()) == float
        assert s.getRT() == testRT
