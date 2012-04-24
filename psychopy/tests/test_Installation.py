import sys

def test_essential_imports():
    import wx
    import numpy
    import scipy
    import matplotlib
    import pygame
    import pyglet
    import OpenGL
    import openpyxl

def test_extra_imports():
    import serial
    import pp
    import egi
    try: import labjack
    except: import u3, u6, ue9, LabJackPython
    import pylink
    import ioLabs
    import hid
    import lxml
    #avbin
    import pyglet
    assert pyglet.media.have_avbin
    #platform specific
    if sys.platform=='win32': import parallel