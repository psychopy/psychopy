#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Module containing validators for various parameters.
"""
import re
import wx
import psychopy.experiment.utils
from psychopy.tools import stringtools
from psychopy.localization import _translate
from . import experiment
from packaging.version import Version
from psychopy.tools.fontmanager import FontManager

fontMGR = FontManager()

if Version(wx.__version__) < Version('4.0.0a1'):
    _ValidatorBase = wx.PyValidator
else:
    _ValidatorBase = wx.Validator

# Symbolic constants representing the 'kind' of warning for instances of
# `ValidatorWarning`.
VALIDATOR_WARNING_NONE = 0
VALIDATOR_WARNING_NAME = 1
VALIDATOR_WARNING_SYNTAX = 2
VALIDATOR_WARNING_FONT_MISSING = 3
VALIDATOR_WARNING_COUNT = 4  # increment when adding more


class ValidatorWarning:
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
        `VALIDATOR_WARNING_NONE`, `VALIDATOR_WARNING_NAME`,
        `VALIDATOR_WARNING_SYNTAX` or `VALIDATOR_WARNING_FONT_MISSING`.

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
        can be one of `VALIDATOR_WARNING_NONE`, `VALIDATOR_WARNING_NAME`,
        `VALIDATOR_WARNING_SYNTAX` or `VALIDATOR_WARNING_FONT_MISSING`.
        """
        return self._kind

    @kind.setter
    def kind(self, value):
        value = int(value)
        assert VALIDATOR_WARNING_NONE <= value < VALIDATOR_WARNING_COUNT
        self._kind = value

    @property
    def isSyntaxWarning(self):
        """`True` if this is a syntax warning (`bool`)."""
        return self._kind == VALIDATOR_WARNING_SYNTAX

    @property
    def isNameWarning(self):
        """`True` if this is a namespace warning (`bool`)."""
        return self._kind == VALIDATOR_WARNING_NAME

    @property
    def allowed(self):
        """`True` if this is a non-critical message which doesn't disable the OK button"""
        return self.kind in [VALIDATOR_WARNING_FONT_MISSING]


class WarningManager:
    """Manager for warnings produced by validators associated with controls
    within the component properties dialog. Assumes that the `parent` dialog
    uses a standardized convention for attribute names for all components.

    Each control can only have a single warning at a time in the current
    implementation of this class.

    Warnings
    --------
    Do not make strong references to instances of this class outside of the
    `parent` dialog. This class must be destroyed along with the `parent` object
    when the `parent` is deleted. This also goes for any `ValidatorWarning`
    objects referenced by this class.

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

        # create an output label box for the parent
        self.output = wx.StaticText(
            self._parent, label="", style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.output.SetForegroundColour(wx.RED)

    @property
    def OK(self):
        """`True` if there are no warnings (`bool`)."""
        if len(self._warnings) == 0:
            return True
        else:
            return all(warning.allowed for warning in self._warnings.values())

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
        use this to process controls which still have warnings registered to
        them.
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

    def validate(self, control=None):
        """Validate one or many controls.

        Calling this will re-run validation on all controls which have active
        warnings presently registered to them. If the specified control(s) no
        longer generate warnings, it will be removed from the manager.

        This can be called make sure that all warnings have been addressed.

        """
        pass

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
        elif hasattr(self.parent, 'OKbtn'):  # another option ...
            okButton = self.parent.OKbtn
        else:
            # raise AttributeError("Parent object does not have an OK button.")
            return  # nop better here?

        if isinstance(okButton, wx.Button):
            okButton.Enable(enable)

    def showWarning(self):
        """Show the active warnings. Disables the OK button if present.
        """
        self._lockout(self.OK)  # enable / disable ok button

        # If there's any errors to show, show them
        messages = self.messages

        if messages:
            self.output.SetLabel("\n".join(messages))
        else:
            self.output.SetLabel("")

        # Update sizer
        sizer = self.output.GetContainingSizer()
        if sizer:
            sizer.Layout()


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
        """Checks namespace.

        Parameters
        ----------
        parent : object
            Component properties dialog or similar.

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
                # NOTE: formatted string literal doesn't work with _translate().
                # So, we have to call format() after _translate() is applied.
                msg = _translate(
                    "That name is in use (by {used}). Try another name."
                    ).format(used=_translate(used))
                OK = False
            elif not namespace.isValid(newName):  # valid as a var name
                msg = _translate("Name can only contain letters, numbers and underscores (_), no spaces or other symbols")
                OK = False
            # warn but allow, chances are good that its actually ok
            elif namespace.isPossiblyDerivable(newName):
                msg = _translate(namespace.isPossiblyDerivable(newName))
                OK = True

        if not OK:
            parent.warnings.setWarning(
                control, msg=msg, kind=VALIDATOR_WARNING_NAME)
        else:
            parent.warnings.clearWarning(control)

        parent.warnings.showWarning()


