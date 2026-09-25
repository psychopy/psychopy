#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Class of text stimuli to be displayed in a :class:`~psychopy.visual.Window`
'''

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).


from .textbox2 import TextBox2
from psychopy.tools.attributetools import attributeSetter, setAttribute

defaultLetterHeight = {'cm': 1.0,
                       'deg': 1.0,
                       'degs': 1.0,
                       'degFlatPos': 1.0,
                       'degFlat': 1.0,
                       'norm': 0.1,
                       'height': 0.2,
                       'pix': 20,
                       'pixels': 20}
defaultWrapWidth = {'cm': 15.0,
                    'deg': 15.0,
                    'degs': 15.0,
                    'degFlatPos': 15.0,
                    'degFlat': 15.0,
                    'norm': 1,
                    'height': 1,
                    'pix': 500,
                    'pixels': 500}


class TextStim(TextBox2):
    """
    Class of text stimuli to be displayed in a
    :class:`~psychopy.visual.Window`.

    Originally, TextStim was a pyglet text object. As of 2027.1.0, it is a subclass of TextBox2, with methods and attributes overloaded to behave like the old TextStim. In general, it is best to use TextBox2 directly.
    """

    def __init__(
        self, 
        win,
        text="Hello World",
        font="Arial",
        pos=(0.0, 0.0),
        depth=0,
        rgb=None,
        color=(1.0, 1.0, 1.0),
        colorSpace='rgb',
        opacity=1.0,
        contrast=1.0,
        units=None,
        ori=0.0,
        height=None,
        antialias=True,
        bold=False,
        italic=False,
        alignHoriz=None,
        alignVert=None,
        alignText='center',
        anchorHoriz='center',
        anchorVert='center',
        fontFiles=(),
        wrapWidth=None,
        flipHoriz=False,
        flipVert=False,
        languageStyle='LTR',
        draggable=False,
        name=None,
        autoLog=None,
        autoDraw=False
    ):
        # handle defaults
        if units in ("", "None", "from experiment...", None):
            units = win.units
        if height is None:
            height = defaultLetterHeight[units]
        if wrapWidth is None:
            wrapWidth = defaultWrapWidth[units]
        # initialise a textbox
        TextBox2.__init__(
            self,
            win,
            text=text,
            font=font,
            bold=bold,
            italic=italic,
            pos=pos,
            ori=ori,
            units=units,
            color=color,
            opacity=opacity,
            contrast=contrast,
            colorSpace=colorSpace,
            depth=depth,
            flipHoriz=flipHoriz,
            flipVert=flipVert,
            languageStyle=languageStyle,
            draggable=draggable,
            name=name,
            autoLog=autoLog,
            autoDraw=autoDraw,
            # use some attributes in a different way
            letterHeight=height,
            size=[wrapWidth, None],
            anchor=[anchorHoriz, anchorVert],
            alignment=[alignHoriz or alignText, alignVert or alignText],
            # and lock others
            fillColor=None,
            borderColor=None,
            borderWidth=0,
            editable=False,
            padding=0
        )
        # add any font files
        self.fontFiles = fontFiles
        # legacy attributes
        self.antialias = True

    @attributeSetter
    def fontFiles(self, value):
        # any font files added this way, add them to font manager
        self.fontMGR.addFontFiles(value)
        
    @attributeSetter
    def anchorHoriz(self, value):
        self.__dict__['anchorHoriz'] = value
        # set anchor
        self.anchor = [value, self.anchor[1]]
    
    @attributeSetter
    def anchorVert(self, value):
        self.__dict__['anchorVert'] = value
        # set anchor
        self.anchor = [self.anchor[0], value]

    @attributeSetter
    def alignHoriz(self, value):
        self.__dict__['alignHoriz'] = value
        # set anchor
        self.alignment = [value, self.alignment[1]]
    
    @attributeSetter
    def alignVert(self, value):
        self.__dict__['alignVert'] = value
        # set anchor
        self.alignment = [self.alignment[0], value]
    
    @attributeSetter
    def height(self, value):
        self.__dict__['height'] = value
        # set letter height
        self.letterHeight = value
        # refresh font
        self.font = self.font
        self._layout()

    @attributeSetter
    def wrapWidth(self, value):
        self.__dict__['wrapWidth'] = value
        # wrap width sets the horizontal size
        self.size = [value, self.size[1]]

    @property
    def posPix(self):
        return self._pos.pix

    def updateOpacity(self):
        """
        Legacy function, does nothing. Opacity is updated as soon as it's set now.
        """
        pass
    
    def _updateVertices(self):
        # update as normal
        TextBox2._updateVertices(self)
        # shrinkwrap to text height
        tight = getattr(self.boundingBox._size, self.units)
        if tight[1] > 0 and tight[1] != self.size[1]:
            self.size = [self.size[0], tight[1]]
