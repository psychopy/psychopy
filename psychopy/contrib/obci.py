from psychopy import visual
from psychopy import constants
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


class Window(visual.Window):
    def __init__(self, obciContext, *args, **kwargs):
        self._tagsToSend = []
        self._tagsToSave = []
        self.obciContext = obciContext
        self.triggerPort = None
        self.trigOnFlip = False
        self.isTrigged = False
        super(Window, self).__init__(*args, **kwargs)
        # TODO check whether obciContext is instance of ExpsHelper?
    
    def sendTagOnFlip(self, name):
        self._tagsToSend.append(str(name))
        
    def saveTagOnFlip(self, name):
        self._tagsToSave.append(str(name))
    
    def enableTrig(self):
        self.trigOnFlip = True
        
    def requestTriggerPort(self):
        self.triggerPort = SerialSender("/dev/ttyUSB0", 0)
    
    def doFlipLogging(self, now):
        # send signal
        if self.trigOnFlip:
            self.triggerPort.send_next()
            self.trigOnFlip = False
        # send tags
        for tagEntry in self._tagsToSend:
            self.obciContext.send_tag(now, now, tagEntry)
        for tagEntry in self._tagsToSave:
            TagOnFlip.tags.append({"name": tagEntry, "start_timestamp": now,
                "end_timestamp": now, "desc": {}})
        self._tagsToSend = []
        self._tagsToSave = []

class TagOnFlip(object):
    tags = []
    def __init__(self, window, tagName="tag",
            doSignal=False, sendTags=False, saveTags=False):
        self.window = window
        self.status = None
        self.tagName = tagName
        self.doSignal = doSignal
        self.sendTags = sendTags
        self.saveTags = saveTags

    def schedule(self):
        self.status = constants.STARTED
        if self.doSignal:
            self.window.enableTrig()
        
        if self.sendTags:
            self.window.sendTagOnFlip(self.tagName)
        if self.saveTags:
            self.window.saveTagOnFlip(self.tagName)

