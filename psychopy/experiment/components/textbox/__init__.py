#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate

# the absolute path to the folder containing this path
from psychopy.visual.textbox import FontManager

thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'textbox.png')
tooltip = _translate('Textbox: present text stimuli but cooler')

# only use _localized values for label values, nothing functional:
_localized = {'text': _translate('Text'),
              'font': _translate('Font'),
              'letterHeight': _translate('Letter height'),
              'wrapWidth': _translate('Wrap width'),
              'flip': _translate('Flip (mirror)'),
              'languageStyle': _translate('Language style'),
              'bold': _translate('Bold'),
              'italic': _translate('Italic'),
              'lineSpacing': _translate('Line Spacing'),
              'padding': _translate('Padding'),
              'anchor': _translate('Anchor'),
              'fillColor': _translate('Fill Colour'),
              'borderColor': _translate('Border Colour'),
              'editable': _translate('Editable?'),
              'autoLog': _translate('Auto Log')
              }


class TextboxComponent(BaseVisualComponent):
    """An event class for presenting text-based stimuli
    """
    categories = ['Stimuli']
    targets = ['PsychoPy', 'PsychoJS']
    def __init__(self, exp, parentName, name='text',
                 # effectively just a display-value
                 text=_translate('Any text\n\nincluding line breaks'),
                 font='Arial', units='from exp settings', bold=False, italic=False,
                 color='$[1, 1, 1, 1]', colorSpace='rgb', opacity=1.0,
                 pos=(0, 0), size=None, letterHeight=20, ori=0,
                 lineSpacing=1.0,padding=None,  # gap between box and text
                 startType='time (s)', startVal=0.0, anchor='center',
                 stopType='duration (s)', stopVal=1.0,
                 flip='', startEstim='', durationEstim='', wrapWidth='',
                 languageStyle='LTR', fillColor=None,
                 borderColor=None,
                 flipHoriz=False,
                 flipVert=False,
                 editable=False, autoLog=None):
        super(TextboxComponent, self).__init__(exp, parentName, name=name,
                                            units=units,
                                            color=color,
                                            colorSpace=colorSpace,
                                            pos=pos,
                                            ori=ori,
                                            startType=startType,
                                            startVal=startVal,
                                            stopType=stopType,
                                            stopVal=stopVal,
                                            startEstim=startEstim,
                                            durationEstim=durationEstim)
        self.type = 'TextBox2'
        self.url = "http://www.psychopy.org/builder/components/text.html"

        # params
        _allow3 = ['constant', 'set every repeat', 'set every frame']  # list
        self.params['text'] = Param(
            text, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("The text to be displayed"),
            label=_localized['text'])
        self.params['font'] = Param(
            font, valType='str', allowedTypes=[],
            allowedVals=FontManager().getFontFamilyNames(),
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("The font name (e.g. Comic Sans)"),
            label=_localized['font'])
        self.params['letterHeight'] = Param(
            letterHeight, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("Specifies the height of the letter (the width"
                            " is then determined by the font)"),
            label=_localized['letterHeight'])

        self.params['wrapWidth'] = Param(
            wrapWidth, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant'],
            hint=_translate("How wide should the text get when it wraps? (in"
                            " the specified units)"),
            label=_localized['wrapWidth'])
        self.params['flipHoriz'] = Param(
            flip, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("horiz = left-right reversed; vert = up-down"
                            " reversed; $var = variable"),
            label=_localized['flip'])
        self.params['flipVert'] = Param(
            flip, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("horiz = left-right reversed; vert = up-down"
                            " reversed; $var = variable"),
            label=_localized['flip'])
        self.params['languageStyle'] = Param(
            languageStyle, valType='str',
            allowedVals=['LTR', 'RTL', 'Arabic'],
            hint=_translate("Handle right-to-left (RTL) languages and Arabic reshaping"),
            label=_localized['languageStyle'])

        self.params['italic'] = Param(
            italic, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Should text be italic?"),
            label=_localized['italic'])
        self.params['bold'] = Param(
            bold, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Should text be bold?"),
            label=_localized['bold'])
        self.params['lineSpacing'] = Param(
            lineSpacing, valType='num', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Defines the space between lines"),
            label=_localized['lineSpacing'])
        self.params['padding'] = Param(
            padding, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Defines the space between text and the textbox border"),
            label=_localized['padding'])
        self.params['anchor'] = Param(
            anchor, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Should text anchor to the top, center or bottom of the box?"),
            label=_localized['anchor'])
        self.params['fillColor'] = Param(
            fillColor, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Textbox background colour"),
            label=_localized['fillColor'])
        self.params['borderColor'] = Param(
            borderColor, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Textbox border colour"),
            label=_localized['borderColor'])
        self.params['editable'] = Param(
            editable, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Should textbox be editable?"),
            label=_localized['editable'])
        self.params['autoLog'] = Param(
            autoLog, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Auto log"),
            label=_localized['autoLog'])

        for prm in ('ori', 'opacity', 'colorSpace', 'units', 'wrapWidth',
                    'flipHoriz', 'flipVert', 'languageStyle'):
            self.params[prm].categ = 'Advanced'

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s,\n" % self.params
        # do writing of init
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params, 'PsychoPy')
        code = (
            "%(name)s = visual.TextBox2(\n"
            "     win, %(text)s, %(font)s,"
            "     pos=%(pos)s,\n"
            "     " + unitsStr +
            "     letterHeight=%(letterHeight)s,\n"
            "     size=%(size)s,\n"
            "     color=%(color)s,\n"
            "     colorSpace=%(colorSpace)s,\n"
            "     opacity=%(opacity)s,\n"
            "     bold=%(bold)s,\n"
            "     italic=%(italic)s,\n"
            "     lineSpacing=%(lineSpacing)s,\n"
            "     padding=%(padding)s,\n"
            "     anchor=%(anchor)s,\n"
            "     fillColor=%(fillColor)s,\n"
            "     borderColor=%(borderColor)s,\n"
            "     flipHoriz=%(flipHoriz)s,\n"
            "     flipVert=%(flipVert)s,\n"
            "     editable=%(editable)s,\n"
            "     name='%(name)s',\n"
            "     autoLog=None\n"
            ");\n"
        )
        if self.params['wrapWidth'].val in ['', 'None', 'none']:
            inits['wrapWidth'] = 'None'
        buff.writeIndentedLines(code % inits)

    def writeInitCodeJS(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = "  units: undefined, \n"
        else:
            unitsStr = "  units: %(units)s, \n" % self.params
        # do writing of init
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params, 'PsychoJS')

        # check for NoneTypes
        for param in inits:
            if inits[param] in [None, 'None', '']:
                inits[param].val = 'undefined'
                if param == 'text':
                    inits[param].val = "''"

        code = ("%(name)s = new visual.TextStim({\n"
                "  win: psychoJS.window,\n"
                "  name: '%(name)s',\n"
                "  text: %(text)s,\n"
                "  font: %(font)s,\n" + unitsStr +
                "  pos: %(pos)s, height: %(letterHeight)s,"
                "  wrapWidth: %(wrapWidth)s, ori: %(ori)s,\n"
                "  color: new util.Color(%(color)s),"
                "  opacity: %(opacity)s,")
        buff.writeIndentedLines(code % inits)

        flip = self.params['flip'].val.strip()
        if flip == 'horiz':
            flipStr = 'flipHoriz : true, '
        elif flip == 'vert':
            flipStr = 'flipVert : true, '
        elif flip:
            msg = ("flip value should be 'horiz' or 'vert' (no quotes)"
                   " in component '%s'")
            raise ValueError(msg % self.params['name'].val)
        else:
            flipStr = ''
        depth = -self.getPosInRoutine()
        code = ("  %sdepth: %.1f \n"
                "});\n\n" % (flipStr, depth))
        buff.writeIndentedLines(code)
