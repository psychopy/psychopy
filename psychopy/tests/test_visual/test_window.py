import importlib
from copy import copy
from pathlib import Path

from psychopy import visual, colors
from psychopy.tests import utils
from psychopy.tests.test_visual.test_basevisual import _TestColorMixin
from psychopy.tools.stimulustools import serialize
from psychopy import colors

class TestWindow:
    def test_serialization(self):
        # make window
        win = visual.Window()
        # serialize window
        params = serialize(win, includeClass=True)
        # get class
        mod = importlib.import_module(params.pop('__module__'))
        cls = getattr(mod, params.pop('__class__'))
        # check class is Window
        assert isinstance(win, cls)
        # recreate win from params
        dupe = cls(**params)
        # delete duplicate
        dupe.close()

    def test_background_image_fit(self):
        _baseCases = [
            # no fitting
            {"fit": None, "image": "default.png",
             "sizes": {'wide': 256, 'tall': 256, 'large': 256, 'small': 256}},
            # cover
            {"fit": "cover", "image": "default.png",
             "sizes": {'wide': 500, 'tall': 500, 'large': 500, 'small': 200}},
            # contain
            {"fit": "contain", "image": "default.png",
             "sizes": {'wide': 200, 'tall': 200, 'large': 500, 'small': 200}},
            # fill
            {"fit": "fill", "image": "default.png",
             "sizes": {'wide': "fill", 'tall': "fill", 'large': 500, 'small': 200}},
            # scaleDown
            {"fit": "scaleDown", "image": "default.png",
             "sizes": {'wide': 200, 'tall': 200, 'large': 256, 'small': 200}},

        ]
        cases = []
        # Create version of each case with different units
        for units in ["pix", "height", "norm"]:
            theseCases = copy(_baseCases)
            for case in theseCases:
                case['units'] = units
                cases.append(case)
        # Additional level of variation: window sizes
        sizes = {
            "wide": (500, 200),
            "tall": (200, 500),
            "large": (500, 500),
            "small": (200, 200),
        }

        for sizeTag, size in sizes.items():
            win = visual.Window(size=size)
            for case in cases:
                # Set image and fit
                win.backgroundFit = case['fit']
                win.backgroundImage = case['image']
                win.flip()
                # Compare
                imgName = Path(case['image']).stem
                filename = f"test_win_bg_{sizeTag}_{case['sizes'][sizeTag]}_{imgName}.png"
                # win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
                try:
                    utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, win, crit=7)
                except AssertionError as err:
                    raise AssertionError(f"Window did not look as expected when:\n"
                                         f"backgroundImage={case['image']},\n"
                                         f"backgroundFit={case['fit']},\n"
                                         f"size={sizeTag},\n"
                                         f"units={case['units']}\n"
                                         f"\n"
                                         f"Original error:"
                                         f"{err}")
            # Close
            win.close()

    def test_win_color_with_image(self):
        """
        Test that the window color is still visible under the background image
        """
        cases = [
            "red",
            "blue",
            "green",
        ]

        win = visual.Window(size=(200, 200), backgroundImage="default.png", backgroundFit="contain")
        for case in cases:
            # Set window color
            win.color = case
            # Draw with background
            win.flip()
            # Check
            filename = f"test_win_bgcolor_{case}.png"
            # win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
            utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, win, crit=10)

    def test_window_colors(self):
        win = visual.Window(size=(200, 200))

        for case in _TestColorMixin.colorTykes + _TestColorMixin.colorExemplars:
            # Go through all TestColorMixin cases
            for colorSpace, color in case.items():
                # Make color to compare against
                target = colors.Color(color, colorSpace)
                # Set each colorspace/color combo
                win.colorSpace = colorSpace
                win.color = color
                win.flip()
                # Check that the middle pixel is this color
                utils.comparePixelColor(
                    win, target,
                    coord=(0, 0),
                    context=f"win_{color}_{colorSpace}")

