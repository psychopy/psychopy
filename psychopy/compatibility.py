# -*- coding: utf-8 -*-
import codecs, cPickle
import psychopy.data

######### Begin Compatibility Class Definitions #########
class _oldStyleBaseTrialHandler:
    """Please excuse these ugly kluges, but in order to unpickle
        psydat pickled trial handlers that were created using the old-style
        (pre python 2.2) class, original classes have to be defined.
    """
    pass
class _oldStyleBaseStairHandler:
    """Stubbed compapatibility class for StairHandler"""
    pass
class _oldStyleTrialHandler:
    """Stubbed compapatibility class for TrialHandler"""
    pass
class _oldStyleStairHandler:
    """Stubbed compapatibility class for StairHandler"""
    pass
######### End Compatibility Class Definitions #########

def _convertToNewStyle(newClass, oldInstance):
    """Converts un-pickled old-style compatibility classes to new-style ones
       by initializing a new-style class and copying the old compatibility
       instance's attributes.
    """
    newHandler = newClass([], 0) #Init a new new-style object
    for thisAttrib in dir(oldInstance):
        #can handle each attribute differently
        if 'instancemethod' in str(type(getattr(oldInstance,thisAttrib))):
            #this is a method
            continue
        else:
            value = getattr(oldInstance, thisAttrib)
            setattr(newHandler, thisAttrib, value)
    return newHandler


def fromFile(filename):
    """In order to switch experiment handler to the new-style (post-python 2.2, 
       circa 2001) classes, this is a proof-of-concept loader based on misc.fromFile
       that will load psydat files created with either new or old style TrialHandlers
       or StairHandlers.
       
       Since this is really just an example, it probably [hopefully] won't be 
       incorporated into upstream code, but it will work.
       
       The method will try to load the file using a normal new-style Pickle loader;
       however, if a type error occurs it will temporarily replace the new-style 
       class with a stubbed version of the old-style class and will then instantiate
       a fresh new-style class with the original attributes.
    """
    with codecs.open(filename, 'rb') as f:
        try:
            contents = cPickle.load(f) # Try to load the psydat file into the new-style class.
        except TypeError as e:
            f.seek(0)
            name = e.args[1].__name__
            if 'TrialHandler' in repr(e):
                currentHandler = psychopy.data.TrialHandler
                psychopy.data.TrialHandler = _oldStyleTrialHandler # Temporarily replace new-style class
                old_contents = cPickle.load(f)
                psychopy.data.TrialHandler = currentHandler
                contents = _convertToNewStyle(psychopy.data.TrialHandler, old_contents)
            elif 'StairHandler' in repr(e):
                currentHandler = psychopy.data.StairHandler
                psychopy.data.StairHandler = _oldStyleStairHandler # Temporarily replace new-style class
                old_contents = cPickle.load(f)
                psychopy.data.StairHandler = currentHandler
                contents = _convertToNewStyle(psychopy.data.StairHandler, old_contents)
            else:
                raise TypeError, ("Didn't recognize %s" % name)

	return contents
