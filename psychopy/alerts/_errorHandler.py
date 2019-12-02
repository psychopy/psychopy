from psychopy.alerts._alerts import alertLog


class _BaseErrorHandler(object):
    """A base class for handling PsychoPy alerts and exceptions.
    """

    def __init__(self):
        self.errors = []
        self.alerts = []
        self.autoFlush = True

    def write(self, toWrite):
        """This is needed for any Python Exceptions, which assume the stderr
        is a file-like object. But we might well simply store the message for
        printing later.
        """
        self.errors.append(toWrite)
        if self.autoFlush:
            self.flush()

    def flush(self):
        """Print errors to console and clear errors.
        """
        for err in self.errors:
            print(err)
        self.errors = []

    def receiveAlert(self, alert):
        """
        Handles PsychoPy alerts (sent by _alerts.alert).
        This function should ONLY be called by _alerts.alert.
        Each alert is published to the _alerts.alertLog variable.

        Parameters:
        -----------
        alert: psychopy.alert._alert.AlertEntry object
            A data object containing alert information.
        """
        self.alerts.append(alert)

    def __del__(self):
        self.flush()


class ErrorHandler(_BaseErrorHandler):
    """A dialog for handling PsychoPy alerts and exceptions
    """
    def __init__(self):
        super(ErrorHandler, self).__init__()

    def flush(self):
        """Stores alerts in alertLog, flushes errors, clears errors and alerts attributes.
        """
        del alertLog[:]
        alertLog.extend(self.alerts)

        for err in self.errors:
            print(err)

        self.errors = []
        self.alerts = []
