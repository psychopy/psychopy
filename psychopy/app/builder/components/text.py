from _visual import * #to get the template visual component
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'text.png')

class TextComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='', 
                 text='"Hint:\nUse double quotes for text (or this looks like a variable)!"', 
                 font='arial',units='window units', colour=[1,1,1], colourSpace='rgb',
                 pos=[0,0], letterHeight=1, ori=0, times=[0,1]):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self, parentName, name=name, units=units, 
                    colour=colour, colourSpace=colourSpace,
                    pos=pos, ori=ori, times=times)
        self.type='Text'
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual'])
        self.parentName=parentName
        #params
        self.order=['name']#make sure this is at top
        self.params['text']=Param(text, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The text to be displayed")
        self.params['font']=Param(font, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The font name, or a list of names, e.g. ['arial','verdana']")
        #change the hint for size
        del self.params['size']#because you can't specify width for text
        self.params['letterHeight']=Param(letterHeight, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Specifies the height of the letter (the width is then determined by the font)")
    def writeInitCode(self,buff):
        #do we need units code?
        if self.params['units'].val=='window units': units=""
        else: units="units=%(units)s, " %self.params 
        #do writing of init
        text = self.params['text'].val
        #turn "some text" into """some text""" so that line breaks don't kill the script 
        if text.startswith('"') and not text.startswith('"""'):
            text= '""'+text+'""' 
        buff.writeIndented("%(name)s=visual.TextStim(win=win, ori=%(ori)s,\n" %(self.params))
        buff.writeIndented("    text=%s,\n" %text)
        buff.writeIndented("    "+units+"pos=%(pos)s, height=%(letterHeight)s,\n" %(self.params))
        buff.writeIndented("    %(colourSpace)s=%(colour)s)\n" %(self.params))  
