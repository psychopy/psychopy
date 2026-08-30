"""Tests for psychopy.tools.gltools which don't need an OpenGL context."""

from psychopy.tools.gltools import TexImage2DInfo, TexImage2DMultisampleInfo


def test_texture_descriptors_store_name():
    """
    Check that texture descriptors can be created and keep the handle they were
    given, as `createTexImage2D` and `createTexImage2DMultisample` require.
    """
    cases = [
        TexImage2DInfo(name=1),
        TexImage2DMultisampleInfo(name=1),
    ]
    for tex in cases:
        assert int(tex.name.value) == 1, (
            f"{type(tex).__name__} should store the texture handle it was "
            f"given, but returned {tex.name}"
        )
