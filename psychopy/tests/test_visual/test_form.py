#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path

import pytest
from pandas import DataFrame

from psychopy.tests.test_visual.test_basevisual import _TestColorMixin, _TestSerializationMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin
from psychopy.visual.window import Window
from psychopy.visual.form import Form
from psychopy.visual.textbox2.textbox2 import TextBox2
from psychopy.visual.slider import Slider
from psychopy.tests import utils
import shutil
from tempfile import mkdtemp
import numpy as np


class Test_Form(_TestColorMixin, _TestBoilerplateMixin, _TestSerializationMixin):
    """Test suite for Form component"""

    def setup_class(self):
        # Store different response types
        self.respTypes = ['heading', 'description', 'rating', 'slider', 'free text', 'choice', 'radio']

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
        self.obj = self.survey
        # Pixel coord of top left corner
        tl = (round(self.obj.win.size[0]/2 - 1*self.obj.win.size[1]/2),
              round(self.obj.win.size[1]/2 - 0.3*self.obj.win.size[1]/2))
        # Pixel which is the border color
        self.obj.border.lineWidth = 2
        self.borderPoint = (tl[1], tl[0])
        self.borderUsed = True
        # Pixel which is the fill color
        self.fillPoint = (tl[1]+4, tl[0]+4)
        self.fillUsed = True

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

        # this doesn't include a itemText or questionText so should get an err
        missingHeader = [{"qText": "What is your gender?",
                      "questionWidth": 0.7,
                      "type": "radio",
                      "responseWidth": 0.3,
                      "options": "Other",
                      "layout": 'vert',
                      "index": 0,
                      "questionColor": "white",
                      "responseColor": "white"}]


        # Check options for list of dicts
        with pytest.raises(ValueError):
            self.survey = Form(self.win, items=missingHeader, size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)

        # Check csv
        self.survey = Form(self.win, items=self.fileName_csv,
                           size=(1.0, 0.3), pos=(0.0, 0.0), autoLog=False)
        # Check Excel
        self.survey = Form(self.win, items=self.fileName_xlsx,
                           size=(1.0, 0.3), pos=(0.0, 0.0), randomize=False, autoLog=False)

    def test_combinations(self):
        """
        Test that question options interact well
        """
        # Define sets of each option
        exemplars = {
            'bigResp': [  # Resp is bigger than item
                {
                    'index': 1,
                    'itemText': "A PsychoPy zealot knows a smidge of wx but JavaScript is the question",
                    'options': [1, "a", "multiple word"],
                    'ticks': [1, 2, 3],
                    'layout': 'vert',
                    'itemColor': 'darkslateblue',
                    'itemWidth': 0.3,
                    'responseColor': 'darkred',
                    'responseWidth': 0.7,
                    'font': 'Noto Sans',
                },
                {
                    'index': 0,
                    'itemText': "A PsychoPy zealot knows a smidge of wx but JavaScript is the question",
                    'options': [1, "a", "multiple word"],
                    'ticks': [1, 2, 3],
                    'layout': 'horiz',
                    'itemColor': 'darkred',
                    'itemWidth': 0.3,
                    'responseColor': 'darkslateblue',
                    'responseWidth': 0.7,
                    'font': 'Noto Sans',
                },
            ],
            'bigItem': [  # Item is bigger than resp
                {
                    'index': 1,
                    'itemText': "A PsychoPy zealot knows a smidge of wx but JavaScript is the question",
                    'options': [1, "a", "multiple word"],
                    'ticks': [1, 2, 3],
                    'layout': 'vert',
                    'itemColor': 'darkslateblue',
                    'itemWidth': 0.7,
                    'responseColor': 'darkred',
                    'responseWidth': 0.3,
                    'font': 'Noto Sans',
                },
                {
                    'index': 0,
                    'itemText': "A PsychoPy zealot knows a smidge of wx but JavaScript is the question",
                    'options': [1, "a", "multiple word"],
                    'ticks': [1, 2, 3],
                    'layout': 'horiz',
                    'itemColor': 'darkred',
                    'itemWidth': 0.7,
                    'responseColor': 'darkslateblue',
                    'responseWidth': 0.3,
                    'font': 'Noto Sans',
                },
            ],
        }
        tykes = {
            'bigRespOverflow': [  # Resp is bigger than item, both together flow over form edge
                {
                    'index': 1,
                    'itemText': "A PsychoPy zealot knows a smidge of wx but JavaScript is the question",
                    'options': [1, "a", "multiple word"],
                    'ticks': [1, 2, 3],
                    'layout': 'vert',
                    'itemColor': 'darkslateblue',
                    'itemWidth': 0.4,
                    'responseColor': 'darkred',
                    'responseWidth': 0.8,
                    'font': 'Noto Sans',
                },
                {
                    'index': 0,
                    'itemText': "A PsychoPy zealot knows a smidge of wx but JavaScript is the question",
                    'options': [1, "a", "multiple word"],
                    'ticks': [1, 2, 3],
                    'layout': 'horiz',
                    'itemColor': 'darkred',
                    'itemWidth': 0.4,
                    'responseColor': 'darkslateblue',
                    'responseWidth': 0.8,
                    'font': 'Noto Sans',
                },
            ],
            'bigItemOverflow': [  # Item is bigger than resp, both together flow over form edge
                {
                    'index': 1,
                    'itemText': "A PsychoPy zealot knows a smidge of wx but JavaScript is the question",
                    'options': [1, "a", "multiple word"],
                    'ticks': [1, 2, 3],
                    'layout': 'vert',
                    'itemColor': 'darkslateblue',
                    'itemWidth': 0.8,
                    'responseColor': 'darkred',
                    'responseWidth': 0.4,
                    'font': 'Noto Sans',
                },
                {
                    'index': 0,
                    'itemText': "A PsychoPy zealot knows a smidge of wx but JavaScript is the question",
                    'options': [1, "a", "multiple word"],
                    'ticks': [1, 2, 3],
                    'layout': 'horiz',
                    'itemColor': 'darkred',
                    'itemWidth': 0.8,
                    'responseColor': 'darkslateblue',
                    'responseWidth': 0.4,
                    'font': 'Noto Sans',
                },
            ],
        }
        cases = exemplars.copy()
        cases.update(tykes)
        # Test every case
        self.win.flip()
        for name, case in cases.items():
            # Test it for each type
            for thisType in self.respTypes:
                # Set type
                for i, q in enumerate(case):
                    case[i]['type'] = thisType
                # Make form
                survey = Form(self.win, units="height", size=(1, 1), fillColor="white", items=case)
                survey.draw()
                # Get name of answer file
                filename = f"test_form_combinations_{thisType}_{name}.png"
                # Do comparison
                #self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
                utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win, crit=20)
                self.win.flip()

    def test_reset(self):
        """
        Test that the reset function can reset all types of form item
        """
        items = []
        # Add an item of each type
        for thisType in self.respTypes:
            items.append({
                'type': thisType,
                'itemText': "A PsychoPy zealot knows a smidge of wx but JavaScript is the question",
                'options': [1, "a", "multiple word"],
                'ticks': [1, 2, 3],
                'layout': 'vert',
                'itemColor': 'darkslateblue',
                'itemWidth': 0.7,
                'responseColor': 'darkred',
                'responseWidth': 0.3,
                'font': 'Noto Sans',
            })
        # Create form
        survey = Form(self.win, units="height", size=(1, 1), fillColor="white", items=items)
        # Reset form to check it doesn't error
        survey.reset()

    def test_scrolling(self):
        # Define basic question to test with
        item = [{
            'type': 'slider',
            'itemText': "A PsychoPy zealot knows a smidge of wx but JavaScript is the question",
            'options': [1, "a", "multiple word"],
            'ticks': [1, 2, 3],
            'layout': 'vert',
            'itemColor': 'darkslateblue',
            'itemWidth': 0.7,
            'responseColor': 'darkred',
            'responseWidth': 0.3,
            'font': 'Noto Sans',
        }]
        # Typical points on slider to test
        exemplars = [
            0,
            0.5,
            1
        ]
        # Problem cases which should be handled
        tykes = [
        ]
        # Try with questions smaller than form, the same size as and much bigger
        for nItems in (1, 3, 10):
            # Make form
            items = []
            for i in range(nItems):
                items.append(item[0].copy())
                # Append index to item text so it's visible in artefacts
                items[i]['itemText'] = str(i) + items[i]['itemText']
            survey = Form(self.win, units="height", size=(1, 0.5), fillColor="white", items=items)
            for case in exemplars + tykes:
                # Set scrollbar
                survey.scrollbar.rating = case
                survey.draw()
                # Compare screenshot
                filename = f"TestForm_scrolling_nq{nItems}_s{case}.png"
                self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
                #utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win, crit=20)
                self.win.flip()

    def test_set_scroll_speed(self):
        items = 2
        for multipliers in [1,2,3,4]:
            assert self.survey.setScrollSpeed([0] * items, multipliers) == items * multipliers
            assert self.survey.setScrollSpeed([0] * items, multipliers) == items * multipliers
            assert self.survey.setScrollSpeed([0] * items, multipliers) == items * multipliers

    def test_response_text_wrap(self):
        options = ['a', 'b', 'c']
        for size in [.2, .3, .4]:
            item = {"responseWidth": size, "options": options}

    def test_set_questions(self):
        survey = Form(self.win, items=[self.genderItem], size=(1.0, 0.3),
                      pos=(0.0, 0.0), autoLog=False)
        ctrl, h, w = survey._setQuestion(self.genderItem)

        assert type(ctrl) == TextBox2
        assert type(h) in [float, np.float64]
        assert type(w) in [float, np.float64]

    def test_set_response(self):
        survey = Form(self.win, items=[self.genderItem], size=(1.0, 0.3),
                      pos=(0.0, 0.0), autoLog=False)
        ctrl, h, w = survey._setQuestion(self.genderItem)
        sliderStim, respHeight = survey._setResponse(self.genderItem)

        assert type(sliderStim) == Slider
        assert type(respHeight) in [float, np.float64]

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

    def test_font(self):
        exemplars = [
            {"file": "form_font_demographics.xlsx", "font": "Noto Sans",
             "screenshot": "form_font_demographics.png"},
        ]
        tykes = [
            {"file": "form_font_demographics.xlsx", "font": "Indie Flower",
             "screenshot": "form_font_nonstandard.png"},
            {"file": "form_font_languages.xlsx", "font": "Rubrik",
             "screenshot": "form_font_languages.png"},
        ]
        for case in exemplars + tykes:
            survey = Form(self.win, items=str(Path(utils.TESTS_DATA_PATH) / case['file']), size=(1, 1), font=case['font'],
                          fillColor=None, borderColor=None, itemColor="white", responseColor="white", markerColor="red",
                          pos=(0, 0), autoLog=False)
            survey.draw()
            self.win.flip()
            # self.win.getMovieFrame(buffer='front').save(Path(utils.TESTS_DATA_PATH) / case['screenshot'])
            utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / case['screenshot'], self.win, crit=20)

    def test_item_padding(self):
        assert self.survey.itemPadding == 0.05

    def test_form_units(self):
        assert self.survey.units == 'height'

    def test_screen_status(self):
        """Test whether the object is visible"""
        assert self.survey._inRange(self.survey.items[0]['itemCtrl'])

    def test_get_data(self):
        self.survey = Form(self.win, items=self.questions, size=(1.0, 0.3),
                           pos=(0.0, 0.0), autoLog=False)
        data = self.survey.getData()
        Qs = [this['itemText'] for this in data]
        indices = [item['index'] for item in data]
        assert Qs == ['What is your gender?',
                      'How much you like running',
                      'How much you like cake',
                      'How much you like programming',]
        assert all([item['response'] is None for item in data])
        assert all([item['rt'] is None for item in data])
        assert list(indices) == list(range(4))

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)
        self.win.close()


if __name__ == "__main__":
    test = Test_Form()
    test.setup_class()
    test.test_get_data()
    test.teardown_class()
