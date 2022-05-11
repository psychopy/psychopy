#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import copy
import psychopy
from .text import TextStim
from .rect import Rect
from psychopy.data.utils import importConditions, listFromString
from psychopy.visual.basevisual import (BaseVisualStim,
                                        ContainerMixin,
                                        ColorMixin)
from psychopy import logging, layout
from random import shuffle
from pathlib import Path

__author__ = 'Jon Peirce, David Bridges, Anthony Haffey'

from ..colors import Color

_REQUIRED = -12349872349873  # an unlikely int

# a dict of known fields with their default vals
_knownFields = {
    'index': None,  # optional field to index into the rows
    'itemText': _REQUIRED,  # (question used until 2020.2)
    'itemColor': None,
    'itemWidth': 1,  # fraction of the form
    'type': _REQUIRED,  # type of response box (see below)
    'options': ('Yes', 'No'),  # for choice box
    'ticks': None,#(1, 2, 3, 4, 5, 6, 7),
    'tickLabels': None,
    'font': None,
    # for rating/slider
    'responseWidth': 1,  # fraction of the form
    'responseColor': None,
    'markerColor': None,
    'layout': 'horiz',  # can be vert or horiz
}
_doNotSave = [
    'itemCtrl', 'responseCtrl',  # these genuinely can't be save
    'itemColor', 'itemWidth', 'options', 'ticks', 'tickLabels',  # not useful?
    'responseWidth', 'responseColor', 'layout',
]
_knownRespTypes = {
    'heading', 'description',  # no responses
    'rating', 'slider',  # slider is continuous
    'free text',
    'choice', 'radio'  # synonyms (radio was used until v2020.2)
}
_synonyms = {
    'itemText': 'questionText',
    'choice': 'radio',
    'free text': 'textBox'
}

# Setting debug to True will set the sub-elements on Form to be outlined in red, making it easier to determine their position
debug = False


