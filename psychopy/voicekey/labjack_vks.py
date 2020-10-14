#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Class for voicekey trip signaling via Labjack device
"""

from __future__ import absolute_import, print_function

from . signal import _BaseVoiceKeySignal
from . vk_tools import get_time, sleep

try:
    from labjack.u3 import U3
    labjack_U3 = U3
    have_labjack = 'from labjack'
# ImportError:  # other errors too, like labjack.u12.U12Exception (??)
except Exception:
    try:
        from psychopy.hardware import labjacks
        labjack_U3 = labjacks.u3.U3
        have_labjack = 'from psychopy.hardware.labjacks'
    except Exception:  # ImportError:
        have_labjack = False


class LabJackU3VoiceKeySignal(_BaseVoiceKeySignal):
    """Class for using a LabJack U3 device as a signal channel.
    """

    def __init__(self, sec=0.010, delay=0, on=1, off=0, address=6008):
        if not have_labjack:
            raise ImportError("could not import labjack (for LabJack u3)")
        super(LabJackU3VoiceKeySignal, self).__init__(sec, delay, on, off)
        self.device = labjack_U3()
        self.address = address
        self.id = address

    def signal(self):
        """Send a signal at the desired time.

        After an optional `delay`, set a port to `on` for `sec`, then to `off`.
        A delay is not recommended unless your system's time.sleep() function
        has ms-level precision (yes Mac or linux, typically no for Windows).
        """
        if self.delay:
            sleep(self.delay)
        t0 = get_time()
        self.device.writeRegister(self.address, self.on)
        # check time and self.running:
        while self.running and get_time() - t0 < self.sec:
            sleep(0.001)
        self.device.writeRegister(self.address, self.off)
