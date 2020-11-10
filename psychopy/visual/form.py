#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division
import copy
import psychopy
from .text import TextStim
from psychopy.data.utils import importConditions, listFromString
from psychopy.visual.basevisual import (BaseVisualStim,
                                        ContainerMixin,
                                        ColorMixin)
from psychopy import logging
from random import shuffle
from pathlib import Path

from psychopy.constants import PY3

__author__ = 'Jon Peirce, David Bridges, Anthony Haffey'

_REQUIRED = -12349872349873  # an unlikely int

# a dict of known fields with their default vals
_knownFields = {
    'index': None,  # optional field to index into the rows
    'itemText': _REQUIRED,  # (question used until 2020.2)
    'itemColor': 'fg',
    'itemWidth': 0.8,  # fraction of the form
    'type': _REQUIRED,  # type of response box (see below)
    'options': ('Yes', 'No'),  # for choice box
    'ticks': (1, 2, 3, 4, 5, 6, 7),
    'tickLabels': None,
    # for rating/slider
    'responseWidth': 0.8,  # fraction of the form
    'responseColor': 'fg',
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


class Form(BaseVisualStim, ContainerMixin, ColorMixin):
    """A class to add Forms to a `psycopy.visual.Window`

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

    def __init__(self,
                 win,
                 name='default',
                 items=None,
                 textHeight=.02,
                 size=(.5, .5),
                 pos=(0, 0),
                 style='dark',
                 itemPadding=0.05,
                 units='height',
                 randomize=False,
                 autoLog=True,
                 ):

        super(Form, self).__init__(win, units, autoLog=False)
        self.win = win
        self.autoLog = autoLog
        self.name = name
        self.style = style
        self.randomize = randomize
        self.items = self.importItems(items)
        self.size = size
        self.pos = pos
        self.itemPadding = itemPadding
        self.scrollSpeed = self.setScrollSpeed(self.items, 4)
        self.units = units
        self.depth = 0


        self.textHeight = textHeight
        self._scrollBarSize = (0.016, size[1])
        self._baseYpositions = []
        self.leftEdge = None
        self.rightEdge = None
        self.topEdge = None
        self._currentVirtualY = 0  # Y position in the virtual sheet
        self._decorations = []
        # Check units - only works with height units for now
        if self.win.units != 'height':
            logging.warning(
                "Form currently only formats correctly using height units. "
                "Please change the units in Experiment Settings to 'height'")

        self._complete = False

        # Create layout of form
        self._createItemCtrls()

        if self.autoLog:
            logging.exp("Created {} = {}".format(self.name, repr(self)))

    def __repr__(self, complete=False):
        return self.__str__(complete=complete)  # from MinimalStim

    knownStyles = ['light', 'dark']

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
                            item[header] = self.colorScheme[defaultValues[header]]
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
                pos=(self.leftEdge+self.itemPadding, 0),  # y pos irrelevant
                size=[w, None],  # expand height with text
                autoLog=False,
                color=item['itemColor'],
                padding=0,  # handle this by padding between items
                borderWidth=1,
                borderColor=None,  # add borderColor to help debug
                editable=False,
                bold=bold,
                font='Arial')

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

        def _sliderLabelWidths():
            return (item['responseWidth'] * self.size[0]) \
                   / (len(item['options']))
        kind = item['type'].lower()

        # what are the ticks for the scale/slider?
        if item['type'].lower() in ['radio', 'choice']:
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
            if kind == 'slider':
                granularity = 0
            else:
                granularity = 1
            style = kind

        # Create x position of response object
        xPos = (self.rightEdge
                - ((item['responseWidth'] * self.size[0]) / 2)
                - self._scrollBarSize[0]
                - self.itemPadding)
        # Set radio button layout
        if item['layout'] == 'horiz':
            w = (item['responseWidth'] * self.size[0]
                - self._scrollBarSize[0] - self.itemPadding) * 0.8
            h = 0.03
        elif item['layout'] == 'vert':
            # for vertical take into account the nOptions
            w = 0.03
            h = self.textHeight*len(item['options'])
            item['options'].reverse()

        # Create Slider
        x = xPos - self._scrollBarSize[0] - self.itemPadding
        resp = psychopy.visual.Slider(
                self.win,
                pos=(x, 0),  # NB y pos is irrelevant here - handled later
                size=(w, h),
                ticks=ticks,
                labels=tickLabels,
                units=self.units,
                labelHeight=self.textHeight,
                labelWrapWidth=_sliderLabelWidths(),
                granularity=granularity,
                flip=True,
                style=style,
                autoLog=False,
                color=item['responseColor'])
        resp.line.lineColorSpace = self.colorScheme['space']
        resp.line.lineColor = self.colorScheme['fg']
        resp.line.fillColorSpace = self.colorScheme['space']
        resp.line.fillColor = self.colorScheme['fg']
        resp.marker.lineColorSpace = self.colorScheme['space']
        resp.marker.lineColor = self.colorScheme['em']
        resp.marker.fillColorSpace = self.colorScheme['space']
        resp.marker.fillColor = self.colorScheme['em']

        if item['layout'] == 'horiz':
            h += self.textHeight*2

        # store virtual pos to combine with scroll bar for actual pos
        resp._baseY = self._currentVirtualY - h/2 - self.itemPadding

        return resp, h

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
        w = (item['responseWidth']*self.size[0]
             - self.itemPadding - self._scrollBarSize[0])
        x = self.rightEdge-self.itemPadding-self._scrollBarSize[0]
        resp = psychopy.visual.TextBox2(
                self.win,
                text='',
                pos=(x, 0),  # y pos irrelevant now (handled by scrollbar)
                size=(w, None),
                letterHeight=self.textHeight,
                units=self.units,
                anchor='top-right',
                color=self.colorScheme['fg'],
                colorSpace=self.colorScheme['space'],
                font='Arial',
                editable=True,
                borderColor=self.colorScheme['fg'],
                borderWidth=2,
                fillColor=self.colorScheme['bg'],
                onTextCallback=self._layoutY,
        )

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
                                      size=self._scrollBarSize,
                                      ticks=[0, 1],
                                      style='slider',
                                      pos=(self.rightEdge - .008, self.pos[1]),
                                      autoLog=False)
        scroll.line.lineColorSpace = self.colorScheme['space']
        scroll.line.lineColor = self.colorScheme['bg']
        scroll.line.fillColorSpace = self.colorScheme['space']
        scroll.line.fillColor = self.colorScheme['bg']
        scroll.marker.lineColorSpace = self.colorScheme['space']
        scroll.marker.lineColor = self.colorScheme['em']
        scroll.marker.fillColorSpace = self.colorScheme['space']
        scroll.marker.fillColor = self.colorScheme['em']

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
                                    fillColorSpace=self.colorScheme['space'],
                                    fillColor=self.colorScheme['bg'],
                                    lineColorSpace=self.colorScheme['space'],
                                    lineColor=self.colorScheme['bg'],
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
                                            pos=(0, 0),
                                            autoLog=False)
        aperture.disable()  # Disable on creation. Only enable on draw.
        return aperture

    def _getScrollOffset(self):
        """Calculate offset position of items in relation to markerPos

        Returns
        -------
        float
            Offset position of items proportionate to scroll bar
        """
        sizeOffset = (1-self.scrollbar.markerPos) * self.size[1]
        maxItemPos = self._currentVirtualY - self.size[1]
        if maxItemPos > -self.size[1]:
            return 0
        return maxItemPos*(1- self.scrollbar.markerPos) + sizeOffset

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
            oneLine = (item['itemWidth']+item['responseWidth'] > 1
                       or not response)
            if oneLine:
                # response on next line
                self._currentVirtualY -= questionHeight + self.itemPadding

            # update response baseY
            if not response:
                continue
            # get height to update current Y
            respHeight = self._getItemHeight(item=item, ctrl=response)

            # update item baseY
            # slider needs to align by middle
            if type(response) == psychopy.visual.Slider:
                response._baseY = self._currentVirtualY - respHeight/2
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
                self._currentVirtualY -= respHeight + self.itemPadding

        self._setDecorations()  # choose whether show/hide scroolbar

    def _setDecorations(self):
        """Sets Form decorations i.e., Border and scrollbar"""
        # add scrollbar if it's needed
        self._decorations = [self.border]
        fractionVisible = self.size[1] / (-self._currentVirtualY)
        if fractionVisible < 1.0:
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

    def draw(self):
        """Draw all form elements"""
        # Check mouse wheel
        self.scrollbar.markerPos += self.scrollbar.mouse.getWheelRel()[
                                        1] / self.scrollSpeed
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
    def complete(self):
        """A read-only property to determine if the current form is complete"""
        self.getData()
        return self._complete

    @property
    def style(self):
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
        # Default colours
        self.colorScheme = {
            'space': 'rgb',  # Colour space
            'em': [0.89, -0.35, -0.28],  # emphasis
            'bg': [0,0,0],  # background
            'fg': [1,1,1],  # foreground
        }
        if 'light' in style:
            self.colorScheme = {
                'space': 'rgb', # Colour space
                'em': [0.89, -0.35, -0.28],  # emphasis
                'bg': [0.89,0.89,0.89],  # background
                'fg': [-1,-1,-1],  # foreground
            }

        if 'dark' in style:
            self.colorScheme = {
                'space': 'rgb',  # Colour space
                'em': [0.89, -0.35, -0.28],  # emphasis
                'bg': [-0.19,-0.19,-0.14],  # background
                'fg': [0.89,0.89,0.89],  # foreground
            }
