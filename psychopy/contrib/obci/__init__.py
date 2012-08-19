from psychopy import visual
from psychopy import constants
from serial_trigger import SerialSender
from psychopy.errors import ExperimentException

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
    
    def sendTagOnFlip(self, name, description):
        self._tagsToSend.append((str(name), description))
        
    def saveTagOnFlip(self, name, description):
        self._tagsToSave.append((str(name), description))
    
    def enableTrig(self):
        self.trigOnFlip = True
        
    def requestTriggerPort(self, triggerDevice):
        try:
            self.triggerPort = SerialSender(triggerDevice, 0)
        except Exception as e:
            raise ExperimentException(e)
    
    def doFlipLogging(self, now):
        # send signal
        if self.trigOnFlip:
            self.triggerPort.send_next()
            self.trigOnFlip = False
        # send tags
        for tagEntry in self._tagsToSend:
            self.obciContext.send_tag(now, now, tagEntry[0], tagEntry[1])
        for tagEntry in self._tagsToSave:
            TagOnFlip.tags.append({"name": tagEntry[0], "start_timestamp": now,
                "end_timestamp": now, "desc": tagEntry[1]})
        self._tagsToSend = []
        self._tagsToSave = []

class TagOnFlip(object):
    tags = []
    def __init__(self, window, tagName="tag", tagDescription={},
            doSignal=False, sendTags=False, saveTags=False):
        self.window = window
        self.status = None
        self.tagName = tagName
        self.doSignal = doSignal
        self.sendTags = sendTags
        self.saveTags = saveTags
        self.tagDescription = tagDescription

    def setTagdescription(self, description):
        self.tagDescription = description

    def schedule(self):
        self.status = constants.STARTED
        if self.doSignal:
            self.window.enableTrig()
        
        if self.sendTags:
            self.window.sendTagOnFlip(self.tagName, self.tagDescription)
        if self.saveTags:
            self.window.saveTagOnFlip(self.tagName, self.tagDescription)

