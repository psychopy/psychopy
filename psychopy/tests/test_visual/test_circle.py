from pathlib import Path

import pytest
from psychopy import visual
from .test_basevisual import _TestColorMixin, _TestUnitsMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin
from .. import utils


class TestCircle(_TestColorMixin, _TestUnitsMixin, _TestBoilerplateMixin):

    @classmethod
    def setup_class(self):

        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        self.obj = visual.Circle(self.win, units="pix", pos=(0, 0), size=(128, 128), lineWidth=3)

        # Pixel which is the border color
        self.borderPoint = (64, 0)
        self.borderUsed = True
        # Pixel which is the fill color
        self.fillPoint = (64, 64)
        self.fillUsed = True
        # Shape has no foreground color
        self.foreUsed = False

    def test_radius(self):
        # Define some use cases
        cases = [
            {'size': [.1, .1], 'radius': 1, 'units': 'height',
             'minvertices': [-.1, -.1], 'maxvertices': [.1, .1],
             'label': ".1height"},
            {'size': [.1, .1], 'radius': 2, 'units': 'height',
             'minvertices': [-.2, -.2], 'maxvertices': [.2, .2],
             'label': ".2height"},
            {'size': [.2, .2], 'radius': 0.5, 'units': 'height',
             'minvertices': [-.1, -.1], 'maxvertices': [.1, .1],
             'label': ".1height"},

            {'size': [10, 10], 'radius': 1, 'units': 'pix',
             'minvertices': [-10, -10], 'maxvertices': [10, 10],
             'label': "10pix"},
            {'size': [10, 10], 'radius': 2, 'units': 'pix',
             'minvertices': [-20, -20], 'maxvertices': [20, 20],
             'label': "20pix"},
            {'size': [20, 20], 'radius': 0.5, 'units': 'pix',
             'minvertices': [-10, -10], 'maxvertices': [10, 10],
             'label': "10pix"},
        ]
        # Test each case
        for case in cases:
            self.win.flip()
            # Apply units, size and radius
            self.obj.units = case['units']
            self.obj.radius = case['radius']
            self.obj.size = case['size']
            # Check that this results in correct vertices
            verts = getattr(self.obj._vertices, case['units'])
            for i in [0, 1]:
                assert min(verts[:, i]) == case['minvertices'][i]
                assert max(verts[:, i]) == case['maxvertices'][i]
            # Check that vertices are drawn correctly
            filename = f"test_circle_radius_{case['label']}.png"
            self.obj.draw()
            # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
            # utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win, crit=20)
