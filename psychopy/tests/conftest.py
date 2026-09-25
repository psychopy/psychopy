"""Shared pytest configuration for the PsychoPy test suite.
"""
import sys
import warnings

import pytest


def _getOpenWindows():
    """Get all windows which are currently open (i.e. not yet closed).
    """
    # if nothing has imported the window module then no windows can have been
    # made, so don't import it just to check
    winModule = sys.modules.get('psychopy.visual.window')
    if winModule is None:
        return []

    return [ref() for ref in winModule.openWindows if ref() is not None]


@pytest.fixture(autouse=True, scope='module')
def closeLeakedWindows(request):
    """Close any windows a test module leaves open.

    A window isn't garbage collected until it's closed, as it registers a
    callback to close itself on exit. So any a test forgets to close stay open
    for the rest of the session, and a build up of them slows down the tests
    which follow (particularly on macOS CI runners). Each one closed here is
    reported with a warning, so the test which leaked it can be fixed.
    """
    windowsBefore = {id(win) for win in _getOpenWindows()}
    yield
    leaked = [
        win for win in _getOpenWindows() if id(win) not in windowsBefore]
    for win in leaked:
        win.close()
    if leaked:
        warnings.warn(
            f"{len(leaked)} window(s) left open by {request.module.__name__}, "
            f"closing them")
