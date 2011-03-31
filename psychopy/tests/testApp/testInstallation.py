import sys

def testEssentialImports():
    import wx
    import numpy
    import scipy
    import matplotlib
    import pygame
    import pyglet
    import OpenGL
    import openpyxl
    
def testExtraImports():
    import serial
    import pp
    import egi
    import labjack
    import pylink
    import ioLabs
    import hid
    import lxml
    #avbin
    import pyglet
    assert pyglet.media.have_avbin
    #platform specific
    if sys.platform=='win32': import parallel