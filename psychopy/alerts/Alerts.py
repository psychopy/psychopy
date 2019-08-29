#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import yaml
import os

"""
The Alerts module is part of the alerts package for used for generating alerts during PsychoPy integrity checks.
The Alerts module contains several classes to for creation, storage and provision of alerts.

Attributes
----------
catalogue : AlertCatalogue
    For loading alert catalogues, or definitions of each alert, from a yaml file.
    Each catalogue entry has a code key, with values of code, warn, msg, and url.
root: AlertLog
    A storage class for storage and provision of alerts. AlertsLog has a write and flush method,
    for adding each alert to storage, and flushing for releasing the information and clearing the alerts container.
master:
    A storage class subclassed from AlertLog. Its purpose is to store all logs in an master alerts logfile.
    MasterLog appends to the current process alerts logfile at the end of each script compilation.
"""

class AlertCatalogue():
    """A class for loading alerts from the alerts catalogue yaml file"""
    def __init__(self):
        self.alert = self.load("alertsCatalogue.yml")

    def load(self, fileName):
        """Loads alert catalogue yaml file

        Parameters
        ----------
        fileName: string
            The name of the alerts catalogue yaml file

        Returns
        -------
        dict
            The alerts catalogue as a Python dictionary
        """
        # Load alert definitions
        alertsYml = Path(os.path.dirname(os.path.abspath(__file__))) / fileName
        with open('{}'.format(alertsYml), 'r') as ymlFile:
            return yaml.load(ymlFile, Loader=yaml.SafeLoader)

class AlertLog():
    """The AlertLog storage class for storage and provision of alert data.
    The AlertLog stores data from a single call to compile script, before being
    flushed to the display, and the MasterLog
    """
    def __init__(self):
        self.alertLog = []

    def write(self, alert):
        """Write to alertLog container

        Parameters
        ----------
        alert: AlertEntry object
            The AlertEntry object instantiated using an alert code
        """
        self.alertLog.append((alert))

    def flush(self):
        master.write(self.alertLog)
        for i in self.alertLog:
            # Print to stdOutFrame
            print(i.name, i.code, i.obj)
        self.alertLog = []

class MasterLog(AlertLog):
    """The master AlertLog storage class for holding all alerts created during
    the current Python process. Writes to master log file on each call to compile
    script.
    """
    def __init__(self):
        super(MasterLog, self).__init__()

    def flush(self, alert=None):
        # TODO: Figure out how to deal with MasterLog data
        for log in self.alertLog:
            print(log)

class AlertEntry():
    """An Alerts data class holding alert data as attributes

    Parameters
    ----------
    name: string
        The name of the AlertLogger instantiating the AlertEntry
    code: int
            The 4 digit code for retrieving alert from AlertCatalogue
    obj: object
        The object related to the alert e.g., TextComponent object. The obj contains component params, including its
        name.
    """
    def __init__(self, name, code, obj):
        self.name = name
        self.code = catalogue.alert[code]['code']
        self.warn = catalogue.alert[code]['warn']
        self.msg = catalogue.alert[code]['msg']
        self.url = catalogue.alert[code]['url']
        self.obj = obj

class AlertLogger():
    """The Alerts logging class used for writing to AlertLog class

    Parameters
    ----------
    name: string
        Logger name e.g., Experiment, Builder, Coder etc
    """
    def __init__(self, name):
        self.name = name

    def write(self, code, obj=object):
        """Write to AlertLog

        Parameters
        ----------
        code: int
            The 4 digit code for retrieving alert from AlertCatalogue
        obj: object
            The object related to the alert e.g., TextComponent object
        """
        root.write(AlertEntry(self.name, code, obj))

    def flush(self):
        root.flush()

# Create catalogue
catalogue = AlertCatalogue()
# Create log objects
root = AlertLog()
master = MasterLog()
