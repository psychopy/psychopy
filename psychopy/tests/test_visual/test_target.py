from psychopy import visual, layout
from .test_basevisual import _TestColorMixin, _TestUnitsMixin, _TestSerializationMixin

class TestTarget(_TestUnitsMixin, _TestSerializationMixin):
    # Pixel which is the border color
    borderPoint = (0, 55)
    borderUsed = True
    # Pixel which is the fill color
    fillPoint = (0, 30)
    fillUsed = False
    # Pixel which is the fore color
    forePoint = (0, 0)
    foreUsed = False

    @classmethod
    def setup_class(cls):
        cls.win = visual.Window(size=(128, 128))
        cls.obj = visual.TargetStim(cls.win, "TargetStim", units='pix', pos=(-64, 64),
                                    innerRadius=20, radius=60, lineWidth=10, innerLineWidth=5)

    def test_radius(self):
        # Define some cases to test
        cases = [
            {"outer": 1, "inner": 0.5, "units": "height"},
            {"outer": 100, "inner": 50, "units": "pix"},
        ]

        for case in cases:
            # Set radiae (radiuses?) and units
            self.obj.units = case['units']
            self.obj.outerRadius = case['outer']
            self.obj.innerRadius = case['inner']
            # Check that the target's size is set to twice the radius value
            assert self.obj.outer._size == layout.Size(case['outer']*2, case['units'], self.win)
            assert self.obj.inner._size == layout.Size(case['inner']*2, case['units'], self.win)
