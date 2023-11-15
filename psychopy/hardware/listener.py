import sys
import threading
import time
from psychopy import logging


class ListenerLoop(threading.Thread):
    """
    Asynchonous execution loop to continuously poll a device for new messages. Not recommended if using listeners
    within an experiment.

    Attributes
    ----------
    device : BaseDevice
        Device whose messages to dispatch on each iteration of the loop.
    refreshRate : float
        How long to sleep inbetween iterations of the loop
    maxTime : float
        Maximum time (s) which this loop is allowed to run for, after this time limit is reached the loop will end.
    """
    def __init__(self):
        # placeholder values for function params
        self.device = self.refreshRate = self.maxTime = None
        # set initial alive state
        self._alive = False
        # initialise base Thread
        threading.Thread.__init__(self, target=self.dispatchLoop)

    def start(self):
        """
        Start the loop polling for new messages.

        Returns
        -------
        bool
            True if the loop was started successfully
        """
        # if already started, do nothing
        if self._alive:
            return
        # set alive state
        self._alive = True
        # start the thread
        threading.Thread.start(self)
        # sleep so it has time to spin up
        time.sleep(self.refreshRate)
        # return confirmation of thread's alive status
        return threading.Thread.is_alive(self)

    def stop(self):
        """
        Stop the loop polling for new messages.

        Returns
        -------
        bool
            True if the loop was stopped successfully
        """
        # if already stopped, do nothing
        if not self._alive:
            return
        # set alive status
        self._alive = False
        # sleep for 2 iterations so it has time to spin down
        time.sleep(self.refreshRate * 2)
        # return confirmation of thread's dead status
        return not threading.Thread.is_alive(self)

    def dispatchLoop(self):
        """
        Function to make continuous calls to the device for responses.
        """
        cont = self._alive
        startTime = time.time()
        # until something says otherwise, continue
        while cont:
            # work out whether to continue
            cont = self._alive
            if self.maxTime is not None:
                cont &= time.time() - startTime < self.maxTime
            # dispatch messages from this device
            self.device.dispatchMessages()
            # sleep for 10ms
            time.sleep(self.refreshRate)


class BaseListener:
    """
    Base class for a "Listener" object. Subclasses must implement the "receiveMessage" method.

    Listeners can be attached to a node (such as a Button or Photodiode) and will receive duplicates of any messages
    received by that node.
    """
    def __init__(self):
        # list in which to store responses (if implemented)
        self.responses = []
        # create threaded loop, but don't start unless asked to
        self.loop = ListenerLoop()

    def startLoop(self, device, refreshRate=0.01, maxTime=None):
        """
        Start a threaded loop listening for responses

        Parameters
        ----------
        device : BaseDevice
            Device whose messages to dispatch on each iteration of the loop.
        refreshRate : float
            How long to sleep inbetween iterations of the loop
        maxTime : float
            Maximum time (s) which this loop is allowed to run for, after this time limit is reached the loop will end.

        Returns
        -------
        bool
            True if loop started successfully
        """
        # if there's an existing loop, stop it
        self.stopLoop()
        # set attributes of loop
        self.loop.device = device
        self.loop.refreshRate = refreshRate
        self.loop.maxTime = maxTime
        # start loop
        return self.loop.start()

    def stopLoop(self):
        """
        Stop the current dispatch loop

        Returns
        -------
        bool
            True if loop started successfully
        """
        return self.loop.stop()


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
    style : str
        What string format to print the output as? One of:
        - "repr": Do nothing before printing - will be stringified by the object's __repr__ method (as normal)
        - "str": Call str() on the output before printing
        - "json": Attempt to convert output to a JSON string (first looking for a getJSON method, then using json.dumps)
    """
    def __init__(self, stream=sys.stdout, style="repr"):
        # init base class
        BaseListener.__init__(self)
        # store handle of stream
        self.stream = stream
        # store output style
        self.style = style

    def receiveMessage(self, message):
        """
        On receiving a message, print it.
        """
        # store message
        self.responses.append(message)
        # process output to desired print style
        if self.style == "str":
            # stringify
            message = str(message)
        if self.style == "json":
            # convert to json
            if hasattr(message, "getJSON"):
                message = message.getJSON()
            else:
                message = {
                    'type': "hardware_response",
                    'class': "Unknown",
                    'data': str(message)
                }

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
        import asyncio
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
        asyncio.run(self.liaison.broadcast(message))
