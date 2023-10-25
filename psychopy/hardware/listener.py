import sys
from psychopy import logging


class BaseListener:
    """
    Base class for a "Listener" object. Subclasses must implement the "receiveMessage" method.

    Listeners can be attached to a node (such as a Button or Photodiode) and will receive duplicates of any messages
    received by that node.
    """
    def __init__(self):
        # list in which to store responses (if implemented)
        self.responses = []

    def receiveMessage(self, message):
        """
        Method defining what to do when receiving a message. Must be implemented by subclasses.

        Parameters
        ----------
        message
            Message received.
        """
        raise NotImplementedError()


class PrintListener(BaseListener):
    """
    Listener which prints any responses to the given stream. Mostly useful for debugging.

    Parameters
    ----------
    stream
        A file-like object to `print` responses to. Default value is sys.stdout (aka same place normal `print()`
        statements are sent to).
    """
    def __init__(self, stream=sys.stdout):
        # init base class
        BaseListener.__init__(self)
        # store handle of stream
        self.stream = stream

    def receiveMessage(self, message):
        """
        On receiving a message, print it.
        """
        # store message
        self.responses.append(message)
        # print message
        print(message, file=self.stream)


class LoggingListener(BaseListener):
    """
    Listener which writes any responses to the given log file. Mostly useful for debugging.

    Parameters
    ----------
    file : logging.LogFile
        Log file to write messages to. Default will be the root logger.
    level : int
        Logging level to log messages as, can be one of the constants from psychopy.logging. Default is logging.DEBUG.
    """
    def __init__(self, file=logging.root, level=logging.DEBUG):
        # init base class
        BaseListener.__init__(self)
        # store params
        self.file = file
        self.level = level

    def receiveMessage(self, message):
        """
        On receiving a message, log it.
        """
        # append
        self.responses.append(message)
        self.file.logger.log(message, level=self.level)


class LiaisonListener(BaseListener):
    """
    Listener which sends any messages to a Liaison server.

    Parameters
    ----------
    liaison : psychopy.liaison.WebSocketServer
        Liaison server to send messages to
    level : int
        Logging level to log messages as, can be one of the constants from psychopy.logging. Default is logging.DEBUG.
    """
    def __init__(self, liaison):
        # init base class
        BaseListener.__init__(self)
        # store reference to liaison
        self.liaison = liaison

    def receiveMessage(self, message):
        """
        On receiving message, send it to Liaison.
        """
        # append
        self.responses.append(message)
        # stringify message
        if hasattr(message, "getJSON"):
            message = message.getJSON()
        else:
            message = {
                'type': "hardware_response",
                'class': "Unknown",
                'data': str(message)
            }
        # send
        self.liaison.broadcast(message)
