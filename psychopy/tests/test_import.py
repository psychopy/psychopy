import cProfile
import importlib
import time
import os


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
        # setup a profiler
        pr = cProfile.Profile()
        # start a timer
        start = time.time()
        # start profiling
        pr.enable()
        try:
            # import module
            importlib.import_module(case['import'])
            # stop profiling
            pr.disable()
        except:
            # if anything fails, stop the profiler
            pr.disable()
        # generate stats
        pr.create_stats()
        # get time taken
        duration = time.time() - start 
        # check that total time is acceptable...
        assert duration < case['maxtime'] * multiplier, f"Importing module {case['import']} took longer than allowed ({duration}s > {case['maxtime'] * multiplier}s)"
        # iterate through all calls from the profile...
        for key, val in pr.stats.items():
            # parse information
            file, lineno, func = key
            cumCalls, nCalls, totalDuration, cumTime, subcalls = val
            # was this call to a module we shouldn't have touched?
            for mod in case['notouch']:
                msg = f"Importing module {case['import']} imports module {mod} when it shouldn't."
                assert mod.replace(".", os.sep) not in file, msg
                # did any subsequent calls touch a module they shouldn't have?
                for call in subcalls:
                    subfile, line, subfunc = call
                    assert mod.replace(".", os.sep) not in subfile, msg
        
if __name__ == "__main__":
    test_import_speed()