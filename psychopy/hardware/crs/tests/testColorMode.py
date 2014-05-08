
from psychopy import visual, core
from pycrsltd import bits

def colorModePsychoPy():
    """ tTest using visual.Window([400,400], bitsMode='color++') """
    win = visual.Window([400,400], screen=1, bitsMode='color++', useFBO=True)
    stim = visual.PatchStim(win, ori=45,mask='gauss')
    stim.draw()
    win.flip()
    core.wait(2.0)
if __name__ == "__main__":
    colorModePsychoPy()
    print 'done'