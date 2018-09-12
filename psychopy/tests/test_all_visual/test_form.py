#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import pytest
from psychopy.visual.window import Window
from psychopy.visual.form import Form
from psychopy.visual.text import TextStim
from psychopy.visual.slider import Slider
from numpy import isclose


class Test_Form(object):
    """Test suite for Form component"""

    def setup_class(self):
        self.questions = []
        self.win = Window(units='height', allowStencil=True)
        # create some questions
        self.genderItem = {"qText": "What is your gender?",
                      "qWidth": 0.7,
                      "aType": "choice",
                      "aWidth": 0.3,
                      "aOptions": ["Male", "Female", "Other"],
                      "aLayout": 'vert'}
        self.questions.append(self.genderItem)
        # then a set of ratings
        items = ["running", "cake"]
        for item in items:
            entry = {"qText": "How much do you like {}".format(item),
                     "qWidth": 0.7,
                     "aType": "rating",
                     "aWidth": 0.3,
                     "aOptions": ["Lots", "Not a lot"],
                     "aLayout": 'horiz'}
            self.questions.append(entry)
        self.survey = Form(self.win, items=self.questions, size=(1.0, 0.3), pos=(0.0, 0.0))

    def test_set_questions(self):
        survey = Form(self.win, items=[], size=(1.0, 0.3), pos=(0.0, 0.0))
        textStim, qHeight, qWidth = survey._setQuestion(self.genderItem)

        assert type(textStim) == TextStim
        assert type(qHeight) == float
        assert type(qWidth) == float

    def test_set_response(self):
        survey = Form(self.win, items=[], size=(1.0, 0.3), pos=(0.0, 0.0))
        textStim, qHeight, qWidth = survey._setQuestion(self.genderItem)
        sliderStim, aHeight = survey._setResponse(self.genderItem, textStim)

        assert type(sliderStim) == Slider
        assert type(aHeight) == float

    def test_questionHeight(self):
        for item in self.survey._items['question']:
            assert self.survey.getQuestionHeight(item) == item.boundingBox[1] / float(self.win.size[1] / 2)

    def test_questionWidth(self):
        for item in self.survey._items['question']:
            assert self.survey.getQuestionWidth(item) == item.boundingBox[0] / float(self.win.size[0] / 2)

    def test_respHeight(self):
        for item in self.survey.items:
            if item['aLayout'] == 'vert':
                assert self.survey.getRespHeight(item) == (len(item['aOptions']) * self.survey.textHeight)
            elif item['aLayout'] == 'horiz':
                assert self.survey.getRespHeight(item) == self.survey.textHeight

    def test_form_size(self):
        assert self.survey.size[0] == (1.0, 0.3)[0]  # width
        assert self.survey.size[1] == (1.0, 0.3)[1]  # height

    def test_aperture_size(self):
        assert self.survey.aperture.size[0] == self.survey.size[0]
        assert self.survey.aperture.size[1] == self.survey.size[1]

    def test_border_limits(self):
        survey = self.survey
        assert survey.leftEdge == survey.pos[0] - survey.size[0]/2.0
        assert survey.rightEdge == survey.pos[0] + survey.size[0]/2.0
        assert survey.topEdge == survey.pos[1] + survey.size[1]/2.0

    def test_text_height(self):
        assert self.survey.textHeight == 0.03

    def test_label_height(self):
        assert self.survey.labelHeight == 0.02

    def test_item_padding(self):
        assert self.survey.itemPadding == 0.05

    def test_form_units(self):
        assert self.survey.units == 'height'

    def test_virtual_height(self):
        assert isclose(self.survey.virtualHeight,
                       (self.survey._baseYpositions[-1]-self.survey.itemPadding),
                       atol=0.02)  # TODO: liberal atol, needs tightening up

    def test_baseYpositions(self):
        survey = Form(self.win, items=self.questions, size=(1.0, 0.3), pos=(0.0, 0.0))
        testPositions = []
        survey.virtualHeight = 0
        for item in survey.items:
            question, qHeight, qWidth = survey._setQuestion(item)
            response, aHeight, = survey._setResponse(item, question)
            testPositions.append(survey.virtualHeight
                                 - max(aHeight, qHeight)
                                 + (aHeight / 2)
                                 - survey.textHeight)
            survey.virtualHeight -= max(aHeight, qHeight) + survey.itemPadding

        for idx, pos in enumerate(survey._baseYpositions):
            assert testPositions[idx] == pos

    def test_scroll_offset(self):
        for idx, positions in enumerate([1, 0]):  # 1 is start position
            self.survey.scrollbar.markerPos = positions
            posZeroOffset = (self.survey.size[1]
                             - self.survey.itemPadding
                             + min(self.survey._baseYpositions))
            assert self.survey._getScrollOffet() == [0., posZeroOffset][idx]

    def test_screen_status(self):
        assert self.survey._inRange(self.survey._items['question'][0])
        with pytest.raises(AssertionError):
            assert self.survey._inRange(self.survey._items['question'][2])

    def teardown_class(self):
        self.win.close()

if __name__ == "__main__":
    test = Test_Form()
    test.setup_class()
    # Add tests
    test.teardown_class()
