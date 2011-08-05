# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path
from psychopy.app.builder import components #for getInitVals()

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'text.png')
tooltip = 'Text: present formatted text'

class TextComponent(VisualComponent):
    """An event class for presenting text-based stimuli"""
    def __init__(self, exp, parentName, name='text',
                text='Any text\n\nincluding line breaks',
                font='Arial',units='from exp settings', color='white', colorSpace='rgb',
                pos=[0,0], letterHeight=0.1, ori=0,
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self, parentName, name=name, units=units,
                    color=color, colorSpace=colorSpace,
                    pos=pos, ori=ori,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Text'
        self.url="http://www.psychopy.org/builder/components/text.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual'])
        self.parentName=parentName
        #params
        self.params['name']=Param(name, valType='code', allowedTypes=[])
        self.params['text']=Param(text, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The text to be displayed")
        self.params['font']=Param(font, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The font name (e.g. Comic Sans)")
        #change the hint for size
        del self.params['size']#because you can't specify width for text
        self.params['letterHeight']=Param(letterHeight, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Specifies the height of the letter (the width is then determined by the font)")
    def writeInitCode(self,buff):
        #do we need units code?
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        #do writing of init
        inits = components.getInitVals(self.params)#replaces variable params with sensible defaults
        buff.writeIndented("%(name)s=visual.TextStim(win=win, ori=%(ori)s, name='%(name)s',\n" %(inits))
        buff.writeIndented("    text=%(text)s,\n" %inits)
        buff.writeIndented("    font=%(font)s,\n" %inits)
        buff.writeIndented("    "+unitsStr+"pos=%(pos)s, height=%(letterHeight)s,\n" %(inits))
        buff.writeIndented("    color=%(color)s, colorSpace=%(colorSpace)s)\n" %(inits))
