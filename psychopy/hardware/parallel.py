import sys
from psychopy import logging, clock
from psychopy.hardware.base import BaseResponseDevice, BaseResponse


class ParallelResponse(BaseResponse):
    def getPin(self, pinNumber):
        """
        Get the value of a specific pin in this response.

        Parameters
        ----------
        pinNumber : int
            Number of the pin to get the value of
        """
        if pinNumber == 10:
            # 10 = ACK
            return (self.value >> 6) & 1
        elif pinNumber == 11:
            # 11 = BUSY
            return (self.value >> 7) & 1
        elif pinNumber == 12:
            # 12 = PAPER-OUT
            return (self.value >> 5) & 1
        elif pinNumber == 13:
            # 13 = SELECT
            return (self.value >> 4) & 1
        elif pinNumber == 15:
            # 15 = ERROR
            return (self.value >> 3) & 1
        elif 2 <= pinNumber <= 9:
            return (self.value >> (pinNumber - 2)) & 1
        else:
            logging.error(
                f"Could not read pin {pinNumber} on parallel response."
            )
            return


class ParallelDevice(BaseResponseDevice):
    responseClass = ParallelResponse

    def __init__(self, address):
        BaseResponseDevice.__init__(self)
        # store address
        if isinstance(address, str) and address.startswith('0x'):
            # convert u"0x0378" into 0x0378
            self.address = int(address, 16)
        else:
            self.address = address
        # pick appropriate backend according to OS
        if sys.platform.startswith('linux'):
            self.backend = _LinuxParallelBackend(self.address)
        elif sys.platform == "win32":
            from ctypes import windll

            # start off with no backend
            self.backend = None
            # check which drivers we have
            for key, cls in [
                ('inpout32', _InpOutParallelBackend),
                ('inpoutx64', _InpOutParallelBackend),
                ('dlportio', _DLPortIOParallelBackend)
            ]:
                # if we don't have the driver, try the next
                try:
                    getattr(windll, key)
                except FileNotFoundError:
                    continue
                # if we do, use the corresponding backend
                self.backend = cls(self.address)
            # if no drivers, error
            if self.backend is None:
                raise SystemError(
                    "No parallel port drivers found. Please install either inpout32, inpoutx64 or "
                    "dlportio"
                )
        else:
            raise OSError(
                "Parallel Port not supported on Mac OS"
            )
        # start timer
        self.timer = clock.Clock()
        # get initial state
        self.dispatchMessages()

    def isSameDevice(self, other):
        if isinstance(other, ParallelDevice):
            return self.address == other.address
        elif isinstance(other, type(self.address)):
            return self.address == other
        else:
            return False

    @staticmethod
    def getAvailableDevices():
        # parallel ports aren't detectable, so just return one
        return [
            {
                'deviceLabel': "Parallel Port",
                'deviceClass': "psychopy.hardware.parallel.ParallelDevice"
            }
        ]

    def dispatchMessages(self):
        # get data
        data = self.backend.readData()
        # do nothing if data hasn't changed
        if len(self.responses) and data == self.responses[-1].value:
            return
        # parse data to a ParallelResponse
        msg = self.parseMessage(data)
        # receive it
        self.receiveMessage(msg)

    def parseMessage(self, message):
        return ParallelResponse(
            t=self.timer.getTime(), 
            value=message, 
            device=self
        )

    def getData(self):
        # dispatch messages to detect any change
        self.dispatchMessages()
        # return data from last response
        return self.responses[-1].value
    
    def setData(self, data):
        self.backend.setData(data)

    def getPin(self, pinNumber):
        # dispatch messages to detect any change
        self.dispatchMessages()
        # return data from last response
        return self.responses[-1].getPin(pinNumber)

    def setPin(self, pinNumber, state):
        # get current state
        data = self.getData()
        # change just this pin
        if state:
            data = data | 2 ** (pinNumber - 2)
        else:
            data = data & (255 ^ 2 ** (pinNumber - 2))
        # set in backend
        self.setData(data)


class _BaseParallelBackend:
    def __init__(self, address):
        """
        Base class for a ParallelBackend; extremely minimal implementation with just get and set 
        data functions.

        Parameters
        ----------
        address : int
            Address of the parallel port
        """
        # store address
        self.address = address

    def setData(self, address, data):
        """
        Set data on the given port

        Parameters
        ----------
        address : int
            Port to set data on
        data : bytes
            Data to set
        """
        raise NotImplementedError()

    def readData(self, address):
        """
        Read data from the given port

        Parameters
        ----------
        address : int
            Port to read data from
        
        Returns
        -------
        bytes
            Data from the port
        """
        raise NotImplementedError()



class _DLPortIOParallelBackend(_BaseParallelBackend):
    def __init__(self, address):
        from ctypes import windll

        _BaseParallelBackend.__init__(self, address=address)
        # get functions
        self.functions = windll.dlportio

    def setData(self, data):
        self.functions.DlPortWritePortUchar(self.address, data)

    def readData(self):
        return self.functions.DlPortReadPortUchar(self.address)


class _InpOutParallelBackend(_BaseParallelBackend):
    def __init__(self, address):
        from numpy import uint8
        from ctypes import windll
        import platform

        _BaseParallelBackend.__init__(self, address=address)
        # get functions
        if platform.architecture()[0] == '32bit':
            self.functions = getattr(windll, 'inpout32')
        elif platform.architecture()[0] == '64bit':
            self.functions = getattr(windll, 'inpoutx64')
        # put into byte mode
        _inp = self.functions.Inp32(
            self.address + 0x402 
        )
        self.functions.Out32(
            self.address + 0x402,
            int((_inp & ~uint8(1 << 5 | 1 << 6 | 1 << 7)) | (1 << 5))
        )
        # make sure bit 5 of control register is not set (to make sure the port is in output mode)
        _inp = self.functions.Inp32(self.address + 2)
        self.functions.Out32(
            self.address + 2,
            int(_inp & ~uint8(1 << 5))
        )

    def setData(self, data):
        self.functions.DlPortWritePortUchar(self.address, data)

    def readData(self):
        return self.functions.DlPortReadPortUchar(self.address)


class _LinuxParallelBackend(_BaseParallelBackend):
    def __init__(self, address):
        import parallel as pyp

        _BaseParallelBackend.__init__(self, address=address)
        # create Parallel object for functions
        self.functions = pyp.Parallel(address)

    def setData(self, data):
        self.functions.setData(data)

    def getData(self, data):
        return self.functions.PPRDATA()
