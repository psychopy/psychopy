#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
Module containing validators for various parameters.
"""

import wx
from ..localization import _translate
from . import experiment
from .localizedStrings import _localized


class BaseValidator(wx.PyValidator):
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
        self.setMessage(parent, message)
        return valid

    def TransferFromWindow(self):
        return True

    def TransferToWindow(self):
        return True

    def check(self, parent):
        raise NotImplementedError

    def setMessage(self, parent, message):
        raise NotImplementedError


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
        if newName == '':
            return _translate("Missing name"), False
        else:
            namespace = parent.frame.exp.namespace
            used = namespace.exists(newName)
            sameAsOldName = bool(newName == parent.params['name'].val)
            if used and not sameAsOldName:
                msg = _translate(
                    "That name is in use (by %s). Try another name.")
                return msg % used, False
            elif not namespace.isValid(newName):  # valid as a var name
                msg = _translate("Name must be alpha-numeric or _, no spaces")
                return msg, False
            # warn but allow, chances are good that its actually ok
            elif namespace.isPossiblyDerivable(newName):
                msg = _translate(namespace.isPossiblyDerivable(newName))
                return msg, True
            else:
                return "", True

    def setMessage(self, parent, message):
        parent.nameOKlabel.SetLabel(message)


class CodeSnippetValidator(BaseValidator):
    """Validation checks if field value is intended to be Python code.
    If so, check that it is valid Python, and if valid, check whether
    it contains bad identifiers (currently only self-reference).

    @see: _BaseParamsDlg
    """
    # class attribute: dict of {fieldName: message} to handle all messages
    clsWarnings = {}

    def __init__(self, fieldName):
        super(CodeSnippetValidator, self).__init__()
        self.fieldName = fieldName
        try:
            self.displayName = _localized[fieldName]
        except KeyError:
            # should have all _localized[fieldName] from .localizedStrings
            # might as well try to do something useful if fail:
            self.displayName = _translate(fieldName)
        self.clsWarnings[fieldName] = ''

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
        control = self.GetWindow()
        if not hasattr(control, 'GetValue'):
            return '', True
        val = control.GetValue()  # same as parent.params[self.fieldName].val
        if not isinstance(val, basestring):
            return '', True
        codeWanted = experiment._unescapedDollarSign_re.search(val)
        isCodeField = bool(parent.params[self.fieldName].valType == 'code')
        if codeWanted or isCodeField:
            # get var names from val, check against namespace:
            code = experiment.getCodeFromParamStr(val)
            try:
                names = compile(code, '', 'eval').co_names
            except SyntaxError:
                # empty '' compiles to a syntax error, ignore
                if not code.strip() == '':
                    msg = _translate('Python syntax error in field `{}`:  {}')
                    return msg.format(self.displayName, code), False
            else:
                # namespace = parent.frame.exp.namespace
                # parent.params['name'].val is not in namespace for new params
                # and is not fixed as .val until dialog closes. Use getvalue()
                # to handle dynamic changes to Name field:
                if 'name' in parent.paramCtrls:  # some components don't have names
                    parentName = parent.paramCtrls['name'].getValue()
                    for name in names:
                        # `name` means a var name within a compiled code snippet
                        if name == parentName:
                            msg = _translate(
                                'Python var `{}` in `{}` is same as Name')
                            return msg.format(name, self.displayName), False
        return '', True

    def setMessage(self, parent, message):
        """Set nameOklabel to the first warning (if any).

        Complexity: Use a single nameOklabel for warnings for all fields.
        And we want to reset a given warning to 'all clear' when fixed by
        user, but not reset all warnings.
        Solution: use a class attribute to collect warnings for all params.
        should only be one param dialog open at a time, making this possible:
        Reset clsWarnings to {} when setting up the dialog.
        """
        self.clsWarnings[self.fieldName] = message
        warnings = [w for w in self.clsWarnings.values() if w] or ['']
        if parent.nameOKlabel:
            parent.nameOKlabel.SetLabel(warnings[0])

