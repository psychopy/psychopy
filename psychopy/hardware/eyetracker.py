from psychopy.constants import STARTED, NOT_STARTED, PAUSED, STOPPED, FINISHED
from psychopy.alerts import alert
from psychopy import logging
from psychopy.iohub.devices import importDeviceModule
from psychopy.tools.attributetools import AttributeGetSetMixin
from copy import copy
import importlib
import sys


class EyetrackerControl(AttributeGetSetMixin):
    currentlyRecording = False

    def __init__(self, tracker, actionType="Start and Stop"):
        self.tracker = tracker
        self.actionType = actionType
        self.status = NOT_STARTED
    
    def start(self):
        """
        Start recording
        """
        # if previously at a full stop, clear events
        if not EyetrackerControl.currentlyRecording:
            logging.exp("eyetracker.clearEvents()")
            self.tracker.clearEvents()
        # start recording
        self.tracker.setRecordingState(True)
        logging.exp("eyetracker.setRecordingState(True)")
        EyetrackerControl.currentlyRecording = True
    
    def stop(self):
        """
        Stop recording
        """
        self.tracker.setRecordingState(False)
        logging.exp("eyetracker.setRecordingState(False)")
        EyetrackerControl.currentlyRecording = False

    @property
    def pos(self):
        """
        Get the current position of the eyetracker
        """
        return self.tracker.getPos()

    def getPos(self):
        return self.pos


class EyetrackerCalibration:
    def __init__(self, win,
                 eyetracker, target,
                 units="height", colorSpace="rgb",
                 progressMode="time", targetDur=1.5, expandScale=1.5,
                 targetLayout="NINE_POINTS", randomisePos=True,
                 movementAnimation=False, targetDelay=1.0, textColor='Auto'
                 ):
        # Store params
        self.win = win
        self.eyetracker = eyetracker
        self.target = target
        self.progressMode = progressMode
        self.targetLayout = targetLayout
        self.randomisePos = randomisePos
        self.textColor = textColor
        self.units = units or self.win.units
        self.colorSpace = colorSpace or self.win.colorSpace
        # Animation
        self.movementAnimation = movementAnimation
        self.targetDelay = targetDelay
        self.targetDur = targetDur
        self.expandScale = expandScale
        # Attribute to store data from last run
        self.last = None

    def __iter__(self):
        """Overload dict() method to return in ioHub format"""
        tracker = self.eyetracker.getIOHubDeviceClass(full=True)
        # split into package and class name
        pkgName = ".".join(tracker.split(".")[:-1])
        clsName = tracker.split(".")[-1]
        # make sure pkgName is fully qualified
        if not pkgName.startswith("psychopy.iohub.devices."):
            pkgName = "psychopy.iohub.devices." + pkgName
        # import package
        pkg = importDeviceModule(pkgName)
        # get tracker class
        trackerCls = getattr(pkg, clsName)
        # get self as dict
        asDict = trackerCls.getCalibrationDict(self)
        
        # return
        for key, value in asDict.items():
            yield key, value

    def run(self):
        tracker = self.eyetracker.getIOHubDeviceClass(full=True)

        # Deliver any alerts as needed
        if tracker == 'eyetracker.hw.sr_research.eyelink.EyeTracker':
            if self.movementAnimation:
                # Alert user that their animation params aren't used
                alert(code=4520, strFields={"brand": "EyeLink"})

        elif tracker == 'eyetracker.hw.gazepoint.gp3.EyeTracker':
            if not self.progressMode == "time":
                # As GazePoint doesn't use auto-pace, alert user
                alert(4530, strFields={"brand": "GazePoint"})

        # Minimise PsychoPy window
        if self.win._isFullScr and sys.platform == 'win32':
            self.win.winHandle.set_fullscreen(False)
            self.win.winHandle.minimize()

        # Run
        self.last = self.eyetracker.runSetupProcedure(dict(self))

        # Bring back PsychoPy window
        if self.win._isFullScr and sys.platform == 'win32':
            self.win.winHandle.set_fullscreen(True)
            self.win.winHandle.maximize()
            # Not 100% sure activate is necessary, but does not seem to hurt.
            self.win.winHandle.activate()

        # SS: Flip otherwise black screen has been seen, not sure why this just started....
        self.win.flip()
