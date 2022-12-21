from psychopy import visual
from .. import utils
from pathlib import Path


class TestPanorama:
    def setup_class(cls):
        cls.path = Path(utils.TESTS_DATA_PATH) / "test_panorama"
        cls.win = visual.Window(monitor="testMonitor")
        cls.obj = visual.PanoramicImageStim(cls.win, image=cls.path / "panoramaTestImage.png")

    def test_movement(self):
        cases = []
        # Try different azimuths & elevations
        intervals = 3
        for az in range(intervals):
            for al in range(intervals - 1):
                cases.append({
                    'azimuth': (az * 2) / intervals - 1,
                    'altitude': ((al + 1) * 2) / intervals - 1,
                })
        # Add tests for extreme altitude
        cases += [
            {'azimuth': 0, 'altitude': -1},  # Min altitude, should be dark colours
            {'azimuth': 0, 'altitude': 1},  # Max altitude, should be light colours
        ]

        self.win.flip()
        for case in cases:
            # Set azimuth and elevation
            self.obj.azimuth = case['azimuth']
            self.obj.altitude = case['altitude']
            # Draw
            self.obj.draw()
            # Construct file path to check against
            exemplar = self.path / "testPanorama_mvmt_{azimuth:.1f}_{altitude:.1f}.png".format(**case)
            # Compare
            #self.win.getMovieFrame(buffer='back').save(exemplar)
            utils.compareScreenshot(str(exemplar), self.win, crit=7)
            # Flip
            self.win.flip()
