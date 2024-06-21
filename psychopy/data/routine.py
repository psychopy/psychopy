from psychopy import constants

class Routine:
    """
    Object representing a Routine, used to store start/stop times and other aspects of Routine settings.
    """
    def __init__(
        self,
        name,
        components=[]
    ):
        self.name = name
        self.components = components
        # start all times as None
        self.tStart = None
        self.tStartRefresh = None
        self.tStop = None
        self.tStopRefresh = None
        # start off assuming not skipped or force ended
        self.skipped = False
        self.forceEnded = False
        # starting status
        self.status = constants.NOT_STARTED
    
    