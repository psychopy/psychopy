#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Experiment classes:
    Experiment, Flow, Routine, Param, Loop*, *Handlers, and NameSpace

The code that writes out a *_lastrun.py experiment file is (in order):
    experiment.Experiment.writeScript() - starts things off, calls other parts
    settings.SettingsComponent.writeStartCode()
    experiment.Flow.writeBody()
        which will call the .writeBody() methods from each component
    settings.SettingsComponent.writeEndCode()
"""

from __future__ import absolute_import, print_function
# from future import standard_library
from past.builtins import basestring
from builtins import object

import re

from psychopy import logging
from . import utils
from . import py2js

# standard_library.install_aliases()


def _findParam(name, node):
    """Searches an XML node in search of a particular param name

    :param name: str indicating the name of the attribute
    :param node: xml element/node to be searched
    :return: None, or a parameter child node
    """
    for attr in node:
        if attr.get('name') == name:
            return attr


class Param(object):
    """Defines parameters for Experiment Components
    A string representation of the parameter will depend on the valType:

    >>> print(Param(val=[3,4], valType='num'))
    asarray([3, 4])
    >>> print(Param(val=3, valType='num')) # num converts int to float
    3.0
    >>> print(Param(val=3, valType='str') # str keeps as int, converts to code
    3
    >>> print(Param(val='3', valType='str')) # ... and keeps str as str
    '3'
    >>> print(Param(val=[3,4], valType='str')) # val is <type 'list'> -> code
    [3, 4]
    >>> print(Param(val='[3,4]', valType='str'))
    '[3,4]'
    >>> print(Param(val=[3,4], valType='code'))
    [3, 4]
    >>> print(Param(val='"yes", "no"', valType='list'))
    ["yes", "no"]

    >>> #### auto str -> code:  at least one non-escaped '$' triggers
    >>> print(Param('[x,y]','str')) # str normally returns string
    '[x,y]'
    >>> print(Param('$[x,y]','str')) # code, as triggered by $
    [x,y]
    >>> print(Param('[$x,$y]','str')) # code, redundant $ ok, cleaned up
    [x,y]
    >>> print(Param('[$x,y]','str')) # code, a $ anywhere means code
    [x,y]
    >>> print(Param('[x,y]$','str')) # ... even at the end
    [x,y]
    >>> print(Param('[x,\$y]','str')) # string, because the only $ is escaped
    '[x,$y]'
    >>> print(Param('[x,\ $y]','str')) # improper escape -> code
    [x,\ y]
    >>> print(Param('/$[x,y]','str')) # improper escape -> code
    /[x,y]
    >>> print(Param('[\$x,$y]','str')) # code, python syntax error
    [$x,y]
    >>> print(Param('["\$x",$y]','str') # ... python syntax ok
    ["$x",y]
    >>> print(Param("'$a'",'str')) # code, with the code being a string
    'a'
    >>> print(Param("'\$a'",'str')) # str, with the str containing a str
    "'$a'"
    >>> print(Param('$$$$$myPathologicalVa$$$$$rName','str'))
    myPathologicalVarName
    >>> print(Param('\$$$$$myPathologicalVa$$$$$rName','str'))
    $myPathologicalVarName
    >>> print(Param('$$$$\$myPathologicalVa$$$$$rName','str'))
    $myPathologicalVarName
    >>> print(Param('$$$$\$$$myPathologicalVa$$$\$$$rName','str'))
    $myPathologicalVa$rName
    """

    def __init__(self, val, valType, allowedVals=None, allowedTypes=None,
                 hint="", label="", updates=None, allowedUpdates=None,
                 categ="Basic"):
        """
        @param val: the value for this parameter
        @type val: any
        @param valType: the type of this parameter ('num', 'str', 'code')
        @type valType: string
        @param allowedVals: possible vals for this param
            (e.g. units param can only be 'norm','pix',...)
        @type allowedVals: any
        @param allowedTypes: if other types are allowed then this is
            the possible types this parameter can have
            (e.g. rgb can be 'red' or [1,0,1])
        @type allowedTypes: list
        @param hint: describe this parameter for the user
        @type hint: string
        @param updates: how often does this parameter update
            ('experiment', 'routine', 'set every frame')
        @type updates: string
        @param allowedUpdates: conceivable updates for this param
            [None, 'routine', 'set every frame']
        @type allowedUpdates: list
        @param categ: category for this parameter
            will populate tabs in Component Dlg
        @type allowedUpdates: string
        """
        super(Param, self).__init__()
        self.label = label
        self.val = val
        self.valType = valType
        self.allowedTypes = allowedTypes or []
        self.hint = hint
        self.updates = updates
        self.allowedUpdates = allowedUpdates
        self.allowedVals = allowedVals or []
        self.staticUpdater = None
        self.categ = categ
        self.readOnly = False

    def __str__(self):
        if self.valType == 'num':
            try:
                # will work if it can be represented as a float
                return "{}".format(float(self.val))
            except Exception:  # might be an array
                return "asarray(%s)" % (self.val)
        elif self.valType == 'int':
            try:
                return "%i" % self.val  # int and float -> str(int)
            except TypeError:
                return "{}".format(self.val)  # try array of float instead?
        elif self.valType == 'str':
            # at least 1 non-escaped '$' anywhere --> code wanted
            # return str if code wanted
            # return repr if str wanted; this neatly handles "it's" and 'He
            # says "hello"'
            if isinstance(self.val, basestring):
                codeWanted = utils.unescapedDollarSign_re.search(self.val)
                if codeWanted:
                    return "%s" % getCodeFromParamStr(self.val)
                else:  # str wanted
                    # remove \ from all \$
                    s = repr(re.sub(r"[\\]\$", '$', self.val))
                    # if target is python2.x then unicode will be u'something'
                    # but for other targets that will raise an annoying error
                    if utils.scriptTarget != 'PsychoPy':
                        if s.startswith("u'") or s.startswith('u"'):
                            s = s[1:]
                    return s
            return repr(self.val)
        elif self.valType in ['code', 'extendedCode']:
            isStr = isinstance(self.val, basestring)
            if isStr and self.val.startswith("$"):
                # a $ in a code parameter is unnecessary so remove it
                val = "%s" % self.val[1:]
            elif isStr and self.val.startswith("\$"):
                # the user actually wanted just the $
                val = "%s" % self.val[1:]
            elif isStr:
                val = "%s" % self.val
            else:  # if val was a tuple it needs converting to a string first
                val = "%s" % repr(self.val)
            if utils.scriptTarget == "PsychoJS":
                if self.valType == 'code':
                    valJS = py2js.expression2js(val)
                elif self.valType == 'extendedCode':
                    valJS = py2js.snippet2js(val)
                if val != valJS:
                    logging.info("py2js: {} -> {}".format(val, valJS))
                return valJS
            else:
                return val
        elif self.valType == 'list':
            return "%s" %(toList(self.val))
        elif self.valType == 'fixedList':
            return "{}".format(self.val)
        elif self.valType == 'bool':
            return "%s" % self.val
        else:
            raise TypeError("Can't represent a Param of type %s" %
                            self.valType)

    def __eq__(self, other):
        """Test for equivalence is needed for Params because what really
        typically want to test is whether the val is the same
        """
        return self.val == other

    def __ne__(self, other):
        """Test for (non)equivalence is needed for Params because what really
        typically want to test is whether the val is the same/different
        """
        return self.val != other

    def __bool__(self):
        """Return a bool, so we can do `if thisParam`
        rather than `if thisParam.val`"""
        return bool(self.val)

    __nonzero__ = __bool__  # for python2 compatibility


def getCodeFromParamStr(val):
    """Convert a Param.val string to its intended python code
    (as triggered by special char $)
    """
    tmp = re.sub(r"^(\$)+", '', val)  # remove leading $, if any
    # remove all nonescaped $, squash $$$$$
    tmp2 = re.sub(r"([^\\])(\$)+", r"\1", tmp)
    out = re.sub(r"[\\]\$", '$', tmp2)  # remove \ from all \$
    if utils.scriptTarget=='PsychoJS':
        out = py2js.expression2js(out)
    return out


def toList(val):
    """

    Parameters
    ----------
    val

    Returns
    -------
    A list of entries in the string value
    """
    # we really just need to check if they need parentheses
    stripped = val.strip()
    if utils.scriptTarget == "PsychoJS":
        return py2js.expression2js(stripped)
    elif not ((stripped.startswith('(') and stripped.endswith(')')) \
              or ((stripped.startswith('[') and stripped.endswith(']')))):
        return "[{}]".format(stripped)
    else:
        return stripped
