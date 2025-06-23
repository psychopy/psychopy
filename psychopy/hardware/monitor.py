import time
from psychopy.hardware.base import BaseDevice
import pyglet.canvas
import numpy as np

from psychopy.localization import _translate
from psychopy.monitors.calibTools import Monitor, DACrange, GammaCalculator


class MonitorDevice(BaseDevice, Monitor):
    """
    A computer monitor (or laptop screen)

    Parameters
    ----------
    index : int
        Numeric index of the monitor, starting at 1
    pos : tuple[int, int], optional
        Pixel position of top left corner of the monitor relative to the full display (top-leftmost 
        point to bottom-rightmost point of all monitors)
    size : tuple[int, int], optional
        Pixel size of the monitor
    frameRate : int, optional
        Number of frame flips per second
    width : float, optional
        Physical width (cm) of the monitor, for calculating positions in cm units
    distance : float, optional
        Distance (cm) between the monitor and the participant, for calculating positions in degrees 
        of visual angle
    gamma : int or numpy.ndarray, optional
        Gamma calibration of this monitor
    """
    
    def __init__(
            self,
            index,
            pos=None,
            size=None,
            frameRate=None,
            width=None,
            distance=None,
            gamma=None,
            otherCalib=None
        ):
        BaseDevice.__init__(self)
        Monitor.__init__(
            self,
            f"Screen {index}",
            width=width,
            distance=distance,
            gamma=gamma,
            currentCalib=otherCalib
        )
        self.setSizePix(size)
        # set attributes not already handled by Monitor
        self.index = index
        self.pos = pos
        self.frameRate = frameRate
    
    @property
    def pyglet(self):
        """
        Returns
        -------
        pyglet.canvas.Screen
            The pyglet object corresponding to this monitor
        """
        if not hasattr(self, "_pyglet"):
            # get all screens
            screens = pyglet.canvas.Display().get_screens()
            # convert index to from-zero with looping
            i = (self.index - 1) % len(screens)
            # store pyglet screen
            self._pyglet = screens[i]
        
        return self._pyglet

    def calibrateGamma(self, win, photometer, patchSize=0.3, nPoints=8):
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
        from psychopy.hardware import DeviceManager, keyboard
        from psychopy import visual
        # get photometer device
        phot = DeviceManager.getDevice(photometer)
        # error if there isn't one
        if phot is None:
            raise ConnectionError(
                "No photometer found. Try setting one up in the device manager."
            )
        # create a patch
        patch = visual.Rect(
            win,
            size=(patchSize, patchSize),
            fillColor=self.getGamma(),
            colorSpace="rgb255",
            units="norm"
        )
        # create instructions
        instr = visual.TextBox2(
            win,
            text=(
                "Point the photometer at the central box and press SPACE (or wait 2s) to "
                "take a reading. Press ESCAPE to quit."
            ),
            size=(2, 0.5),
            pos=(0, 1),
            padding=0.05,
            anchor="top center",
            letterHeight=0.1
        )
        # create progress
        gunProg = visual.Progress(
            win, 
            pos=(-1, -0.8), 
            size=(2, 0.2), 
            anchor="bottom-left", 
            units="norm"
        )
        lvlProg = visual.Progress(
            win, 
            pos=(-1, -1), 
            size=(2, 0.2), 
            anchor="bottom-left", 
            units="norm"
        )
        # get keyboard
        kb = keyboard.Keyboard()
        # this will hold the measured luminance values
        lumSeries = np.zeros((4, nPoints), 'd')
        # iterate through levels
        for lvl, dac in enumerate(DACrange(nPoints)):
            # update progress indicator
            lvlProg.progress = (lvl + 1) / nPoints
            # iterate through guns per level
            for gun in range(4):
                # update progress indicator
                gunProg.progress = (gun + 1) / 4
                # set the patch color
                if gun == 0:
                    # if gun is 0 (aka luminance), set as flat
                    patch.fillColor = dac
                else:
                    # otherwise, set just the relevant gun and leave the rest black
                    patch.fillColor = [
                        dac if i == gun-1 else -1
                        for i in range(3)
                    ]
                # draw
                patch.draw()
                instr.draw()
                lvlProg.draw()
                gunProg.draw()
                win.flip()
                # allow the screen to settle
                time.sleep(0.2)
                # listen for keypress or 2s
                keys = kb.waitKeys(keyList=["escape", "space"], maxWait=2)
                # abort if requested
                if keys and "escape" in keys:
                    return
                # take reading
                lum = phot.getLum()
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
    
    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical device as a given other object.

        Parameters
        ----------
        other : BaseDevice, dict
            Other device object to compare against, or a dict of params.

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        # compare against another MonitorDevice
        if isinstance(other, MonitorDevice):
            return other.index == self.index
        # compare against index
        if isinstance(other, int):
            return other == self.index
        # compare against device profile
        if isinstance(other, dict) and "index" in other:
            return other['index']
        
        return False

    @staticmethod
    def getAvailableDevices():
        """
        Get all available devices of this type.

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise each device.
        """
        output = []
        # iterate through pyglet screens
        for i, screen in enumerate(pyglet.canvas.Display().get_screens()):
            # get ScreenMode object
            mode = screen.get_mode()
            # construct profile
            output.append({
                'deviceName': f"Screen {i+1} ({screen.width}x{screen.height}px)",
                'deviceClass': "psychopy.hardware.monitor.MonitorDevice",
                'index': i+1,
                'pos': (screen.x, screen.y),
                'size': (screen.width, screen.height),
                'frameRate': mode.rate
            })

        return output