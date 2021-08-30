
from psychopy import visual
from psychopy.tests import utils
import os
import pytest

v = [(1, 1), (1, -1), (-1, -1), (-1, 1)]  # vertices to use = square
n = 15  # size of the base square
pimg = (n, n)  # position for the image
pgrn = (-n, -n)  # position for green square
img_name = os.path.join(utils.TESTS_DATA_PATH, 'filltext.png')


class Test_Win_Scale_Pos_Ori:
    def setup_class(self):
        self.win = visual.Window(size=(200, 200), units='pix',
                                 allowGUI=False, autoLog=False)

    def teardown_class(self):
        self.win.close()

    @pytest.mark.scalepos
    def test_winScalePosOri(self):
        """test window.viewScale and .viewPos simultaneous
        negative-going scale should mirror-reverse, and position should
        account for that visually, the green square/rect should move clockwise
        around the text

        Non-zero viewOri would not currently pass with a nonzero viewPos
        """
        with pytest.raises(ValueError):
            # units must be define for viewPos!
            _, = visual.Window(size=(200, 200), viewPos=(1, 1), viewOri=1)
        with pytest.raises(NotImplementedError):
            # simultaneous viewPos and viewOri prohibited at present
            _, = visual.Window(size=(200, 200), units='pix',
                               viewPos=(1, 1), viewOri=1)

        for ori in [0, 45]:
            self.win.viewOri = ori
            for offset in [(0, 0), (-0.4, 0)]:
                if ori and (offset[0] or offset[1]):
                    continue  # this combination is NotImplemented
                else:  # NB assumes test win is in pixels!
                    # convert from normalised offset to pixels
                    offset_pix = (round(offs * siz / 2.) for offs, siz in
                                  zip(offset, self.win.size))

                    self.win.viewPos = offset_pix

                for scale in [[1, 1],  # normal: green at lower left
                              [1, -1],  # mirror vert only: green appears to
                                        # move up, text mirrored
                              [-1, -1],  # mirror horiz & vert: green appears
                                         # to move right, text normal but
                                         # upside down
                              [-1, 1],  # mirror horiz only: green appears to
                                        # move down, text mirrored
                              [2, 2],  # same, but both larger
                              [2, -2],
                              [-2, -2],
                              [-2, 2]]:
                    self.win.viewScale = scale
                    self.win.flip()
                    grn = visual.ShapeStim(self.win, vertices=v, pos=pgrn,
                                           size=n, fillColor='darkgreen')
                    img = visual.ImageStim(self.win, image=img_name, size=2*n,
                                           pos=pimg)
                    grn.draw()
                    img.draw()

                    oristr = str(ori)
                    scalestr = str(scale[0]) + '_' + str(scale[1])
                    posstr = str(offset[0]) + '_' + str(offset[1])
                    filename = 'winScalePos_ori%s_scale%s_pos%s.png' % \
                        (oristr, scalestr, posstr)
                    utils.compareScreenshot(filename, self.win, crit=15)
