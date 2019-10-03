import sys


class _BaseErrorHandler(object):
    """A base class for error (and warning) handlers to receive PsychoPy standard
    warnings as well as Python Exceptions.
    Subclass this for any actual handler (e.g. wx diaog to handle warnings)
    """

    def __init__(self):
        """Create the handler, assign and keep track of previous stderr
        """
        self.errors = []
        self.alerts = []
        self.autoFlush=True

    def setStdErr(self):
        """Set self to be sys.stderr.
        Can be reverted with unsetStdErr()
        """
        self.origErr = sys.stderr
        sys.stderr = self

    def unsetStdErr(self):
        """Revert stderr to be the previous sys.stderr when self.setStdErr()
        was last called
        """
        if self == sys.stderr:
            sys.stderr = self.origErr

    def flush(self):
        """This is the key function to override. Flush needs to handle a list
        of errs/warnings that could be strings (Python Exceptions) or dicts
        such as:
            {'code':1001,'obj':stim, 'msg':aString, 'trace':listOfStrings}
        An ErrorHandler might simply collect warnings until the flush()
        method is called
        """
        for err in self.errors:
            print(err)
        self.errors = []

    def receiveAlert(self, alert):
        """
        Implement this to handle PsychoPy alerts (sent my _alerts.alert).
        This function should ONLY be called by _alerts.alert.
        Parameters:
        -----------
        alert: psychopy.alert._alert.AlertEntry object
            A data object containing alert information.
        """

        # self.alerts.append("Component Type: {type} | "
        #                       "Component Name: {name} | "
        #                       "Code: {code} | "
        #                       "Category: {cat} | "
        #                       "Message: {msg} | "
        #                       "Traceback: {trace}".format(type=alert.type,
        #                                                   name=alert.name,
        #                                                   code=alert.code,
        #                                                   cat=alert.cat,
        #                                                   msg=alert.msg,
        #                                                   trace=alert.trace))
        self.alerts.append(alert)

    def write(self, toWrite):
        """This is needed for any Python Exceptions, which assume the stderr
        is a file-like object. But we might well simply store the message for
        printing later.
        """
        self.errors.append(toWrite)
        if self.autoFlush:
            self.flush()

    def __del__(self):
        """Make sure any current warnings are flushed and then revert the
        """
        self.flush()


class ErrorHandler(_BaseErrorHandler):
    """A dialog for handling PsychoPy Warnings and Python Exceptions
    """
    def __init__(self):
        """Create the handler, assign and keep track of previous stderr
        """
        super(ErrorHandler, self).__init__()

    def flush(self):
        for err in self.errors:
            print(err)
        self.errors = []
        self.alerts = []