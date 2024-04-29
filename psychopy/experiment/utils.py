#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Utility functions to support Experiment classes
"""
import re

# this needs to be accessed from __str__ method of Param
scriptTarget = "PsychoPy"

# predefine some regex's; deepcopy complains if do in NameSpace.__init__()
unescapedDollarSign_re = re.compile(r"^\$|[^\\]\$")  # detect "code wanted"
valid_var_re = re.compile(r"^[a-zA-Z_][\w]*$")  # filter for legal var names
nonalphanumeric_re = re.compile(r'\W')  # will match all bad var name chars
list_like_re = re.compile(r"(?<!\\),")  # will match for strings which could be a list


class CodeGenerationException(Exception):
    """
    Exception thrown by a component when it is unable to generate its code.
    """

    def __init__(self, source, message=""):
        super(CodeGenerationException, self).__init__()
        self.source = source
        self.message = message

    def __str__(self):
        return "{}: ".format(self.source, self.message)


def canBeNumeric(inStr):
    """Determines whether the input can be converted to a float
    (using a try: float(instr))
    """
    try:
        float(inStr)
        return True
    except Exception:
        return False
