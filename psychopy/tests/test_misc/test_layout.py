import gc
import weakref

import numpy
from psychopy import layout, visual


class TestVertices:
    def setup_method(self):
        self.win = visual.Window(size=(128, 64), monitor="testMonitor")

    def teardown_method(self):
        self.win.close()
        del self.win

    def test_obj_not_kept_alive(self):
        """
        Check that stimuli aren't kept alive by their own vertices, which would
        leave them (and their textures etc.) waiting for the cyclic garbage
        collector rather than freed as soon as they're dropped
        (psychopy/psychopy#7459)
        """
        makers = [
            lambda: visual.Rect(self.win, size=0.5),
            lambda: visual.GratingStim(self.win, size=0.5),
            lambda: visual.ImageStim(self.win, size=0.5),
        ]
        gc.collect()
        gc.disable()  # so only reference counting can free them
        try:
            for make in makers:
                stim = make()
                stim.draw()
                assert stim._vertices.obj is stim
                name = type(stim).__name__
                ref = weakref.ref(stim)
                del stim
                assert ref() is None, f"{name} wasn't freed when dropped"
        finally:
            gc.enable()
        self.win.flip()

    def test_obj_attributes(self):
        """
        Check that vertices still take attributes from the object they belong
        to, whether or not it can be weakly referenced, and do without once it
        has gone
        """
        verts = [[0.5, 0.5], [-0.5, -0.5]]
        # scaled by size (2, 4) then offset by pos (10, 20)
        expected = [[11, 22], [9, 18]]

        class Obj:
            pass

        class SlotsObj:
            # without `__weakref__` in its slots, it can't be weakly referenced
            __slots__ = ('win', '_pos', '_size', 'units', 'anchor')

        def make(cls):
            obj = cls()
            obj.win = self.win
            obj._pos = layout.Position((10, 20), 'pix', self.win)
            obj._size = layout.Size((2, 4), 'pix', self.win)
            obj.units = 'pix'
            obj.anchor = 'center'
            return obj

        for cls in (Obj, SlotsObj):
            obj = make(cls)
            vertices = layout.Vertices(verts, obj=obj)
            assert vertices.obj is obj
            assert vertices.units == 'pix'
            assert (vertices.pix == expected).all(), cls.__name__

        # weakly referenced objects are let go of...
        obj = make(Obj)
        vertices = layout.Vertices(verts, obj=obj)
        del obj
        assert vertices.obj is None
        # ...but those which can't be are kept, as they were before
        obj = make(SlotsObj)
        vertices = layout.Vertices(verts, obj=obj)
        del obj
        assert isinstance(vertices.obj, SlotsObj)

        # values given explicitly don't need an object
        vertices = layout.Vertices(
            verts, size=layout.Size((2, 4), 'pix', self.win),
            pos=layout.Position((10, 20), 'pix', self.win), units='pix')
        assert vertices.obj is None
        assert (vertices.pix == expected).all()


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
