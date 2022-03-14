import numpy as np
from psychopy import visual


class TestDots:

    @classmethod
    def setup(self):
        self.win = visual.Window([128, 128], pos=[50,50], allowGUI=False, autoLog=False)

    def test_movement(self):
        obj = visual.DotStim(
            self.win, nDots=1,
            fieldPos=(0, 0), fieldSize=(1, 1), units="height",
            dotSize=(32, 32), dotLife=0, noiseDots='direction',
            dir=0, speed=0.25, coherence=1
        )
        # Draw dots
        obj.draw()
        self.win.flip()
        # Get screenshot 1
        screen1 = np.array(self.win.screenshot)
        # Draw again, triggering position update
        obj.draw()
        self.win.flip()
        # Get screenshot 2
        screen2 = np.array(self.win.screenshot)
        # Create compound screenshot with a dot in BOTH positions
        compound = np.clip(screen1 + screen2, 0, 255)
        # If dots have moved, then there should be more white on the compound screen than on either original
        assert compound.mean() > screen1.mean() and compound.mean() > screen2.mean(), (
            "Dot stimulus does not appear to have moved across two frames."
        )