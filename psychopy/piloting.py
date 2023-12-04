from psychopy import logging

# global variable used throughout PsychoPy to tell whether we're in pilot mode
PILOTING = False


def setPilotMode(mode):
    """
    Set pilot mode to be True or False to enable/disable piloting features.

    Parameters
    ----------
    mode : bool
        True for piloting, False otherwise.
    """
    global PILOTING
    # set mode
    PILOTING = bool(mode)
    # log change
    logging.exp(
        "Running in pilot mode."
    )


def getPilotMode():
    """
    Get the current state of pilot mode.

    Returns
    -------
    bool
        True for piloting, False otherwise.
    """
    global PILOTING

    return PILOTING


def setPilotModeFromArgs():
    """
    Set pilot mode according to the arguments passed to whatever script invoked PsychoPy.

    Returns
    -------
    bool
        True for piloting, False otherwise.
    """
    import argparse
    global PILOTING
    # make argument parser
    parser = argparse.ArgumentParser()
    # define pilot arg and abbreviation
    parser.add_argument('--pilot', action='store_true', dest='pilot')
    parser.add_argument('--d', action='store_true', dest='pilot')
    # set mode
    setPilotMode(
        parser.parse_args().pilot
    )

    return getPilotMode()
