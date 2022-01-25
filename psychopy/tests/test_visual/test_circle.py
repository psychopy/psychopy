import pytest
from psychopy import visual
from .test_basevisual import _TestColorMixin, _TestUnitsMixin


class TestCircle(_TestColorMixin, _TestUnitsMixin):

    @classmethod
    def setup_class(self):

        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        self.obj = visual.Circle(self.win, units="pix", pos=(0, 0), size=(128, 128), lineWidth=10)

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
            {'size': [1, 1], 'radius': 1, 'minvertices': [-1, -1], 'maxvertices': [1, 1], 'units': 'height'},
            {'size': [1, 1], 'radius': 2, 'minvertices': [-2, -2], 'maxvertices': [2, 2], 'units': 'height'},
            {'size': [2, 2], 'radius': 0.5, 'minvertices': [-1, -1], 'maxvertices': [1, 1], 'units': 'height'},

            {'size': [100, 100], 'radius': 1, 'minvertices': [-100, -100], 'maxvertices': [100, 100], 'units': 'pix'},
            {'size': [100, 100], 'radius': 2, 'minvertices': [-200, -200], 'maxvertices': [200, 200], 'units': 'pix'},
            {'size': [200, 200], 'radius': 0.5, 'minvertices': [-100, -100], 'maxvertices': [100, 100], 'units': 'pix'},
        ]
        # Test each case
        for case in cases:
            # Apply units, size and radius
            self.obj.units = case['units']
            self.obj.radius = case['radius']
            self.obj.size = case['size']
            # Check that this results in correct vertices
            verts = getattr(self.obj._vertices, case['units'])
            for i in [0, 1]:
                assert min(verts[:, i]) == case['minvertices'][i]
                assert max(verts[:, i]) == case['maxvertices'][i]
