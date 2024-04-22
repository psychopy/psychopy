#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""All tests in this file involve rapidly changing colours, do not run these
tests in a setting where you can view the output if you have photosensitive
epilepsy.

"""
from psychopy.alerts._errorHandler import _BaseErrorHandler
from psychopy.tests import utils
from psychopy import visual, colors
import numpy as np

# Define expected values for different spaces
exemplars = [
    {'rgb': ( 1.00,  1.00,  1.00), 'rgb255': (255, 255, 255), 'hsv': (  0, 0.00, 1.00), 'hex': '#ffffff', 'named': 'white'},  # Pure white
    {'rgb': ( 0.00,  0.00,  0.00), 'rgb255': (128, 128, 128), 'hsv': (  0, 0.00, 0.50), 'hex': '#808080', 'named': 'gray'},  # Mid grey
    {'rgb': (-1.00, -1.00, -1.00), 'rgb255': (  0,   0,   0), 'hsv': (  0, 0.00, 0.00), 'hex': '#000000', 'named': 'black'},  # Pure black
    {'rgb': ( 1.00, -1.00, -1.00), 'rgb255': (255,   0,   0), 'hsv': (  0, 1.00, 1.00), 'hex': '#ff0000', 'named': 'red'},  # Pure red
    {'rgb': (-1.00,  1.00, -1.00), 'rgb255': (  0, 255,   0), 'hsv': (120, 1.00, 1.00), 'hex': '#00ff00', 'named': 'lime'},  # Pure green
    {'rgb': (-1.00, -1.00,  1.00), 'rgb255': (  0,   0, 255), 'hsv': (240, 1.00, 1.00), 'hex': '#0000ff', 'named': 'blue'},  # Pure blue
    # Psychopy colours
    {'rgb': (-0.20, -0.20, -0.14), 'rgb255': (102, 102, 110), 'hsv': (240, 0.07, 0.43), 'hex': '#66666e'},  # grey
    {'rgb': ( 0.35,  0.35,  0.38), 'rgb255': (172, 172, 176), 'hsv': (240, 0.02, 0.69), 'hex': '#acacb0'},  # light grey
    {'rgb': ( 0.90,  0.90,  0.90), 'rgb255': (242, 242, 242), 'hsv': (  0, 0.00, 0.95), 'hex': '#f2f2f2'},  # offwhite
    {'rgb': ( 0.90, -0.34, -0.29), 'rgb255': (242,  84,  91), 'hsv': (357, 0.65, 0.95), 'hex': '#f2545b'},  # red
    {'rgb': (-0.98,  0.33,  0.84), 'rgb255': (  2, 169, 234), 'hsv': (197, 0.99, 0.92), 'hex': '#02a9ea'},  # blue
    {'rgb': (-0.15,  0.60, -0.09), 'rgb255': (108, 204, 116), 'hsv': (125, 0.47, 0.80), 'hex': '#6ccc74'},  # green
    {'rgb': ( 0.85,  0.18, -0.98), 'rgb255': (236, 151,   3), 'hsv': ( 38, 0.99, 0.93), 'hex': '#ec9703'},  # orange
    {'rgb': ( 0.89,  0.65, -0.98), 'rgb255': (241, 211,   2), 'hsv': ( 52, 0.99, 0.95), 'hex': '#f1d302'},  # yellow
    {'rgb': ( 0.53,  0.49,  0.94), 'rgb255': (195, 190, 247), 'hsv': (245, 0.23, 0.97), 'hex': '#c3bef7'},  # violet
]
# A few values which are likely to mess things up
tykes = [
    {'rgba': ( 1.00,  1.00,  1.00, 0.50), 'rgba255': (255, 255, 255, 0.50), 'hsva': (  0, 0.00, 1.00, 0.50)},  # Make sure opacities work in every space
    {'rgba': "white", 'rgba255': "white", "hsva": "white", "hex": "white", "rgb255": "#ffffff"},  # Overriding colorSpace with hex or named values
    {'rgba': None, 'named': None, 'hex': None, 'hsva': None},  # None as a value
]

class Test_Window:
    """Some tests just for the window - we don't really care about what's drawn inside it
    """
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        self.error = _BaseErrorHandler()

    @classmethod
    def teardown_class(self):
        self.win.close()

    # Begin test
    def test_colors(self):
        for colorSet in exemplars + tykes:
            # Construct matrix of space pairs
            spaceMatrix = []
            for space1 in colorSet:
                spaceMatrix.extend([[space1, space2] for space2 in colorSet if space2 != space1])
            # Compare each space pair for consistency
            for space1, space2 in spaceMatrix:
                col1 = colors.Color(colorSet[space1], space1)
                col2 = colors.Color(colorSet[space2], space2)
                closeEnough = all(abs(col1.rgba[i]-col2.rgba[i])<0.02 for i in range(4))
                # Check that valid color has been created
                assert (bool(col1) and bool(col2))
                # Check setters
                assert (col1 == col2 or closeEnough)

    def test_window_colors(self):
        # Iterate through color sets
        for colorSet in exemplars + tykes:
            for space in colorSet:
                # Set window color
                self.win.colorSpace = space
                self.win.color = colorSet[space]
                self.win.flip()
                utils.comparePixelColor(self.win, colors.Color(colorSet[space], space))

    def test_shape_colors(self):
        # Create rectangle with chunky border
        obj = visual.Rect(self.win, units="pix", pos=(0,0), size=(128, 128), lineWidth=10)
        # Iterate through color sets
        for colorSet in exemplars + tykes:
            for space in colorSet:
                # Check border color
                obj.colorSpace = space
                obj.borderColor = colorSet[space]
                obj.fillColor = 'white'
                obj.opacity = 1  # Fix opacity at full as this is not what we're testing
                self.win.flip()
                obj.draw()
                if colorSet[space]: # skip this comparison if color is None
                    utils.comparePixelColor(self.win, colors.Color(colorSet[space], space), coord=(1, 1))
                utils.comparePixelColor(self.win, colors.Color('white'), coord=(50, 50))
                # Check fill color
                obj.colorSpace = space
                obj.fillColor = colorSet[space]
                obj.borderColor = 'white'
                obj.opacity = 1  # Fix opacity at full as this is not what we're testing
                self.win.flip()
                obj.draw()
                if colorSet[space]: # skip this comparison if color is None
                    utils.comparePixelColor(self.win, colors.Color(colorSet[space], space), coord=(50, 50))
                utils.comparePixelColor(self.win, colors.Color('white'), coord=(1,1))

                # Testing foreColor is already done in test_textbox

    def test_element_array_colors(self):
        # Create element array with two elements covering the whole window in two block colours
        obj = visual.ElementArrayStim(self.win, units="pix",
                                      fieldPos=(0, 0), fieldSize=(128, 128), fieldShape='square', nElements=2,
                                      sizes=[[64, 128], [64, 128]], xys=[[-32, 0], [32, 0]], elementMask=None, elementTex=None)
        # Iterate through color sets
        for colorSet in exemplars + tykes:
            for space in colorSet:
                if space not in colors.strSpaces and not isinstance(colorSet[space], (str, type(None))):
                    # Check that setting color arrays renders correctly
                    obj.colorSpace = space
                    col1 = np.array(colorSet[space]).reshape((1, -1))
                    col2 = getattr(colors.Color('black'), space).reshape((1, -1))
                    obj.colors = np.append(col1, col2, 0)  # Set first color to current color set, second to black in same color space
                    obj.opacity = 1  # Fix opacity at full as this is not what we're testing
                    self.win.flip()
                    obj.draw()
                    utils.comparePixelColor(self.win, colors.Color(colorSet[space], space), coord=(10, 10))
                    utils.comparePixelColor(self.win, colors.Color('black'), coord=(10, 100))

    def test_visual_helper(self):
        # Create rectangle with chunky border
        obj = visual.Rect(self.win, units="pix", pos=(0, 0), size=(128, 128), lineWidth=10)
        # Iterate through color sets
        for colorSet in exemplars + tykes:
            for space in colorSet:
                # Check border color
                visual.helpers.setColor(obj,
                                        color=colorSet[space], colorSpace=space,
                                        colorAttrib="borderColor")
                obj.fillColor = 'white'
                obj.opacity = 1  # Fix opacity at full as this is not what we're testing
                self.win.flip()
                obj.draw()
                if colorSet[space]:  # skip this comparison if color is None
                    utils.comparePixelColor(self.win, colors.Color(colorSet[space], space), coord=(1, 1))
                utils.comparePixelColor(self.win, colors.Color('white'), coord=(50, 50))
                # Check fill color
                visual.helpers.setColor(obj,
                                        color=colorSet[space], colorSpace=space,
                                        colorAttrib="fillColor")
                obj.borderColor = 'white'
                obj.opacity = 1  # Fix opacity at full as this is not what we're testing
                self.win.flip()
                obj.draw()
                if colorSet[space]:  # skip this comparison if color is None
                    utils.comparePixelColor(self.win, colors.Color(colorSet[space], space), coord=(50, 50))
                utils.comparePixelColor(self.win, colors.Color('white'), coord=(1, 1))
        # Check color addition
        obj.fillColor = 'white'
        visual.helpers.setColor(obj,
                                color='black',
                                colorAttrib='fillColor',
                                operation='+')
        self.win.flip()
        obj.draw()
        utils.comparePixelColor(self.win, colors.Color('white') + colors.Color('black'), coord=(50, 50))
        # Check color subtraction
        obj.fillColor = 'grey'
        visual.helpers.setColor(obj,
                                color='black',
                                colorAttrib='fillColor',
                                operation='-')
        self.win.flip()
        obj.draw()
        utils.comparePixelColor(self.win, colors.Color('grey') - colors.Color('black'), coord=(50, 50))

        # Check alerts
        visual.helpers.setColor(obj, color="white", colorSpaceAttrib="colorSpace", rgbAttrib="fillRGB")
        assert any(err.code == 8105 for err in self.error.alerts), "Alert 8105 not triggered"
        assert any(err.code == 8110 for err in self.error.alerts), "Alert 8110 not triggered"

    def test_contrast(self):
        # Create rectangle with chunky border
        obj = visual.Rect(self.win, units="pix", pos=(0, 0), size=(128, 128), lineWidth=10)
        # Set its colors to be rgb extremes
        obj.fillColor = 'red'
        obj.borderColor = 'blue'
        obj.opacity = 1  # Fix opacity at full as this is not what we're testing
        # Halve contrast
        obj.contrast = 0.5
        # Refresh
        self.win.flip()
        obj.draw()
        # Check rendered color
        utils.comparePixelColor(self.win, colors.Color(( 0.5, -0.5, -0.5), "rgb"), coord=(50, 50))
        utils.comparePixelColor(self.win, colors.Color((-0.5, -0.5,  0.5), "rgb"), coord=(1, 1))


def test_color_operators():
    """Test for operators used to compare colors."""
    red255 = colors.Color((255, 0, 0), space='rgb255')
    redRGB = colors.Color((1, -1, -1), space='rgb')
    redRGB1 = colors.Color((1, 0, 0), space='rgb1')

    assert (red255 == redRGB == redRGB1)
