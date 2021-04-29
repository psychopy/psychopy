# Provisional (super simple) test file which doesn't really test anything else
# besides simply opening a `pyGLFW` window. Add more complete `glfw` backend
# tests to other scripts ASAP, then remove this file.
from psychopy.tests import utils
from psychopy.visual.window import Window

@utils.skip_under_ghActions()
def test_open_glfw_window():
    win = Window(winType='glfw', autoLog=False)
    assert win.winType == 'glfw'
    win.flip()
    win.close()
