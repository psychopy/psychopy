import pytest
from psychopy import visual
from psychopy import colors
from psychopy.tests import utils


class _TestColorMixin:
    # Define expected values for different spaces
    colorExemplars = [
        {'rgb': (1.00, 1.00, 1.00), 'rgb255': (255, 255, 255), 'hsv': (0, 0.00, 1.00), 'hex': '#ffffff',
         'named': 'white'},  # Pure white
        {'rgb': (0.00, 0.00, 0.00), 'rgb255': (128, 128, 128), 'hsv': (0, 0.00, 0.50), 'hex': '#808080',
         'named': 'gray'},  # Mid grey
        {'rgb': (-1.00, -1.00, -1.00), 'rgb255': (0, 0, 0), 'hsv': (0, 0.00, 0.00), 'hex': '#000000', 'named': 'black'},
        # Pure black
        {'rgb': (1.00, -1.00, -1.00), 'rgb255': (255, 0, 0), 'hsv': (0, 1.00, 1.00), 'hex': '#ff0000', 'named': 'red'},
        # Pure red
        {'rgb': (-1.00, 1.00, -1.00), 'rgb255': (0, 255, 0), 'hsv': (120, 1.00, 1.00), 'hex': '#00ff00',
         'named': 'lime'},  # Pure green
        {'rgb': (-1.00, -1.00, 1.00), 'rgb255': (0, 0, 255), 'hsv': (240, 1.00, 1.00), 'hex': '#0000ff',
         'named': 'blue'},  # Pure blue
        # Psychopy colours
        {'rgb': (-0.20, -0.20, -0.14), 'rgb255': (102, 102, 110), 'hsv': (240, 0.07, 0.43), 'hex': '#66666e'},  # grey
        {'rgb': (0.35, 0.35, 0.38), 'rgb255': (172, 172, 176), 'hsv': (240, 0.02, 0.69), 'hex': '#acacb0'},
        # light grey
        {'rgb': (0.90, 0.90, 0.90), 'rgb255': (242, 242, 242), 'hsv': (0, 0.00, 0.95), 'hex': '#f2f2f2'},  # offwhite
        {'rgb': (0.90, -0.34, -0.29), 'rgb255': (242, 84, 91), 'hsv': (357, 0.65, 0.95), 'hex': '#f2545b'},  # red
        {'rgb': (-0.98, 0.33, 0.84), 'rgb255': (2, 169, 234), 'hsv': (197, 0.99, 0.92), 'hex': '#02a9ea'},  # blue
        {'rgb': (-0.15, 0.60, -0.09), 'rgb255': (108, 204, 116), 'hsv': (125, 0.47, 0.80), 'hex': '#6ccc74'},  # green
        {'rgb': (0.85, 0.18, -0.98), 'rgb255': (236, 151, 3), 'hsv': (38, 0.99, 0.93), 'hex': '#ec9703'},  # orange
        {'rgb': (0.89, 0.65, -0.98), 'rgb255': (241, 211, 2), 'hsv': (52, 0.99, 0.95), 'hex': '#f1d302'},  # yellow
        {'rgb': (0.53, 0.49, 0.94), 'rgb255': (195, 190, 247), 'hsv': (245, 0.23, 0.97), 'hex': '#c3bef7'},  # violet
    ]
    # A few values which are likely to mess things up
    colorTykes = [
        {'rgba': (1.00, 1.00, 1.00, 0.50), 'rgba255': (255, 255, 255, 0.50), 'hsva': (0, 0.00, 1.00, 0.50)},
        # Make sure opacities work in every space
        {'rgba': "white", 'rgba255': "white", "hsva": "white", "hex": "white", "rgb255": "#ffffff"},
        # Overriding colorSpace with hex or named values
        {'rgba': None, 'named': None, 'hex': None, 'hsva': None},  # None as a value
    ]
    # Pixel which is the border color
    borderPoint = (0, 0)
    borderUsed = False
    # Pixel which is the fill color
    fillPoint = (50, 50)
    fillUsed = False
    # Pixel which is the fore color
    forePoint = (50, 50)
    foreUsed = False
    # Placeholder for testing object and window
    obj = None
    win = None

    def test_colors(self):
        # If this test object has no obj, skip
        if not self.obj:
            return
        # Test each case
        for case in self.colorTykes + self.colorExemplars:
            for space, color in case.items():
                # Make color to compare against
                target = colors.Color(color, space)
                # Prepare object
                self.obj.colorSpace = space
                self.obj.fillColor = 'white'
                self.obj.foreColor = 'white'
                self.obj.borderColor = 'white'
                self.obj.opacity = 1
                if hasattr(self.obj, "text"):
                    self.obj.text = "A PsychoPy zealot knows a smidge of wx, but JavaScript is the question."
                # Test fill color
                if self.fillUsed:
                    # Set fill
                    self.obj.fillColor = color
                    self.obj.opacity = 1
                    self.win.flip()
                    self.obj.draw()
                    if color is not None:
                        # Make sure fill is set
                        utils.comparePixelColor(self.win, target, coord=self.fillPoint)
                        # Make sure border is not
                        if self.borderUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.borderPoint)
                        # Make sure fore is not
                        if self.foreUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.forePoint)
                    # Reset fill
                    self.obj.fillColor = 'white'
                    self.obj.opacity = 1
                # Test border color
                if self.borderUsed:
                    # Set border
                    self.obj.borderColor = color
                    self.obj.opacity = 1
                    self.win.flip()
                    self.obj.draw()
                    if color is not None:
                        # Make sure border is set
                        utils.comparePixelColor(self.win, target, coord=self.borderPoint)
                        # Make sure fill is not
                        if self.fillUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.fillPoint)
                        # Make sure fore is not
                        if self.foreUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.forePoint)
                    # Reset border
                    self.obj.borderColor = 'white'
                    self.obj.opacity = 1
                # Test fore color
                if self.foreUsed:
                    # Set fore
                    self.obj.foreColor = color
                    self.obj.opacity = 1
                    self.win.flip()
                    self.obj.draw()
                    if color is not None:
                        # Make sure fore is set
                        utils.comparePixelColor(self.win, target, coord=self.forePoint)
                        # Make sure fill is not
                        if self.fillUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.fillPoint)
                        # Make sure border is not
                        if self.borderUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.borderPoint)
                    # Reset fore
                    self.obj.foreColor = 'white'
                    self.obj.opacity = 1

    def test_legacy_setters(self):
        # If this test object has no obj, skip
        if not self.obj:
            return
        # Test each case
        for case in self.colorTykes + self.colorExemplars:
            for space, color in case.items():
                if color is None:
                    continue
                # Make color to compare against
                target = colors.Color(color, space)
                # Prepare object
                self.obj.colorSpace = space
                self.obj.fillColor = 'white'
                self.obj.foreColor = 'white'
                self.obj.borderColor = 'white'
                self.obj.opacity = 1
                if hasattr(self.obj, "text"):
                    self.obj.text = "A PsychoPy zealot knows a smidge of wx, but JavaScript is the question."

                # Test property aliases:
                # color == foreColor
                self.obj.color = color
                assert self.obj._foreColor == target
                self.obj.color = colors.Color('white')
                self.obj.opacity = 1
                # backColor == fillColor
                self.obj.backColor = color
                assert self.obj._fillColor == target
                self.obj.backColor = colors.Color('white')
                self.obj.opacity = 1
                # lineColor == borederColor
                self.obj.lineColor = color
                assert self.obj._borderColor == target
                self.obj.lineColor = colors.Color('white')
                self.obj.opacity = 1

                if space == 'rgb':
                    # Test RGB properties
                    # foreRGB
                    self.obj.foreRGB = color
                    assert self.obj._foreColor == target
                    self.obj.foreRGB = colors.Color('white')
                    self.obj.opacity = 1
                    # RGB
                    self.obj.RGB = color
                    assert self.obj._foreColor == target
                    self.obj.RGB = colors.Color('white')
                    self.obj.opacity = 1
                    # fillRGB
                    self.obj.fillRGB = color
                    assert self.obj._fillColor == target
                    self.obj.fillRGB = colors.Color('white')
                    self.obj.opacity = 1
                    # backRGB
                    self.obj.backRGB = color
                    assert self.obj._fillColor == target
                    self.obj.backRGB = colors.Color('white')
                    self.obj.opacity = 1
                    # borderRGB
                    self.obj.borderRGB = color
                    assert self.obj._borderColor == target
                    self.obj.borderRGB = colors.Color('white')
                    self.obj.opacity = 1
                    # lineRGB
                    self.obj.lineRGB = color
                    assert self.obj._borderColor == target
                    self.obj.lineRGB = colors.Color('white')
                    self.obj.opacity = 1

                    # Test RGB methods
                    # setRGB
                    self.obj.setRGB(color)
                    assert self.obj._foreColor == target
                    self.obj.setRGB('white')
                    self.obj.opacity = 1
                    # setFillRGB
                    self.obj.setFillRGB(color)
                    assert self.obj._fillColor == target
                    self.obj.setFillRGB('white')
                    self.obj.opacity = 1
                    # setBackRGB
                    self.obj.setBackRGB(color)
                    assert self.obj._fillColor == target
                    self.obj.setBackRGB('white')
                    self.obj.opacity = 1
                    # setBorderRGB
                    self.obj.setBorderRGB(color)
                    assert self.obj._borderColor == target
                    self.obj.setBorderRGB('white')
                    self.obj.opacity = 1
                    # setLineRGB
                    self.obj.setLineRGB(color)
                    assert self.obj._borderColor == target
                    self.obj.setLineRGB('white')
                    self.obj.opacity = 1

                # Test methods:
                # setForeColor
                self.obj.setForeColor(color)
                assert self.obj._foreColor == target
                self.obj.setForeColor('white')
                self.obj.opacity = 1
                # setColor
                self.obj.setColor(color)
                assert self.obj._foreColor == target
                self.obj.setColor('white')
                self.obj.opacity = 1
                # setFillColor
                self.obj.setFillColor(color)
                assert self.obj._fillColor == target
                self.obj.setFillColor('white')
                self.obj.opacity = 1
                # setBackColor
                self.obj.setBackColor(color)
                assert self.obj._fillColor == target
                self.obj.setBackColor('white')
                self.obj.opacity = 1
                # setBorderColor
                self.obj.setBorderColor(color)
                assert self.obj._borderColor == target
                self.obj.setBorderColor('white')
                self.obj.opacity = 1
                # setLineColor
                self.obj.setLineColor(color)
                assert self.obj._borderColor == target
                self.obj.setLineColor('white')
                self.obj.opacity = 1

                # Test old color space setters
                # foreColorSpace
                self.obj.foreColorSpace = space
                assert self.obj.colorSpace == space
                self.obj.foreColorSpace = 'named'
                # fillColorSpace
                self.obj.fillColorSpace = space
                assert self.obj.colorSpace == space
                self.obj.fillColorSpace = 'named'
                # backColorSpace
                self.obj.backColorSpace = space
                assert self.obj.colorSpace == space
                self.obj.backColorSpace = 'named'
                # borderColorSpace
                self.obj.borderColorSpace = space
                assert self.obj.colorSpace == space
                self.obj.borderColorSpace = 'named'
                # lineColorSpace
                self.obj.lineColorSpace = space
                assert self.obj.colorSpace == space
                self.obj.lineColorSpace = 'named'