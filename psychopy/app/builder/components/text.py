# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path
from psychopy.app.builder import components #for getInitVals()

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'text.png')
tooltip = 'Text: present text stimuli'

class TextComponent(VisualComponent):
    """An event class for presenting text-based stimuli"""
    categories = ['Stimuli']
    def __init__(self, exp, parentName, name='text',
                text='Any text\n\nincluding line breaks',
                font='Arial',units='from exp settings', color='white', colorSpace='rgb',
                pos=[0,0], letterHeight=0.1, ori=0,
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                mirror='',
                startEstim='', durationEstim='', wrapWidth=''):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self, exp, parentName, name=name, units=units,
                    color=color, colorSpace=colorSpace,
                    pos=pos, ori=ori,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Text'
        self.url="http://www.psychopy.org/builder/components/text.html"
        self.exp.requirePsychopyLibs(['visual'])
        #params
        self.params['name']=Param(name, valType='code', allowedTypes=[],
            label="Name")
        self.params['text']=Param(text, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The text to be displayed",
            label="Text")
        self.params['font']=Param(font, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The font name (e.g. Comic Sans)",
            label="Font")
        #change the hint for size
        del self.params['size']#because you can't specify width for text
        self.params['letterHeight']=Param(letterHeight, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Specifies the height of the letter (the width is then determined by the font)",
            label="Letter height")
        self.params['wrapWidth']=Param(wrapWidth, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant'],
            hint="How wide should the text get when it wraps? (in the specified units)",
            label="Wrap width")
        self.params['mirror']=Param(mirror, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat', 'set every frame'],
            hint="'horiz' = left-right reversed; 'vert' = up-down reversed; $var = dynamic",
            label="Mirror")

    def writeInitCode(self,buff):
        #do we need units code?
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        #do writing of init
        inits = components.getInitVals(self.params)#replaces variable params with sensible defaults
        if self.params['wrapWidth'].val in ['','None','none']:
            inits['wrapWidth']='None'
        buff.writeIndented("%(name)s = visual.TextStim(win=win, ori=%(ori)s, name='%(name)s',\n" %(inits))
        buff.writeIndented("    text=%(text)s," %inits)
        buff.writeIndented("    font=%(font)s,\n" %inits)
        buff.writeIndented("    "+unitsStr+"pos=%(pos)s, height=%(letterHeight)s, wrapWidth=%(wrapWidth)s,\n" %(inits))
        buff.writeIndented("    color=%(color)s, colorSpace=%(colorSpace)s, opacity=%(opacity)s,\n" %(inits))
        mirror = self.params['mirror'].val
        if len(mirror) and not '$' in mirror: # $ for code
            mirrorHoriz = bool(mirror == 'horiz')
            mirrorVert = bool(mirror == 'vert')
            if mirrorHoriz or mirrorVert:
                buff.writeIndented("    horizMirror=%s, vertMirror=%s,\n" % (mirrorHoriz, mirrorVert) )
        depth=-self.getPosInRoutine()
        buff.writeIndented("    depth=%.1f)\n" %(depth))

    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" %(self.params['name']))
        if '$' in self.params['mirror'].val:
            buff.writeIndented("%s.setMirror(%s)\n" % (self.params['name'], str(self.params['mirror'])))

        self.writeStartTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.writeIndented("%(name)s.setAutoDraw(True)\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        #test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)#writes an if statement to determine whether to draw etc
            buff.writeIndented("%(name)s.setAutoDraw(False)\n" %(self.params))
            buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        #set parameters that need updating every frame
        if self.checkNeedToUpdate('set every frame'):#do any params need updating? (this method inherited from _base)
            buff.writeIndented("if %(name)s.status == STARTED:  # only update if being drawn\n" %(self.params))
            buff.setIndentLevel(+1, relative=True)#to enter the if block
            self.writeParamUpdates(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)#to exit the if block