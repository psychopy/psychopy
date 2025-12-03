from ._alerts import BaseAlertHandler
import sys


class StderrAlertHandler(BaseAlertHandler):
    def receiveAlert(self, msg):
        # print message to stderr
        sys.stderr.write(str(msg))