import numpy
from psychopy import layout, visual


class TestVector:
    def setup_method(self):
        self.win = visual.Window(size=(128, 64), monitor="testMonitor")

    def teardown_method(self):
        self.win.close()
        del self.win

    def test_values(self):
        """
        Check that Vector objects with various values return as intended in a variety of unit spaces.
        """
        # List of objects with their intended values in various spaces
        cases = [
            # (1, 1) height
            (layout.Vector((1, 1), 'height', self.win),
             {'pix': (64, 64), 'height': (1, 1), 'norm': (1, 2), 'cm': (1.875, 1.875)}),
            # (1, 1) norm
            (layout.Vector((1, 1), 'norm', self.win),
             {'pix': (64, 32), 'height': (1, 0.5), 'norm': (1, 1), 'cm': (1.875, 0.9375)}),
            # (1, 1) pix
            (layout.Vector((1, 1), 'pix', self.win),
             {'pix': (1, 1), 'height': (1/64, 1/64), 'norm': (1/64, 1/32), 'cm': (1.875/64, 1.875/64)}),
            # (1, 1) cm
            (layout.Vector((1, 1), 'cm', self.win),
             {'pix': (64/1.875, 64/1.875), 'height': (1/1.875, 1/1.875), 'norm': (1/1.875, 1/0.9375), 'cm': (1, 1)}),
            # Check ratio of pt to cm
            (layout.Vector(1, 'pt', self.win),
             {'pt': 1, 'cm': 0.03527778}),
            # Negative values
            (layout.Vector((-1, -1), 'height', self.win),
             {'pix': (-64, -64), 'height': (-1, -1), 'norm': (-1, -2), 'cm': (-1.875, -1.875)}),
        ]

        # Check that each object returns the correct value in each space specified
        for obj, ans in cases:
            for space in ans:
                # Convert both value and answer to numpy arrays and round to 5dp
                val = numpy.array(getattr(obj, space)).round(5)
                thisAns = numpy.array(ans[space]).round(5)
                # Check that they match
                assert (val == thisAns).all(), (
                    f"Vector of {obj._requested} in {obj._requestedUnits} should return {ans[space]} in {space} units, "
                    f"but instead returned {val}"
                )


class TestVertices:
    def test_setas_inverts_getas(self):
        """
        Vertices.setas should undo exactly what Vertices.getas does, so that
        setas(getas(x)) recovers x. This only shows up as a difference from
        the identity transform when the object has a non-zero position and/or
        a non-unit size, which is the case for almost any real stimulus (e.g.
        a TextBox2 that isn't centred at (0, 0) with size (1, 1), whose
        speechPoint tail is placed via setas).
        """
        size = layout.Size([200, 100], 'pix')
        pos = layout.Position([300, 0], 'pix')
        base = numpy.array([
            [0.5, -0.5],
            [-0.5, -0.5],
            [-0.5, 0.5],
            [0.5, 0.5],
        ])
        # Known absolute pixel positions for `base` scaled by `size` and
        # offset by `pos` (default anchor is centre, so no extra adjustment)
        expectedAbs = numpy.array([
            [400, -50],
            [200, -50],
            [200, 50],
            [400, 50],
        ])

        verts = layout.Vertices(base.copy(), size=size, pos=pos, units='pix')
        absPix = verts.getas('pix')
        numpy.testing.assert_allclose(absPix, expectedAbs)

        # Feeding those same absolute coordinates back through setas should
        # recover the original, normalised base vertices
        verts2 = layout.Vertices(base.copy(), size=size, pos=pos, units='pix')
        verts2.setas(absPix, 'pix')
        numpy.testing.assert_allclose(verts2.base, base)
