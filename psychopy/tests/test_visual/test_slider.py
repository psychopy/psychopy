#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

from psychopy.tests import utils
from psychopy.tests.test_visual.test_basevisual import _TestColorMixin, _TestSerializationMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin
from psychopy.visual.window import Window
from psychopy.visual.slider import Slider
from psychopy.visual.elementarray import ElementArrayStim
from psychopy.visual.shape import ShapeStim
from psychopy.visual.rect import Rect
from psychopy import constants
from numpy import array_equal
import random


class Test_Slider(_TestColorMixin, _TestBoilerplateMixin, _TestSerializationMixin):
    def setup_class(self):

        # Make a Window
        self.win = Window([128,128], pos=[50,50], monitor="testMonitor", allowGUI=False,
                          autoLog=False)
        
        # Create a Slider
        self.obj = Slider(self.win, units="height", size=(1, 0.1), pos=(0, 0.5), style='radio')

        # Set the Marker position to 0 
        self.obj.markerPos = 0

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
        # Delete created object
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

            # Filename to a png file with the tag for this case
            filename = f"test_slider_horiz_{case['tag']}.png"

            # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)

            # Compare the created slider to a screenshot of what we expect to see tests/data folder for screenshots
            utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win, crit=10)
            self.win.flip()

    def test_reset(self):
        # Test reset function of the slider
        s = Slider(self.win, size=(1, 0.1))

        # Set up the slider with some default vals
        s.markerPos = 1
        s.history = [1]
        s.rating = 1
        s.rt = 1
        s.status = constants.STARTED

        # Call the reset function
        s.reset()
        assert s.markerPos == None
        assert s.history == []
        assert s.rating == None
        assert s.rt == None
        assert s.status == constants.NOT_STARTED

    def test_elements(self):
        # Test slider elements

        # Create the slider (s)
        s = Slider(self.win, size=(1, 0.1))

        assert type(s.line) == type(Rect(self.win)) # Check the line is a rectangle
        assert type(s.tickLines) == type(ElementArrayStim(self.win)) # Check the ticklines are element array stim
        assert type(s.marker) == type(ShapeStim(self.win)) # Check marker is ShapeStim 
        assert type(s.validArea) == type(Rect(self.win))
        
    def test_pos(self):
        # Test slider position 

        # Create the slider (s)
        s = Slider(self.win, size=(1, 0.1))

        # List of positions to test
        positions = [(.05, .05),(0.2, .2)]

        # For each position in list
        for newPos in positions:
            s.pos = newPos
            assert array_equal(s.pos, newPos) # Check that the position updates

    def test_triangle_marker(self):
        # Test with triangular marker 

        # Test all combinations of horiz and flip
        cases = [
            {"horiz": True, "flip": True},
            {"horiz": True, "flip": False},
            {"horiz": False, "flip": True},
            {"horiz": False, "flip": False},
        ]
        # Create slider
        s = Slider(self.win, units="height", pos=(0, 0), ticks=(0, 1, 2), styleTweaks=["triangleMarker"])
        s.rating = 1
        # Try each case
        for case in cases:
            # Make horizontal/vertical
            if case['horiz']:
                s.size = (1, 0.1)
            else:
                s.size = (0.1, 1)
            # Flip or not
            s.flip = case['flip']
            # Compare
            s.draw()
            filename = "test_slider_triangle_horiz_%(horiz)s_flip_%(flip)s.png" % case
            #self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)

            # Compare the created slider to a screenshot of what we expect to see tests/data folder for screenshots
            utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win)
            self.win.flip()
        
    def test_ratingToPos(self):
        # Test translationg between rating and marker positions

        # Create the slider (s)
        s = Slider(self.win, size=(1, 0.1), )

        assert s._ratingToPos(3)[0] == 0 # check a rating of 3 is central position
        assert s._ratingToPos(1)[0] == -.5 # check a rating of 1 is furthest left
        assert s._ratingToPos(5)[0] == .5 # check a rating of 5 is furthest right

    def test_posToRatingToPos(self):
        # Test translationg between marker position and ratings

        # Create the slider (s)
        s = Slider(self.win, size=(1, 0.1), )

        assert s._posToRating((0, 0)) == 3 # check central position is a rating of 3
        assert s._posToRating((-.5, 0)) == 1 # check furthest left is a rating of 1
        assert s._posToRating((.5, 0)) == 5 # check furthest right is a rating of 5

    def test_tick_and_label_locs(self):
        # Test ticks an label locations

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

            # Compare the created slider to a screenshot of what we expect to see tests/data folder for screenshots
            utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win)
            self.win.flip()

    def test_granularity(self):
        # Test granularity of Slider works as expected

        # Create the slider (s)
        s = Slider(self.win, size=(1, 0.1), granularity=1)

        # Set minimum and maximum ratings
        minRating, maxRating = 1, 5

        assert s.granularity == 1 # Check granulariy is 1
        assert s._granularRating(1) == minRating
        assert s._granularRating(5) == maxRating
        assert s._granularRating(0) == minRating
        assert s._granularRating(6) == maxRating

    def test_rating(self):
        # Test rating sets and updates as expected 

        # Create the slider (s)
        s = Slider(self.win, size=(1, 0.1))

        # Set minimum and maximum ratings
        minRating, maxRating = 1, 5

        s.rating = 1 # Set to minimum rating
        assert s.rating == minRating # Check it is minimum rating
        s.rating = 5 # Set to maximum rating
        assert s.rating == maxRating # Check it is maximum rating
        s.rating = 0 # Set below minimum rating
        assert s.rating == minRating # Check it is minimum rating
        s.rating = 6 # Set above maximum rating
        assert s.rating == maxRating # Check it is maximum rating

    def test_markerPos(self):
        # Test marker value sets and updates as expected 

        # Create the slider (s)
        s = Slider(self.win, size=(1, 0.1))

        s._updateMarkerPos = False

        # Set minimum and maximum positions
        minPos, maxPos = 1, 5

        assert s._updateMarkerPos != True
        s.markerPos = 1 # Set to minimum position
        assert s.markerPos == minPos # Check it is minimum position
        s.markerPos = 5 # Set to maximum position
        assert s.markerPos == maxPos # Check it is maximum position
        s.markerPos = 0 # Set below minimum position
        assert s.markerPos == minPos# Check it is minimum position
        s.markerPos = 6 # Set above maximum position
        assert s.markerPos == maxPos # Check it is maximum position
        assert s._updateMarkerPos == True

    def test_recordRating(self):
        # Test recording of rating values 

        # Create the slider (s)
        s = Slider(self.win, size=(1, 0.1))

        # Provide a minRating and a maxRating 
        minRating, maxRating = 1, 5

        
        counter = 0
        for rates in range(0,7):
            s.recordRating(rates, random.random()) # "rates" will be rating random.random() generates random response time val
            counter +=1

        # Get a list of ratings and response times for all ratings made
        ratings = [rating[0] for rating in s.history]
        RT = [rt[1] for rt in s.history]

        assert len(s.history) == counter 
        assert len(ratings) == counter # Check the number of ratings is equal to expected
        assert min(ratings) == minRating # Check ratings never go below minimum cap
        assert max(ratings) == maxRating # Check ratings never go above maximum cap
        assert len(RT) == counter # Check the number of rts is equal to expected
        assert max(RT) <= 1 # check the max RT is less than or equal to 1
        assert min(RT) >= 0 # check the min RT is greater than or equal to 1

    def test_getRating(self):
        # Test fetching of the rating data e.g. that minRating and maxRating caps the ratings as expected

        # Create the slider (s)
        s = Slider(self.win, size=(1, 0.1))

        # Provide a minRating and a maxRating 
        minRating, maxRating = 1, 5

        s.rating = 1 # Set a rating value that is the minimum rating
        assert s.getRating() == minRating # Check getRating() is the minRating - expect return True
        s.rating = 5 # Set a rating value that is the maximum rating
        assert s.getRating() == maxRating # Check getRating() is the maxRating - expect return True
        s.rating = 0 # Set a rating value that is below the minimum rating
        assert s.getRating() == minRating # Check getRating() is the minRating - expect return True
        s.rating = 6 # Set a rating value that is above the maximum rating
        assert s.getRating() == maxRating # Check getRating() is the maxRating - expect return True

    def test_getRT(self):
        # Test fetching of the response time data 

        # Create the slider (s)
        s = Slider(self.win, size=(1, 0.1))

        # Provide example response time
        testRT = .89

        # Give the response time to the Slider
        s.recordRating(2, testRT)
        assert s.history[-1][1] == s.getRT()
        assert type(s.getRT()) == float # Check thet getRT() returns a float (as expected)
        assert s.getRT() == testRT # Check that getRT() returns the provided testRT
