#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import yaml
import os
import time

"""
The Alerts module is part of the alerts package for used for generating alerts during PsychoPy integrity checks.
The Alerts module contains several classes for creation, storage and provision of alerts.

Attributes
----------
catalogue : AlertCatalogue
    For loading alert catalogues, or definitions of each alert, from a yaml file.
    Each catalogue entry has a code key, with values of code, category, msg, and url.
root: AlertLog
    A storage class for storage and provision of alerts. AlertsLog has a write and flush method,
    for adding each alert to storage, and flushing for releasing the information and clearing the alerts container.
master: MasterLog
    The MasterLogs responsibility is to store all logs in master alerts logfiles.
    MasterLog appends to the current process' alerts logfile each time the AlertLog is flushed.
"""

class AlertCatalogue():
    """A class for loading alerts from the alerts catalogue yaml file"""
    def __init__(self):
        self.alert = self.load("alertsCatalogue.yml")

    def load(self, fileName):
        """Loads alert catalogue yaml file

        Parameters
        ----------
        fileName: str
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
    The AlertLog stores data for only a single call to compile script, before being
    flushed to the display, and written to the MasterLog.
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
        for alert in self.alertLog:
            # Print to stdOutFrame
            msg = ("AlertLogger: {logName} | "
                   "Component Type: {type} | "
                   "Component Name: {name} | "
                   "Code: {code} | "
                   "Category: {cat} | "
                   "Message: {msg} | ".format(logName=alert.logName,
                                              type=alert.type,
                                              name=alert.name,
                                              code=alert.code,
                                              cat=alert.cat,
                                              msg=alert.msg))
            master.write(msg)  # Write to log file
            print(msg)  # Send to terminal or stdOutFrame
        self.alertLog = []  # reset alertLog

class MasterLog():
    """The MasterLog writes all alerts created during the current Python process
    to a log file on each flush of the AlertLog class. The MasterLog will only
    store 5 most recent alert log files.
    """
    def __init__(self):
        self.logFolder = None
        self.logFile = None
        self.alertLogFile = None

    def setLogPath(self, filePath=None):
        """
        Sets the directory for the master log.

        Parameters
        ----------
        filePath: str
            File path for the master logs folder
        """
        # Only create MasterLog folder if filePath provided
        if filePath is None:
            return

        self.logFile = "alertLog_{}.log".format(time.strftime("%Y.%m.%d.%H.%M.%S"))
        self.logFolder = Path(os.path.abspath(filePath)) / "alertLogs"
        self.alertLogFile = self.logFolder / self.logFile

        if not self.logFolder.exists():
            self.logFolder.mkdir(parents=True)
        else:
            # Store only 5 most recent alert log files
            logs = [log for log in self.logFolder.glob('*.log')]
            if len(logs) >= 5:
                os.remove(logs[0])

    def write(self, msg):
        with open("{}".format(self.alertLogFile), 'a+') as fp:
            fp.write(msg + '\n')

class AlertEntry():
    """An Alerts data class holding alert data as attributes

    Attributes
    ----------
    logName: str
        Name of the AlertLogger
    type: str
        Type of component being tested
    name: str
        Name of component being tested
    code: int
        The 4 digit code for retrieving alert from AlertCatalogue
    cat: str
        The category of the alert
    msg: str
        The alert message
    url: str
        A URL for pointing towards information resources for solving the issue
    obj: object
        The object related to the alert e.g., TextComponent object.

    Parameters
    ----------
    name: str
        The name of the AlertLogger instantiating the AlertEntry
    code: int
            The 4 digit code for retrieving alert from AlertCatalogue
    obj: object
        The object related to the alert e.g., TextComponent object.
    strFormat: dict
            Dict containing relevant values for formatting messages
    """
    def __init__(self, name, code, obj, strFormat=None):
        self.logName = name
        self.type = self._componentType(obj)
        self.name = self._componentName(obj)
        self.code = catalogue.alert[code]['code']
        self.cat = catalogue.alert[code]['cat']
        self.msg = self._formatMsg(
            catalogue.alert[code]['msg'],
            strFormat)
        self.url = catalogue.alert[code]['url']
        self.obj = obj

    def _formatMsg(self, msg, strFormat):
        """
        Formats message text if strFormat value given.

        Parameters
        ----------
        msg: str
            The alerts catalogue message entry
        strFormat: dict
            Values to format msg

        Returns
        -------
        msg: str
            Either original or formatted message
        """
        if strFormat is not None:
            return msg.format(**strFormat)
        return msg

    def _componentType(self, obj):
        """
        Checks component for type

        Parameters
        ----------
        obj: Component
            Component object being tested

        Returns
        -------
        type: str
            The type of component if exists, or None.
        """
        if hasattr(obj, "type"):
            return obj.type
        return None

    def _componentName(self, obj):
        """
        Checks component for name

        Parameters
        ----------
        obj: Component
            Component object being tested

        Returns
        -------
        name: str
            The name of the component if the parameter exists, or None.
        """
        if hasattr(obj, "params"):
            return obj.params['name'].val
        return None

class AlertLogger():
    """The Alerts logging class used for writing to AlertLog class

    Parameters
    ----------
    name: str
        Logger name e.g., Experiment, Builder, Coder etc
    """
    def __init__(self, name, filePath=None):
        self.name = name
        master.setLogPath(filePath)  # Default sets on new/opened Builder file

    def write(self, code, obj=object, strFormat=None):
        """Write to AlertLog

        Parameters
        ----------
        code: int
            The 4 digit code for retrieving alert from AlertCatalogue
        obj: object
            The object related to the alert e.g., TextComponent object
        strFormat: dict
            Dict containing relevant values for formatting messages
        """
        root.write(AlertEntry(self.name, code, obj, strFormat))

    def flush(self):
        root.flush()

# Create catalogue
catalogue = AlertCatalogue()
# Create log objects
root = AlertLog()
master = MasterLog()
