# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'text.png')

class TextComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='text', 
                 text='Any text\n\nincluding line breaks', 
                 font='Arial',units='window units', color='white', colorSpace='rgb',
                 pos=[0,0], letterHeight=0.1, ori=0, startTime=0.0, duration=1.0):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self, parentName, name=name, units=units, 
                    color=color, colorSpace=colorSpace,
                    pos=pos, ori=ori, startTime=startTime, duration=duration)
        self.type='Text'
        self.url="http://www.psychopy.org/builder/components/text.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual'])
        self.parentName=parentName
        #params
        self.order=['name','startTime','duration']#make sure this is at top
        self.params['name']=Param(name, valType='code', allowedTypes=[])
        self.params['text']=Param(text, valType='str', allowedTypes=[],
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
        text = unicode(self.params['text'])
        buff.writeIndented("%(name)s=visual.TextStim(win=win, ori=%(ori)s,\n" %(self.params))
        buff.writeIndented("    text=%s,\n" %text)
        buff.writeIndented("    "+units+"pos=%(pos)s, height=%(letterHeight)s,\n" %(self.params))
        buff.writeIndented("    color=%(color)s, colorSpace=%(colorSpace)s)\n" %(self.params))  
