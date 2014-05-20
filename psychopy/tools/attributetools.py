#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Functions and classes related to attribute handling'''

import numpy

from psychopy import logging

class attributeSetter(object):
    ''' Makes functions appear as attributes. Takes care of autologging.'''
    def __init__(self, func, doc=None):
        self.func = func
        self.__doc__ = doc if doc is not None else func.__doc__

    def __set__(self, obj, value):
        newValue = self.func(obj, value)
        logAttrib(obj, log=None, attrib=self.func.__name__, value=value)  # log=None defaults to obj.autoLog
        
        # Useful for inspection/debugging. Keeps track of all settings of attributes.
        """
        import traceback
        origin = traceback.extract_stack()[-2]
        #print '%s.%s = %s (line %i)' %(obj.__class__.__name__, self.func.__name__, value.__repr__(), origin[1])  # short
        #print '%s.%s = %s (%s in in %s, line %i' %(obj.__class__.__name__, self.func.__name__, value.__repr__(), origin[1], origin[0].split('/')[-1], origin[1], origin[3].__repr__())  # long
        """
        return newValue

    def __repr__(self):
        return repr(self.__getattribute__)

def setAttribute(self, attrib, value, log, operation=False, stealth=False):
    """
    This function is useful to direct the old set* functions to the
    @attributeSetter. It has the same functionality but supports logging control 
    as well, making it useful for cross-@attributeSetter calls as well with log=False.
    
    Typical usage: e.g. in setSize(self, value, operation, log=None) do::
    
        def setSize(self, value, operation, log=None):
            setAttribute(self, 'size', value, log, operation)  # call attributeSetter
    
    Sets an object property (scalar or numpy array), optionally with an operation
    given in a string. If operation is None or '', value is multiplied with old 
    to keep shape.
    
    If stealth is True, then use self.__dict[key] = value and avoid calling attributeSetters. 
    If stealth is False, use setattr(). autoLog controls the value of autoLog during this setattr().    
    
    History: introduced in version 1.79 to avoid exec-calls. Even though it looks
    complex, it is very fast :-)"""
    
    # Change the value of "value" if there is an operation. Even if it is '',
    # that indicates that this value could potentially be subjected to an operation.
    if operation is not False:
        # Only apply operation if not None or str - they do strange things when converted to numpy arrays!
        if not (value is None or type(value) is str) and operation in ('', None):
            try:
                oldValue = getattr(self, attrib)
                oldValue = numpy.array(oldValue, float)
        
                # Calculate new value using operation
                if operation in ('', None):
                    value = oldValue * 0 + value  # Preserves dimensions, if array
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
                    raise ValueError('Unsupported value "', operation, '" for operation when setting', attrib, 'in', self.__class__.__name__)
        
            except AttributeError:
                # attribute is not set yet. Do it now in a non-updating manner
                value = numpy.array(value, float)
            except TypeError as error:
                # Attribute is "None" or an unset attributeSetter. This is a sign that we are just initing
                if (oldValue is None or isinstance(oldValue, attributeSetter)) and operation in ('', None):
                    value = numpy.array(value, float)
                else:
                    raise TypeError, error
            except ValueError as error:
                # The old value is a string, typical of a color change from named to e.g. rgb.
                if type(oldValue) is str and operation in ('', None):
                    value = numpy.array(value, float)
                else:
                    raise ValueError, error
    
    # Ok, operation or not, change the attribute in self without callback to attributeSetters
    if stealth:
        self.__dict__[attrib] = value  # without logging as well
    else:
        # Trick to control logging of attributeSetter. Set logging in self.autoLog
        autoLogOrig = self.autoLog  # save original value
        self.__dict__['autoLog'] = log or autoLogOrig and log is None  # set to desired logging. log=None dafaults to autoLog
        setattr(self, attrib, value)  # set attribute, calling attributeSetter if it exists
        if attrib != 'autoLog':  # hack: if attrib was 'autoLog', do not set it back to original value!
            self.__dict__['autoLog'] = autoLogOrig  # return autoLog to original


def logAttrib(obj, log, attrib, value=None):
    """
    Logs a change of a visual attribute on the next window.flip.
    If value=None, it will take the value of self.attrib.
    """
    # Default to autoLog if log isn't set explicitly
    if log or log is None and obj.autoLog:
        if value is None:
            value = getattr(obj, attrib)
        
        # Log on next flip
        message = "%s: %s = %s" % (obj.name, attrib, value.__repr__())
        try:
            obj.win.logOnFlip(message, level=logging.EXP, obj=obj)
        except AttributeError:  # this is probably a Window, having no "win" attribute
            logging.log(message, level=logging.EXP, obj=obj)