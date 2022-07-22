from pathlib import Path

from psychopy import visual, colors, core
from .test_basevisual import _TestUnitsMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin
from .. import utils

from ..utils import TESTS_DATA_PATH


class TestImage(_TestUnitsMixin, _TestBoilerplateMixin):
    """
    Test that images render as expected. Note: In BaseVisual tests, image colors will look different than
    seems intuitive as foreColor will be set to `"blue"`.
    """
    def setup(self):
        self.win = visual.Window()
        self.obj = visual.ImageStim(
            self.win,
            str(Path(TESTS_DATA_PATH) / 'testimage.jpg'),
            colorSpace='rgb1',
        )

    def test_anchor_flip(self):
        """
        Check that flipping the image doesn't flip the direction of the anchor
        """
        # Setup obj
        self.obj.units = "height"
        self.obj.pos = (0, 0)
        self.obj.size = (0.5, 0.5)
        self.obj.anchor = "bottom left"
        # Flip vertically
        self.obj.flipVert = True
        self.obj.flipHoriz = False
        # Check
        self.win.flip()
        self.obj.draw()
        # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / "test_image_flip_anchor_vert.png")
        utils.compareScreenshot("test_image_flip_anchor_vert.png", self.win, crit=7)
        # Flip horizontally
        self.obj.flipVert = False
        self.obj.flipHoriz = True
        # Check
        self.win.flip()
        self.obj.draw()
        # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / "test_image_flip_anchor_horiz.png")
        utils.compareScreenshot("test_image_flip_anchor_horiz.png", self.win, crit=7)


class TestImageAnimation:
    """
    Tests for using ImageStim to create frame animations
    """
    @classmethod
    def setup_class(cls):
        nFrames = 16
        # Define array of sizes/desired frame rates
        cls.cases = [
            {'size': 6 ** 2, 'fps': 16},
            {'size': 8 ** 2, 'fps': 16},
            {'size': 10 ** 2, 'fps': 8},
            {'size': 12 ** 2, 'fps': 2},
        ]
        # Create frames
        for i, case in enumerate(cls.cases):
            size = case['size']
            # Create window and shapes
            win = visual.Window(size=(size, size), color='purple')
            shape1 = visual.ShapeStim(win,
                                      pos=(0.2, 0.2), size=(0.5, 0.5),
                                      lineWidth=size * 0.1,
                                      fillColor='red', lineColor='green',
                                      )
            shape2 = visual.ShapeStim(win,
                                      pos=(-0.2, -0.2), size=(0.5, 0.5),
                                      lineWidth=size * 0.1,
                                      fillColor='blue', lineColor='yellow'
                                      )

            frames = []

            for thisFrame in range(nFrames):
                # Cycle window hue
                win.color = colors.Color(
                    (win._color.hsv[0] + 360 * thisFrame / nFrames, win._color.hsv[1], win._color.hsv[2]),
                    'hsv'
                )
                # Cycle shape hues
                shape1._fillColor.hsv = (
                    shape1._fillColor.hsv[0] + 360 * thisFrame / nFrames, shape1._fillColor.hsv[1],
                    shape1._fillColor.hsv[2]
                )
                shape1._borderColor.hsv = (
                    shape1._borderColor.hsv[0] - 360 * thisFrame / nFrames, shape1._borderColor.hsv[1],
                    shape1._borderColor.hsv[2]
                )
                shape2._fillColor.hsv = (
                    shape2._fillColor.hsv[0] + 360 * thisFrame / nFrames, shape2._fillColor.hsv[1],
                    shape2._fillColor.hsv[2]
                )
                shape2._borderColor.hsv = (
                    shape2._borderColor.hsv[0] - 360 * thisFrame / nFrames, shape2._borderColor.hsv[1],
                    shape2._borderColor.hsv[2]
                )
                # Rotate shapes
                shape1.ori = shape1.ori + 360 * thisFrame / nFrames
                shape2.ori = shape2.ori - 360 * thisFrame / nFrames
                # Render
                win.flip()
                shape1.draw()
                shape2.draw()
                # Get frame
                frame = win.getMovieFrame(buffer='back')
                frames.append(
                    frame
                )

            # Cleanup
            win.close()
            del shape1
            del shape2
            # Update case
            cls.cases[i]['frames'] = frames

    def test_fps(self):
        """
        Check that images can be updated sufficiently fast to create frame animations
        """
        # Create clock
        clock = core.Clock()
        # Try at each size
        for case in self.cases:
            size = case['size']
            # Make window and image
            win = visual.Window(size=(size, size))
            img = visual.ImageStim(win, units='pix', size=(size, size))
            # Iterate through frames
            refr = []
            for frame in case['frames']:
                # Reset clock
                clock.reset()
                # Set image contents
                img.image = frame
                # Update
                img.draw()
                win.flip()
                # Store time taken
                refr.append(clock.getTime())
            # Print frame rate for this size
            fps = round(1 / max(refr))
            assert fps > case['fps'], (
                f"Max frame rate for {size}x{size} animations should be at least {case['fps']}, but was {fps}"
            )
            # Cleanup
            win.close()
            del img
