# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutionse
# Distributed under the terms of the GNU General Public License (GPL).
import sys


def print2err(*args):
    for a in args:
        sys.stderr.write(u"{0}".format(a))
    sys.stderr.write(u"\n")
    sys.stderr.flush()


def printExceptionDetailsToStdErr():
    import sys
    import traceback
    import pprint
    exc_type, exc_value, exc_traceback = sys.exc_info()
    pprint.pprint(exc_type, stream=sys.stderr, indent=1, width=80, depth=None)
    pprint.pprint(exc_value, stream=sys.stderr, indent=1, width=80, depth=None)
    pprint.pprint(
        traceback.format_tb(exc_traceback),
        stream=sys.stderr,
        indent=1,
        width=80,
        depth=None)


class ioHubError(Exception):

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args)
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return repr(self)

    def __repr__(self):
        r = 'ioHubError:\nArgs: {0}\n'.format(self.args)
        for k, v in self.kwargs.iteritems():
            r += '\t{0}: {1}\n'.format(k, v)
        return r
