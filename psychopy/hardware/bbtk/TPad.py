from .. import serialdevice as sd


class TPad:
    class TPadResponse:
        def __init__(self, raw):
            self.raw = raw
            self.channel, self.state, self.time = raw.split(" ")

        def isPress(self):
            return self.state == "P"

        def isRelease(self):
            return self.state == "R"

    def __init__(self):
        # setup port
        self.serial = sd.SerialDevice("COM8", 115200)
        self.com = self.serial.com
        # array for responses
        self.responses = []

    def read(self):
        # ready data from serial port
        data = self.com.read().decode()
        # split into lines
        for line in data.split("\n"):
            # create a Response object for each line
            resp = self.TPadResponse(line)
            # store Response object
            self.responses.append(resp)

    def write(self, msg):
        # write data to the serial port
        self.com.write(msg.encode())


