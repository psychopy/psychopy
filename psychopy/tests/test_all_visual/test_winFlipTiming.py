

import sys
from psychopy import visual, clock
import pytest
import numpy as np

try:
    from psychtoolbox import GetSecs
    havePTB = True
except ImportError:
    havePTB = False

class Test_WinFlipTiming():
    def setup_class(self):
        self.win = visual.Window(size=(200, 200), units='pix',
                                 allowGUI=False, autoLog=False,
                                 waitBlanking=True)
        self.rate = self.win.getActualFrameRate()

        if self.rate and 40<self.rate<160:
            self.testOutputs = True
        else:
            self.testOutputs = False

    def teardown_class(self):
        self.win.close()

    def _runSeriesOfFlips(self, usePTB):
        if usePTB:
            getTime = GetSecs
            clk = 'ptb'
        else:
            getTime = clock.monotonicClock.getTime
            clk = clock.monotonicClock

        self.win.flip()
        now = clock.monotonicClock.getTime()
        next = self.win.getFutureFlipTime(clock=clk)
        self.win.flip()

        errsNext = []
        # check nextFrame against reality for 10 frames
        for frameN in range(10):
            self.win.flip()
            this = getTime()
            # print('this', this)
            # print('err', next-this)
            errsNext.append(next-this)
            #then update next
            next = self.win.getFutureFlipTime(clock=clk)
            # print('next', next)
        return errsNext

    def test_winFutureFlip(self):
        """test window.viewScale and .viewPos simultaneous
        negative-going scale should mirror-reverse, and position should
        account for that visually, the green square/rect should move clockwise
        around the text

        Non-zero viewOri would not currently pass with a nonzero viewPos
        """
        self.win.flip()
        now = clock.monotonicClock.getTime()
        next = self.win._frameTimes[-1] + self.win.monitorFramePeriod

        errs = self._runSeriesOfFlips(usePTB=False)
        print()
        print('getFutureFlipTime(0): mean={:.6f}, std={:6f}, all={}'
              .format(np.mean(errs), np.std(errs), errs))
        if self.testOutputs:
            assert np.mean(errs)<0.005  # checks for any systematic bias

        if havePTB:
            errs = self._runSeriesOfFlips(usePTB=True)
            print('PTB getFutureFlipTime(0): mean={:.6f}, std={:6f}, all={}'
                  .format(np.mean(errs), np.std(errs), errs))
            if self.testOutputs:
                assert np.mean(errs)<0.005  # checks for any systematic bias

        now = clock.monotonicClock.getTime()
        predictedFrames = []
        print('now={:.5f}, lastFrame={:.5f}'.format(now, self.win._frameTimes[-1]))
        print('delay requestT expectT diff'.format(now, self.win._frameTimes[-1]))
        for requested in np.arange(0, 0.04, 0.001):
            expect = self.win.getFutureFlipTime(requested)
            diff = expect-(now+requested)
            print("{:.4f}, {:.5f} {:.5f} {:.5f}".format(requested, requested, expect, diff))
            # should always be within 1/2 frame
        if self.testOutputs and sys.platform != 'darwin':
            assert abs(diff) < self.win.monitorFramePeriod/2.0


if __name__ == "__main__":
    pytest.main(__file__)
