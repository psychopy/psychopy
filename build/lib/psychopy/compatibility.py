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
class _oldStyleMultiStairHandler:
    """Stubbed compapatibility class for MultiStairHandler"""
    pass
######### End Compatibility Class Definitions #########

def _convertToNewStyle(newClass, oldInstance):
    """Converts un-pickled old-style compatibility classes to new-style ones
       by initializing a new-style class and copying the old compatibility
       instance's attributes.
    """
    #if the oldInstance was an ExperimentHandler it wouldn't throw an error related
    #to itself, but to the underlying loops within it. So check if we have that and then
    #do imports on each loop
    if oldInstance.__class__.__name__=='ExperimentHandler':
        newHandler = psychopy.data.ExperimentHandler()
        #newClass() #Init a new new-style object
    else:
        newHandler = newClass([], 0) #Init a new new-style object
    for thisAttrib in dir(oldInstance):
        #can handle each attribute differently
        if 'instancemethod' in str(type(getattr(oldInstance,thisAttrib))):
            #this is a method
            continue
        elif thisAttrib=='__weakref__':
            continue
        else:
            value = getattr(oldInstance, thisAttrib)
            setattr(newHandler, thisAttrib, value)
    return newHandler


def fromFile(filename):
    """In order to switch experiment handler to the new-style (post-python 2.2,
       circa 2001) classes, this is a proof-of-concept loader based on tools.filetools.fromFile
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
            if name == 'TrialHandler':
                currentHandler = psychopy.data.TrialHandler
                psychopy.data.TrialHandler = _oldStyleTrialHandler # Temporarily replace new-style class
                old_contents = cPickle.load(f)
                psychopy.data.TrialHandler = currentHandler
                contents = _convertToNewStyle(psychopy.data.TrialHandler, old_contents)
            elif name == 'StairHandler':
                currentHandler = psychopy.data.StairHandler
                psychopy.data.StairHandler = _oldStyleStairHandler # Temporarily replace new-style class
                old_contents = cPickle.load(f)
                psychopy.data.StairHandler = currentHandler
                contents = _convertToNewStyle(psychopy.data.StairHandler, old_contents)
            elif name == 'MultiStairHandler':
                newStair = psychopy.data.StairHandler
                newMulti = psychopy.data.MultiStairHandler
                psychopy.data.StairHandler = _oldStyleStairHandler # Temporarily replace new-style class
                psychopy.data.MultiStairHandler = _oldStyleMultiStairHandler # Temporarily replace new-style class
                old_contents = cPickle.load(f)
                psychopy.data.MultiStairHandler = newMulti
                psychopy.data.StairHandler = newStair # Temporarily replace new-style class
                contents = _convertToNewStyle(psychopy.data.MultiStairHandler, old_contents)
            else:
                raise TypeError, ("Didn't recognize %s" % name)
    return contents

def checkCompatibility(old, new, prefs=None, fix=True):
    """Check for known compatibility issue between a pair of versions and fix
    automatically if possible. (This facility, and storing the most recently run
    version of the app, was added in version 1.74.00)

    usage::

        ok, msg =  checkCompatibility(old, new, prefs, fix=True)

    prefs is a standard psychopy preferences object. It isn't needed by all checks
    but may be useful.
    This function can be used simply to check for issues by setting fix=False
    """
    if old==new:
        return 1,"" #no action needed
    if old>new:#switch them over
        old,new=new,old

    msg="From %s to %s:" %(old, new)
    warning = False
    if old[0:4]<'1.74':
        msg += "\n\nThere were many changes in version 1.74.00 that will break" + \
            "\ncompatibility with older versions. Make sure you read the changelog carefully" + \
            "\nbefore using this version. Do not upgrade to this version halfway through an experiment.\n"
        if fix and 'PatchComponent' not in prefs.builder['hiddenComponents']:
            prefs.builder['hiddenComponents'].append('PatchComponent')
        warning = True
    if not warning:
        msg+= "\nNo known compatibility issues"
    return (not warning), msg
