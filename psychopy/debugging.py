from psychopy import logging

# global variable used throughout PsychoPy to tell whether we're in debug mode
debugMode = False


def setDebugMode(mode):
    """
    Set debug mode to be True or False to enable/disable debugging features.

    Parameters
    ----------
    mode : bool
        True for debugging, False otherwise.
    """
    global debugMode
    # set mode
    debugMode = bool(mode)
    # log change
    logging.exp(
        "Running in debug mode."
    )


def getDebugMode():
    """
    Get the current state of debug mode.

    Returns
    -------
    bool
        True for debugging, False otherwise.
    """
    global debugMode

    return debugMode


def setDebugModeFromArgs():
    """
    Set debug mode according to the arguments passed to whatever script invoked PsychoPy.

    Returns
    -------
    bool
        True for debugging, False otherwise.
    """
    import argparse
    global debugMode
    # make argument parser
    parser = argparse.ArgumentParser()
    # define debug arg and abbreviation
    parser.add_argument('--debug', action='store_true', dest='debug')
    parser.add_argument('--d', action='store_true', dest='debug')
    # set mode
    setDebugMode(
        parser.parse_args().debug
    )

    return getDebugMode()
