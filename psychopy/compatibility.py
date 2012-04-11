import codecs
import cPickle
import psychopy.data

def legacy_load(filename):
    """In order to switch experiment handler to the new-style (post-python 2.2, 
       circa 2001) classes, this is a proof-of-concept loader based on misc.fromFile
       that will load psydat files created with either new or old style TrialHandlers.
       
       Since this is really just an example, it probably [hopefully] won't be 
       incorporated into upstream code, but it will work.
       
       The method will try to load the file using a normal new-style Pickle loader;
       however, if a type error occurs it will temporarily replace the new-style 
       class with a stubbed version of the old-style class and will then instantiate
       a fresh new-style class with the original attributes.
    """
    with open(filename, 'rb') as f:
        try:
            contents = cPickle.load(f) # Try to load the psydat file into the new-style class.
        except TypeError:
            f.seek(0)
            current_trialHandler = psychopy.data.TrialHandler
            psychopy.data.TrialHandler = psychopy.data._oldStyleTrialHandler # Temporarily replace new-style class
            old_contents = cPickle.load(f)
            psychopy.data.TrialHandler = current_trialHandler
            contents = old_contents._convertToNewStyle()

	return contents
