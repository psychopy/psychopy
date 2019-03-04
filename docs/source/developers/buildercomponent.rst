.. _addNewComponent:

Adding a new Builder Component
=====================================

Builder Components are auto-detected and displayed to the experimenter as icons (in the right-most panel of the Builder interface panel). This makes it straightforward to add new ones.

All you need to do is create a list of parameters that the Component needs to know about (that will automatically appear in the Component's dialog) and a few pieces of code specifying what code should be called at different points in the script (e.g. beginning of the Routine, every frame, end of the study etc...). Many of these will come simply from subclassing the _base or _visual Components.

To get started, :ref:`addfeatureBranch` for the development of this component. (If this doesn't mean anything to you then see :ref:`usingRepos` )

You'll mainly be working in the directory `.../psychopy/experiment/components/`. 
Take a look at several existing Components (such as `image.py`), and key files including `_base.py` and `_visual.py`.

There are three main steps, the first being by far the most involved.

1. Create the file defining the component: newcomp.py
-------------------

It's most straightforward to model a new Component on one of the existing ones. Be prepared to specify what your Component needs to do at several different points in time: the first trial, every frame, at the end of each routine, and at the end of the experiment. In addition, you may need to sacrifice some complexity in order to keep things streamlined enough for a Builder (see e.g., `ratingscale.py`).

Your new Component class (in your file `newcomp.py`) should inherit from `BaseComponent` (in `_base.py`), `VisualComponent` (in `_visual.py`), or `KeyboardComponent` (in `keyboard.py`). You may need to rewrite some or all some of these methods, to override default behavior::

    class NewcompComponent(BaseComponent): # or (VisualComponent)
        def __init__(...):
            super(NewcompComponent, self).__init__(...)
                ...
        def writeInitCode(self, buff):
        def writeRoutineStartCode(self, buff):
        def writeFrameCode(self, buff):
        def writeRoutineEndCode(self, buff):

Calling `super()` will create the basic default set of `params` that almost every component will need: `name`, `startVal`, `startType`, etc. Some of these fields may need to be overridden (e.g., `durationEstim` in `sound.py`). Inheriting from `VisualComponent` (which in turn inherits from `BaseComponent`) adds default visual params, plus arranges for Builder scripts to import `psychopy.visual`. If your component will need other libs, call `self.exp.requirePsychopyLib(['neededLib'])` (see e.g., `parallelPort.py`).

At the top of a component file is a dict named `_localized`. It contains mappings that allow a strict separation of internal string values (= used in logic, never displayed) from values used for display in the Builder interface (= for display only, possibly translated, never used in logic). The `.hint` and `.label` fields of `params['someParam']` should always be set to a localized value, either by using a dict entry such as `_localized['message']`, or via the globally available translation function, `_('message')`. Localized values must **not** be used elsewhere in a component definition.

Very occasionally, you may also need to edit `settings.py`, which writes out the set-up code for the whole experiment (e.g., to define the window). For example, this was necessary for the ApertureComponent, to pass `allowStencil=True` to the window creation.

Your new Component writes code into a buffer that becomes an executable python file, `xxx_lastrun.py` (where `xxx` is whatever the experimenter specifies when saving from the Builder, `xxx.psyexp`). You will do a bunch of this kind of call in your `newcomp.py` file::

   buff.writeIndented(your_python_syntax_string_here)

You have to manage the indentation level of the output code, see `experiment.IndentingBuffer()`.

`xxx_lastrun.py` is the file that gets built when you run `xxx.psyexp` from the Builder. So you will want to look at `xxx_lastrun.py` frequently when developing your component.

**Name-space**

There are several internal variables (i.e. names of Python objects) that have a specific, hardcoded meaning within `xxx_lastrun.py`. You can expect the
following to be there, and they should only be used in the original way (or something will break for the end-user, likely in a mysterious way)::

    win    # the window
    t      # time within the trial loop, referenced to `trialClock`
    x,  y  # mouse coordinates, but only if the experimenter uses a mouse component

Handling of variable names is under active development, so this list may well be out of date. (If so, you might consider updating it or posting a note to the PsychoPy Discourse developer forum.)

Preliminary testing suggests that there are 600-ish names from numpy or numpy.random, plus the following::

    ['KeyResponse', '__builtins__', '__doc__', '__file__', '__name__', '__package__', 'buttons', 'core', 'data', 'dlg', 'event', 'expInfo', 'expName', 'filename', 'gui', 'logFile', 'os', 'psychopy', 'sound', 't', 'visual', 'win', 'x', 'y']

Yet other names get derived from user-entered names, like `trials` --> `thisTrial`.

**Params**

`self.params` is a key construct that you build up in `__init__`. You need name, startTime, duration, and several other params to be defined or you get errors. `'name'` should be of type `'code'`.

The `Param()` class is defined in `psychopy.app.builder.experiment.Param()`. A very useful thing that Params know is how to create a string suitable for writing into the .py script. In particular, the `__str__` representation of a Param will format its value (`.val`) based on its type (`.valType`) appropriately. This means that you don't need to check or handle whether the user entered a plain string, a string with a code trigger character (`$`), or the field was of type `code` in the first place. If you simply request the `str()` representation of the param, it is formatted correctly.

To indicate that a param (eg, `thisParam`) should be considered as an advanced feature, set its category to advanced: `self.params['thisParam'].categ = 'Advanced'`. Then the GUI shown to the experimenter will automatically place it on the 'Advanced' tab. Other categories work similarly (`Custom`, etc).

During development, it can sometimes be helpful to save the params into the `xxx_lastrun.py` file as comments, so you can see what is happening::

    def writeInitCode(self,buff):
        # for debugging during Component development:
        buff.writeIndented("# self.params for aperture:\n")
        for p in self.params:
            try: buff.writeIndented("# %s: %s <type %s>\n" % (p, self.params[p].val, self.params[p].valType))
            except: pass

A lot more detail can be inferred from existing components.

Making things loop-compatible looks interesting -- see `keyboard.py` for an example, especially code for saving data at the end.

Notes & gotchas
----------------

    *syntax errors in new_comp.py:*
        The PsychoPy app will fail to start if there are syntax error in any of the components that are auto-detected. Just correct them and start the app again.

    *param[].val:*
        If you have a boolean variable (e.g., `my_flag`) as one of your params, note that `self.param["my_flag"]` is always True (the param exists --> True). So in a boolean context you almost always want the `.val` part, e.g., `if self.param["my_flag"].val:`.

        However, you do not always want `.val`. Specifically, in a string/unicode context (= to trigger the self-formatting features of Param()s), you almost always want `"%s" % self.param['my_flag']`, without `.val`. Note that it's better to do this via `"%s"` than `str()` because `str(self.param["my_flag"])` coerces things to type str (squashing unicode) whereas `%s` works for both str and unicode.

    *Travis testing*
        Before submitting a pull request with the new component, you should regenerate the `componsTemplate.txt` file. This is a text file that lists the attributes of all of the user interface settings and options in the various components. It is used during the Travis automated testing process when a pull request is submitted to GitHub, allowing the detection of errors that may have been caused in refactoring. Your new component needs to have entries added to this file if the Travis testing is going to pass successfully.
        
        To re-generate the file, cd to this directory `.../psychopy/tests/test_app/test_builder/` and run::

        `python genComponsTemplate.py --out`

        This will over-write the existing file so you might want to make a copy in case the process fails. *Compatibility issues:* As at May 2018, that script is not yet Python 3 compatible, and on a Mac you might need to use `pythonw`.

2. Icon: newcomp.png
------------------------
Using your favorite image software, make an icon for your Component with a descriptive name, e.g., `newcomp.png`. Dimensions = 48 × 48. Put it in the components directory.

In `newcomp.py`, have a line near the top::

   iconFile = path.join(thisFolder, 'newcomp.png')

3. Documentation: newcomp.rst
---------------------------------
Just make a descriptively-named text file that ends in `.rst` ("restructured text"), and put it in `psychopy/docs/source/builder/components/` . It will get auto-formatted and end up at `http://www.psychopy.org/builder/components/newcomp.html`
