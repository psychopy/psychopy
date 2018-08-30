#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A class to add survey forms to a `psycopy.visual.Window`"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy.visual.basevisual import (BaseVisualStim,
                                        ContainerMixin, ColorMixin)
from psychopy import visual, event


class Form(BaseVisualStim, ContainerMixin, ColorMixin):
    def __init__(self,
                 win,
                 questionList,
                 size,
                 pos=(0, 0),
                 itemPadding=0.05,
                 units='height',
                 ):

        self.win = win
        self.questionList = questionList
        self.size = size
        self.pos = pos
        self.itemPadding = itemPadding
        self.labelHeight = 0.02
        self.textHeight = 0.03
        self.units = units

        self.virtualHeight = 0
        self._scrollOffset = 0

        self._doLayout()

    def _doLayout(self):
        self._items = []
        self._baseYpositions = []
        leftEdge = self.pos[0] - self.size[0]/2.0
        rightEdge = self.pos[0] + self.size[0]/2.0
        topEdge = self.pos[1] + self.size[1]/2.0
        for item in self.questionList:
            # set up the question text
            q = visual.TextStim(self.win,
                                text=item['qText'],
                                units=self.units,
                                height=self.textHeight,
                                alignHoriz='left',
                                wrapWidth=item['qWidth']*self.size[0])
            qHeight = q.boundingBox[1] / float(self.win.size[1]/2)
            w = q.boundingBox[0] / float(self.win.size[0]/2)
            q.pos = (leftEdge,
                     topEdge+self.virtualHeight-qHeight/2-self.itemPadding)

            self._items.append(q)
            # we'll update the position on each draw using
            # self._baseYpositions + form.pos[1] + _scrollOffset
            self._baseYpositions.append(self.virtualHeight-qHeight/2)

            if item['aType'].lower() in ['rating', 'slider']:
                pos = (rightEdge-item['aWidth']*self.size[0],
                       q.pos[1])
                resp = visual.Slider(self.win,
                                     pos=pos,
                                     size=(item['aWidth']*self.size[0], 0.03),
                                     ticks=[0, 1],
                                     labels=item['aOptions'],
                                     units=self.units,
                                     labelHeight=self.labelHeight,
                                     flip=True)
            elif item['aType'].lower() in ['choice']:
                pos = (rightEdge-item['aWidth']*self.size[0],
                       q.pos[1])
                aHeight = len(item['aOptions'])*self.textHeight
                resp = visual.Slider(self.win,
                                     pos=pos,
                                     size=(0.03, aHeight),
                                     ticks=None,
                                     labels=item['aOptions'],
                                     units=self.units,
                                     labelHeight=self.textHeight,
                                     style='radio',
                                     flip=True)

            self._items.append(resp)

            # update height ready for next row
            self.virtualHeight -= max(aHeight, qHeight) + self.itemPadding

        # position a slider on right-hand edge
        self.scrollbar = visual.Slider(
                self.win, size=(0.03, self.size[1]),
                ticks=[0,1], style='slider',
                pos=(rightEdge, self.pos[1]))
        self.border = visual.Rect(win, units=self.units,
                                  pos=self.pos,
                                  width=self.size[0], height=self.size[1],
                                  )

    def draw(self):
        decorations = [self.border]  #add scrollbar if it's needed
        fractionVisible = self.size[1]/(-self.virtualHeight)
        if fractionVisible < 1.0:
            decorations.append(self.scrollbar)
            scrollPos = self.scrollbar.markerPos


        # draw the box and scrollbar
        for decoration in decorations:
            decoration.draw()

        # draw the questions etc
        for item in self._items:
            item.draw()


if __name__ == "__main__":

    # create some questions
    questions = []
    genderItem = {"qText": "What is your gender?",
                 "qWidth": 0.7,
                 "aType": "choice",
                 "aWidth": 0.3,
                 "aOptions": ["Male", "Female", "Other"]}
    questions.append(genderItem)
    # then a set of ratings
    items = ["running", "cake", "eating sticks", "programming",
             "tickling", "being tickled", "cycling", "driving", "swimming"]
    for item in items:
        entry = {"qText": "How much do you like {}".format(item),
                 "qWidth": 0.7,
                 "aType": "rating",
                 "aWidth": 0.3,
                 "aOptions": ["Lots", "Not a lot"]}
        questions.append(entry)

    # create window and display
    win = visual.Window(units='height')
    print(win.backend.shadersSupported, win._haveShaders)
    title = visual.TextStim(win, "My test survey", units='height', pos=[0,0.45])
    survey = Form(win, questionList=questions,
                  pos=(0.0, 0.0), size=(1.0, 0.6))

    for n in range(600):
        survey.draw()
        win.flip()
