import _base
from os import path
from psychopy.app.builder.experiment import Param

class VisualComponent(_base.BaseComponent):
    """Base class for most visual stimuli
    """
    def __init__(self, parentName, name='', units='window units', colour=[1,1,1],
        pos=[0,0], size=[0,0], ori=0, times=[0,1], colourSpace='rgb'):
        self.order=['name']#make name come first (others don't matter)
        self.params={}
        self.params['name']=Param(name,  valType='code', updates="never", 
            hint="Name of this stimulus")
        self.params['units']=Param(units, valType='str', allowedVals=['window units', 'deg', 'cm', 'pix', 'norm'],
            hint="Units of dimensions for this stimulus")
        self.params['colour']=Param(colour, valType='num', allowedTypes=['num','str','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="Colour of this stimulus (e.g. [1,1,0], 'red' )")
        self.params['colourSpace']=Param(colourSpace, valType='str', allowedVals=['rgb','dkl','lms'],
            hint="Choice of colour space for the colour (rgb, dkl, lms)")
        self.params['pos']=Param(pos, valType='num', allowedTypes=['num','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="Position of this stimulus (e.g. [1,2] ")
        self.params['size']=Param(size, valType='num', allowedTypes=['num','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] ")
        self.params['ori']=Param(ori, valType='num', allowedTypes=['num','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="Orientation of this stimulus (in deg)")
        self.params['times']=Param(times, valType='code', allowedTypes=['code'],
            updates="never", allowedUpdates=["never"],
            hint="Start and end times for this stimulus (e.g. [0,1] or [[0,1],[2,3]] for a repeated appearance")
            
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """    
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the times test
        #set parameters that need updating every frame
        self.writeParamUpdates(buff, 'frame')
        #draw the stimulus
        buff.writeIndented("%(name)s.draw()\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)

