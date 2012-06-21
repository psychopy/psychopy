import sys
from psychopy.tests import utils

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
    import os, pwd
    user = pwd.getpwuid(os.getuid()).pw_name
    if user not in ['jwp','lpzjwp']:
        utils.skip('Testing extra imports is only needed for building Standalone distributions')
    import serial
    import pp
    import egi
    try:
        import labjack
    except:
        import u3, u6, ue9, LabJackPython
    import pylink
    import ioLabs
    import hid
    #avbin
    import pyglet
    assert pyglet.media.have_avbin
    #platform specific
    if sys.platform=='win32': import parallel