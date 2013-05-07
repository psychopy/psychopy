"""
ioHub
.. file: ioHub/examples/sequentialFixationTask/experimentResources.py

"""

from psychopy import visual

from psychopy.iohub import ScreenState

from shapely.geometry import Point

class TargetScreen(ScreenState):
    TARGET_OUTER_RADIUS=15
    TARGET_INNER_RADIUS=5
    TARGET_OUTER_COLOR=[255,255,255]
    TARGET_INNER_COLOR=[255,255,255]
    WITHIN_AOI_SAMPLE_COUNT_THRESHOLD=5
    def __init__(self,experimentRuntime, eventTriggers=None, timeout=None):
        ScreenState.__init__(self,experimentRuntime, eventTriggers, timeout)
        self.stim['OUTER_POINT']=visual.Circle(self.window(),
                        radius=(self.TARGET_OUTER_RADIUS,self.TARGET_OUTER_RADIUS),
                        lineWidth=0, lineColor=None, lineColorSpace='rgb255',
                        name='FP_OUTER', opacity=1.0, interpolate=False,
                        units='pix',pos=(0,0))
        self.stimNames.append('OUTER_POINT')
        self.stim['OUTER_POINT'].setFillColor(self.TARGET_OUTER_COLOR,'rgb255')

        self.stim['INNER_POINT']=visual.Circle(self.window(),
                        radius=(self.TARGET_INNER_RADIUS,self.TARGET_INNER_RADIUS),
                        lineWidth=0, lineColor=None, lineColorSpace='rgb255', 
                        name='FP_INNER', opacity=1.0, interpolate=False, 
                        units='pix', pos=(0,0))
        self.stimNames.append('INNER_POINT')        
        self.stim['INNER_POINT'].setFillColor(self.TARGET_INNER_COLOR,'rgb255')

        self._showDynamicStim=False
        self.dynamicStimPositionFuncPtr=None
        ppd=experimentRuntime.devices.display.getPixelsPerDegree()
        self.stim['DYNAMIC_STIM']=visual.GratingStim(self.window(),tex=None, 
                        mask="gauss", pos=[0,0],size=ppd,color='purple',opacity=0.0)
        self.stimNames.append('DYNAMIC_STIM')
        
        self.nextAreaOfInterest=None
        self.aoiTriggeredTime=None
        self.aoiTriggeredID=None

    def setTargetOuterColor(self,rgbColor):
        self.stim['OUTER_POINT'].setFillColor(rgbColor,'rgb255')
        self.dirty=True

    def setTargetInnerColor(self,rgbColor):
        self.stim['INNER_POINT'].setFillColor(rgbColor,'rgb255')
        self.dirty=True

    def setTargetOuterSize(self,r):
        self.stim['OUTER_POINT'].setRadius(r)
        self.dirty=True

    def setTargetInnerSize(self,r):
        self.stim['INNER_POINT'].setRadius(r)
        self.dirty=True

    def setTargetPosition(self,pos):
        self.stim['OUTER_POINT'].setPos(pos)
        self.stim['INNER_POINT'].setPos(pos)
        self.dirty=True
        self.aoiTriggeredTime=None
        self.aoiTriggeredID=None
        self.withinAOIcount=0
        self.aoiBestGaze=None
        self._mindist=100000.0
        
    def toggleDynamicStimVisibility(self,flipTime,stateDuration,event):
        self._showDynamicStim=not self._showDynamicStim
        if self._showDynamicStim is True:
            self.stim['DYNAMIC_STIM'].setOpacity(1.0)
        else:
            self.stim['DYNAMIC_STIM'].setOpacity(0.0)
        self.flip()
        self.dirty=True
        return False

    def setDynamicStimPosition(self,flipTime,stateDuration,event):
        if self.dynamicStimPositionFuncPtr:
            x,y=self.dynamicStimPositionFuncPtr()
            
            if self.nextAreaOfInterest:
                p=Point(x,y)
                if self.nextAreaOfInterest.contains(p):                         
                    self.withinAOIcount+=1
                    if self.withinAOIcount>=self.WITHIN_AOI_SAMPLE_COUNT_THRESHOLD:
                        if self.aoiTriggeredID is None:                        
                            self.aoiTriggeredTime=event.time
                            self.aoiTriggeredID=event.event_id
                            cdist=self.nextAreaOfInterest.centroid.distance(p)
                            if cdist<self._mindist:
                                self._mindist=cdist
                                self.aoiBestGaze=x,y
                else:
                    self.withinAOIcount=0
                del p
                    
            if self._showDynamicStim is True:
                self.stim['DYNAMIC_STIM'].setPos((x,y))
                self.dirty=True
                self.flip()
        return False

    def flip(self, text=''):
        if text is not None:
            text="TARGET_SCREEN SYNC: [%s] [%s] "%(str(self.stim['OUTER_POINT'].pos),text)
        return ScreenState.flip(self,text)


