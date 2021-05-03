# Provisional (super simple) test file which doesn't really test anything else
# besides simply opening a `pyGLFW` window. Add more complete `glfw` backend
# tests to other scripts ASAP, then remove this file.
from psychopy.tests import skip_under_vm
import pytest


@skip_under_vm(reason="GLFW doesn't work on (macOS) virtual machine")
def test_open_glfw_window():
    from psychopy.visual.window import Window
    win = Window(winType='glfw', autoLog=False)
    assert win.winType == 'glfw'
    win.flip()
    win.close()
