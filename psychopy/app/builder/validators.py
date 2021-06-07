#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Module containing validators for various parameters.
"""
from __future__ import absolute_import, print_function

import re
from past.builtins import basestring
import wx
import psychopy.experiment.utils
from psychopy.localization import _translate
from . import experiment
from .localizedStrings import _localized
from pkg_resources import parse_version
from ...visual.textbox2.fontmanager import FontManager
from ...data.utils import listFromString
from pyglet.window import key

fontMGR = FontManager()

if parse_version(wx.__version__) < parse_version('4.0.0a1'):
    _ValidatorBase = wx.PyValidator
else:
    _ValidatorBase = wx.Validator

# Symbolic constants representing the 'kind' of warning for instances of
# `ValidatorWarning`.
VALIDATOR_WARNING_NONE = 0
VALIDATOR_WARNING_NAME = 1
VALIDATOR_WARNING_SYNTAX = 2
VALIDATOR_WARNING_COUNT = 3  # increment when adding more


class ValidatorWarning(object):
    """Class for validator warnings.

    These are used internally by the `WarningManager`, do not create instances
    of this class unless you know what you're doing with them.

    Parameters
    ----------
    parent : wx.Window or wx.Panel
        Dialog associate with this warning.
    control : wx.Window or wx.Panel
        Control associated with the validator which threw this warning.
    msg : str
        Message text associated with the warning to be displayed.
    kind : int
        Symbolic constant representing the type of warning. Values can be one of
        `VALIDATOR_WARNING_NONE`, `VALIDATOR_WARNING_NAME` or
        `VALIDATOR_WARNING_SYNTAX`.

    """
    __slots__ = [
        '_parent',
        '_control',
        '_msg',
        '_kind']

    def __init__(self, parent, control, msg="", kind=VALIDATOR_WARNING_NONE):
        self.parent = parent
        self.control = control
        self.msg = msg
        self.kind = kind

    @property
    def parent(self):
        """Dialog associate with this warning (`wx.Window` or similar)."""
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def control(self):
        """Control associated with the validator which threw this warning
        (`wx.Window` or similar).
        """
        return self._control

    @control.setter
    def control(self, value):
        self._control = value

    @property
    def msg(self):
        """Message text associated with the warning to be displayed (`str`).
        """
        return self._msg

    @msg.setter
    def msg(self, value):
        self._msg = str(value)

    @property
    def kind(self):
        """Symbolic constant representing the type of warning (`int`). Values
        can be one of `VALIDATOR_WARNING_NONE`, `VALIDATOR_WARNING_NAME` or
        `VALIDATOR_WARNING_SYNTAX`.
        """
        return self._kind

    @kind.setter
    def kind(self, value):
        value = int(value)
        assert VALIDATOR_WARNING_NONE <= value < VALIDATOR_WARNING_COUNT
        self._kind = value


class WarningManager(object):
    """Manager for warnings produced by validators associate with controls
    within the component properties dialog. Assumes that the `parent` dialog
    uses a standardized convention for attribute names for all components.

    Each control can only have a single warning at a time in the current
    implementation of this class.

    Parameters
    ----------
    parent : wx.Window
        Component properties dialog or panel.

    """
    def __init__(self, parent):
        self._parent = parent
        # Dictionary for storing warnings, keys are IDs for the controls that
        # produced them. In the future we should use wx object names to
        # reference these objects instead of IDs.
        self._warnings = {}

    @property
    def parent(self):
        """Parent dialog (`wx.Panel` or `wx.Window`). This attribute is
        read-only."""
        return self._parent

    @property
    def warnings(self):
        """Raw dictionary of warning objects (`dict`). Keys are IDs for the
        objects representing controls as integers, values are the
        `ValidatorWarning` instances associated with them."""
        return self._parent

    @property
    def messages(self):
        """List of warning messages (`list`). Messages are displayed in the
        order they have been added.
        """
        if not self._warnings:  # no warnings, return empty string
            return []

        warnings = self._warnings.values()  # warning objects
        return [warning.msg for warning in warnings]

    def getControlsWithWarnings(self):
        """Get a list of controls which have active warnings (`list`). You can
        use this to re-validate any controls which have warnings still.
        """
        if not self._warnings:  # no active warnings
            return []

        _, warnings = self._warnings.items()
        return [warning.control for warning in warnings]

    def setWarning(self, control, msg='', kind=VALIDATOR_WARNING_NONE):
        """Set a warning for a control. A control can only have one active
        warning associate with it at any given time.

        Parameters
        ----------
        control : wx.Window or wx.Panel
            Control to set an active warning for.
        msg : str
            Warning message text (e.g., "Syntax error").
        kind : int
            Symbolic constant representing the type of warning (e.g.,
            `VALIDATOR_WARN_SYNTAX`).

        """
        self._warnings[id(control)] = ValidatorWarning(
            self.parent, control, msg, kind)

    def getWarning(self, control):
        """Get an active warning associated with the control.

        Parameters
        ----------
        control : wx.Window or wx.Panel
            Control to check if there is a warning active against it.

        Returns
        -------
        ValidatorWarning or None
            Warning validator if there is warning, else None.

        """
        try:
            return self._warnings[id(control)]
        except KeyError:
            return None

    def clearWarning(self, control):
        """Clear the warning associated with a given control.

        Parameters
        ----------
        control : wx.Window or wx.Panel
            Control to clear any warnings against it.

        Returns
        -------
        bool
            `True` if the warning was cleared. `False` if there was no warning
            associated with the `control` provided.

        """
        wasCleared = True
        try:
            del self._warnings[id(control)]
        except KeyError:
            wasCleared = False

        return wasCleared

    def _lockout(self, enable=True):
        """Lockout the dialog, preventing user changes from being applied.

        Parameters
        ----------
        enable : bool
            Lockout the dialog if `True`. `False` will re-enable the OK button.
            Assumes the parent dialog has an `ok` attribute which points to a
            `wx.Button` object or similar.

        """
        if hasattr(self.parent, 'ok'):
            okButton = self.parent.ok
        elif hasattr(self.parent, 'OKbtn'):  # other option ...
            okButton = self.parent.OKbtn
        else:
            raise AttributeError("Parent object does not have an Okay button.")

        if isinstance(okButton, wx.Button):
            okButton.Enable(enable)

    def showWarning(self, control):
        """Show the active warning for the control in the dialog warning text
        area.

        Parameters
        ----------
        control : wx.Window or wx.Panel
            Control to show show any active warnings for.

        """
        # Enable / disable ok button
        if not self._warnings:
            print("No warnings.")

        # If there's any errors to show, show them
        messages = self.messages
        print(messages)
        # self.output.SetLabel("\n".join(messages))
        # # Update sizer
        # sizer = self.output.GetContainingSizer()
        # if sizer:
        #     sizer.Layout()


# class WarningManager(dict):
#     class ValidManager(dict):
#         def __init__(self, parent):
#             dict.__init__(self)
#             self.parent = parent
#
#         def __bool__(self):
#             if self.values():
#                 return all(bool(val) for val in self.values())
#             else:
#                 return True
#
#         def __setitem__(self, key, value):
#             dict.__setitem__(self, key, value)
#             self.parent.check()
#
#         def __delitem__(self, key):
#             dict.__delitem__(self, key)
#             self.parent.check()
#
#     def __init__(self, parent, ok=None):
#         dict.__init__(self)
#         self.parent = parent
#         self.ok = ok
#         self.output = wx.StaticText(parent, label="", style=wx.ALIGN_CENTRE_HORIZONTAL)
#         self.output.SetForegroundColour(wx.RED)
#         self._valid = self.ValidManager(self)
#
#     @property
#     def valid(self):
#         return bool(self._valid)
#
#     def __setitem__(self, key, value):
#         dict.__setitem__(self, key, value)
#         # if given a blank value, delete the key
#         if not value:
#             del self[key]
#             return
#         # update
#         self.check()
#
#     def __delitem__(self, key):
#         dict.__delitem__(self, key)
#         # update
#         self.check()
#
#     def check(self):
#         # Enable / disable ok button
#         if isinstance(self.ok, wx.Button):
#             self.ok.Enable(self.valid)
#         # If there's any errors to show, show them
#         messages = list(self.values())
#         self.output.SetLabel("\n".join(messages))
#         # Update sizer
#         sizer = self.output.GetContainingSizer()
#         if sizer:
#             sizer.Layout()


class BaseValidator(_ValidatorBase):
    """Component name validator for _BaseParamsDlg class. It depends on access
    to an experiment namespace.

    Validate calls check, which needs to be implemented per class.

    Messages are passed to user as text in nameOklabel.

    See Also
    --------
    _BaseParamsDlg

    """
    def __init__(self):
        super(BaseValidator, self).__init__()

    def Clone(self):
        return self.__class__()

    def Validate(self, parent):
        # we need to find the dialog to which the Validate event belongs
        # (the event might be fired by a sub-panel and won't have builder exp)
        while not hasattr(parent, 'warnings'):
            try:
                parent = parent.GetParent()
            except Exception:
                raise AttributeError("Could not find warnings manager")
        self.check(parent)
        #return parent.warnings.valid
        return True

    def TransferFromWindow(self):
        return True

    def TransferToWindow(self):
        return True

    def check(self, parent):
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
        print(newName)

        # msg, OK = '', True  # until we find otherwise
        # if newName == '':
        #     msg = _translate("Missing name")
        #     OK = False
        # else:
        #     namespace = parent.frame.exp.namespace
        #     used = namespace.exists(newName)
        #     sameAsOldName = bool(newName == parent.params['name'].val)
        #     if used and not sameAsOldName:
        #         msg = _translate("That name is in use (by %s). Try another name.") % _translate(used)
        #         # NOTE: formatted string literal doesn't work with _translate().
        #         # So, we have to call format() after _translate() is applied.
        #         msg = _translate("That name is in use (by {used}). Try another name."
        #             ).format(used = _translate(used))
        #         OK = False
        #     elif not namespace.isValid(newName):  # valid as a var name
        #         msg = _translate("Name must be alpha-numeric or _, no spaces")
        #         OK = False
        #     # warn but allow, chances are good that its actually ok
        #     elif namespace.isPossiblyDerivable(newName):
        #         msg = _translate(namespace.isPossiblyDerivable(newName))
        #         OK = True
        #
        # parent.warnings['name'] = msg
        # parent.warnings._valid['name'] = OK


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

    def notifyError(self, parent, msg=''):
        """Sets the field to invalid and passes an error string to the parent.

        Call `clearError` to reset the field state if valid.

        Parameters
        ----------
        parent : object
            Component properties dialog or similar.
        msg : str
            Error string.

        """
        if hasattr(parent, 'warnings'):
            parent.warnings[self.fieldName] = msg
            parent.warnings._valid[self.fieldName] = False

    def clearError(self, parent):
        """Clear error message prior to validation.

        Parameters
        ----------
        parent : object
            Component properties dialog or similar.

        """
        if hasattr(parent, 'warnings'):
            parent.warnings[self.fieldName] = ''
            parent.warnings._valid[self.fieldName] = True

    def _validateAsCode(self):
        """Validate the text in the input box as code.

        Returns
        -------
        bool
            `True` if validation was successful. This means that code in the box
            is valid by having the correct syntax and raises no type errors.

        """
        pass

    def check(self, parent):
        """Check Python syntax code snippets."""
        control = self.GetWindow()  # control associated with this validator

        if hasattr(control, "GetValue"):
            code = control.GetValue()
        else:
            return

        # If we're a code component, check for syntax errors by compiling the
        # code.
        try:
            names = compile(code, '', 'exec').co_names
        except (SyntaxError, TypeError) as e:
            # empty '' compiles to a syntax error, ignore
            if not code.strip() == '':
                msg = _translate('Python syntax error in field `{}`:  {}')
                parent.warnings.setWarning(
                    control, msg=msg, kind=VALIDATOR_WARNING_SYNTAX)
                print('has warning')

            return
        else:
            hasCodeWarning = parent.warnings.getWarning(control)
            if hasCodeWarning is not None:
                parent.warnings.clearWarning(control)
                print('warning cleared')

            print('no warnings now')

    # def check(self, parent):
    #     """Checks python syntax of code snippets, and for self-reference.
    #
    #     Note: code snippets simply use existing names in the namespace,
    #     like from condition-file headers. They do not add to the
    #     namespace (unlike Name fields).
    #
    #     Code snippets in param fields will often be user-defined
    #     vars, especially condition names. Can also be expressions like
    #     random(1,100). Hard to know what will be problematic.
    #     But its always the case that self-reference is wrong.
    #     """
    #     # first check if there's anything to validate (and return if not)
    #
    #     def _checkParamUpdates(parent):
    #         """Checks whether param allows updates. Returns bool."""
    #         if parent.params[self.fieldName].allowedUpdates is not None:
    #             # Check for new set with elements common to lists compared -
    #             # True if any elements are common
    #             return bool(
    #                 set(parent.params[self.fieldName].allowedUpdates) &
    #                 set(allowedUpdates))
    #
    #     def _highlightParamVal(parent, error=False):
    #         """Highlights text containing error - defaults to black"""
    #         try:
    #             if error:
    #                 parent.paramCtrls[
    #                     self.fieldName].valueCtrl.SetForegroundColour("Red")
    #             else:
    #                 parent.paramCtrls[
    #                     self.fieldName].valueCtrl.SetForegroundColour("Black")
    #         except KeyError:
    #             pass
    #
    #     # clear previous error if present
    #     self.clearError(parent)
    #
    #     OK = True
    #
    #     # Get attributes of value control
    #     control = self.GetWindow()
    #     if not hasattr(control, 'GetValue'):
    #         return '', True
    #     val = control.GetValue()  # same as parent.params[self.fieldName].val
    #     if not isinstance(val, basestring):
    #         return '', True
    #     field = self.fieldName
    #     allowedUpdates = ['set every repeat', 'set every frame']
    #
    #     _highlightParamVal(parent)
    #     # What valType should code be treated as?
    #     codeWanted = psychopy.experiment.utils.unescapedDollarSign_re.search(val)
    #     isCodeField = bool(parent.params[self.fieldName].valType == 'code')
    #
    #     # Validate as list
    #     # allKeyBoardKeys = list(key._key_names.values()) + [str(num) for num in range(10)]
    #     # allKeyBoardKeys = [key.lower() for key in allKeyBoardKeys]
    #
    #     # Check if it is a Google font
    #     if self.fieldName == 'font' and not val.startswith('$'):
    #         fontInfo = fontMGR.getFontNamesSimilar(val)
    #         if not fontInfo:
    #             msg = _translate(
    #                 "Font `{val}` not found locally, will attempt to retrieve "
    #                 "from Google Fonts when this experiment next runs"
    #             ).format(val=val)
    #
    #     names = []
    #
    #     # Validate as code
    #     if codeWanted or isCodeField:
    #         # get var names from val, check against namespace:
    #         code = experiment.getCodeFromParamStr(val)
    #         try:
    #             names = compile(code, '', 'exec').co_names
    #         except (SyntaxError, TypeError) as e:
    #             # empty '' compiles to a syntax error, ignore
    #             if not code.strip() == '':
    #                 _highlightParamVal(parent, True)
    #                 msg = _translate('Python syntax error in field `{}`:  {}')
    #                 self.notifyError(parent, msg.format(self.displayName, code))
    #
    #             return
    #
    #         self.clearError(parent)
    #
    #         if isCodeField and _checkParamUpdates(parent):
    #             # Check whether variable param entered as a constant
    #             if parent.paramCtrls[self.fieldName].getUpdates() not in allowedUpdates:
    #                 try:
    #                     eval(code)
    #                 except NameError as e:
    #                     _highlightParamVal(parent, True)
    #                     # NOTE: formatted string literal doesn't work with _translate().
    #                     # So, we have to call format() after _translate() is applied.
    #                     msg = _translate(
    #                         "Looks like your variable '{code}' in "
    #                         "'{displayName}' should be set to update."
    #                         ).format(code=code, displayName=self.displayName)
    #                 except SyntaxError as e:
    #                     msg = ''
    #
    #         # namespace = parent.frame.exp.namespace
    #         # parent.params['name'].val is not in namespace for new params
    #         # and is not fixed as .val until dialog closes. Use getvalue()
    #         # to handle dynamic changes to Name field:
    #         if 'name' in parent.paramCtrls:  # some components don't have names
    #             parentName = parent.paramCtrls['name'].getValue()
    #             for name in names:
    #                 # `name` means a var name within a compiled code snippet
    #                 if name == parentName:
    #                     _highlightParamVal(parent, True)
    #                     msg = _translate(
    #                         'Python var `{}` in `{}` is same as Name')
    #                     msg = msg.format(name, self.displayName)
    #                     OK = True
    #
    #             for newName in names:
    #                 namespace = parent.frame.exp.namespace
    #                 if newName in [*namespace.user, *namespace.builder, *namespace.constants]:
    #                     # Continue if name is a variable
    #                     continue
    #                 if newName in [*namespace.nonUserBuilder, *namespace.numpy] and not re.search(newName+r"(?!\(\))", val):
    #                     # Continue if name is an external function being called correctly
    #                     continue
    #                 used = namespace.exists(newName)
    #                 sameAsOldName = bool(newName == parent.params['name'].val)
    #                 if used and not sameAsOldName:
    #                     # NOTE: formatted string literal doesn't work with _translate().
    #                     # So, we have to call format() after _translate() is applied.
    #                     msg = _translate("Variable name ${newName} is in use (by {used}). Try another name."
    #                         ).format(newName=newName, used=_translate(used))
    #                     # let the user continue if this is what they intended
    #                     OK = True
    #
    #     if not OK:
    #         self.notifyError(parent, msg)


if __name__ == "__main__":
    pass
