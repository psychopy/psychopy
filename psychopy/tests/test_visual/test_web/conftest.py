import copy

import pytest


@pytest.fixture(autouse=True)
def restoreEventState():
    """Put back the `event` module's mouse state after tests which send mouse
    events through windows, so they don't affect later tests."""
    from psychopy import event
    names = ('mouseButtons', 'mouseTimes', 'mouseWheelRel')
    saved = {name: copy.copy(getattr(event, name)) for name in names}
    yield
    for name, value in saved.items():
        setattr(event, name, value)
    event.clearEvents()
