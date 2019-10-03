#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import traceback
import yaml
import os
import sys
from psychopy import logging

"""
The Alerts module is part of the alerts package for used for generating alerts during PsychoPy integrity checks.

Attributes
----------
catalogue : AlertCatalogue
    For loading alert catalogues, or definitions of each alert, from a yaml file.
    Each catalogue entry has a code key, with values of code, category, msg, and url.
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
    trace: sys.exec_info() traceback object
            The traceback
    """
    def __init__(self, code, obj, strFormat=None, trace=None):
        self.type = self._componentType(obj)
        self.name = self._componentName(obj)
        self.code = catalogue.alert[code]['code']
        self.cat = catalogue.alert[code]['cat']
        self.msg = self._formatMsg(
            catalogue.alert[code]['msg'],
            strFormat)
        self.url = catalogue.alert[code]['url']
        self.obj = obj
        self.trace = self._formatTrace(trace)

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

    def _formatTrace(self, trace=None):
        """
           Formats message text if strFormat value given.

        Parameters
        ----------
        trace: sys.exec_info() traceback object
            The traceback

        Returns
        -------
        str
            The traceback message formatted as string
        """
        if trace:
            errorType, value, tb = trace
            return ''.join(traceback.format_exception(errorType, value, tb))

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


def alert(code=None, obj=object, strFormat=None, trace=None):
    """The Alerts logging function used for writing to AlertLog class

    Parameters
    ----------
    code: int
        The 4 digit code for retrieving alert from AlertCatalogue
    obj: object
        The object related to the alert e.g., TextComponent object
    strFormat: dict
        Dict containing relevant values for formatting messages
    traceback *********
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

