import numpy as np
from psychopy import visual, colors


class TestDots:

    @classmethod
    def setup(self):
        self.win = visual.Window([128, 128], monitor="testMonitor", pos=[50,50], allowGUI=False, autoLog=False)

    def test_fieldSize(self):
        """
        Check that dot stim field size is interpreted correctly. Creates a dot stim at various sizes, and poygons at
        the same size to act as a reference.
        """
        def _findColors(win):
            """
            The window background is set to red, the max guides are white, the min guides are blue, and the dots
            are black at 50% opacity. If fieldSize is correct, dots should only be visible against guides, not
            background - so there should be grey and dark blue pixels, with no dark red pixels.
            """
            # Define acceptable margin of error (out of 255)
            err = 5

            # Get screenshot
            img = np.array(win._getFrame(buffer="back"))
            # Flatten screenshot
            img = img.flatten()
            # Unflatten screenshot to pixel level
            img = img.reshape((-1, 3))
            # Get unique colors
            cols = np.unique(img, axis=0)

            # Define colors to seek/avoid
            darkblue = colors.Color(
                (np.array([-1, -1, 1]) + np.array([-1, -1, -1])) / 2,
                "rgb")
            grey = colors.Color(
                (np.array([1, 1, 1]) + np.array([-1, -1, -1])) / 2,
                "rgb")
            darkred = colors.Color(
                (np.array([1, -1, -1]) + np.array([-1, -1, -1])) / 2,
                "rgb")
            # We want dark blue - it means the middle is drawn
            inrange = np.logical_and((darkblue.rgb255 - err) < cols, cols < (darkblue.rgb255 + err))
            inrange = np.all(inrange, axis=1)
            assert np.any(inrange), (
                f"No pixel of color {darkblue.rgb255} found in dotstim, meaning the middle of the field is not drawn.\n"
                f"\n"
                f"Colors found:\n"
                f"{cols}"
            )
            # We want grey - it means the edges are drawn
            inrange = np.logical_and((grey.rgb255 - err) < cols, cols < (grey.rgb255 + err))
            inrange = np.all(inrange, axis=1)
            assert np.any(inrange), (
                f"No pixel of color {grey.rgb255} found in dotstim, meaning the field of dots is too small.\n"
                f"\n"
                f"Colors found:\n"
                f"{cols}"
            )
            # We don't want dark red - it means there are dots outside the field
            inrange = np.logical_and((darkred.rgb255 - err) < cols, cols < (darkred.rgb255 + err))
            inrange = np.all(inrange, axis=1)
            assert not np.any(inrange), (
                f"Pixel of color {darkred.rgb255} found in dotstim, meaning the field of dots is too big.\n"
                f"\n"
                f"Colors found:\n"
                f"{cols}"
            )

        # Define cases to try
        cases = [
            {'size': np.array([.5, .5]),
             'units': 'height'},
            {'size': np.array([1, 1]),
             'units': 'deg'}
        ]
        # Define an acceptable margin of error (in proportion of size)
        err = 0.1
        # Create dots
        params = {
            "win": self.win,
            "nDots": 50,
            "fieldPos": (0, 0),
            "dotSize": (5, 5), "dotLife": 0, "noiseDots": 'direction',
            "dir": 0, "speed": 0.25, "coherence": 1, "color": "black", "opacity": 0.5
        }
        objCircle = visual.DotStim(
            fieldShape='circle', **params
        )
        objRect = visual.DotStim(
            fieldShape='sqr', **params
        )
        # Create reference objects for maximum size
        maxCircle = visual.Circle(self.win, fillColor="white")
        maxRect = visual.Rect(self.win, fillColor="white")
        # Create reference objects for minimum size
        minCircle = visual.Circle(self.win, fillColor="blue")
        minRect = visual.Rect(self.win, fillColor="blue")
        # Set window background and store original
        ogColor = self.win.color
        self.win.color = "red"
        # Draw a frame of each case
        for case in cases:
            self.win.flip()
            # Set params of dots
            objCircle.units = objRect.units = case['units']
            objCircle.fieldSize = objRect.fieldSize = case['size']
            # Set params of guides
            maxCircle.units = maxRect.units = minCircle.units = minRect.units = case['units']
            maxCircle.size = maxRect.size = case['size'] * (1 + err)
            minCircle.size = minRect.size = case['size'] * (1 - err)
            # Test circle dots
            maxCircle.draw()
            minCircle.draw()
            objCircle.draw()
            _findColors(self.win)
            self.win.flip()
            # Test square dots
            maxRect.draw()
            minRect.draw()
            objRect.draw()
            _findColors(self.win)
            self.win.flip()
        # Restore window color
        self.win.color = ogColor

    def test_movement(self):
        # Window needs to be black so that adding 2 screens doesn't make a white screen
        self.win.color = "black"
        self.win.flip()
        # Create dots
        obj = visual.DotStim(
            self.win, nDots=1,
            fieldPos=(0, 0), fieldSize=(1, 1), units="height",
            dotSize=(32, 32), dotLife=0, noiseDots='direction',
            dir=0, speed=0.25, coherence=1
        )
        # Draw dots
        obj.draw()
        # Get screenshot 1
        screen1 = np.array(self.win._getFrame(buffer="back"))
        self.win.flip()
        # Draw again, triggering position update
        obj.draw()
        # Get screenshot 2
        screen2 = np.array(self.win._getFrame(buffer="back"))
        self.win.flip()
        # Create compound screenshot with a dot in BOTH positions
        compound = np.clip(screen1 + screen2, 0, 255)
        # If dots have moved, then there should be more white on the compound screen than on either original
        assert compound.mean() > screen1.mean() and compound.mean() > screen2.mean(), (
            "Dot stimulus does not appear to have moved across two frames."
        )