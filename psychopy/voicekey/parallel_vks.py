#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Completely untested. Doesn't work at all on Mac (no parallel).
"""

from . signal import _BaseVoiceKeySignal
from . vk_tools import get_time, sleep

try:
    from psychopy import parallel
    have_parallel = True
except Exception:  # ImportError:
    have_parallel = False


class ParallelVoiceKeySignal(_BaseVoiceKeySignal):
    """Class for using PsychoPy parallel as a signal channel.
    """

    def __init__(self, sec=0.010, delay=0, on=1, off=0, address=0x378, pin=2):
        if not have_parallel:
            raise ImportError("could not import parallel (for signaler)")
        super(ParallelVoiceKeySignal, self).__init__(sec, delay, on, off)
        self.id = '({0}, pin={1})'.format(hex(address), pin)
        self.address = address
        self.pin = pin  # 2-9
        self.port = parallel.ParallelPort(address)

    def signal(self):
        """Send a signal at the desired time.

        After an optional `delay`, set a pin to `on` for `sec`, then to `off`.
        A delay is not recommended unless your system's time.sleep() function
        has ms-level precision (yes Mac or linux, typically no for Windows).
        """
        if self.delay:
            sleep(self.delay)
        t0 = get_time()
        self.port.setData(self.on)
        # check time and self.running:
        while self.running and get_time() - t0 < self.sec:
            sleep(0.001)
        self.port.setData(self.off)
