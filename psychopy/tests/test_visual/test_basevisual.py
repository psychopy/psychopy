import json
from pathlib import Path

import pytest
from psychopy import visual, layout, event
from psychopy import colors
from psychopy.monitors import Monitor
from copy import copy
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
                # Prepare window
                self.win.flip()
                # Test fill color
                if self.fillUsed:
                    # Set fill
                    self.obj.fillColor = color
                    self.obj.opacity = 1
                    self.obj.draw()
                    if color is not None:
                        # Make sure fill is set
                        utils.comparePixelColor(self.win, target, coord=self.fillPoint, context=f"{self.__class__.__name__}_fill")
                        # Make sure border is not
                        if self.borderUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.borderPoint, context=f"{self.__class__.__name__}_fill")
                        # Make sure fore is not
                        if self.foreUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.forePoint, context=f"{self.__class__.__name__}_fill")
                    # Reset fill
                    self.obj.fillColor = 'white'
                    self.obj.opacity = 1
                # Test border color
                if self.borderUsed:
                    # Set border
                    self.obj.borderColor = color
                    self.obj.opacity = 1
                    self.obj.draw()
                    if color is not None:
                        # Make sure border is set
                        utils.comparePixelColor(self.win, target, coord=self.borderPoint, context=f"{self.__class__.__name__}_border")
                        # Make sure fill is not
                        if self.fillUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.fillPoint, context=f"{self.__class__.__name__}_border")
                        # Make sure fore is not
                        if self.foreUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.forePoint, context=f"{self.__class__.__name__}_border")
                    # Reset border
                    self.obj.borderColor = 'white'
                    self.obj.opacity = 1
                # Test fore color
                if self.foreUsed:
                    # Set fore
                    self.obj.foreColor = color
                    self.obj.opacity = 1
                    self.obj.draw()
                    if color is not None:
                        # Make sure fore is set
                        utils.comparePixelColor(self.win, target, coord=self.forePoint, context=f"{self.__class__.__name__}_fore")
                        # Make sure fill is not
                        if self.fillUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.fillPoint, context=f"{self.__class__.__name__}_fore")
                        # Make sure border is not
                        if self.borderUsed:
                            utils.comparePixelColor(self.win, colors.Color('white'), coord=self.borderPoint, context=f"{self.__class__.__name__}_fore")
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


