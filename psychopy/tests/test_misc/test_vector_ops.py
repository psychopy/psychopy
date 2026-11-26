import numpy as np
from psychopy import layout


def test_vector_magnitude_and_comparisons():
    v2 = layout.Vector((3, 4), "pix")
    assert np.isclose(v2.magnitude, 5.0)

    v3 = layout.Vector((3, 4, 12), "pix")
    assert np.isclose(v3.magnitude, 13.0)

    small = layout.Vector((1, 2), "pix")
    large = layout.Vector((6, 8), "pix")
    assert small < large
    assert small <= large
    assert large > small
    assert large >= small
    assert small < 10.0
    assert large > 5.0

    multi = layout.Vector([[3, 4], [5, 12]], "pix")
    np.testing.assert_allclose(multi.magnitude, [5.0, 13.0])


def test_vector_direction_2d_and_3d():
    v2 = layout.Vector((10, 10), "pix")
    np.testing.assert_allclose(v2.direction, [45.0, 45.0])

    v3 = layout.Vector((3, 4, 5), "pix")
    np.testing.assert_allclose(v3.direction[2], 45.0)

    v3_z = layout.Vector((0, 0, 5), "pix")
    assert v3_z.direction == [90.0, 90.0, 90.0]


def test_invalid_repr_formatting():
    v = layout.Vector((1, 1), "pix")
    v.valid = False
    assert repr(v) == "<psychopy.layout.Vector: Invalid>"

    verts = layout.Vertices(
        [[0, 0], [1, 1]],
        size=layout.Size((2, 4), "pix"),
        pos=layout.Position((10, 20), "pix"),
        units="pix",
    )
    assert "Vertices:" in repr(verts)
    verts._size = None
    verts._pos = None
    assert repr(verts) == "<psychopy.layout.Vertices: Invalid>"
