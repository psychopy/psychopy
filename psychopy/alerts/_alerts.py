#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import traceback
import yaml
import os
import sys
from psychopy import logging

"""
The Alerts module is used for generating alerts during PsychoPy integrity checks.

Attributes
----------
catalogue : AlertCatalogue
    For loading alert catalogues, or definitions of each alert, from a yaml file.
    Each catalogue entry has a code key, with values of code, category, msg, and url.
alertLog : List
    For storing alerts that are otherwise lost when flushing standard stream. The stored
    lists can be used to feed AlertPanel using in Project Info and new Runner frame.
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


class AlertEntry():
    """An Alerts data class holding alert data as attributes

    Attributes
    ----------

    code: int
        The 4 digit code for retrieving alert from AlertCatalogue
    cat: str
        The category of the alert
    url: str
        A URL for pointing towards information resources for solving the issue
    obj: object
        The object related to the alert e.g., TextComponent object.
    type: str
        Type of component being tested
    name: str
        Name of component being tested
    msg: str
        The alert message
    trace: sys.exec_info() traceback object
            The traceback

    Parameters
    ----------
    code: int
            The 4 digit code for retrieving alert from AlertCatalogue
    obj: object
        The object related to the alert e.g., TextComponent object.
    strFormat: dict
            Dict containing relevant values for formatting messages
    trace: sys.exec_info() traceback object
            The traceback
    """
    def __init__(self, code, obj, strFormat=None, trace=None):
        self.code = catalogue.alert[code]['code']
        self.cat = catalogue.alert[code]['cat']
        self.url = catalogue.alert[code]['url']
        self.obj = obj

        if hasattr(obj, 'type'):
            self.type = obj.type
        else:
            self.type = None

        if hasattr(obj, "params"):
            self.name = obj.params['name'].val
        else:
            self.name = None

        if strFormat:
            self.msg = catalogue.alert[code]['msg'].format(**strFormat)
        else:
            self.msg = catalogue.alert[code]['msg']

        if trace:
            self.trace = ''.join(traceback.format_exception(trace[0], trace[1], trace[2]))
        else:
            self.trace = None


def alert(code=None, obj=object, strFormat=None, trace=None):
    """The alert function is used for writing alerts to the standard error stream.
    Only the ErrorHandler class can receive alerts via the "receiveAlert" method.

    Parameters
    ----------
    code: int
        The 4 digit code for retrieving alert from AlertCatalogue
    obj: object
        The object related to the alert e.g., TextComponent object
    strFormat: dict
        Dict containing relevant values for formatting messages
    trace: sys.exec_info() traceback object
            The traceback
    """

    msg = AlertEntry(code, obj, strFormat, trace)

    # format the warning into a string for console and logging targets
    msgAsStr = ("Component Type: {type} | "
                "Component Name: {name} | "
                "Code: {code} | "
                "Category: {cat} | "
                "Message: {msg} | "
                "Traceback: {trace}".format(type=msg.type,
                                            name=msg.name,
                                            code=msg.code,
                                            cat=msg.cat,
                                            msg=msg.msg,
                                            trace=msg.trace))

    # if we have a psychopy warning instead of a file-like stderr then pass on the raw info
    if hasattr(sys.stderr, 'receiveAlert'):
        sys.stderr.receiveAlert(msg)
    else:
        sys.stderr.write(msgAsStr)  # For tests detecting output - change when error handler set up
    logging.warning(msgAsStr)

# Create catalogue
catalogue = AlertCatalogue()
alertLog = []