class _TestUnitsMixin:
    """
    Base tests for all objects which use units
    """
    # Define exemplar positions (assumes win.pos = (256, 128) and 1cm = 64 pix)
    posExemplars = [
        {'suffix': "center_center",
         'norm': (0, 0), 'height': (0, 0), 'pix': (0, 0), 'cm': (0, 0)},
        {'suffix': "bottom_left",
         'norm': (-1, -1), 'height': (-1, -0.5), 'pix': (-128, -64), 'cm': (-2, -1)},
        {'suffix': "top_left",
         'norm': (-1, 1), 'height': (-1, 0.5), 'pix': (-128, 64), 'cm': (-2, 1)},
        {'suffix': "bottom_right",
         'norm': (1, -1), 'height': (1, -0.5), 'pix': (128, -64), 'cm': (2, -1)},
        {'suffix': "top_right",
         'norm': (1, 1), 'height': (1, 0.5), 'pix': (128, 64), 'cm': (2, 1)},
    ]
    posTykes = []

    # Define exemplar sizes (assumes win.pos = (256, 128) and 1cm = 64 pix)
    sizeExemplars = [
        {'suffix': "w128h128",
         'norm': (1, 2), 'height': (1, 1), 'pix': (128, 128), 'cm': (2, 2)},
        {'suffix': "w128h64",
         'norm': (1, 1), 'height': (1, 0.5), 'pix': (128, 64), 'cm': (2, 1)},
        {'suffix': "w64h128",
         'norm': (0.5, 2), 'height': (0.5, 1), 'pix': (64, 128), 'cm': (1, 2)},
        {'suffix': "w64h64",
         'norm': (0.5, 1), 'height': (0.5, 0.5), 'pix': (64, 64), 'cm': (1, 1)},
    ]
    sizeTykes = []

    # Placeholder for testing object and window
    obj = None
    win = None

    def test_pos_size(self):
        # If this test object has no obj, skip
        if not self.obj:
            return
        # Setup window for this test
        monitor = Monitor("testMonitor")
        monitor.setSizePix((256, 128))
        monitor.setWidth(4)
        monitor.setDistance(50)
        win = visual.Window(size=(256, 128), monitor=monitor)
        win.useRetina = False
        # Setup object for this test
        obj = copy(self.obj)
        obj.win = win
        if hasattr(obj, "fillColor"):
            obj.fillColor = 'red'
        if hasattr(obj, "foreColor"):
            obj.foreColor = 'blue'
        if hasattr(obj, 'borderColor'):
            obj.borderColor = 'green'
        if hasattr(obj, 'opacity'):
            obj.opacity = 1
        # Run positions through each size exemplar
        for size in self.sizeExemplars + self.sizeTykes:
            for pos in self.posExemplars + self.posTykes:
                for units in set(list(pos) + list(size)):
                    if units == 'suffix':
                        continue
                    # Set pos and size
                    obj.units = units
                    obj.size = size[units]
                    obj.pos = pos[units]
                    # Draw
                    obj.draw()
                    # Compare screenshot
                    filename = f"{self.__class__.__name__}_{size['suffix']}_{pos['suffix']}.png"
                    #win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
                    utils.compareScreenshot(filename, win, crit=8)
                    win.flip()
        # Cleanup
        win.close()
        del obj
        del win

    # def test_wh_setters(self):
    #     """
    #     Test that the width and height setters function the same as using the size setter
    #     """
    #     # Define some sizes to try out
    #     cases = [
    #         {'size': 100,
    #          'units': 'pix'},
    #         {'size': 200,
    #          'units': 'pix'},
    #     ]
    #     # Create duplicate of object for safety
    #     obj = copy(self.obj)
    #     # Try each case
    #     for case in cases:
    #         # Set units
    #         obj.units = case['units']
    #         # Set width and height using setters
    #         obj.width = case['size']
    #         obj.height = case['size']
    #         # Check that the resulting size is as desired
    #         assert all(obj.size == case['size'])

    def test_unit_mismatch(self):
        """
        Test that a given stimulus can be drawn without error in all combinations of stimulus units x window units and
        checking that it looks the same as when both units are pix.
        """
        # Test all unit types apart from None and ""
        unitTypes = layout.unitTypes[2:]
        # Create window (same size as was used for other tests)
        win = visual.Window(self.obj.win.size, pos=self.obj.win.pos, monitor="testMonitor")
        # Create object
        obj = copy(self.obj)
        obj.win = win
        # Create model image (pix units for both)
        win.units = 'pix'
        obj.units = 'pix'
        obj.draw()
        filename = Path(utils.TESTS_DATA_PATH) / "test_unit_mismatch.png"
        win.getMovieFrame(buffer='back').save(filename)
        if hasattr(obj, "_size"):
            # Get model sizes
            targetSizes = {units: getattr(obj._size, units) for units in unitTypes}
        # Flip screen
        win.flip()
        # Iterate through window and object units
        for winunits in unitTypes:
            for objunits in unitTypes:
                # Create a window and object
                win.units = winunits
                obj.units = objunits
                # Draw object
                obj.draw()
                # Compare appearance
                utils.compareScreenshot(filename, win, tag=f"{winunits}X{objunits}")
                if hasattr(obj, "_size"):
                    # Compare reported size
                    assert layout.Size(obj.size, obj.units, obj.win) == layout.Size(targetSizes[objunits], objunits, obj.win), (
                        f"Object size ({obj.size}, in {obj.units}) did not match desired size ({targetSizes[objunits]} "
                        f"in {objunits} when window was {obj.win.size}px in {winunits}."
                    )
                # Flip screen
                win.flip()
        # Close window
        win.close()
        # Delete model image
        filename.unlink()

    def test_manual(self):
        """
        For local use only: Uncomment desired manual tests to have them picked up by the test suite when you next run
        it. Useful as it means you can actually interact with the stimulus to make sure it behaves right, rather than
        relying on static screenshot comparisons.

        IMPORTANT: Comment them back out before committing, otherwise the test suite will stall!
        """
        # self.manual_unit_mismatch()

    def manual_unit_mismatch(self):
        """
        For manually testing stimulus x window unit mismatches. Won't be run by the test suite but can be useful to run
        yourself as it allows you to interact with the stimulus to make sure it's working as intended.
        """
        # Test all unit types apart from None and ""
        unitTypes = layout.unitTypes[2:]

        # Load / create file to store reference to combinations which are marked as good (saves time)
        goodPath = Path(utils.TESTS_DATA_PATH) / "manual_unit_test_good_local.json"
        if goodPath.is_file():
            # Load good file if present
            with open(goodPath, "r") as f:
                good = json.loads(f.read())
        else:
            # Create good file if not
            good = []
            with open(goodPath, "w") as f:
                f.write("[]")

        # Iterate through window and object units
        for winunits in unitTypes:
            for objunits in unitTypes:
                # If already marked as good, skip this combo
                if [winunits, objunits] in good:
                    continue
                try:
                    # Create a window and object
                    win = visual.Window(monitor="testMonitor", units=winunits)
                    win.monitor.setSizePix((256, 128))
                    win.monitor.setWidth(4)
                    win.monitor.setDistance(50)
                    obj = copy(self.obj)
                    obj.win = win
                    obj.units = objunits
                    # Add a label for the units
                    label = visual.TextBox2(win, text=f"Window: {winunits}, Slider: {objunits}", font="Open Sans",
                                            anchor="top-center", alignment="center top", padding=0.05, units="norm",
                                            pos=(0, 1))
                    # Add instructions
                    instr = visual.TextBox2(win,
                                            text=(
                                                f"Press ENTER if object is functioning as intended, otherwise press "
                                                f"any other key."
                                            ), font="Open Sans", anchor="top-center", alignment="center bottom",
                                            padding=0.05, units="norm", pos=(0, -1))
                    # Draw loop until button is pressed
                    keys = []
                    while not keys:
                        keys = event.getKeys()
                        obj.draw()
                        label.draw()
                        instr.draw()
                        win.flip()

                    if 'return' in keys:
                        # If enter was pressed, mark as good
                        good.append([winunits, objunits])
                        with open(goodPath, "w") as f:
                            f.write(json.dumps(good))
                    else:
                        # If any other key was pressed, mark as bad
                        raise AssertionError(
                            f"{self.obj.__class__.__name__} marked as bad when its units were {objunits} and window "
                            f"units were {winunits}"
                        )
                    win.close()
                except BaseException as err:
                    err.args = err.args + ([winunits, objunits],)
                    raise err

    def test_default_units(self):
        for units in layout.unitTypes:
            if units in [None, "None", "none", ""]:
                continue
            # Create a window with given units
            win = visual.Window(monitor="testMonitor", units=units)
            win.monitor.setSizePix((256, 128))
            win.monitor.setWidth(4)
            win.monitor.setDistance(50)
            # When setting units to None with win, does it inherit units?
            self.obj.win = win
            self.obj.units = None
            assert self.obj.units == units
            # Cleanup
            win.close()
            del win

        # Reset obj win
        self.obj.win = self.win
