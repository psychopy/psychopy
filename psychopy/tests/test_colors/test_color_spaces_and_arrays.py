import numpy as np
from psychopy.colors import Color, colorNames


def test_dklCart_and_dklaCart_roundtrip():
    col = Color([0.2, -0.1, 0.3], space="dklCart")
    assert col.valid
    from_rgb = Color(col.rgb, space="rgb")
    np.testing.assert_allclose(from_rgb.dklCart, [0.2, -0.1, 0.3], atol=1e-4)

    col_alpha = Color([0.0, 0.0, 0.0, 0.25], space="dklaCart")
    assert col_alpha.alpha == 0.25
    assert col_alpha.dklaCart.shape == (4,)
    np.testing.assert_allclose(col_alpha.dklaCart, [0.0, 0.0, 0.0, 0.25], atol=1e-6)


def test_hex_2d_formatting_preserves_trailing_zeros():
    # Values ending in 0 in hex (0x00, 0x10=16, 0xa0=160) must not have '0' stripped
    col = Color([[0, 16, 160], [255, 0, 32]], space="rgb255")
    assert list(col.hex) == ["#0010a0", "#ff0020"]


def test_hex_array_setter_1d_and_2d():
    col_1d = Color(["#ff0000", "#00ff00", "#0000ff"], space="hex")
    assert len(col_1d) == 3
    np.testing.assert_array_equal(
        col_1d.rgb255,
        [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
    )

    col_2d = Color([["#102030"], ["#000000"]], space="hex")
    assert len(col_2d) == 2
    np.testing.assert_array_equal(col_2d.rgb255, [[16, 32, 48], [0, 0, 0]])
    assert list(col_2d.hex) == ["#102030", "#000000"]


def test_named_array_setter_preserves_each_row():
    col = Color(["red", "lime", "blue"], space="named")
    assert len(col) == 3
    expected = np.array([
        colorNames["red"][:3],
        colorNames["lime"][:3],
        colorNames["blue"][:3],
    ])
    np.testing.assert_allclose(col.rgb, expected)

    col_with_none = Color([["red"], ["none"]], space="named")
    assert len(col_with_none) == 2
    np.testing.assert_allclose(col_with_none.alpha, [1.0, 0.0])


def test_grayscale_plus_alpha_2col_validation():
    # Single grayscale value + alpha must tile luminance (column 0), not alpha (column 1)
    col = Color((-1.0, 0.25), space="rgb")
    np.testing.assert_allclose(col.rgb, [-1.0, -1.0, -1.0])
    assert col.alpha == 0.25


def test_integer_space_rounding_and_hsv_cache():
    col = Color((127.6, 0.4, 254.9), space="rgb255")
    np.testing.assert_array_equal(col.rgb255, [128, 0, 255])

    hsv1 = col.hsv
    assert "hsv" in col._cache
    assert col.hsv is hsv1
