#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for signals to be sent upon voice-key trip events.
"""

import threading


class _BaseVoiceKeySignal(threading.Thread):
    """Class to support sending a signal upon detection of an event.

    Non-blocking unless you .join() the thread. An adjustable `delay` allows
    a deferred start.

    Subclass and override `signal`.
    """

    def __init__(self, sec=0.010, delay=0, on=1, off=0):
        super(_BaseVoiceKeySignal, self).__init__(None, 'EventSignal', None)
        self.sec = sec
        self.delay = delay
        self.on = on
        self.off = off
        self.running = False
        # self.daemon = True
        self.id = None

    def __repr__(self):
        text = '<{0} instance, id={1}>'
        return text.format(self.__class__.__name__, self.id)

    def run(self):
        self.running = True
        self.signal()
        self.running = False

    def signal(self):
        pass

    def stop(self):
        self.running = False
