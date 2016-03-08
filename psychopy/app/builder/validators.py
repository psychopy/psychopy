'''
Module containing validators for various parameters.
'''
import wx
from ..localization import _translate
from . import experiment


class BaseValidator(wx.PyValidator):
    """
    Component name validator for _BaseParamsDlg class. It depends on access
    to an experiment namespace. Validation checks if it is a valid Python
    identifier and if it does not clash with existing names.

    @see: _BaseParamsDlg
    """

    def __init__(self):
        super(BaseValidator, self).__init__()
        self.message = ""

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
        parent.nameOKlabel.SetLabel(message)
        return valid

    def TransferFromWindow(self):
        return True

    def TransferToWindow(self):
        return True

    def check(self, parent):
        raise NotImplementedError


class NameValidator(BaseValidator):
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
                    "That name is in use (it's a %s). Try another name.")
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


class CodeValidator(BaseValidator):
    """
    Component code validator for _BaseParamsDlg class. It depends on access
    to an experiment namespace. Validation checks if it is a valid Python
    code, and if so, whether it contains identifiers that clash with
    existing names (in the to-be-generated python script).

    @see: _BaseParamsDlg
    """

    def __init__(self):
        super(CodeValidator, self).__init__()

    def check(self, parent):
        """checks intersection of names in code and namespace
        """
        control = self.GetWindow()
        if not hasattr(control, 'GetValue'):
            return '', True
        val = control.GetValue()  # same as parent.params[self.fieldName].val
        codeWanted = experiment._unescapedDollarSign_re.search(val)
        if codeWanted:  # ... or valType == 'code' -- require fieldName?
            # get var names from val, check against namespace:
            code = experiment.getCodeFromParamStr(val)
            try:
                names = compile(code, '', 'eval').co_names
            except SyntaxError:
                pass
            else:
                namespace = parent.frame.exp.namespace
                for name in names:
                    # params['name'] not in namespace yet if its a new param
                    if (name == parent.params['name'].val or
                            namespace.exists(name)):
                        msg = _translate('Name `{}` is already used')
                        return msg.format(name), False
        return '', True
