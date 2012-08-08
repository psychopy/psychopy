from psychopy import visual

class OBCIWindow(visual.Window):
    def __init__(self, *args, **kwargs):
        self._toTag = []
        try:
          self.obciContext = kwargs["obciContext"]
        except KeyError, e:
          raise Excpetion("Missing obciContext argument")
        
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