class Form(BaseVisualStim, ContainerMixin, ColorMixin):
    """A class to add Forms to a `psychopy.visual.Window`

    The Form allows Psychopy to be used as a questionnaire tool, where
    participants can be presented with a series of questions requiring responses.
    Form items, defined as questions and response pairs, are presented
    simultaneously onscreen with a scrollable viewing window.

    Example
    -------
    survey = Form(win, items=[{}], size=(1.0, 0.7), pos=(0.0, 0.0))

    Parameters
    ----------
    win : psychopy.visual.Window
        The window object to present the form.
    items : List of dicts or csv or xlsx file
        a list of dicts or csv file should have the following key, value pairs / column headers:
                 "index": The item index as a number
                 "itemText": item question string,
                 "itemWidth": fraction of the form width 0:1
                 "type": type of rating e.g., 'radio', 'rating', 'slider'
                 "responseWidth": fraction of the form width 0:1,
                 "options": list of tick labels for options,
                 "layout": Response object layout e.g., 'horiz' or 'vert'
    textHeight : float
        Text height.
    size : tuple, list
        Size of form on screen.
    pos : tuple, list
        Position of form on screen.
    itemPadding : float
        Space or padding between form items.
    units : str
        units for stimuli - Currently, Form class only operates with 'height' units.
    randomize : bool
        Randomize order of Form elements
    """

    knownStyles = {
        'light': {
            'fillColor': [0.89, 0.89, 0.89],
            'borderColor': None,
            'itemColor': 'black',
            'responseColor': 'black',
            'markerColor': [0.89, -0.35, -0.28],
            'font': "Open Sans",
        },
        'dark': {
            'fillColor': [-0.19, -0.19, -0.14],
            'borderColor': None,
            'itemColor': 'white',
            'responseColor': 'white',
            'markerColor': [0.89, -0.35, -0.28],
            'font': "Open Sans",
        },
    }

    def __init__(self,
                 win,
                 name='default',
                 colorSpace='rgb',
                 fillColor=None,
                 borderColor=None,
                 itemColor='white',
                 responseColor='white',
                 markerColor='red',
                 items=None,
                 font=None,
                 textHeight=.02,
                 size=(.5, .5),
                 pos=(0, 0),
                 style=None,
                 itemPadding=0.05,
                 units='height',
                 randomize=False,
                 autoLog=True,
                 # legacy
                 color=None,
                 foreColor=None
                 ):

        super(Form, self).__init__(win, units, autoLog=False)
        self.win = win
        self.autoLog = autoLog
        self.name = name
        self.randomize = randomize
        self.items = self.importItems(items)
        self.size = size
        self._pos = pos
        self.itemPadding = itemPadding
        self.scrollSpeed = self.setScrollSpeed(self.items, 4)
        self.units = units
        self.depth = 0

        # Appearance
        self.colorSpace = colorSpace
        self.fillColor = fillColor
        self.borderColor = borderColor
        self.itemColor = itemColor
        self.responseColor = responseColor
        self.markerColor = markerColor
        if color:
            self.foreColor = color
        if foreColor:
            self.foreColor = color

        self.font = font or "Open Sans"

        self.textHeight = textHeight
        self._baseYpositions = []
        self.leftEdge = None
        self.rightEdge = None
        self.topEdge = None
        self._currentVirtualY = 0  # Y position in the virtual sheet
        self._vheight = 0  # Height of the virtual sheet
        self._decorations = []
        self._externalDecorations = []
        # Check units - only works with height units for now
        if self.win.units != 'height':
            logging.warning(
                "Form currently only formats correctly using height units. "
                "Please change the units in Experiment Settings to 'height'")

        self._complete = False

        # Create layout of form
        self._createItemCtrls()

        self.style = style

        if self.autoLog:
            logging.exp("Created {} = {}".format(self.name, repr(self)))

    def __repr__(self, complete=False):
        return self.__str__(complete=complete)  # from MinimalStim

    def importItems(self, items):
        """Import items from csv or excel sheet and convert to list of dicts.
        Will also accept a list of dicts.

        Note, for csv and excel files, 'options' must contain comma separated values,
        e.g., one, two, three. No parenthesis, or quotation marks required.

        Parameters
        ----------
        items :  Excel or CSV file, list of dicts
            Items used to populate the Form

        Returns
        -------
        List of dicts
            A list of dicts, where each list entry is a dict containing all fields for a single Form item
        """
        def _checkSynonyms(items, fieldNames):
            """Checks for updated names for fields (i.e. synonyms)"""

            replacedFields = set()
            for field in _synonyms:
                synonym = _synonyms[field]
                for item in items:
                    if synonym in item:
                        # convert to new name
                        item[field] = item[synonym]
                        del item[synonym]
                        replacedFields.add(field)
            for field in replacedFields:
                fieldNames.append(field)
                fieldNames.remove(_synonyms[field])
                logging.warning("Form {} included field no longer used {}. "
                                "Replacing with new name '{}'"
                                .format(self.name, _synonyms[field], field))

        def _checkRequiredFields(fieldNames):
            """Checks for required headings (do this after checking synonyms)"""
            for hdr in _knownFields:
                # is it required and/or present?
                if _knownFields[hdr] == _REQUIRED and hdr not in fieldNames:
                    raise ValueError("Missing header ({}) in Form ({}). "
                                     "Headers found were: {}"
                                     .format(hdr, self.name, fieldNames))


        def _checkTypes(types, itemText):
            """A nested function for testing the number of options given

            Raises ValueError if n Options not > 1
            """
            itemDiff = set([types]) - set(_knownRespTypes)

            for incorrItemType in itemDiff:
                if incorrItemType == _REQUIRED:
                    if self._itemsFile:
                        itemsFileStr =  ("in items file '{}'"
                                         .format(self._itemsFile))
                    else:
                        itemsFileStr = ""
                    msg = ("Item {}{} is missing a required "
                           "value for its response type. Permitted types are "
                           "{}.".format(itemText, itemsFileStr,
                                        _knownRespTypes))
                if self.autoLog:
                    logging.error(msg)
                raise ValueError(msg)

        def _addDefaultItems(items):
            """
            Adds default items when missing. Works in-place.

            Parameters
            ----------
            items : List of dicts
            headers : List of column headers for each item
            """
            def isPresent(d, field):
                # check if the field is there and not empty on this row
                return (field in d and d[field] not in [None, ''])

            missingHeaders = []
            defaultValues = _knownFields
            for index, item in enumerate(items):
                defaultValues['index'] = index
                for header in defaultValues:
                    # if header is missing of val is None or ''
                    if not isPresent(item, header):
                        oldHeader = header.replace('item', 'question')
                        if isPresent(item, oldHeader):
                            item[header] = item[oldHeader]
                            logging.warning(
                                "{} is a deprecated heading for Forms. "
                                "Use {} instead"
                                .format(oldHeader, header)
                            )
                            continue
                        # Default to colour scheme if specified
                        if defaultValues[header] in ['fg', 'bg', 'em']:
                            item[header] = self.color
                        else:
                            item[header] = defaultValues[header]
                        missingHeaders.append(header)

            msg = "Using default values for the following headers: {}".format(
                missingHeaders)
            if self.autoLog:
                logging.info(msg)

        if self.autoLog:
            logging.info("Importing items...")

        if not isinstance(items, list):
            # items is a conditions file
            self._itemsFile = Path(items)
            items, fieldNames = importConditions(items, returnFieldNames=True)
        else:  # we already have a list so lets find the fieldnames
            fieldNames = set()
            for item in items:
                fieldNames = fieldNames.union(item)
            fieldNames = list(fieldNames)  # convert to list at the end
            self._itemsFile = None

        _checkSynonyms(items, fieldNames)
        _checkRequiredFields(fieldNames)
        # Add default values if entries missing
        _addDefaultItems(items)

        # Convert options to list of strings
        for idx, item in enumerate(items):
            if item['ticks']:
                item['ticks'] = listFromString(item['ticks'])
            if 'tickLabels' in item and item['tickLabels']:
                item['tickLabels'] = listFromString(item['tickLabels'])
            if 'options' in item and item['options']:
                item['options'] = listFromString(item['options'])

        # Check types
        [_checkTypes(item['type'], item['itemText']) for item in items]
        # Check N options > 1
        # Randomise items if requested
        if self.randomize:
            shuffle(items)
        return items

    def setScrollSpeed(self, items, multiplier=2):
        """Set scroll speed of Form. Higher multiplier gives smoother, but
        slower scroll.

        Parameters
        ----------
        items : list of dicts
            Items used to populate the form
        multiplier : int (default=2)
            Number used to calculate scroll speed

        Returns
        -------
        int
            Scroll speed, calculated using N items by multiplier
        """
        return len(items) * multiplier

    def _getItemRenderedWidth(self, size):
        """Returns text width for item text based on itemWidth and Form width.

        Parameters
        ----------
        size : float, int
            The question width

        Returns
        -------
        float
            Wrap width for question text
        """
        return size * self.size[0] - (self.itemPadding * 2)

    def _setQuestion(self, item):
        """Creates TextStim object containing question

        Parameters
        ----------
        item : dict
            The dict entry for a single item

        Returns
        -------
        psychopy.visual.text.TextStim
            The textstim object with the question string
        questionHeight
            The height of the question bounding box as type float
        questionWidth
            The width of the question bounding box as type float
        """
        if self.autoLog:
            logging.exp(
                    u"Question text: {}".format(item['itemText']))

        if item['type'] == 'heading':
            letterScale = 1.5
            bold = True
        else:
            letterScale = 1.0
            bold = False
        w = self._getItemRenderedWidth(item['itemWidth'])
        question = psychopy.visual.TextBox2(
                self.win,
                text=item['itemText'],
                units=self.units,
                letterHeight=self.textHeight * letterScale,
                anchor='top-left',
                alignment='center-left',
                pos=(self.leftEdge+self.itemPadding, 0),  # y pos irrelevant
                size=[w, 0.1],  # expand height with text
                autoLog=False,
                colorSpace=self.colorSpace,
                color=item['itemColor'] or self.itemColor,
                fillColor=None,
                padding=0,  # handle this by padding between items
                borderWidth=1,
                borderColor='red' if debug else None,  # add borderColor to help debug
                editable=False,
                bold=bold,
                font=item['font'] or self.font)
        # Resize textbox to be at least as tall as the text
        question._updateVertices()
        textHeight = getattr(question.boundingBox._size, question.units)[1]
        if textHeight > question.size[1]:
            question.size[1] = textHeight + question.padding[1] * 2
            question._layout()

        questionHeight = question.size[1]
        questionWidth = question.size[0]
        # store virtual pos to combine with scroll bar for actual pos
        question._baseY = self._currentVirtualY

        # Add question objects to Form element dict
        item['itemCtrl'] = question

        return question, questionHeight, questionWidth

    def _setResponse(self, item):
        """Makes calls to methods which make Slider or TextBox response objects
        for Form

        Parameters
        ----------
        item : dict
            The dict entry for a single item
        question : TextStim
            The question text object

        Returns
        -------
        psychopy.visual.slider.Slider
            The Slider object for response
        psychopy.visual.TextBox
            The TextBox object for response
        respHeight
            The height of the response object as type float
        """
        if self.autoLog:
            logging.info(
                    "Adding response to Form type: {}, layout: {}, options: {}"
                    .format(item['type'], item['layout'], item['options']))

        if item['type'].lower() == 'free text':
            respCtrl, respHeight = self._makeTextBox(item)
        elif item['type'].lower() in ['heading', 'description']:
            respCtrl, respHeight = None, 0
        elif item['type'].lower() in ['rating', 'slider', 'choice', 'radio']:
            respCtrl, respHeight = self._makeSlider(item)

        item['responseCtrl'] = respCtrl
        return respCtrl, float(respHeight)

    def _makeSlider(self, item):
        """Creates Slider object for Form class

        Parameters
        ----------
        item : dict
            The dict entry for a single item
        pos : tuple
            position of response object

        Returns
        -------
        psychopy.visual.slider.Slider
            The Slider object for response
        respHeight
            The height of the response object as type float
        """
        # Slider dict

        kind = item['type'].lower()

        # what are the ticks for the scale/slider?
        if item['type'].lower() in ['radio', 'choice']:
            if item['ticks']:
                ticks = item['ticks']
            else:
                ticks = None
            tickLabels = item['tickLabels'] or item['options'] or item['ticks']
            granularity = 1
            style = 'radio'
        else:
            if item['ticks']:
                ticks = item['ticks']
            elif item['options']:
                ticks = range(0, len(item['options']))

            else:
                raise ValueError("We don't appear to have either options or "
                                 "ticks for item '{}' of {}."
                                 .format(item['itemText'], self.name))
            # how to label those ticks
            if item['tickLabels']:
                tickLabels = [str(i).strip() for i in item['tickLabels']]
            elif 'options' in item and item['options']:
                tickLabels = [str(i).strip() for i in item['options']]
            else:
                tickLabels = None
            # style/granularity
            if kind == 'slider' and 'granularity' in item:
                if item['granularity']:
                    granularity = item['granularity']
                else:
                    granularity = 0
            elif kind == 'slider' and 'granularity' not in item:
                granularity = 0
            else:
                granularity = 1
            style = kind

        # Make invisible guide rect to help with laying out slider
        w = (item['responseWidth'] - self.itemPadding * 2) * (self.size[0] - self.scrollbarWidth) * 0.8
        if item['layout'] == 'horiz':
            h = self.textHeight * 2 + 0.03
        elif item['layout'] == 'vert':
            h = self.textHeight * 1.1 * len(item['options'])
        x = self.rightEdge - self.itemPadding - self.scrollbarWidth - w * 0.1
        guide = Rect(
            self.win,
            size=(w, h),
            pos=(x, 0),
            anchor="top-right",
            lineColor="red",
            fillColor=None,
            units=self.units,
            autoLog=False
        )
        # Get slider pos and size
        if item['layout'] == 'horiz':
            x = guide.pos[0] - guide.size[0] / 2
            w = guide.size[0]
            h = 0.03
            wrap = None  # Slider defaults are fine for horizontal
        elif item['layout'] == 'vert':
            # for vertical take into account the nOptions
            x = guide.pos[0] - guide.size[0]
            w = 0.03
            h = guide.size[1]
            wrap = guide.size[0] / 2 - 0.03
            item['options'].reverse()

        # Create Slider
        resp = psychopy.visual.Slider(
                self.win,
                pos=(x, 0),  # NB y pos is irrelevant here - handled later
                size=(w, h),
                ticks=ticks,
                labels=tickLabels,
                units=self.units,
                labelHeight=self.textHeight,
                labelWrapWidth=wrap,
                granularity=granularity,
                flip=True,
                style=style,
                autoLog=False,
                font=item['font'] or self.font,
                color=item['responseColor'] or self.responseColor,
                fillColor=item['markerColor'] or self.markerColor,
                borderColor=item['responseColor'] or self.responseColor,
                colorSpace=self.colorSpace)
        resp.guide = guide

        # store virtual pos to combine with scroll bar for actual pos
        resp._baseY = self._currentVirtualY - guide.size[1] / 2 - self.itemPadding

        return resp, guide.size[1]

    def _getItemHeight(self, item, ctrl=None):
        """Returns the full height of the item to be inserted in the form"""
        if type(ctrl) == psychopy.visual.TextBox2:
            return ctrl.size[1]
        if type(ctrl) == psychopy.visual.Slider:
            # Set radio button layout
            if item['layout'] == 'horiz':
                return 0.03 + ctrl.labelHeight*3
            elif item['layout'] == 'vert':
                # for vertical take into account the nOptions
                return ctrl.labelHeight*len(item['options'])

    def _makeTextBox(self, item):
        """Creates TextBox object for Form class

        NOTE: The TextBox 2 in work in progress, and has not been added to Form class yet.
        Parameters
        ----------
        item : dict
            The dict entry for a single item
        pos : tuple
            position of response object

        Returns
        -------
        psychopy.visual.TextBox
            The TextBox object for response
        respHeight
            The height of the response object as type float
        """
        w = (item['responseWidth'] - self.itemPadding * 2) * (self.size[0] - self.scrollbarWidth)
        x = self.rightEdge - self.itemPadding - self.scrollbarWidth
        resp = psychopy.visual.TextBox2(
                self.win,
                text='',
                pos=(x, 0),  # y pos irrelevant now (handled by scrollbar)
                size=(w, 0.1),
                letterHeight=self.textHeight,
                units=self.units,
                anchor='top-right',
                color=item['responseColor'] or self.responseColor,
                colorSpace=self.colorSpace,
                font=item['font'] or self.font,
                editable=True,
                borderColor=item['responseColor'] or self.responseColor,
                borderWidth=2,
                fillColor=None,
                onTextCallback=self._layoutY,
        )
        if debug:
            resp.borderColor = "red"
        # Resize textbox to be at least as tall as the text
        resp._updateVertices()
        textHeight = getattr(resp.boundingBox._size, resp.units)[1]
        if textHeight > resp.size[1]:
            resp.size[1] = textHeight + resp.padding[1] * 2
            resp._layout()

        respHeight = resp.size[1]
        # store virtual pos to combine with scroll bar for actual pos
        resp._baseY = self._currentVirtualY

        return resp, respHeight

    def _setScrollBar(self):
        """Creates Slider object for scrollbar

        Returns
        -------
        psychopy.visual.slider.Slider
            The Slider object for scroll bar
        """
        scroll = psychopy.visual.Slider(win=self.win,
                                        size=(self.scrollbarWidth, self.size[1] / 1.2),  # Adjust size to account for scrollbar overflow
                                        ticks=[0, 1],
                                        style='scrollbar',
                                        borderColor=self.responseColor,
                                        fillColor=self.markerColor,
                                        pos=(self.rightEdge - self.scrollbarWidth / 2, self.pos[1]),
                                        autoLog=False)
        return scroll

    def _setBorder(self):
        """Creates border using Rect

        Returns
        -------
        psychopy.visual.Rect
            The border for the survey
        """
        return psychopy.visual.Rect(win=self.win,
                                    units=self.units,
                                    pos=self.pos,
                                    width=self.size[0],
                                    height=self.size[1],
                                    colorSpace=self.colorSpace,
                                    fillColor=self.fillColor,
                                    lineColor=self.borderColor,
                                    opacity=None,
                                    autoLog=False)

    def _setAperture(self):
        """Blocks text beyond border using Aperture

        Returns
        -------
        psychopy.visual.Aperture
            The aperture setting viewable area for forms
        """
        aperture = psychopy.visual.Aperture(win=self.win,
                                            name='aperture',
                                            units=self.units,
                                            shape='square',
                                            size=self.size,
                                            pos=self.pos,
                                            autoLog=False)
        aperture.disable()  # Disable on creation. Only enable on draw.
        return aperture

    def _getScrollOffset(self):
        """Calculate offset position of items in relation to markerPos. Offset is a proportion of
        `vheight - height`, meaning the max offset (when scrollbar.markerPos is 1) is enough
        to take the bottom element to the bottom of the border.

        Returns
        -------
        float
            Offset position of items proportionate to scroll bar
        """
        offset = max(self._vheight - self.size[1], 0) * (1 - self.scrollbar.markerPos) * -1
        return offset

    def _createItemCtrls(self):
        """Define layout of form"""
        # Define boundaries of form
        if self.autoLog:
            logging.info("Setting layout of Form: {}.".format(self.name))

        self.leftEdge = self.pos[0] - self.size[0] / 2.0
        self.rightEdge = self.pos[0] + self.size[0] / 2.0

        # For each question, create textstim and rating scale
        for item in self.items:
            # set up the question object
            self._setQuestion(item)
            # set up the response object
            self._setResponse(item)


        # position a slider on right-hand edge
        self.scrollbar = self._setScrollBar()
        self.scrollbar.markerPos = 1  # Set scrollbar to start position
        self.border = self._setBorder()
        self.aperture = self._setAperture()
        # then layout the Y positions
        self._layoutY()

        if self.autoLog:
            logging.info("Layout set for Form: {}.".format(self.name))

    def _layoutY(self):
        """This needs to be done when editable textboxes change their size
        because everything below them needs to move too"""

        self.topEdge = self.pos[1] + self.size[1] / 2.0

        self._currentVirtualY = self.topEdge - self.itemPadding
        # For each question, create textstim and rating scale
        for item in self.items:
            question = item['itemCtrl']
            response = item['responseCtrl']

            # update item baseY
            question._baseY = self._currentVirtualY
            # and get height to update current Y
            questionHeight = self._getItemHeight(item=item, ctrl=question)

            # go on to next line if together they're too wide
            oneLine = (item['itemWidth']+item['responseWidth'] <= 1
                       or not response)
            if not oneLine:
                # response on next line
                self._currentVirtualY -= questionHeight + self.itemPadding / 4

            # update response baseY
            if not response:
                self._currentVirtualY -= questionHeight + self.itemPadding
                continue
            # get height to update current Y
            respHeight = self._getItemHeight(item=item, ctrl=response)

            # update item baseY
            # slider needs to align by middle
            if type(response) == psychopy.visual.Slider:
                response._baseY = self._currentVirtualY - max(questionHeight, respHeight)/2
            else:  # hopefully we have an object that can anchor at top?
                response._baseY = self._currentVirtualY

            # go on to next line if together they're too wide
            if oneLine:
                # response on same line - work out which is bigger
                self._currentVirtualY -= (
                    max(questionHeight, respHeight) + self.itemPadding
                )
            else:
                # response on next line
                self._currentVirtualY -= respHeight + self.itemPadding * 5/4

        # Calculate virtual height as distance from top edge to bottom of last element
        self._vheight = abs(self.topEdge - self._currentVirtualY)

        self._setDecorations()  # choose whether show/hide scroolbar

    def _setDecorations(self):
        """Sets Form decorations i.e., Border and scrollbar"""
        # add scrollbar if it's needed
        self._decorations = [self.border]
        if self._vheight > self.size[1]:
            self._decorations.append(self.scrollbar)

    def _inRange(self, item):
        """Check whether item position falls within border area

        Parameters
        ----------
        item : TextStim, Slider object
            TextStim or Slider item from survey

        Returns
        -------
        bool
            Returns True if item position falls within border area
        """
        upperRange = self.size[1]
        lowerRange = -self.size[1]
        return (item.pos[1] < upperRange and item.pos[1] > lowerRange)

    def _drawDecorations(self):
        """Draw decorations on form."""
        [decoration.draw() for decoration in self._decorations]

    def _drawExternalDecorations(self):
        """Draw decorations outside the aperture"""
        [decoration.draw() for decoration in self._externalDecorations]

    def _drawCtrls(self):
        """Draw elements on form within border range.

        Parameters
        ----------
        items : List
            List of TextStim or Slider item from survey
        """
        for idx, item in enumerate(self.items):
            for element in [item['itemCtrl'], item['responseCtrl']]:
                if element is None:  # e.g. because this has no resp obj
                    continue

                element.pos = (element.pos[0],
                               element._baseY - self._getScrollOffset())
                if self._inRange(element):
                    element.draw()
                    if debug and hasattr(element, "guide"):
                        # If debugging, draw position guide too
                        element.guide.pos = (element.guide.pos[0], element._baseY - self._getScrollOffset() + element.guide.size[1] / 2)
                        element.guide.draw()

    def setAutoDraw(self, value, log=None):
        """Sets autoDraw for Form and any responseCtrl contained within
        """
        for i in self.items:
            if i['responseCtrl']:
                i['responseCtrl'].__dict__['autoDraw'] = value
                self.win.addEditable(i['responseCtrl'])
        BaseVisualStim.setAutoDraw(self, value, log)

    def draw(self):
        """Draw all form elements"""
        # Check mouse wheel
        self.scrollbar.markerPos += self.scrollbar.mouse.getWheelRel()[
                                        1] / self.scrollSpeed
        # draw the box and scrollbar
        self._drawExternalDecorations()
        # enable aperture
        self.aperture.enable()
        # draw the box and scrollbar
        self._drawDecorations()
        # Draw question and response objects
        self._drawCtrls()
        # disable aperture
        self.aperture.disable()

    def getData(self):
        """Extracts form questions, response ratings and response times from
        Form items

        Returns
        -------
        list
            A copy of the data as a list of dicts
        """
        nIncomplete = 0
        nIncompleteRequired = 0
        for thisItem in self.items:
            if 'responseCtrl' not in thisItem or not thisItem['responseCtrl']:
                continue  # maybe a heading or similar
            responseCtrl = thisItem['responseCtrl']
            # get response if available
            if hasattr(responseCtrl, 'getRating'):
                thisItem['response'] = responseCtrl.getRating()
            else:
                thisItem['response'] = responseCtrl.text
            if thisItem['response'] in [None, '']:
                # todo : handle required items here (e.g. ending with * ?)
                nIncomplete += 1
            # get RT if available
            if hasattr(responseCtrl, 'getRT'):
                thisItem['rt'] = responseCtrl.getRT()
            else:
                thisItem['rt'] = None
        self._complete = (nIncomplete == 0)
        return copy.copy(self.items)  # don't want users changing orig

    def reset(self):
        """
        Clear all responses and set all items to their initial values.
        """
        # Iterate through all items
        for item in self.items:
            # If item doesn't have a response ctrl, skip it
            if "responseCtrl" not in item:
                continue
            # If response ctrl is a slider, set its rating to None
            if isinstance(item['responseCtrl'], psychopy.visual.Slider):
                item['responseCtrl'].rating = None
            # If response ctrl is a textbox, set its text to blank
            elif isinstance(item['responseCtrl'], psychopy.visual.TextBox2):
                item['responseCtrl'].text = ""
        # Set scrollbar to top
        self.scrollbar.rating = 1

    def addDataToExp(self, exp, itemsAs='rows'):
        """Gets the current Form data and inserts into an
        :class:`~psychopy.experiment.ExperimentHandler` object either as rows
        or as columns

        Parameters
        ----------
        exp : :class:`~psychopy.experiment.ExperimentHandler`
        itemsAs: 'rows','cols' (or 'columns')

        Returns
        -------

        """
        data = self.getData()  # will be a copy of data (we can trash it)
        asCols = itemsAs.lower() in ['cols', 'columns']
        # iterate over items and fields within each item
        # iterate all items and all fields before calling nextEntry
        for ii, thisItem in enumerate(data):  # data is a list of dicts
            for fieldName in thisItem:
                if fieldName in _doNotSave:
                    continue
                if asCols:  # for columns format, we need index for item
                    columnName = "{}[{}].{}".format(self.name, ii, fieldName)
                else:
                    columnName = "{}.{}".format(self.name, fieldName)
                exp.addData(columnName, thisItem[fieldName])
                # finished field
            if not asCols:  # for rows format we add a newline each item
                exp.nextEntry()
            # finished item
        # finished form
        if asCols:  # for cols format we add a newline each item
            exp.nextEntry()

    def formComplete(self):
        """Deprecated in version 2020.2. Please use the Form.complete property
        """
        return self.complete

    @property
    def pos(self):
        if hasattr(self, '_pos'):
            return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value
        if hasattr(self, 'aperture'):
            self.aperture.pos = value
        if hasattr(self, 'border'):
            self.border.pos = value
        self.leftEdge = self.pos[0] - self.size[0] / 2.0
        self.rightEdge = self.pos[0] + self.size[0] / 2.0
        # Set horizontal position of elements
        for item in self.items:
            for element in [item['itemCtrl'], item['responseCtrl']]:
                if element is None:  # e.g. because this has no resp obj
                    continue
                element.pos = [value[0], element.pos[1]]
                element._baseY = value[1]
                if hasattr(element, 'anchor'):
                    element.anchor = 'top-center'
        # Calculate new position for everything on the y axis
        self.scrollbar.pos = (self.rightEdge - .008, self.pos[1])
        self._layoutY()

    @property
    def scrollbarWidth(self):
        """
        Width of the scrollbar for this Form, in the spatial units of this Form. Can also be set as a
        `layout.Vector` object.
        """
        if not hasattr(self, "_scrollbarWidth"):
            # Default to 15px
            self._scrollbarWidth = layout.Vector(15, 'pix', self.win)
        return getattr(self._scrollbarWidth, self.units)[0]

    @scrollbarWidth.setter
    def scrollbarWidth(self, value):
        self._scrollbarWidth = layout.Vector(value, self.units, self.win)
        self.scrollbar.width[0] = self.scrollbarWidth

    @property
    def opacity(self):
        return BaseVisualStim.opacity.fget(self)

    @opacity.setter
    def opacity(self, value):
        BaseVisualStim.opacity.fset(self, value)
        self.fillColor = self._fillColor
        self.borderColor = self._borderColor
        if hasattr(self, "_foreColor"):
            self._foreColor.alpha = value
        if hasattr(self, "_itemColor"):
            self._itemColor.alpha = value
        if hasattr(self, "_responseColor"):
            self._responseColor.alpha = value
        if hasattr(self, "_markerColor"):
            self._markerColor.alpha = value

    @property
    def complete(self):
        """A read-only property to determine if the current form is complete"""
        self.getData()
        return self._complete

    @property
    def foreColor(self):
        """
        Sets both `itemColor` and `responseColor` to the same value
        """
        return ColorMixin.foreColor.fget(self)

    @foreColor.setter
    def foreColor(self, value):
        ColorMixin.foreColor.fset(self, value)
        self.itemColor = value
        self.responseColor = value

    @property
    def fillColor(self):
        """
        Color of the form's background
        """
        return ColorMixin.fillColor.fget(self)

    @fillColor.setter
    def fillColor(self, value):
        ColorMixin.fillColor.fset(self, value)
        if hasattr(self, "border"):
            self.border.fillColor = value

    @property
    def borderColor(self):
        """
        Color of the line around the form
        """
        return ColorMixin.borderColor.fget(self)

    @borderColor.setter
    def borderColor(self, value):
        ColorMixin.borderColor.fset(self, value)
        if hasattr(self, "border"):
            self.border.borderColor = value

    @property
    def itemColor(self):
        """
        Color of the text on form items
        """
        return getattr(self._itemColor, self.colorSpace)

    @itemColor.setter
    def itemColor(self, value):
        self._itemColor = Color(value, self.colorSpace)
        # Set text color on each item
        for item in self.items:
            if 'itemCtrl' in item:
                if isinstance(item['itemCtrl'], psychopy.visual.TextBox2):
                    item['itemCtrl'].foreColor =  self._itemColor

    @property
    def responseColor(self):
        """
        Color of the lines and text on form responses
        """
        if hasattr(self, "_responseColor"):
            return getattr(self._responseColor, self.colorSpace)

    @responseColor.setter
    def responseColor(self, value):
        self._responseColor = Color(value, self.colorSpace)
        # Set line color on scrollbar
        if hasattr(self, "scrollbar"):
            self.scrollbar.borderColor = self._responseColor
        # Set line and label color on each item
        for item in self.items:
            if 'responseCtrl' in item:
                if isinstance(item['responseCtrl'], psychopy.visual.Slider) or isinstance(item['responseCtrl'], psychopy.visual.TextBox2):
                    item['responseCtrl'].borderColor = self._responseColor
                    item['responseCtrl'].foreColor = self._responseColor

    @property
    def markerColor(self):
        """
        Color of the marker on any sliders in this form
        """
        if hasattr(self, "_markerColor"):
            return getattr(self._markerColor, self.colorSpace)

    @markerColor.setter
    def markerColor(self, value):
        self._markerColor = Color(value, self.colorSpace)
        # Set marker color on scrollbar
        if hasattr(self, "scrollbar"):
            self.scrollbar.fillColor = self._markerColor
        # Set marker color on each item
        for item in self.items:
            if 'responseCtrl' in item:
                if isinstance(item['responseCtrl'], psychopy.visual.Slider):
                    item['responseCtrl'].fillColor = self._markerColor

    @property
    def style(self):
        if hasattr(self, "_style"):
            return self._style

    @style.setter
    def style(self, style):
        """Sets some predefined styles or use these to create your own.

        If you fancy creating and including your own styles that would be great!

        Parameters
        ----------
        style: string

            Known styles currently include:

                'light': black text on a light background
                'dark': white text on a dark background

        """
        self._style = style
        # If style is custom, skip the rest
        if style in ['custom...', 'None', None]:
            return
        # If style is a string of a known style, use that
        if style in self.knownStyles:
            style = self.knownStyles[style]
        # By here, style should be a dict
        if not isinstance(style, dict):
            return
        # Apply each key in the style dict as an attr
        for key, val in style.items():
            if hasattr(self, key):
                setattr(self, key, val)

    @property
    def values(self):
        # Iterate through each control and append its value to a dict
        out = {}
        for item in self.getData():
            out.update(
                {item['index']: item['response']}
            )
        return out

    @values.setter
    def values(self, values):
        for item in self.items:
            if item['index'] in values:
                ctrl = item['responseCtrl']
                # set response if available
                if hasattr(ctrl, "rating"):
                    ctrl.rating = values[item['index']]
                elif hasattr(ctrl, "value"):
                    ctrl.value = values[item['index']]
                else:
                    ctrl.text = values[item['index']]
