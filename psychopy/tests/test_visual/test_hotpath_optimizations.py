import numpy as np
import pytest
from psychopy import monitors, visual
from psychopy.tools import arraytools, monitorunittools
from psychopy.visual import helpers


def test_extendArr_1d_2d_3d_equivalence():
    arr1 = [1, 2, 3]
    np.testing.assert_array_equal(arraytools.extendArr(arr1, 5), [1, 2, 3, 0, 0])

    arr2 = np.arange(6, dtype=np.float32).reshape(2, 3)
    out2 = arraytools.extendArr(arr2, (4, 5))
    assert out2.dtype == np.float32
    assert out2.shape == (4, 5)
    np.testing.assert_array_equal(out2[:2, :3], arr2)
    np.testing.assert_array_equal(out2[2:, :], 0)
    np.testing.assert_array_equal(out2[:, 3:], 0)

    arr3 = np.ones((2, 2, 2), dtype=int)
    out3 = arraytools.extendArr(arr3, (3, 4, 5))
    assert out3.shape == (3, 4, 5)
    assert out3.sum() == 8


def test_val2array_behavior():
    assert arraytools.val2array(None, withNone=True) is None
    with pytest.raises(ValueError):
        arraytools.val2array(None, withNone=False)

    np.testing.assert_array_equal(arraytools.val2array(5, length=3), [5.0, 5.0, 5.0])
    with pytest.raises(ValueError):
        arraytools.val2array(5, withScalar=False, length=2)

    src = np.array([1.5, 2.5])
    out = arraytools.val2array(src, length=2)
    np.testing.assert_array_equal(out, [1.5, 2.5])
    assert out is not src  # must still return a distinct copy from input ndarray


def test_point_in_polygon_and_overlap_paths(monkeypatch):
    square = np.array([[-1.0, -1.0], [1.0, -1.0], [1.0, 1.0], [-1.0, 1.0]])
    shifted = np.array([[0.5, 0.5], [2.5, 0.5], [2.5, 2.5], [0.5, 2.5]])
    disjoint = np.array([[5.0, 5.0], [6.0, 5.0], [6.0, 6.0], [5.0, 6.0]])

    assert bool(helpers.pointInPolygon(0.0, 0.0, square)) is True
    assert bool(helpers.pointInPolygon(3.0, 3.0, square)) is False
    assert bool(helpers.polygonsOverlap(square, shifted)) is True
    assert bool(helpers.polygonsOverlap(square, disjoint)) is False

    # Pure-Python fallback when haveMatplotlib is disabled
    monkeypatch.setattr(helpers, "haveMatplotlib", False)
    assert helpers.pointInPolygon(0.0, 0.0, square) is True
    assert helpers.pointInPolygon(3.0, 3.0, square) is False
    assert helpers.polygonsOverlap(square, shifted) is True
    assert helpers.polygonsOverlap(square, disjoint) is False


def test_monitorunittools_zero_copy_equivalence():
    mon = monitors.Monitor("testPerfMon", width=50.0, distance=57.0)
    mon.setSizePix((1920, 1080))

    class DummyWin:
        size = np.array([1920, 1080])
        pixScaleFactor = 1.0
        monitor = mon

    verts = np.array([[-0.5, -0.5], [0.5, 0.5]])
    pos = np.array([0.25, -0.25])
    np.testing.assert_allclose(
        monitorunittools.convertToPix(verts, pos, "norm", DummyWin),
        (pos + verts) * DummyWin.size / 2.0,
    )
    deg_vals = [1.0, 2.0]
    np.testing.assert_allclose(
        monitorunittools.deg2cm(deg_vals, mon, correctFlat=False),
        np.array(deg_vals) * 57.0 * 0.017455,
    )


def test_elementarray_and_dotstim_in_place_updates():
    win = visual.Window(size=(128, 128), monitor="testMonitor", autoLog=False)
    try:
        elem = visual.ElementArrayStim(
            win,
            units="pix",
            nElements=16,
            sizes=12,
            oris=np.linspace(0, 180, 16),
            sfs=2.0,
            phases=0.25,
            autoLog=False,
        )
        elem._updateVertices()
        elem.updateElementColors()
        elem.updateTextureCoords()
        mask_ref = elem._maskCoords
        tex_orig = elem._texCoords.copy()

        # Verify exact texCoord layout [[R, B], [L, B], [L, T], [R, T]]
        L = (-elem.sfs[:, 0] / 2) - elem.phases[:, 0] + 0.5
        R = (+elem.sfs[:, 0] / 2) - elem.phases[:, 0] + 0.5
        T = (+elem.sfs[:, 1] / 2) - elem.phases[:, 1] + 0.5
        B = (-elem.sfs[:, 1] / 2) - elem.phases[:, 1] + 0.5
        expected_tex = (
            np.concatenate([[R, B], [L, B], [L, T], [R, T]])
            .transpose()
            .reshape([16, 4, 2])
            .astype("d")
        )
        np.testing.assert_allclose(tex_orig, expected_tex)
        assert elem._texCoords.flags["C_CONTIGUOUS"]

        # Updating phases reuses _maskCoords buffer when nElements is unchanged
        elem.phases = 0.5
        elem.updateTextureCoords()
        assert elem._maskCoords is mask_ref

        dots = visual.DotStim(
            win,
            units="pix",
            nDots=64,
            fieldSize=(100, 100),
            fieldShape="circle",
            noiseDots="position",
            coherence=0.5,
            speed=2.0,
            autoLog=False,
        )
        verts_obj = dots._vertices
        for _ in range(5):
            dots._update_dotsXY()
        assert dots._vertices is verts_obj
        assert dots.verticesPix.shape == (64, 2)
    finally:
        win.close()
