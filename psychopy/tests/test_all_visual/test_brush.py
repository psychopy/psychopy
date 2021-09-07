#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from psychopy.visual.window import Window
from psychopy.visual.brush import Brush
from psychopy.visual.shape import ShapeStim


class Test_Brush():
    """Test suite for Brush component"""
    def setup_class(self):
        self.win = Window([128,128],
                          pos=[50,50],
                          allowGUI=False,
                          autoLog=False)

    def teardown_class(self):
        self.win.close()

    def test_line_color(self):
        colors = ['black', 'red']
        for color in colors:
            testBrush = Brush(self.win, lineColor=color)
            assert testBrush.lineColor == color

    def test_line_width(self):
        widths = [1, 5]
        for width in widths:
            testBrush = Brush(self.win, lineWidth=width)
            assert testBrush.lineWidth == width

    def test_close_shape(self):
        testBrush = Brush(self.win)
        assert testBrush.closeShape == False

    def test_create_stroke(self):
        testBrush = Brush(self.win)
        testBrush._createStroke()
        assert len(testBrush.shapes) == 1
        assert isinstance(testBrush.shapes[0], ShapeStim)

    def test_brush_down(self):
        testBrush = Brush(self.win)
        assert testBrush.brushDown == False

    def test_brush_vertices(self):
        testBrush = Brush(self.win)
        assert testBrush.brushPos == []

    def test_at_start_point(self):
        testBrush = Brush(self.win)
        assert testBrush.atStartPoint == False

    def test_current_shape(self):
        testBrush = Brush(self.win)
        testBrush._createStroke()
        assert testBrush.currentShape == 0

    def test_reset(self):
        testBrush = Brush(self.win)
        testBrush._createStroke()
        testBrush.reset()
        assert testBrush.shapes == []
        assert testBrush.atStartPoint == False
