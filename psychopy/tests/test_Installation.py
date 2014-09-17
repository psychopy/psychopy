import sys
import pytest

def test_essential_imports():
    import wx
    import numpy
    import scipy
    import matplotlib
    import pygame
    import pyglet
    import OpenGL
    import openpyxl
    import lxml

def test_extra_imports():
    # only Jon needs to run this, so test first if you are him!
    import os
    if sys.platform=='win32':
        import win32api
        user=win32api.GetUserName()
    else:
        import pwd
        user = pwd.getpwuid(os.getuid()).pw_name
    if user not in ['jwp','lpzjwp']:
        pytest.skip('Testing extra imports is only needed for building Standalone distributions')
    #OK, it's Jon , so run it
    import yaml, msgpack, gevent
    import IPython, tornado
    import psychopy_ext
    #avbin
    import pyglet
    assert pyglet.media.have_avbin
    import serial
    import hid
    import pyo
    if sys.platform=='win32':
        import parallel
    #specific hardware libs
    import egi
    try:
        import labjack
    except:
        import u3, u6, ue9, LabJackPython
    import ioLabs
    #platform specific
    import pylink
