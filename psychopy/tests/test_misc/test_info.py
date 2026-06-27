# -*- coding: utf-8 -*-

from psychopy import info, visual
import pytest

# py.test -k info --cov-report term-missing --cov info.py


def test_all_names_defined():
    """Every name exported in ``info.__all__`` must actually be defined.

    Guards against dangling ``__all__`` entries such as the removed
    ``_getSvnVersion``/``_getHgVersion`` helpers, which lingered in
    ``__all__`` (and in silently-failing call sites) after their definitions
    were deleted.
    """
    missing = [name for name in info.__all__ if not hasattr(info, name)]
    assert not missing, f"names in __all__ are undefined: {missing}"


@pytest.mark.info
class TestInfo():
    @classmethod
    def setup_class(self):
        self.win = visual.Window(size=(100,100), autoLog=False)
    def teardown_method(self):
        self.win.close()

    def test_info(self):
        info.RunTimeInfo(win=self.win, userProcsDetailed=True, verbose=True)
