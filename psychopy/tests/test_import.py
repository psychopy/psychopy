import cProfile
import importlib
import time
import os
from psychopy.tests.utils import profiledImport


def test_import_speed():
    """
    Test the speed of importing various parts of psychopy
    """
    # establish a baseline system speed (in case the runners are having a bad day)
    start = time.time()
    # this should take about 1s on a mid-range PC...
    for n in range(10000000):
        y = n + 1
    # ...so use its duration as a multipler for max time
    multiplier = time.time() - start
    
    # define cases:
    # - import: Module to import
    # - maxtime: Maximum allowed time (s) for import, will be adjusted for system speed
    # - notouch: Modules which importing this module shouldn't touch
    cases = [
        {
            'import': "psychopy.experiment",
            'maxtime': 5,
            'notouch': [
                "psychopy.visual",
                "psychopy.sound",
                "psychopy.hardware"
            ]
        }
    ]

    for case in cases:
        # do a profiled import
        profiledImport(
            ref=case['import'],
            maxtime=case['maxtime'] * multiplier,
            notouch=case['notouch']
        )
        
if __name__ == "__main__":
    test_import_speed()