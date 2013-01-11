from psychopy import visual
from psychopy import constants
from serial_trigger import SerialSender
from psychopy.errors import ExperimentException

class Window(visual.Window):
    def __init__(self, mx_adapter, *args, **kwargs):
        self._tagsToStart = []
        self._tagsToSend = []
        self._tagsToSave = []
        self.mx_adapter = mx_adapter
        self.triggerPort = None
        self.trigOnFlip = False
        self.isTrigged = False
        super(Window, self).__init__(*args, **kwargs)
    
    def startTagOnFlip(self, tagger):
        self._tagsToStart.append(tagger)
    
    def sendTagOnFlip(self, tagger):
        self._tagsToSend.append(tagger)
        
    def saveTagOnFlip(self, tagger):
        self._tagsToSave.append(tagger)
    
    def enableTrig(self):
        self.trigOnFlip = True
        
    def requestTriggerPort(self, triggerDevice):
        try:
            self.triggerPort = SerialSender(triggerDevice, 0)
        except Exception as e:
            raise ExperimentException(e)
    
    def doFlipLogging(self, now):
        # start tag
        for tagger in self._tagsToStart:
            tagger.startTime = now
        # send signal
        if self.trigOnFlip:
            self.triggerPort.send_next()
            self.trigOnFlip = False
        # send tags
        for tagger in self._tagsToSend:
            self.mx_adapter.send_tag(tagger.startTime, now, tagger.tagName, tagger.tagDescription)
        for tagger in self._tagsToSave:
            TagOnFlip.tags.append({"name": tagger.tagName, "start_timestamp": tagger.startTime,
                "end_timestamp": now, "desc": tagger.tagDescription})
        self._tagsToStart = []
        self._tagsToSend = []
        self._tagsToSave = []

class TagOnFlip(object):
    tags = []
    def __init__(self, window, tagName="tag", tagDescription={},
            doSignal=False, sendTags=False, saveTags=False):
        self.window = window
        self.status = None
        self.startTime = None
        self.tagName = str(tagName)
        self.doSignal = doSignal
        self.sendTags = sendTags
        self.saveTags = saveTags
        self.tagDescription = tagDescription

    def setTagdescription(self, description):
        self.tagDescription = description

    def setTagname(self, name):
        self.tagName = name

    def scheduleStart(self):
        if self.doSignal:
            self.window.enableTrig()
        if self.sendTags or self.saveTags:
            self.window.startTagOnFlip(self)

    def scheduleStop(self):
        if self.sendTags:
            self.window.sendTagOnFlip(self)
        if self.saveTags:
            self.window.saveTagOnFlip(self)

