from psychopy import visual

class OBCIWindow(visual.Window):
    def __init__(self, *args, **kwargs):
        self._toTag = []
        try:
            self.obciContext = kwargs["obciContext"]
        except KeyError:
            raise Exception("Missing obciContext argument")
        
        super(OBCIWindow, self).__init__(*args, **kwargs)
        # TODO check whether obciContext is instance of ExpsHelper?
    
    def tagOnFlip(self, name):
        self._toTag.append(str(name))
    
    def doFlipLogging(self, now):
        super(OBCIWindow, self).doFlipLogging(now)
        
        # send tags
        for tagEntry in self._toTag:
            self.obciContext.send_tag(now, now, tagEntry)
        self._toTag = []

class TagOnFlip(object):
    def __init__(self, window, doTag = True, tagName = "tag",
            doSignal = False, signalByte = 'A'):
        self.window = window
        self.status = None
        self.doTag = doTag
        self.tagName = tagName
        self.doSignal = doSignal
        self.signalByte = signalByte
    def schedule(self):
        pass
