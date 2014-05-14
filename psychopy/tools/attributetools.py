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
        if (obj.autoLog is True) and (self.func.__name__ is not 'autoLog'):
            message = "%s: %s = %s" % (obj.__class__.__name__, self.func.__name__, value)
            try:
                obj.win.logOnFlip(message, level=logging.EXP, obj=obj)
            except AttributeError:  # this is probably a Window, having no "win" attribute
                logging.log(message, level=logging.EXP, obj=obj)
        
        # Useful for inspection/debugging. Keeps track of all settings of attributes.
        """
        import traceback
        origin = traceback.extract_stack()[-2]
        print '%s.%s = %s (line %i)' %(obj.__class__.__name__, self.func.__name__, value.__repr__(), origin[1])  # short
        #print '%s.%s = %s (%s in in %s, line %i' %(obj.__class__.__name__, self.func.__name__, value.__repr__(), origin[1], origin[0].split('/')[-1], origin[1], origin[3].__repr__())  # long
        """
        return newValue

    def __repr__(self):
        return repr(self.__getattribute__)

def callAttributeSetter(self, attrib, value, log=None):
    """Often, the get*() functions just add the ability to log compared to attributeSetter.
    As attributeSetter respects self.autoLog, we can do the following to control logging"""
    autoLogOrig = self.autoLog  # save original value
    self.autoLog = log or autoLogOrig and log is None  # set to desired logging. None dafaults to autoLog
    setattr(self, attrib, value)  # set attribute, calling attributeSetter
    self.autoLog = autoLogOrig  # return autoLog to original

def setWithOperation(self, attrib, value, operation, stealth=False, autoLog=True):
    """ Sets an object property (scalar or numpy array) with an operation.
    If stealth is True, then use self.__dict[key] = value and avoid calling attributeSetters. 
    
    If stealth is False, use setattr(). autoLog controls the value of autoLog during this setattr().
    This is useful to translate the old set* functions to the new @attributeSetters. In set*, just do:
    
        setWithOperation(self, attrib='size', operation=op, autoLog=log)
    
    History: introduced in version 1.79 to avoid exec-calls"""

    # Handle cases where attribute does not support operations (is not defined or is str).
    try:
        oldValue = getattr(self, attrib)
        oldValue = numpy.asarray(oldValue, float)

        # Calculate new value using operation
        if operation in ('', None):
            newValue = oldValue * 0 + value  # Preserves dimensions, if array
        elif operation == '+':
            newValue = oldValue + value
        elif operation == '*':
            newValue = oldValue * value
        elif operation == '-':
            newValue = oldValue - value
        elif operation == '/':
            newValue = oldValue / value
        elif operation == '**':
            newValue = oldValue ** value
        elif operation == '%':
            newValue = oldValue % value
        else:
            raise ValueError('Unsupported value "', operation, '" for operation when setting', attrib, 'in', self.__class__.__name__)
    except AttributeError as inst:
        # attribute is not set yet. Do it now in a non-updating manner
        newValue = numpy.asarray(value, float)
    except TypeError as inst:
        # Attribute is "None" or an unset attributeSetter. This is a sign that we are just initing
        if oldValue is None or isinstance(oldValue, attributeSetter) and operation in ('', None):
            newValue = numpy.asarray(value, float)
        elif value is None:
            # Not an operation, but let's be friendly...
            newValue = value
        else:
            raise TypeError
    except ValueError:
        # The old value is a string, typical of a color change from named to e.g. rgb.
        if type(oldValue) is str and operation in ('', None):
            newValue = numpy.asarray(value, float)
        else:
            raise ValueError
    except Exception:
        # We do not accept other exceptions!
        raise Exception
    finally:
        # Set new value, with or without callback to attributeSetters
        if stealth:
            self.__dict__[attrib] = newValue
        # Control logging with self.autoLog in case an attributeSetter is listening
        else:
            callAttributeSetter(self, attrib, newValue, autoLog)

def logAttrib(self, log, attrib, value=None):
    """
    Logs a change of a visual attribute on the next window.flip.
    If value=None, it will take the value of self.attrib.
    """
    if log or log is None and self.autoLog:
        if value is None:
            value = getattr(self, attrib)
        self.win.logOnFlip("Set %s %s=%s" %(self.name, attrib, value),
            level=logging.EXP,obj=self)
