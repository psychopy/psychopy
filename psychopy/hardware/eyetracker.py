from psychopy.constants import STARTED, NOT_STARTED, PAUSED, STOPPED, FINISHED
from psychopy.alerts import alert
from copy import copy
import sys

class EyetrackerControl:
    def __init__(self, server, tracker=None):
        if tracker is None:
            tracker = server.getDevice('tracker')
        self.server = server
        self.tracker = tracker
        self._status = NOT_STARTED

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        old = self._status
        new = self._status = value
        # Skip if there's no change
        if new == old:
            return
        # Start recording if set to STARTED
        if new in (STARTED,):
            if old in (NOT_STARTED, STOPPED, FINISHED):
                # If was previously at a full stop, clear events before starting again
                self.server.clearEvents()
            # Start recording
            self.tracker.setRecordingState(True)
        # Stop recording if set to any stop constants
        if new in (NOT_STARTED, PAUSED, STOPPED, FINISHED):
            self.tracker.setRecordingState(False)

    @property
    def pos(self):
        return self.tracker.getPosition()

    def getPos(self):
        return self.pos


class EyetrackerCalibration:
    def __init__(self, win,
                 eyetracker, target,
                 units="height", colorSpace="rgb",
                 progressMode="time", targetDur=1.5, expandScale=1.5,
                 targetLayout="NINE_POINTS", randomisePos=True,
                 movementAnimation=False, targetDelay=1.0
                 ):
        # Store params
        self.win = win
        self.eyetracker = eyetracker
        self.target = target
        self.progressMode = progressMode
        self.targetLayout = targetLayout
        self.randomisePos = randomisePos
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

        # Make sure that target will use the same color space and units as calibration
        if self.target.colorSpace == self.colorSpace and self.target.units == self.units:
            target = self.target
        else:
            target = copy(self.target)
            target.colorSpace = self.colorSpace
            target.units = self.units
        # Get self as dict
        asDict = {}
        if tracker == 'eyetracker.hw.sr_research.eyelink.EyeTracker':
            # As EyeLink
            asDict = {
                'target_attributes': dict(target),
                'type': self.targetLayout,
                'auto_pace': self.progressMode == "time",
                'pacing_speed': self.targetDelay,
                'screen_background_color': getattr(self.win._color, self.colorSpace)
            }
        elif tracker == 'eyetracker.hw.tobii.EyeTracker':
            # calibration:
            #     type: NINE_POINTS
            #     color_type:
            #     unit_type:
            #     randomize: True
            #     auto_pace: True
            #     target_duration: 1.5
            #     target_delay: 0.75
            #
            #     # **pacing_speed is deprecated. Please use 'target_delay' instead.**
            #     pacing_speed:
            #     screen_background_color: [128, 128, 128]
            #     target_attributes:
            #         outer_diameter: 35.0
            #         outer_stroke_width: 2.0
            #         outer_fill_color: [128, 128, 128]
            #         outer_line_color: [255, 255, 255]
            #         inner_diameter: 7.0
            #         inner_stroke_width: 1.0
            #         inner_fill_color: [0, 0, 0]
            #         inner_line_color: [0, 0, 0]
            #         animate:
            #             enable: True
            #             expansion_ratio: 3.0
            #             contract_only: True
            #             # ** movement_velocity: Deprecated, please use target_delay instead. **
            #             #
            #             movement_velocity:
            #             # ** expansion_speed: Deprecated, target_duration is now used. **
            #             #
            #             expansion_speed:

            # As Tobii
            targetAttrs = dict(target)
            targetAttrs['animate'] = {
                'enable': self.movementAnimation,
                'expansion_ratio': self.expandScale,
                #'expansion_speed': self.targetDur,
                'contract_only': self.expandScale == 1
            }
            asDict = {
                'target_attributes': targetAttrs,
                'type': self.targetLayout,
                'randomize': self.randomisePos,
                'auto_pace': self.progressMode == "time",
                #'pacing_speed': self.targetDelay,
                'target_delay': self.targetDelay,
                'target_duration': self.targetDur,
                'unit_type': self.units,
                'color_type': self.colorSpace,
                'screen_background_color': getattr(self.win._color, self.colorSpace),
            }
        elif tracker == 'eyetracker.hw.gazepoint.gp3.EyeTracker':
            # As GazePoint
            targetAttrs = dict(target)
            targetAttrs['animate'] = {
                'enable': self.movementAnimation,
                'expansion_ratio': self.expandScale,
                'contract_only': self.expandScale == 1
            }
            asDict = {
                'use_builtin': False,
                'target_delay': self.targetDelay,
                'target_duration': self.targetDur,
                'target_attributes': targetAttrs,
                'type': self.targetLayout,
                'randomize': self.randomisePos,
                'unit_type': self.units,
                'color_type': self.colorSpace,
                'screen_background_color': getattr(self.win._color, self.colorSpace),
            }

        elif tracker == 'eyetracker.hw.mouse.EyeTracker':
            # As MouseGaze
            targetAttrs = dict(target)
            targetAttrs['animate'] = {
                'enable': self.movementAnimation,
                'expansion_ratio': self.expandScale,
                'contract_only': self.expandScale == 1
            }
            # Run as MouseGaze
            asDict = {
                'target_attributes': targetAttrs,
                'type': self.targetLayout,
                'randomize': self.randomisePos,
                'auto_pace': self.progressMode == "time",
                'pacing_speed': self.targetDelay,
                'unit_type': self.units,
                'color_type': self.colorSpace,
                'screen_background_color': getattr(self.win._color, self.colorSpace),
            }
        # Return
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
