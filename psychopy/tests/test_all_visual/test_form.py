#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import os
import pytest
from pandas import DataFrame
from psychopy.visual.window import Window
from psychopy.visual.form import Form
from psychopy.visual.text import TextStim
from psychopy.visual.slider import Slider
from psychopy import constants
import shutil
from tempfile import mkdtemp


class Test_Form(object):
    """Test suite for Form component"""

    def setup_class(self):
        # Create temp files for storing items
        self.temp_dir = mkdtemp()
        self.fileName_xlsx = os.path.join(self.temp_dir, 'items.xlsx')
        self.fileName_csv = os.path.join(self.temp_dir, 'items.csv')

        # create some questions
        self.questions = []
        self.genderItem = {"questionText": "What is your gender?",
                           "questionWidth": 0.7,
                           "type": "radio",
                           "responseWidth": 0.3,
                           "options": "Male, Female, Other",
                           "layout": 'vert',
                           "index": 0,
                           "questionColor": "white",
                           "responseColor": "white"
                           }
        self.questions.append(self.genderItem)
        # then a set of ratings
        items = ["running", "cake", "programming"]
        for idx, item in enumerate(items):
            entry = {"questionText": "How much you like {}".format(item),
                     "questionWidth": 0.7,
                     "type": "rating",
                     "responseWidth": 0.3,
                     "options":"Lots, some, Not a lot, Longest Option",
                     "layout": 'horiz',
                     "index": idx+1,
                     "questionColor": "white",
                     "responseColor": "white"
                     }
            self.questions.append(entry)

        self.win = Window(units='height', allowStencil=True, autoLog=False)
        self.survey = Form(self.win, items=self.questions, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

        # Create datafiles
        df = DataFrame(self.questions)
        df.to_excel(self.fileName_xlsx, index=False)
        df.to_csv(self.fileName_csv, index=False)

    def test_importItems(self):
        wrongFields = [{"a": "What is your gender?",
                      "b": 0.7,
                      "c": "radio",
                      "d": 0.3,
                      "e": "Male, Female, Other",
                      "f": 'vert',
                      "g": "white",
                      "h": "white"
                        }]

        wrongOptions = [{"questionText": "What is your gender?",
                      "questionWidth": 0.7,
                      "type": "radio",
                      "responseWidth": 0.3,
                      "options": "Other",
                      "layout": 'vert',
                      "index": 0,
                      "questionColor": "white",
                      "responseColor": "white"}]

        reducedHeaders = [{"questionText": "What is your gender?"}]

        # Check options for list of dicts
        with pytest.raises(ValueError):
            self.survey = Form(self.win, items=wrongOptions, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

        # Check default values are applied
        self.survey = Form(self.win, items=reducedHeaders, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

        # Check csv
        self.survey = Form(self.win, items=self.fileName_csv,
                           size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        # Check Excel
        self.survey = Form(self.win, items=self.fileName_xlsx,
                           size=(1.0, 0.3), pos=(0.0, 0.0), randomize=False, autoLog=False)

    def test_randomize_items(self):
        assert self.questions == self.survey.items
        self.survey.randomize = True
        assert self.questions != self.survey.randomizeItems(self.questions)

    def test_set_scroll_speed(self):
        items = 2
        for multipliers in [1,2,3,4]:
            assert self.survey.setScrollSpeed([0] * items, multipliers) == items * multipliers
            assert self.survey.setScrollSpeed([0] * items, multipliers) == items * multipliers
            assert self.survey.setScrollSpeed([0] * items, multipliers) == items * multipliers

    def test_question_text_wrap(self):
        for size in [.2, .3, .4]:
            assert self.survey._questionTextWrap(size) == size * self.survey.size[0] - (self.survey.itemPadding * 2)

    def test_response_text_wrap(self):
        options = ['a', 'b', 'c']
        for size in [.2, .3, .4]:
            item = {"responseWidth": size, "options": options}
            assert self.survey._responseTextWrap(item) == size * self.survey.size[0] / len(options)

    def test_set_questions(self):
        survey = Form(self.win, items=[self.genderItem], size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        textStim, questionHeight, questionWidth = survey._setQuestion(self.genderItem)

        assert type(textStim) == TextStim
        assert type(questionHeight) == float
        assert type(questionWidth) == float

    def test_set_response(self):
        survey = Form(self.win, items=[self.genderItem], size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        textStim, questionHeight, questionWidth = survey._setQuestion(self.genderItem)
        sliderStim, respHeight = survey._setResponse(self.genderItem, textStim)

        assert type(sliderStim) == Slider
        assert type(respHeight) == float

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
        assert self.survey.textHeight == 0.02

    def test_item_padding(self):
        assert self.survey.itemPadding == 0.05

    def test_form_units(self):
        assert self.survey.units == 'height'

    def test_scroll_offset(self):
        for idx, positions in enumerate([1, 0]):  # 1 is start position
            self.survey.scrollbar.markerPos = positions
            posZeroOffset = (self.survey.size[1]
                             - self.survey.itemPadding
                             + min(self.survey._baseYpositions))
            assert self.survey._getScrollOffset() == [0., posZeroOffset][idx]

    def test_screen_status(self):
        assert self.survey._inRange(self.survey.formElements['question'][0])
        if constants.PY3:
            with pytest.raises(AssertionError):
                assert self.survey._inRange(self.survey.formElements['question'][3])

    def test_get_data(self):
        self.survey = Form(self.win, items=self.questions, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        data = self.survey.getData()
        assert set(data['questions']) == {'What is your gender?',
                                          'How much you like running',
                                          'How much you like cake',
                                          'How much you like programming',}
        assert set(data['ratings']) == {None}
        assert set(data['rt']) == {None}
        assert set(data['itemIndex']) == {0, 1, 2, 3}

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)
        self.win.close()


if __name__ == "__main__":
    test = Test_Form()
    test.setup_class()
    test.teardown_class()
