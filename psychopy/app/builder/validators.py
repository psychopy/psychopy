#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
Module containing validators for various parameters.
"""
from __future__ import absolute_import, print_function

from past.builtins import basestring
import wx

import psychopy.experiment.utils
from psychopy.localization import _translate
from . import experiment
from .localizedStrings import _localized
from pkg_resources import parse_version

if parse_version(wx.__version__) < parse_version('4.0.0a1'):
    _ValidatorBase = wx.PyValidator
else:
    _ValidatorBase = wx.Validator

from pyglet.window import key


class BaseValidator(_ValidatorBase):
    """
    Component name validator for _BaseParamsDlg class. It depends on access
    to an experiment namespace.

    Validate calls check, which needs to be implemented per class.

    Messages are passed to user as text in nameOklabel.

    @see: _BaseParamsDlg
    """

    def __init__(self):
        super(BaseValidator, self).__init__()

    def Clone(self):
        return self.__class__()

    def Validate(self, parent):
        """
        """
        # we need to find the dialog to which the Validate event belongs
        # (the event might be fired by a sub-panel and won't have builder exp)
        while not hasattr(parent, 'frame'):
            try:
                parent = parent.GetParent()
            except Exception:
                print("Couldn't find the root dialog for this event")
        message, valid = self.check(parent)
        self.updateMessage(parent)
        return valid

    def TransferFromWindow(self):
        return True

    def TransferToWindow(self):
        return True

    def check(self, parent):
        raise NotImplementedError

    def updateMessage(self, parent):
        """Checks the dict of warning messages for the parent and inserts the
        top one
        :param parent: a component params dialog
        :param message: a
        :return:
        """
        warnings = [w for w in list(parent.warningsDict.values()) if w] or ['']
        msg = warnings[0]
        if parent.nameOKlabel and parent.nameOKlabel.GetLabel() != msg:
            parent.nameOKlabel.SetLabel(msg)
            parent.Layout()


class NameValidator(BaseValidator):
    """Validation checks if the value in Name field is a valid Python
    identifier and if it does not clash with existing names.
    """

    def __init__(self):
        super(NameValidator, self).__init__()

    def check(self, parent):
        """checks namespace, return error-msg (str), enable (bool)
        """
        control = self.GetWindow()
        newName = control.GetValue()
        msg, OK = '', True  # until we find otherwise
        if newName == '':
            msg = _translate("Missing name")
            OK = False
        else:
            namespace = parent.frame.exp.namespace
            used = namespace.exists(newName)
            sameAsOldName = bool(newName == parent.params['name'].val)
            if used and not sameAsOldName:
                msg = _translate("That name is in use (by %s). Try another name.") % used
                OK = False
            elif not namespace.isValid(newName):  # valid as a var name
                msg = _translate("Name must be alpha-numeric or _, no spaces")
                OK = False
            # warn but allow, chances are good that its actually ok
            elif namespace.isPossiblyDerivable(newName):
                msg = _translate(namespace.isPossiblyDerivable(newName))
                OK = True
        parent.warningsDict['name'] = msg
        return msg, OK


class CodeSnippetValidator(BaseValidator):
    """Validation checks if field value is intended to be Python code.
    If so, check that it is valid Python, and if valid, check whether
    it contains bad identifiers (currently only self-reference).

    @see: _BaseParamsDlg
    """

    def __init__(self, fieldName):
        super(CodeSnippetValidator, self).__init__()
        self.fieldName = fieldName
        try:
            self.displayName = _localized[fieldName]
        except KeyError:
            # should have all _localized[fieldName] from .localizedStrings
            # might as well try to do something useful if fail:
            self.displayName = _translate(fieldName)

    def Clone(self):
        return self.__class__(self.fieldName)

    def check(self, parent):
        """Checks python syntax of code snippets, and for self-reference.

        Note: code snippets simply use existing names in the namespace,
        like from condition-file headers. They do not add to the
        namespace (unlike Name fields).

        Code snippets in param fields will often be user-defined
        vars, especially condition names. Can also be expressions like
        random(1,100). Hard to know what will be problematic.
        But its always the case that self-reference is wrong.
        """
        # first check if there's anything to validate (and return if not)

        def _checkParamUpdates(parent):
            """Checks whether param allows updates. Returns bool."""
            if parent.params[self.fieldName].allowedUpdates is not None:
                # Check for new set with elements common to lists compared - True if any elements are common
                return bool(set(parent.params[self.fieldName].allowedUpdates) & set(allowedUpdates))

        def _highlightParamVal(parent, error=False):
            """Highlights text containing error - defaults to black"""
            try:
                if error:
                    parent.paramCtrls[self.fieldName].valueCtrl.SetForegroundColour("Red")
                else:
                    parent.paramCtrls[self.fieldName].valueCtrl.SetForegroundColour("Black")
            except KeyError:
                pass

        control = self.GetWindow()
        if not hasattr(control, 'GetValue'):
            return '', True
        val = control.GetValue()  # same as parent.params[self.fieldName].val
        if not isinstance(val, basestring):
            return '', True

        field = self.fieldName
        msg, OK = '', True  # until we find otherwise
        _highlightParamVal(parent)
        codeWanted = psychopy.experiment.utils.unescapedDollarSign_re.search(val)
        isCodeField = bool(parent.params[self.fieldName].valType == 'code')
        allowedUpdates = ['set every repeat', 'set every frame']

        # Check if variable incorrectly defined in correct answer
        allKeyBoardKeys = list(key._key_names.values()) + [str(num) for num in range(10)]
        if self.fieldName == 'correctAns' and not val.startswith('$'):
            if ',' in val:  # comma separated
                keyList = val.upper().split(',')
                keyList = [thisKey.replace(' ', '') for thisKey in keyList if len(thisKey) > 0]
            else:  # whitespace separated
                keyList = val.upper().split(' ')
                keyList = [thisKey.replace(' ', '') for thisKey in keyList if len(thisKey) > 0]

            potentialVars = list(set(keyList) - set(allKeyBoardKeys))  # Elements of keyList not in allKeyBoardKeys
            _highlightParamVal(parent, bool(potentialVars))
            if len(potentialVars):
                msg = _translate("It looks like your 'Correct answer' contains a variable - prepend variables with '$' e.g. ${val}")
                msg = msg.format(val=potentialVars[0].lower())

        if codeWanted or isCodeField:
            # get var names from val, check against namespace:
            code = experiment.getCodeFromParamStr(val)
            try:
                names = compile(code, '', 'exec').co_names
            except SyntaxError as e:
                # empty '' compiles to a syntax error, ignore
                if not code.strip() == '':
                    _highlightParamVal(parent, True)
                    msg = _translate('Python syntax error in field `{}`:  {}')
                    msg = msg.format(self.displayName, code)
                    OK = False
            else:
                # Check whether variable param entered as a constant
                if isCodeField and _checkParamUpdates(parent):
                    if parent.paramCtrls[self.fieldName].getUpdates() not in allowedUpdates:
                        try:
                            eval(code)
                        except NameError as e:
                            _highlightParamVal(parent, True)
                            msg = _translate("Looks like your variable '{code}' in '{displayName}' should be set to update.")
                            msg = msg.format(code=code, displayName=self.displayName)
                        except SyntaxError as e:
                            msg = ''

                # namespace = parent.frame.exp.namespace
                # parent.params['name'].val is not in namespace for new params
                # and is not fixed as .val until dialog closes. Use getvalue()
                # to handle dynamic changes to Name field:
                if 'name' in parent.paramCtrls:  # some components don't have names
                    parentName = parent.paramCtrls['name'].getValue()
                    for name in names:
                        # `name` means a var name within a compiled code snippet
                        if name == parentName:
                            _highlightParamVal(parent, True)
                            msg = _translate(
                                'Python var `{}` in `{}` is same as Name')
                            msg = msg.format(name, self.displayName)
                            OK = True


        parent.warningsDict[field] = msg
        return msg, OK
