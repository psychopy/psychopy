import serial

BAUD_RATE = 115200

class SerialSender(object):
    def __init__(self, port_name, init_value):
        self.send_value = init_value
        import serial
        try:
            self.port = serial.Serial(
                port=port_name,
                baudrate=BAUD_RATE,
                #parity=serial.PARITY_ODD,
                #stopbits=serial.STOPBITS_TWO,
                #bytesize=serial.SEVENBITS
                )
        except serial.SerialException, e:
            print "Nieprawidlowa nazwa portu."
            raise e
        self.send(self.send_value)
    
    def open(self):
        self.port.open()
        self.send(self.send_value)

    def close(self):
        self.port.close()
        
    def send(self, value):
        self.port.setRTS(value)
        
    def send_next(self):
        self.send_value = (self.send_value + 1) % 2
        self.send(self.send_value)
