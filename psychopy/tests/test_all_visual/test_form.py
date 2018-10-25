#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import pytest
from pandas import DataFrame
from psychopy.visual.window import Window
from psychopy.visual.form import Form
from psychopy.visual.text import TextStim
from psychopy.visual.slider import Slider
from numpy import isclose


class Test_Form(object):
    """Test suite for Form component"""

    def setup_class(self):
        self.questions = []
        self.win = Window(units='height', allowStencil=True, autoLog=False)
        # create some questions
        self.genderItem = {"questionText": "What is your gender?",
                      "questionWidth": 0.7,
                      "type": "choice",
                      "responseWidth": 0.3,
                      "options": ["Male", "Female", "Other"],
                      "layout": 'vert'}
        self.questions.append(self.genderItem)
        # then a set of ratings
        items = ["running", "cake", "running", "cake", "running", "cake", "running", "cake"]
        for item in items:
            entry = {"questionText": "How much you like {}".format(item),
                     "questionWidth": 0.7,
                     "type": "rating",
                     "responseWidth": 0.3,
                     "options": ["Lots", "some", "Not a lot", "Longest Option"],
                     "layout": 'horiz'}
            self.questions.append(entry)
        self.survey = Form(self.win, items=self.questions, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

    @pytest.fixture(scope="session")
    def create_file(self, tmpdir_factory, type, data, dirName):
        if type == 'csv':
            csvFile = DataFrame(data)
            formData = tmpdir_factory.mkdir(dirName).join("formData.csv")
            csvFile.to_csv(formData, index=False)
            return str(formData)
        elif type == 'xlsx':
            xlsxFile = DataFrame(data)
            formData = tmpdir_factory.mkdir(dirName).join("formData.xlsx")
            xlsxFile.to_excel(formData, index=False)
            return str(formData)
        elif type == 'txt':
            txtFile = DataFrame(data)
            formData = tmpdir_factory.mkdir(dirName).join("formData.txt")
            txtFile.to_csv(formData, index=False)
            return str(formData)

    def test_importItems(self, tmpdir):
        wrongFields = [{"a": "What is your gender?",
                      "b": 0.7,
                      "c": "choice",
                      "d": 0.3,
                      "e": ["Male", "Female", "Other"],
                      "f": 'vert'}]

        wrongOptions = {"questionText": "What is your gender?",
                      "questionWidth": 0.7,
                      "type": "choice",
                      "responseWidth": 0.3,
                      "options": ["Other"],
                      "layout": 'vert'}

        # Check wrong field error
        with pytest.raises(NameError):
            self.survey = Form(self.win, items=wrongFields, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

        # Check options for list of dicts
        with pytest.raises(ValueError):
            self.survey = Form(self.win, items=[wrongOptions], size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

        # Check options for single dict entry
        with pytest.raises(ValueError):
            self.survey = Form(self.win, items=wrongOptions, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

        # Check output of importItems
        self.survey = Form(self.win, items=self.questions, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        assert self.survey.importItems(self.questions) == self.questions

        # Check csv
        self.survey = Form(self.win, items=self.create_file(tmpdir, 'csv', self.questions, 'checkCSV'),
                           size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

        # Check Excel
        self.survey = Form(self.win, items=self.create_file(tmpdir, 'xlsx', self.questions, 'checkExcel'),
                           size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

        # Check filename error
        with pytest.raises(OSError):
            self.survey = Form(self.win, items='doesNotExist',
                               size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        # Check filetype error
        with pytest.raises(TypeError):
            self.survey = Form(self.win, items=self.create_file(tmpdir, 'txt', self.questions, 'fileType'),
                               size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

        # Check options for csv (same as excel)
        with pytest.raises(ValueError):
            self.survey = Form(self.win, items=self.create_file(tmpdir, 'csv', [wrongOptions], 'checkOptions'),
                               size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

    def test_set_questions(self):
        survey = Form(self.win, items=[], size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        textStim, questionHeight, questionWidth = survey._setQuestion(self.genderItem)

        assert type(textStim) == TextStim
        assert type(questionHeight) == float
        assert type(questionWidth) == float

    def test_set_response(self):
        survey = Form(self.win, items=[], size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        textStim, questionHeight, questionWidth = survey._setQuestion(self.genderItem)
        sliderStim, respHeight = survey._setResponse(self.genderItem, textStim)

        assert type(sliderStim) == Slider
        assert type(respHeight) == float

    def test_questionHeight(self):
        for item in self.survey._items['question']:
            assert self.survey.getQuestionHeight(item) == item.boundingBox[1] / float(self.win.size[1] / 2)

    def test_questionWidth(self):
        for item in self.survey._items['question']:
            assert self.survey.getQuestionWidth(item) == item.boundingBox[0] / float(self.win.size[0] / 2)

    def test_respHeight(self):
        for item in self.survey.items:
            if item['layout'] == 'vert':
                assert self.survey.getRespHeight(item) == (len(item['options']) * self.survey.textHeight)
            elif item['layout'] == 'horiz' and len(item['options']) <= 3:
                assert self.survey.getRespHeight(item) == self.survey.textHeight
            elif item['layout'] == 'horiz' and len(item['options']) > 3 and not item['type'] == 'rating':
                longest = len(item['options'][-1])
                assert self.survey.getRespHeight(item) == (self.survey.textHeight * longest) - (.0155 * longest)

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
                       self.survey._baseYpositions[-1],
                       atol=0.02)  # TODO: liberal atol, needs tightening up

    def test_baseYpositions(self):
        survey = Form(self.win, items=self.questions, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        testPositions = []
        survey.virtualHeight = 0
        for item in survey.items:
            question, questionHeight, questionWidth = survey._setQuestion(item)
            response, respHeight, = survey._setResponse(item, question)
            testPositions.append(survey.virtualHeight
                                 - max(respHeight, questionHeight)
                                 - survey.textHeight
                                 + (respHeight / 2) * (item['layout'] == 'vert'))
            survey.virtualHeight -= max(respHeight, questionHeight) + survey.itemPadding

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
            assert self.survey._inRange(self.survey._items['question'][5])

    def test_get_data(self):
        self.survey = Form(self.win, items=self.questions, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        data = self.survey.getData()
        assert set(data['questions']) == {'What is your gender?', 'How much you like running', 'How much you like cake'}
        assert set(data['ratings']) == {None}
        assert set(data['rt']) == {None}

    def teardown_class(self):
        self.win.close()

if __name__ == "__main__":
    test = Test_Form()
    test.setup_class()
    # Add tests
    test.teardown_class()
