from psychopy.constants import STARTED, NOT_STARTED, PAUSED, STOPPED, FINISHED
from psychopy.alerts import alert


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


class EyetrackerCalibration:
    def __init__(self, win,
                 eyetracker, target,
                 pacingSpeed="", autoPace=True,
                 targetLayout="NINE_POINTS", randomisePos=True,
                 enableAnimation=False, velocity=0.5, expandScale=3, expandDur=0.75
                 ):
        # Store params
        self.win = win
        self.eyetracker = eyetracker
        self.target = target
        self.pacingSpeed = pacingSpeed
        self.autoPace = autoPace
        self.targetLayout = targetLayout
        self.randomisePos = randomisePos
        self.enableAnimation = enableAnimation
        self.velocity = velocity
        self.expandScale = expandScale
        self.expandDur = expandDur

    def run(self):
        tracker = self.eyetracker.getIOHubDeviceClass(full=True)

        if tracker == 'eyetracker.hw.sr_research.eyelink.EyeTracker':
            # Run as eyelink
            if self.enableAnimation:
                alert() # todo: make alert for animation params when not needed

            # As EyeLink doesn't allow custom layouts, if given one, estimate
            targetLayout = self.targetLayout
            if targetLayout not in ['THREE_POINTS', 'FIVE_POINTS', 'NINE_POINTS', "THIRTEEN_POINTS"]:
                alert()  # todo: make alert for when custom positions are simplified
                if len(targetLayout) <= 4:
                    targetLayout = "THREE_POINTS"
                elif len(targetLayout) <= 7:
                    targetLayout = "FIVE_POINTS"
                elif len(targetLayout) <= 11:
                    targetLayout = "NINE_POINTS"
                else:
                    targetLayout = "THIRTEEN_POINTS"
            # Make params dict
            self.eyetracker.runSetupProcedure({
                'target_attributes': self.target.getCalibSettings('SR Research Ltd'),
                'type': targetLayout,
                'auto_pace': self.autoPace,
                'pacing_speed': self.pacingSpeed or 1.5,
                'screen_background_color': self.win.color
            })

        elif tracker == 'eyetracker.hw.tobii.EyeTracker':

            # As Tobii doesn't allow custom layouts, if given one, estimate
            targetLayout = self.targetLayout
            if targetLayout not in ['THREE_POINTS', 'FIVE_POINTS', 'NINE_POINTS']:
                alert() # todo: make alert for when custom positions are simplified
                if len(targetLayout) <= 4:
                    targetLayout = "THREE_POINTS"
                elif len(targetLayout) <= 7:
                    targetLayout = "FIVE_POINTS"
                else:
                    targetLayout = "NINE_POINTS"

            # Run as tobii
            self.eyetracker.runSetupProcedure({
                'target_attributes': self.target.getCalibSettings('Tobii Technology'),
                'type': self.targetLayout,
                'randomize': self.randomisePos,
                'auto_pace': self.autoPace,
                'pacing_speed': self.pacingSpeed or 1,
                'screen_background_color': self.win.color,
                'animate': {
                    'enable': self.enableAnimation,
                    'movement_velocity': self.velocity,
                    'expansion_ratio': self.expandScale,
                    'expansion_speed': self.expandDur
                }
            })

        elif tracker == 'eyetracker.hw.gazepoint.gp3.EyeTracker':
            # Run as gazepoint
            if self.enableAnimation:
                alert()  # todo: make alert for animation params when not needed

            self.eyetracker.runSetupProcedure({
                'target_delay': self.velocity if self.enableAnimation else 0.5,
                'target_duration': self.pacingSpeed or 1.5
            })

        else:
            self.eyetracker.runSetupProcedure({})
