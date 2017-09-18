#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from . signal import _BaseVoiceKeySignal


class DemoVoiceKeySignal(_BaseVoiceKeySignal):
    """Demo: print to stdout.
    """

    def signal(self):
        print('>> demo signal <<')
