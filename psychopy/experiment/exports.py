#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Experiment classes:
    Experiment, Flow, Routine, Param, Loop*, *Handlers, and NameSpace

The code that writes out a *_lastrun.py experiment file is (in order):
    experiment.Experiment.writeScript() - starts things off, calls other parts
    settings.SettingsComponent.writeStartCode()
    experiment.Flow.writeBody()
        which will call the .writeBody() methods from each component
    settings.SettingsComponent.writeEndCode()
"""

import io
import keyword
import re

import psychopy
from psychopy import constants
from psychopy.localization import _translate
from .components.settings import _numpyImports, _numpyRandomImports
from .utils import nonalphanumeric_re, valid_var_re

# predefine some regex's; deepcopy complains if do in NameSpace.__init__()


class IndentingBuffer(io.StringIO):

    def __init__(self, target='PsychoPy', initial_value='', newline='\n'):
        io.StringIO.__init__(self, initial_value, newline)
        self.oneIndent = "    "
        self.indentLevel = 0
        self._writtenOnce = []
        self.target = target  # useful to keep track of what language is written here

    def writeIndented(self, text):
        """Write to the StringIO buffer, but add the current indent.
        Use write() if you don't want the indent.

        To test if the prev character was a newline use::
            self.getvalue()[-1]=='\n'

        """
        for line in text.splitlines(keepends=True):
            self.write(self.oneIndent * self.indentLevel + line)

    def writeIndentedLines(self, text):
        """As writeIndented(text) except that each line in text gets
        the indent level rather than the first line only.
        """
        if not text.endswith("\n"):
            text += "\n"
        self.writeIndented(text)

    def writeOnceIndentedLines(self, text):
        """Add code to the experiment that is only run exactly once,
        (typically this is used to write the writeOnceInit sections after
        all `import`s were done but before Window creation).

        Parameters
        ----------
        text : str
            The code to run. May include newline characters to write several
            lines of code at once.

        Notes
        -----
        For running an `import`, use meth:~`Experiment.requireImport` or
        :meth:~`Experiment.requirePsychopyLibs` instead.

        See also
        --------
        :meth:~`Experiment.requireImport`,
        :meth:~`Experiment.requirePsychopyLibs`
        """
        if text not in self._writtenOnce:
            self.writeIndentedLines(text)
            self._writtenOnce.append(text)

    def setIndentLevel(self, newLevel, relative=False):
        """Change the indent level for the buffer to a new value.

        Set relative to True to increment or decrement the current value.
        """
        if relative:
            self.indentLevel += newLevel
        else:
            self.indentLevel = newLevel

    def write(self, text):
        io.StringIO.write(self, "{}".format(text))


# noinspection PyUnresolvedReferences
class NameSpace:
    """class for managing variable names in builder-constructed experiments.

    The aim is to help detect and avoid name-space collisions from
    user-entered variable names.
    Track four groups of variables:
        numpy =    part of numpy or numpy.random
        psychopy = part of psychopy, such as event or data; include os here
        builder =  used internally by the builder when constructing an expt
        user =     used 'externally' by a user when programming an experiment
    Some vars, like core, are part of both psychopy and numpy, so the order of
    operations can matter

    Notes for development:
    are these all of the ways to get into the namespace?
    - import statements at top of file: numpy, psychopy, os, etc
    - a handful of things that always spring up automatically, like t and win
    - routines: user-entered var name = routine['name'].val, plus sundry
        helper vars, like theseKeys
    - flow elements: user-entered = flowElement['name'].val
    - routine & flow from either GUI or .psyexp file
    - each routine and flow element potentially has a ._clockName,
        loops have thisName, albeit thisNam (missing end character)
    - column headers in condition files
    - abbreviating parameter names (e.g. rgb=thisTrial.rgb)

    :Author:
        2011 Jeremy Gray
    """

    def __init__(self, exp):
        """Set-up an experiment's namespace: reserved words and user space
        """
        super(NameSpace, self).__init__()
        self.exp = exp
        # deepcopy fails if you pre-compile regular expressions and stash here

        self.numpy = _numpyImports + _numpyRandomImports + ['np']
        # noinspection PyUnresolvedReferences
        self.keywords = keyword.kwlist + dir(__builtins__) + ['self']
        # these are based on a partial test, known to be incomplete:
        self.psychopy = psychopy.__all__ + ['psychopy', 'os']
        self.constants = dir(constants)
        self.builder = ['KeyResponse', 'keyboard', 'buttons',
                        'continueRoutine', 'expInfo', 'expName', 'thisExp',
                        'filename', 'logFile', 'paramName',
                        't', 'frameN', 'currentLoop', 'dlg', '_thisDir',
                        'endExpNow',
                        'globalClock', 'routineTimer', 'frameDur',
                        'theseKeys', 'win', 'x', 'y', 'level', 'component',
                        'thisComponent']
        # user-entered, from Builder dialog or conditions file:
        self.user = []
        self.nonUserBuilder = self.numpy + self.keywords + self.psychopy

    def __str__(self, numpy_count_only=True):
        varibs = self.user + self.builder + self.psychopy
        if numpy_count_only:
            return "%s + [%d numpy]" % (str(varibs), len(self.numpy))
        return str(varibs + self.numpy)

    @property
    def all(self):
        return (
                self.builder +
                self.constants +
                self.keywords +
                self.nonUserBuilder +
                self.numpy +
                self.psychopy +
                self.user
        )

    def getCategories(self, name):
        """
        Get list of categories in which a given name is found.

        Parameters
        ----------
        name : str
            Name to look for
        """
        # Define possible categories
        categories = (
            "builder",
            "constants",
            "keywords",
            "nonUserBuilder",
            "numpy",
            "psychopy",
            "user"
        )
        # Check for name in each category
        found = []
        for cat in categories:
            if name in getattr(self, cat):
                found.append(cat)

        return found



    def getDerived(self, basename):
        """ buggy
        idea: return variations on name, based on its type, to flag name that
        will come to exist at run-time;
        more specific than is_possibly-derivable()
        if basename is a routine, return continueBasename and basenameClock,
        if basename is a loop, return makeLoopIndex(name)
        """
        derived_names = []
        for flowElement in self.exp.flow:
            if flowElement.getType() in ('LoopInitiator', 'LoopTerminator'):
                flowElement = flowElement.loop  # we want the loop itself
                # basename can be <type 'instance'>
                derived_names += [self.makeLoopIndex(basename)]
            if (basename == str(flowElement.params['name']) and
                    basename + 'Clock' not in derived_names):
                derived_names += [basename + 'Clock',
                                  'continue' + basename.capitalize()]
        # other derived_names?
        #
        return derived_names

    def getCollisions(self):
        """return None, or a list of names in .user that are also in
        one of the other spaces
        """
        standard = set(self.builder + self.psychopy + self.numpy)
        duplicates = list(set(self.user).intersection(standard))
        su = sorted(self.user)
        duplicates += [var for i, var in enumerate(su)
                       if i < len(su) - 1 and su[i + 1] == var]
        return duplicates or None

    def isValid(self, name):
        """var-name compatible? return True if string name is
        alphanumeric + underscore only, with non-digit first
        """
        return bool(valid_var_re.match(name))

    def isPossiblyDerivable(self, name):
        """catch all possible derived-names, regardless of whether currently
        """
        derivable = (name.startswith('this') or
                     name.startswith('these') or
                     name.startswith('continue') or
                     name.endswith('Clock') or
                     name.lower().find('component') > -1)
        if derivable:
            return (" Avoid `this`, `these`, `continue`, `Clock`,"
                    " or `component` in name")
        return None

    def exists(self, name):
        """returns None, or a message indicating where the name is in use.
        cannot guarantee that a name will be conflict-free.
        does not check whether the string is a valid variable name.

        >>> exists('t')
        Builder variable
        """
        try:
            name = str(name)  # convert from unicode if possible
        except Exception:
            pass

        # check getDerived:

        # check in this order: return unlocalized value
        if name in self.user:
            return "one of your Components, Routines, or condition parameters"
        if name in self.builder:
            return "Builder variable"
        if name in self.psychopy:
            return "Psychopy module"
        if name in self.numpy:
            return "numpy function"
        if name in self.keywords:
            return "python keyword"

        return  # None, meaning does not exist already

    def add(self, name, sublist='default'):
        """add name to namespace by appending a name or list of names to a
        sublist, eg, self.user
        """
        if name is None:
            return
        if sublist == 'default':
            sublist = self.user
        if not isinstance(name, list):
            sublist.append(name)
        else:
            sublist += name

    def remove(self, name, sublist='default'):
        """remove name from the specified sublist (and hence from the
        name-space), eg, self.user
        """
        if name is None:
            return
        if sublist == 'default':
            sublist = self.user
        if not isinstance(name, list):
            name = [name]
        for n in list(name):
            if n in sublist:
                del sublist[sublist.index(n)]

    def rename(self, name, newName, sublist='default'):
        if name is None:
            return
        if sublist == 'default':
            sublist = self.user
        if not isinstance(name, list):
            name = [name]
        for n in list(name):
            if n in sublist:
                sublist[sublist.index(n)] = newName

    def makeValid(self, name, prefix='var'):
        """given a string, return a valid and unique variable name.
        replace bad characters with underscore, add an integer suffix until
        its unique

        >>> makeValid('Z Z Z')
        'Z_Z_Z'
        >>> makeValid('a')
        'a'
        >>> makeValid('a')
        'a_2'
        >>> makeValid('123')
        'var_123'
        """

        # make it legal:
        try:
            # convert from unicode, flag as uni if can't convert
            name = str(name)
        except Exception:
            prefix = 'uni'
        if not name:
            name = prefix + '_1'
        if name[0].isdigit():
            name = prefix + '_' + name
        # replace all bad chars with _
        name = nonalphanumeric_re.sub('_', name)

        # try to make it unique; success depends on accuracy of self.exists():
        i = 2  # skip _1: user can rename the first one to be _1 if desired
        # maybe it already has _\d+? if so, increment from there
        if self.exists(name) and '_' in name:
            basename, count = name.rsplit('_', 1)
            try:
                i = int(count) + 1
                name = basename
            except Exception:
                pass
        nameStem = name + '_'
        while self.exists(name):  # brute-force a unique name
            name = nameStem + str(i)
            i += 1
        return name

    def makeLoopIndex(self, name):
        """return a valid, readable loop-index name:
            'this' + (plural->singular).capitalize() [+ (_\\d+)]
        """
        try:
            newName = str(name)
        except Exception:
            newName = name
        prefix = 'this'
        irregular = {'stimuli': 'stimulus',
                     'mice': 'mouse', 'people': 'person'}
        for plural, singular in list(irregular.items()):
            nn = re.compile(plural, re.IGNORECASE)
            newName = nn.sub(singular, newName)
        if newName.endswith('s') and newName.lower() not in list(irregular.values()):
            newName = newName[:-1]  # trim last 's'
        else:  # might end in s_2, so delete that s; leave S
            match = re.match(r"^(.*)s(_\d+)$", newName)
            if match:
                newName = match.group(1) + match.group(2)
        # retain CamelCase:
        newName = prefix + newName[0].capitalize() + newName[1:]
        newName = self.makeValid(newName)
        return newName
