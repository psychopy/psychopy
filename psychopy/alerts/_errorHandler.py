#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from ._alerts import _activeAlertHandlers


class _BaseErrorHandler:
    """A base class for handling PsychoPy alerts and exceptions.
    """

    def __init__(self, targets=("stdout", "stderr", "alert"), alwaysReceive=True, autoFlush=True):
        self.errors = []
        self.alerts = []
        self.targets = targets
        self.alwaysReceive = alwaysReceive
        self.autoFlush = autoFlush
        _activeAlertHandlers.append(self)

    def write(self, toWrite):
        """This is needed for any Python Exceptions, which assume the stderr
        is a file-like object. But we might well simply store the message for
        printing later.
        """
        self.errors.append(toWrite)
        if self.autoFlush:
            self.flush()

    def flush(self):
        """Print errors and alerts to console and clear errors.
        """
        for err in self.errors:
            print(err)
        self.errors = []

    def receiveAlert(self, alert):
        """
        Handles PsychoPy alerts (sent by _alerts.alert).
        This function should ONLY be called by _alerts.alert.

        Parameters:
        -----------
        alert: psychopy.alert._alert.AlertEntry object
            A data object containing alert information.
        """
        self.alerts.append(alert)

    def __del__(self):
        if self in _activeAlertHandlers:
            i = _activeAlertHandlers.index(self)
            _activeAlertHandlers.pop(i)
        self.flush()
