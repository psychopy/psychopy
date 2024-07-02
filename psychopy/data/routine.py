from psychopy import constants

class Routine:
    """
    Object representing a Routine, used to store start/stop times and other aspects of Routine settings.

    Parameters
    ----------
    name : str
        Name of the Routine
    components : list[object]
        List of handles to Components associated with this Routine
    maxDuration : float or None
        Maximum time this Routine can take. None if there is no maximum.
    
    Attributes
    ----------
    tStart : float or None
        Time (UTC) when this Routine started
    tStartRefresh : float or None
        Time (UTC) of the first frame flip of this Routine
    tStop : float or None
        Time (UTC) when this Routine ended
    tStopRefresh : float or None
        Time (UTC) of the last frame flip of this Routine
    maxDurationReached : bool
        True if this Routine ended by its max duration being reached
    skipped : bool
        True if this Routine was skipped by the "Skip if..." parameter of its settings
    forceEnded : bool
        True if this Routine was forcibly ended (e.g. by a key press)
    status : int
        Value from psychopy.constants.status indicating whether this Routine has started, is finished, etc.
    """
    def __init__(
        self,
        name,
        components=[],
        maxDuration=None,
    ):
        self.name = name
        self.components = components
        self.maxDuration = maxDuration
        # start all times as None
        self.tStart = None
        self.tStartRefresh = None
        self.tStop = None
        self.tStopRefresh = None
        # start off assuming not skipped, timed out or force ended
        self.maxDurationReached = False
        self.skipped = False
        self.forceEnded = False
        # starting status
        self.status = constants.NOT_STARTED
    
    