from psychopy.tests import utils
from psychopy.tools import animationtools as at
import numpy as np


def testSinusoidalFuncs():
    cases = (
        # max/min sizes
        {'startSize': 0, 'apexSize': 1, 'duration': 1, 'time': 1, 'ans': 1},
        {'startSize': 0, 'apexSize': 1, 'duration': 1, 'time': 0, 'ans': 0},
        # arrays
        {'startSize': (0, 1), 'apexSize': (1, 0), 'duration': 1, 'time': 0, 'ans': (0, 1)},
        {'startSize': (0, 1), 'apexSize': (1, 0), 'duration': 1, 'time': 1, 'ans': (1, 0)},
        # midpoints
        {'startSize': 0, 'apexSize': 1, 'duration': 1, 'time': 0.5, 'ans': 0.5},
        {'startSize': 1, 'apexSize': 0, 'duration': 1, 'time': 0.5, 'ans': 0.5},
        # intermediate points
        {'startSize': 0, 'apexSize': 1, 'duration': 1, 'time': 1/3, 'ans': 0.25},
        {'startSize': 0, 'apexSize': 1, 'duration': 1, 'time': 2/3, 'ans': 0.75},
        {'startSize': 1, 'apexSize': 0, 'duration': 1, 'time': 1/3, 'ans': 0.75},
        {'startSize': 1, 'apexSize': 0, 'duration': 1, 'time': 2/3, 'ans': 0.25},
    )

    for case in cases:
        # apply parameters from case dict to function
        ans = at.sinusoidalGrowth(
            startSize=case['startSize'],
            apexSize=case['apexSize'],
            duration=case['duration'],
            time=case['time']
        )
        ans = np.round(ans, decimals=3)
        # verify answer
        assert utils.forceBool(ans == case['ans'], handler=all), (
            f"Params: startSize=%(startSize)s, apexSize=%(apexSize)s, duration=%(duration)s, time=%(time)s\n"
            f"Expected: %(ans)s\n"
            f"Got: {ans}\n"
        ) % case
        # verify that aslias functions behave the same
        mov = at.sinusoidalMovement(
            startPos=case['startSize'],
            apexPos=case['apexSize'],
            duration=case['duration'],
            time=case['time']
        )
        mov = np.round(mov, decimals=3)
        assert utils.forceBool(mov == case['ans'], handler=all), (
            f"Params: startSize=%(startSize)s, apexSize=%(apexSize)s, duration=%(duration)s, time=%(time)s\n"
            f"Expected: %(ans)s\n"
            f"Got: {ans}\n"
        ) % case
