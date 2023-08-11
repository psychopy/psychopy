import serial


class TPad:
    class TPadResponse:
        def __init__(self, raw):
            self.raw = raw
            self.channel, self.state, self.time = raw.split(" ")

        def isPress(self):
            return self.state == "P"

        def isRelease(self):
            return self.state == "R"

    def __init__(self, timeout=1):
        # setup port
        self.serial = serial.Serial("COM8", 115200, timeout=timeout)
        # array for responses
        self.responses = []

    def read(self):
        # ready data from serial port
        data = self.serial.read().decode()
        # split into lines
        for line in data.split("\n"):
            # create a Response object for each line
            resp = self.TPadResponse(line)
            # store Response object
            self.responses.append(resp)

    def write(self, msg):
        # write data to the serial port
        self.serial.write(msg.encode())


