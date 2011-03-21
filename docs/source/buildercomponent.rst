.. _buildercomponent:

Notes on making a new builder component:
=====================================

Builder components are auto-detected and displayed to the experimenter as icons (builder, right panel). This makes it straightforward to add new ones.

To get started, find the directory psychopy/app/builder/components/ . Take a look at several existing components (such as 'patch.py'), and key files including '_base.py' and '_visual.py'.

There are three main steps, the first being by far the most involved.

Step 1. Make a new file: 'newcomp.py'
=================

Its pretty straightforward to model a new component on one of the existing ones. Be prepared to specify what your component needs to do at several different points in time: before the first trial, every frame, at the end of each routine, and at the end of the experiment. In addition, you may need to sacrifice some complexity in order to keep things streamlined enough for a Builder. 

Your new component class (in 'newcomp.py') will probably inherit from either BaseComponent (_base.py) or VisualComponent (_visual.py). You may need to rewrite some or all some of these methods, to override default behavior.::

    class NewcompComponent(BaseComponent): # or (VisualComponent)
        def __init__(<lots of stuff>):
        def writeInitCode(self, buff):
        def writeRoutineStartCode(self, buff):
        def writeFrameCode(self, buff):
        def writeRoutineEndCode(self, buff):

Note that while writing a new component, if there's a syntax error in newcomp.py, the whole app (psychopy) is likely to fail to start (because components are auto-detected and loaded).

In addition, you may need to edit settings.py, which writes out the set-up code for the whole experiment (e.g., to define the window). For example, this was necessary for ApertureComponent, to pass "allowStencil=True" to the window creation.

Your new component writes code into a buffer that becomes an executable python file, xxx_lastrun.py (where xxx is whatever the experimenter
specifies when saving from the builder, xxx.psyexp). You will do a bunch of this kind of call in your newcomp.py file::

   buff.writeIndented(your_python_syntax_string_here)

xxx_lastrun.py is the file that gets built when you run xxx.psyexp from the builder. So you will want to look at xxx_lastrun.py when developing your component. If you run from the builder and get a tiny, blank window ("Psychopy output window"), it can mean that there's a syntax error in xxx_lastrun.py. Unfortunately, it seems like the error trace is lost to the world; maybe there's a way to redirect stderr somewhere for debugging?

There are several internal variables (er, python objects) that have a specific, hardcoded meaning within xxx_lastrun.py. You can expect the
following to be there, and they should only be used in the original way (or something will break for the end-user, likely in a mysterious way):
   'win' = the window
   'continueTrial' = boolean; set to False when you want to end the trial (prior to a time-out based on duration)
   'trialClock' = a core.Clock() for the current trial
   't' = time within the trial loop, referenced to trialClock

These variable names are an area of active development, so this list may well be out of date. (If so, you might consider updating it or posting a note to psychopy-dev.)

Preliminary testing suggests that there are 565 names from numpy or numpy.random, plus the following::
    ['KeyResponse', '__builtins__', '__doc__', '__file__', '__name__', '__package__', 'buttons', 'continueTrial', 'core', 'data', 'dlg', 'event', 'expInfo', 'expName', 'filename', 'gui', 'logFile', 'os', 'psychopy', 'sound', 't', 'theseKeys', 'trialClock', 'visual', 'win', 'x', 'y']

self.params is a key construct that you build up in __init__. You need name, startTime, duration, and several other params to be defined or you get errors. 'name' should be of type 'code'.

To indicate that a param should be considered as an advanced feature, add it to the list self.params['advancedParams']. The the GUI shown to the experimenter will initially hides it as an option. Nice, easy.

During development, I found it helpful at times to save the params and values into the xxx_lastrun.py file as comments::

    def writeInitCode(self,buff):
        # for debugging during component development:
        buff.writeIndented("# self.params for aperture:\n")
        for p in self.params.keys():
            if p != 'advancedParams':
                buff.writeIndented("# %s: %s <type %s>\n" % (p, self.params[p].val, self.params[p].valType))    

A lot more detail can be infered from Jon's code.

Making things loop-compatible looks interesting.

Step 2. Make an icon: 'newcomp.png':
=================
Using your favorite image software, make an icon for your component, 'newcomp.png'. Dimensions = 48 x 36  (or 48 x 48) seem good. Put it in the components directory.

In 'newcomp.py', have a line near the top::

   iconFile = path.join(thisFolder, 'newcomp.png')

Step 3.  Write some documentation: 'newcomp.rst':
=================
Just make a text file that ends in .rst ("restructured text"), and put it in psychopy/docs/source/builder/components/ . It will get auto-formatted and end up at http://www.psychopy.org/builder/components/newcomp.html

