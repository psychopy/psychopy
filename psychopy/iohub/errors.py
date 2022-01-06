# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import sys
import traceback


def print2err(*args):
    """
    Note: As of at least Jan-2020, this function seems to 
    cause iohub to fail to start if the script is started from Coder. 
    try: except: at least stops whatever is crashing, 
    (Appears to be use of sys.stderr.write) but prints() do not appear in 
    Coder Console. Not sure how to get iohub process prints to 
    appear in Builder Console...??? Issue is specific to running script from Coder.
    
    Using the standard python print() function from the iohub server process
    will not print anything to the psychopy process stdout. Use print2err
    for this purpose. Each element of *args is unicode formatted and then
    written to sys.stderr.
    
    :param args: 0 to N objects of any type.
    """
    try:
        for a in args:
            sys.stderr.write("{0}".format(a))
        sys.stderr.write("\n")
        sys.stderr.flush()
    except:
        for a in args:
            print("{0}".format(a))
        print()
        	
def printExceptionDetailsToStdErr():
    """
    Print the last raised exception in the iohub (well, calling) process
    to the psychopy process stderr.
    """
    try:
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
    except:
        traceback.print_exc()

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