class CodeSnippetValidator(BaseValidator):
    """Validation checks if field value is intended to be Python code.
    If so, check that it is valid Python, and if valid, check whether
    it contains bad identifiers (currently only self-reference).

    @see: _BaseParamsDlg
    """

    def __init__(self, fieldName, displayName=None):
        super(CodeSnippetValidator, self).__init__()
        self.fieldName = fieldName
        if displayName is None:
            displayName = fieldName
        self.displayName = displayName

    def Clone(self):
        return self.__class__(self.fieldName, self.displayName)

    def check(self, parent):
        """Checks python syntax of code snippets, and for self-reference.

        Note: code snippets simply use existing names in the namespace, like
        from condition-file headers. They do not add to the namespace (unlike
        Name fields). Code snippets in param fields will often be user-defined
        vars, especially condition names. Can also be expressions like
        random(1,100). Hard to know what will be problematic. But its always the
        case that self-reference is wrong.

        Parameters
        ----------
        parent : object
            Component properties dialog or similar.

        """
        # first check if there's anything to validate (and return if not)
        def _checkParamUpdates(parent):
            """Checks whether param allows updates. Returns bool."""
            if parent.params[self.fieldName].allowedUpdates is not None:
                # Check for new set with elements common to lists compared -
                # True if any elements are common
                return bool(
                    set(parent.params[self.fieldName].allowedUpdates) &
                    set(allowedUpdates))

        def _highlightParamVal(parent, error=False):
            """Highlights text containing error - defaults to black"""
            try:
                if error:
                    parent.paramCtrls[
                        self.fieldName].valueCtrl.SetForegroundColour("Red")
                else:
                    parent.paramCtrls[
                        self.fieldName].valueCtrl.SetForegroundColour("Black")
            except KeyError:
                pass

        # Get attributes of value control
        control = self.GetWindow()
        if not hasattr(control, 'GetValue'):
            return '', True  # mdc - why return anything here?

        val = control.GetValue()  # same as parent.params[self.fieldName].val
        if not isinstance(val, str):
            return '', True

        allowedUpdates = ['set every repeat', 'set every frame']
        # Set initials
        msg, OK = '', True  # until we find otherwise
        _highlightParamVal(parent)
        # What valType should code be treated as?
        codeWanted = psychopy.experiment.utils.unescapedDollarSign_re.search(val)
        isCodeField = bool(parent.params[self.fieldName].valType == 'code')

        # Validate as list
        # allKeyBoardKeys = list(key._key_names.values()) + [str(num) for num in range(10)]
        # allKeyBoardKeys = [key.lower() for key in allKeyBoardKeys]

        # Check if it is a Google font
        if self.fieldName == 'font' and not val.startswith('$'):
            fontInfo = fontMGR.getFontNamesSimilar(val)
            if not fontInfo:
                msg = _translate(
                    "Font `{val}` not found locally, will attempt to retrieve "
                    "from Google Fonts when this experiment next runs"
                ).format(val=val)
                parent.warnings.setWarning(
                    control, msg=msg, kind=VALIDATOR_WARNING_FONT_MISSING)
            else:
                parent.warnings.clearWarning(control)

        # Validate as code
        if codeWanted or isCodeField:
            # get var names from val, check against namespace:
            code = experiment.getCodeFromParamStr(val, target="PsychoPy")
            try:
                names = list(stringtools.getVariables(code))
                parent.warnings.clearWarning(control)
            except (SyntaxError, TypeError) as e:
                # empty '' compiles to a syntax error, ignore
                if not code.strip() == '':
                    _highlightParamVal(parent, True)
                    msg = _translate('Python syntax error in field `{}`:  {}')
                    msg = msg.format(self.displayName, code)
                    parent.warnings.setWarning(
                        control, msg=msg, kind=VALIDATOR_WARNING_SYNTAX)
            else:
                # Check whether variable param entered as a constant
                if isCodeField and _checkParamUpdates(parent):
                    if parent.paramCtrls[self.fieldName].getUpdates() not in allowedUpdates:
                        try:
                            eval(code)  # security risk here?
                        except NameError as e:
                            _highlightParamVal(parent, True)
                            # NOTE: formatted string literal doesn't work with _translate().
                            # So, we have to call format() after _translate() is applied.
                            msg = _translate(
                                "Looks like your variable '{code}' in "
                                "'{displayName}' should be set to update."
                                ).format(code=code, displayName=self.displayName)
                            parent.warnings.setWarning(
                                control, msg=msg, kind=VALIDATOR_WARNING_NAME)
                        except SyntaxError as e:
                            parent.warnings.setWarning(
                                control, msg=msg, kind=VALIDATOR_WARNING_SYNTAX)

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
                            parent.warnings.setWarning(
                                control, msg=msg, kind=VALIDATOR_WARNING_NAME)
                    else:
                        parent.warnings.clearWarning(control)

                    for newName in names:
                        namespace = parent.frame.exp.namespace
                        if newName in [*namespace.user, *namespace.builder,
                                       *namespace.constants]:
                            # Continue if name is a variable
                            continue
                        if newName in [*namespace.nonUserBuilder, *namespace.numpy] \
                                and not re.search(newName+r"(?!\(\))", val):
                            # Continue if name is an external function being called correctly
                            continue
                        used = namespace.exists(newName)
                        sameAsOldName = bool(newName == parent.params['name'].val)
                        if used and not sameAsOldName:
                            # NOTE: formatted string literal doesn't work with _translate().
                            # So, we have to call format() after _translate() is applied.
                            msg = _translate(
                                "Variable name ${newName} is in use (by "
                                "{used}). Try another name."
                                ).format(newName=newName, used=_translate(used))
                            parent.warnings.setWarning(
                                control, msg=msg, kind=VALIDATOR_WARNING_NAME)
                        else:
                            parent.warnings.clearWarning(control)
        else:
            parent.warnings.clearWarning(control)

        parent.warnings.showWarning()  # show most recent warnings


if __name__ == "__main__":
    pass
