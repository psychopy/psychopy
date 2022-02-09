#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to attribute handling
"""

import numpy
from psychopy import logging


class attributeSetter:
    """Makes functions appear as attributes. Takes care of autologging.
    """

    def __init__(self, func, doc=None):
        self.func = func
        if doc is not None:
            self.__doc__ = doc
        else:
            self.__doc__ = func.__doc__

    def __set__(self, obj, value):
        newValue = self.func(obj, value)
        # log=None defaults to obj.autoLog:
        logAttrib(obj, log=None, attrib=self.func.__name__,
                  value=value)

        # Useful for inspection/debugging. Keeps track of all settings of
        # attributes.
        '''
        import traceback
        origin = traceback.extract_stack()[-2]
        # print('%s.%s = %s (line %i)' %(obj.__class__.__name__,
        #        self.func.__name__, value.__repr__(), origin[1]))  # short
        # print('%s.%s = %s (%s in %s, line %i' %(obj.__class__.__name__,
        #        self.func.__name__, value.__repr__(),
        #        origin[1], origin[0].split('/')[-1],
        #        origin[1], origin[3].__repr__())))  # long
        '''
        return newValue

    def __repr__(self):
        return repr(self.__getattribute__)


def setAttribute(self, attrib, value, log,
                 operation=False, stealth=False):
    """This function is useful to direct the old set* functions to the
    @attributeSetter.

    It has the same functionality but supports logging control as well, making
    it useful for cross-@attributeSetter calls as well with log=False.

    Typical usage: e.g. in setSize(self, value, operation, log=None) do::

        def setSize(self, value, operation, log=None):
            # call attributeSetter:
            setAttribute(self, 'size', value, log, operation)

    Sets an object property (scalar or numpy array), optionally with
    an operation given in a string. If operation is None or '', value
    is multiplied with old to keep shape.

    If `stealth` is True, then use self.__dict[key] = value and avoid
    calling attributeSetters. If `stealth` is False, use `setattr()`.
    `autoLog`  controls the value of autoLog during this `setattr()`.

    History: introduced in version 1.79 to avoid exec-calls.
    Even though it looks complex, it is very fast :-)
    """

    # Change the value of "value" if there is an operation. Even if it is '',
    # which indicates that this value could potentially be subjected to an
    # operation.
    if operation is not False:
        try:
            oldValue = getattr(self, attrib)
        except AttributeError:
            # attribute is not set yet. Set it to None to skip
            # operation and just set value.
            oldValue = None

        # Apply operation except for the case when new or old value
        # are None or string-like
        if (value is not None and type(value)!=str
                and oldValue is not None and type(oldValue)!=str):
            value = numpy.array(value, float)

            # Calculate new value using operation
            if operation in ('', None):
                if (value.shape == () and
                        not isinstance(oldValue, attributeSetter)):  # scalar
                    # Preserves dimensions in case oldValue is array-like.
                    value = oldValue * 0 + value
            elif operation == '+':
                value = oldValue + value
            elif operation == '*':
                value = oldValue * value
            elif operation == '-':
                value = oldValue - value
            elif operation == '/':
                value = oldValue / value
            elif operation == '**':
                value = oldValue ** value
            elif operation == '%':
                value = oldValue % value
            else:
                msg = ('Unsupported value "%s" for operation when '
                       'setting %s in %s')
                vals = (operation, attrib, self.__class__.__name__)
                raise ValueError(msg % vals)

        elif operation not in ('', None):
            msg = ('operation %s invalid for %s (old value) and %s '
                   '(operation value)')
            vals = (operation.__repr__(), oldValue, value)
            raise TypeError(msg % vals)

    # Ok, operation or not, change the attribute in self without callback to
    # attributeSetters
    if stealth:
        self.__dict__[attrib] = value  # without logging as well
    else:
        # Trick to control logging of attributeSetter. Set logging in
        # self.autoLog
        autoLogOrig = self.autoLog  # save original value
        # set to desired logging. log=None defaults to autoLog
        self.__dict__['autoLog'] = log or autoLogOrig and log is None
        # set attribute, calling attributeSetter if it exists
        setattr(self, attrib, value)
        # hack: if attrib was 'autoLog', do not set it back to original value!
        if attrib != 'autoLog':
            # return autoLog to original
            self.__dict__['autoLog'] = autoLogOrig


def logAttrib(obj, log, attrib, value=None):
    """Logs a change of a visual attribute on the next window.flip.
    If value=None, it will take the value of self.attrib.
    """
    # Default to autoLog if log isn't set explicitly
    if log or log is None and obj.autoLog == True:
        if value is None:
            value = getattr(obj, attrib)

        # for numpy arrays bigger than 2x2 repr is slow (up to 1ms) so just
        # say it was an array
        if isinstance(value, numpy.ndarray) and (value.ndim > 2 or value.size > 2):
            valStr = repr(type(value))
        else:
            valStr = value.__repr__()
        message = "%s: %s = %s" % (obj.name, attrib, valStr)

        try:
            obj.win.logOnFlip(message, level=logging.EXP, obj=obj)
        except AttributeError:
            # the "win" attribute only exists if sync-to-visual (e.g. stimuli)
            logging.log(message, level=logging.EXP, obj=obj)
