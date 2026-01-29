from psychopy.monitors import Monitor, DACrange, GammaCalculator
from psychopy.hardware import DeviceManager, keyboard
import numpy as np
import time

__all__ = [
    "Monitor",
    "calibrateGamma"
]


def calibrateGamma(
        win, 
        photometer, 
        patchSize=0.3, 
        nPoints=8
    ):
    """
    Use a photometer to calibrate the gamma for this monitor.

    Parameters
    ----------
    win : psychopy.visual.Window
        Window to run calibration in
    photometer : str
        Name of a photometer setup already in device manager
    patchSize : float, optional
        Size of the calibration patch as a proportion of the screen size (0-1), by default 0.3
    nPoints : int, optional
        Number of calibration points to use, by default 8
    """
    from psychopy import visual
    from psychopy.hardware.photometer import BasePhotometerDevice

    # get photometer device (if not given one)
    if isinstance(photometer, BasePhotometerDevice):
        phot = photometer
    else:
        phot = DeviceManager.getDevice(photometer)
    # error if there isn't one
    if phot is None:
        raise ConnectionError(
            "No photometer found. Try setting one up in the device manager."
        )
    # make sure nPoints is an integer
    nPoints = int(nPoints)
    # create a patch
    patch = visual.GratingStim(
        win,
        tex="sqr",
        size=(patchSize*2, patchSize*2),
        units="norm",
        rgb=(255, 255, 255),
        colorSpace="rgb255",
    )
    # create instructions
    instr = visual.TextBox2(
        win,
        text=(
            "Point the photometer at the central box and press SPACE (or wait 2s) to "
            "take a reading. Press ESCAPE to cancel."
        ),
        size=(2, 0.5),
        pos=(0, 1),
        padding=0.05,
        anchor="top center",
        alignment="top center",
        letterHeight=0.05
    )
    # create progress indicator
    prog = visual.TextBox2(
        win,
        text="Waiting for keypress...",
        size=(1, 0.2),
        pos=(-1, -1),
        padding=0.05,
        anchor="bottom left",
        alignment="bottom left",
        letterHeight=0.05
    )
    # do initial draw
    win.flip()
    patch.draw()
    instr.draw()
    prog.draw()
    win.flip()
    # this will hold the measured luminance values
    lumSeries = np.zeros((4, nPoints), 'd')
    # listen for keypress or 30s
    kb = keyboard.Keyboard()
    keys = kb.waitKeys(keyList=["escape", "space"], maxWait=30)
    # abort if requested
    if keys and "escape" in keys:
        return
    # clear instructions & update current action once responded
    instr.text = ""
    # iterate through levels
    for lvl, dac in enumerate(DACrange(nPoints)):
        # get relevant guns
        if lvl == 0:
            # guns are irrelevant when intensity is 0
            guns = [None]
        else:
            guns = range(4)
        # iterate through guns per level
        for gun in guns:
            # update progress indicator
            prog.text = f"Level {lvl+1}/{nPoints}  Gun {gun+1 if gun is not None else 'NA'}/4"
            # set the patch color
            if gun in (0, None):
                # if gun is 0 (aka luminance), set as flat
                patch.color = dac
            else:
                # otherwise, set just the relevant gun and leave the rest black
                patch.color = [
                    dac if i == gun-1 else -1
                    for i in range(3)
                ]
            # draw all & flip
            patch.draw()
            prog.draw()
            win.flip()
            # allow the screen to settle
            time.sleep(0.2)
            # take reading
            lum = phot.getLum()
            # if no gun, set for all
            if gun is None:
                for thisGun in range(4):
                    lumSeries[thisGun, lvl] = lum
            else:
                lumSeries[gun, lvl] = lum
    # transform lum series to a gamma grid
    gammaGrid = []
    for lumRow in lumSeries:
        calc = GammaCalculator(
            inputs=DACrange(nPoints),
            lums=lumRow
        )
        gammaGrid.append(
            [calc.min, calc.max, calc.gammaModel[0]]
        )

    return gammaGrid
