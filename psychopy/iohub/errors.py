# coding=utf-8
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, absolute_import

import sys
import traceback


def print2err(*args):
    """
    Using the standard python print() function from the iohub server process
    will not print anything to the psychopy process stdout. Use print2err
    for this purpose. Each element of *args is unicode formatted and then
    written to sys.stderr.
    :param args: 0 to N objects of any type.
    """
    for a in args:
        sys.stderr.write(u"{0}".format(a))
    sys.stderr.write(u"\n")
    sys.stderr.flush()


def printExceptionDetailsToStdErr():
    """
    Print the last raised exception in the iohub (well, calling) process
    to the psychopy process stderr.
    """
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()

class ioHubError(Exception):
    #TODO: Fix the way exceptions raised in the iohub process are handled
    #      and reported to the psychopy process.
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args)
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return repr(self)

    def __repr__(self):
        r = 'ioHubError:\nArgs: {0}\n'.format(self.args)
        for k, v in self.kwargs.items():
            r += '\t{0}: {1}\n'.format(k, v)
        return r
