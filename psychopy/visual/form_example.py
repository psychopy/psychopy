#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v3.0.0b9),
    on September 15, 2018, at 17:21
If you publish work using this script please cite the PsychoPy publications:
    Peirce, JW (2007) PsychoPy - Psychophysics software in Python.
        Journal of Neuroscience Methods, 162(1-2), 8-13.
    Peirce, JW (2009) Generating stimuli for neuroscience using PsychoPy.
        Frontiers in Neuroinformatics, 2:10. doi: 10.3389/neuro.11.010.2008
"""

from __future__ import absolute_import, division
from psychopy import locale_setup, sound, gui, visual, core, data, event, logging, clock
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle
import os  # handy system and path functions
import sys  # to get file system encoding

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

# Store info about the experiment session
expName = 'keyboard_text'  # from the Builder filename that created this script
expInfo = {'participant': '', 'session': '001'}
dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)
if dlg.OK == False:
    core.quit()  # user pressed cancel
expInfo['date'] = data.getDateStr()  # add a simple timestamp
expInfo['expName'] = expName

# Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
filename = _thisDir + os.sep + u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])

# An ExperimentHandler isn't essential but helps with data saving
thisExp = data.ExperimentHandler(name=expName, version='',
                                 extraInfo=expInfo, runtimeInfo=None,
                                 originPath='D:\\Dropbox\\backup\\keyboard_text.py',
                                 savePickle=True, saveWideText=True,
                                 dataFileName=filename)
# save a log file for detail verbose info
logFile = logging.LogFile(filename + '.log', level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

endExpNow = False  # flag for 'escape' or other condition => quit the exp

# Start Code - component code to be run before the window creation

## Form Class - will wrap this into visual.Form later


######################## Below code will need to be embedded rather than hard coded

multichoice = ['rating','likert']

import surveys #seems easier to create for every experiment, even if it's empty, to allow adding of surveys by name
surveys.initialize()
import pandas as pd #need this for managing data frame?
import math

from psychopy.visual.basevisual import (BaseVisualStim,
                                        ContainerMixin, ColorMixin)

class Form(BaseVisualStim, ContainerMixin, ColorMixin): #VisualComponent
    """A class to add Forms to a `psycopy.visual.Window`

    The Form allows Psychopy to be used as a questionnaire tool, where
    participants can be presented with a series of questions requiring responses.
    Form items, defined as questions and response pairs, are presented
    simultaneously onscreen with a scrollable viewing window.

    Example
    -------
    survey = Form(win, excelFile='AQ.xlsx', size=(1, 1), pos=(0.0, 0.0),name="first")

    Parameters
    ----------
    win : psychopy.visual.Window
        The window object to present the form.
    items : List of dicts
        a list of dicts with the following key, value pairs:
                 "qText": item question string,
                 "qWidth": question width between 0:1
                 "aType": type of rating e.g., 'choice', 'rating', 'slider'
                 "aWidth": question width between 0:1,
                 "aOptions": list of tick labels for options,
                 "aLayout": Response object layout e.g., 'horiz' or 'vert'
    textHeight : float
        Text height.
    size : tuple, list
        Size of form on screen.
    pos : tuple, list
        Position of form on screen.
    itemPadding : float
        Space or padding between form items.
    units : str
        units for stimuli, e.g., 'height', 'norm', 'pixels' etc.
    """

    def __init__(self,
                 win,
                 name,
                 excelFile,
                 #items,
                 textHeight=.03,
                 size=(.5, .5),
                 pos=(0, 0),
                 itemPadding=0.05,
                 units='height',
                 ):

        super(Form, self).__init__(win, units)
        self._baseYpositions = []
        self._items = {'question': [], 'response': []}
        self._scrollOffset = 0
        self.excelFile = excelFile
        self.items = 'tbc'
        self.itemPadding = itemPadding
        self.labelHeight = 0.02
        self.leftEdge = None
        self.name = name
        self.pos = pos
        self.rightEdge = None
        self.size = size
        self.textHeight = textHeight
        self.topEdge = None
        self.units = units
        self.virtualHeight = 0  # Virtual height determines pos from boundary box
        self.win = win

        self.loadExcel()



    def loadExcel(self):
        questions = []

        ## initiate this survey
        surveys.content[self.name] = {
            "items": {},
            "scoring": {}
        }

        my_data = pd.read_excel(self.excelFile)
        my_data.columns = map(str.lower, my_data.columns)

        ## add each scoring column
        scoringCols = list(filter(lambda x: "score:" in x, my_data.columns))


        for scoringCol in scoringCols:
            surveys.content[self.name]["scoring"][scoringCol] = {
                "items":{},
                "total":0
            }
            for i in range(len(my_data["item_name"])):
                thisScoreCode = my_data[scoringCol][i]
                print(thisScoreCode)
                thisItemName = my_data["item_name"][i]
                if isinstance(thisScoreCode,str):
                    print("hi")
                    surveys.content[self.name]["scoring"][scoringCol]["items"][thisItemName] = {
                        "code": thisScoreCode,
                        "value": 0
                    }
                elif math.isnan(thisScoreCode) == False:
                    print("ho")
                    surveys.content[self.name]["scoring"][scoringCol]["items"][thisItemName ] = {
                        "code" :thisScoreCode,
                        "value":0
                    }

        for i in range(len(my_data["item_name"])):
            thisItemName = my_data["item_name"][i]
            surveys.content[self.name]["items"][thisItemName] = {
                "optional" : my_data["optional"][i],
                "response":"",
                "value":"",
                "answers":my_data["answers"][i],
                "answerValues": my_data["values"][i]
            }


            if (my_data["type"][i].lower() == "button"):
                thisItem = {"qText": my_data["text"][i],
                            "qName": thisItemName,
                            "qWidth": .5,
                            "aType": my_data["type"][i],
                            "aWidth": 0,
                            "aOptions": my_data["answers"][i]  # .split("|")
                            }
                questions.append(thisItem)

            if (my_data["type"][i].lower() == "instruct"):
                thisItem = {"qText": my_data["text"][i],
                            "qName": self.name + "|" + thisItemName,
                            "qWidth": 1,
                            "aType": my_data["type"][i],
                            "aWidth": 0,
                            "aOptions": "tbc",  # my_data["answers"][i] #.split("|")
                            "aLayout": 'horiz'
                            }
                questions.append(thisItem)
            if (my_data["type"][i].lower() in multichoice):
                thisItem = {"qText": my_data["text"][i],
                            "qName": self.name + "|" + thisItemName,
                            "qWidth": .5,
                            "aType": my_data["type"][i],
                            "aWidth": .5,
                            "aOptions": my_data["answers"][i],
                            "aLayout": 'vert'
                            }
                questions.append(thisItem)
            if (my_data["type"][i].lower() == "radio"):
                thisItem = {"qText": my_data["text"][i],


                            "qName": self.name + "|" + thisItemName,
                            #make use of this to be able to name the radio buttons appropriately!



                            "qWidth": .7,
                            "aType": my_data["type"][i],
                            "aWidth": .3,
                            "aOptions": my_data["answers"][i].split("|"),
                            "aLayout": 'vert'
                            }
                questions.append(thisItem)

            if (my_data["type"][i].lower() == "slider"):
                thisItem = {"qText": my_data["text"][i],
                            "qName": self.name + "|" + thisItemName,
                            "qWidth": .7,
                            "aType": my_data["type"][i],
                            "aWidth": .3,
                            "aOptions": my_data["answers"][i].split("|"),
                            "aLayout": 'horiz'
                            }
                questions.append(thisItem)
        self.items = questions
        print(surveys.content)
        self._doLayout()

    def _setQuestion(self, item):
        """Creates TextStim object containing question

        Returns
        -------
        psychopy.visual.text.TextStim
            The textstim object with the question string
        qHeight
            The height of the question bounding box as type float
        qWidth
            The width of the question bounding box as type float
        """

        if (item['aType'] == "instruct"):
            question_color = "blue"
        else:
            question_color = "black"

        question = visual.TextStim(self.win,
                                   text=item['qText'],
                                   units=self.units,
                                   height=self.textHeight,
                                   alignHoriz='left',
                                   color = question_color,
                                   wrapWidth=item['qWidth'] * self.size[0])

        qHeight = self.getQuestionHeight(question)
        qWidth = self.getQuestionWidth(question)
        self._items['question'].append(question)

        return question, qHeight, qWidth

    def _setResponse(self, item, question):
        """Creates slider object for responses

        Returns
        -------
        psychopy.visual.slider.Slider
            The Slider object for response
        aHeight
            The height of the response object as type float
        """
        pos = (self.rightEdge - item['aWidth'] * self.size[0], question.pos[1])
        aHeight = self.getRespHeight(item)

        # Set radio button choice layout
        if item['aLayout'] == 'horiz':
            aSize = (item['aWidth'] * self.size[0], 0.03)
        elif item['aLayout'] == 'vert':
            aSize = (0.03, aHeight)


        if item['aType'].lower() in ['instruct']:

            #below does nothing except stop the code breaking
            resp = visual.Slider(self.win,
                                 pos=pos,
                                 size=(item['aWidth'] * self.size[0], 0.03),
                                 #ticks=[0, 1],
                                 #labels=item['aOptions'],
                                 units=self.units,
                                 labelHeight=self.labelHeight,
                                 flip=True)

        if item['aType'].lower() in ['slider']: #'rating',
            resp = visual.Slider(self.win,
                                 pos=pos,
                                 name=item["qName"],
                                 size=(item['aWidth'] * self.size[0], 0.03),
                                 ticks=[0, 1],
                                 color='blue',
                                 labels=item['aOptions'],
                                 units=self.units,
                                 labelHeight=self.labelHeight,
                                 flip=True)
        elif item['aType'].lower() in ['radio']:
            resp = visual.Slider(self.win,
                                 pos=pos,
                                 name=item["qName"],
                                 size=aSize,
                                 color='blue',
                                 ticks=None,
                                 labels=item['aOptions'],
                                 units=self.units,
                                 labelHeight=self.textHeight,
                                 style='radio',
                                 flip=True)

        self._items['response'].append(resp)
        return resp, aHeight

    def getQuestionHeight(self, question=None):
        """Takes TextStim and calculates height of bounding box

        Returns
        -------
        float
            The height of the question bounding box
        """
        return question.boundingBox[1] / float(self.win.size[1] / 2)

    def getQuestionWidth(self, question=None):
        """Takes TextStim and calculates width of bounding box

        Returns
        -------
        float
            The width of the question bounding box
        """
        return question.boundingBox[0] / float(self.win.size[0] / 2)

    def getRespHeight(self, item):
        """Takes list and calculates height of answer

        Returns
        -------
        float
            The height of the response object
        """
        if item['aLayout'] == 'vert':
            aHeight = len(item['aOptions']) * self.textHeight
        elif item['aLayout'] == 'horiz':
           aHeight = self.textHeight

        # TODO: Return size based on response types e.g., textbox
        return aHeight

    def _setScrollBar(self):
        """Creates Slider object for scrollbar

        Returns
        -------
        psychopy.visual.slider.Slider
            The Slider object for scroll bar
        """
        return visual.Slider(win=self.win, size=(0.03, self.size[1]),
                             ticks=[0, 1], style='slider',
                             pos=(self.rightEdge, self.pos[1]))

    def _setBorder(self):
        """Creates border using Rect
        Returns
        -------
        psychopy.visual.Rect
            The border for the survey
        """
        return visual.Rect(win=self.win, units=self.units, pos=self.pos,
                           width=self.size[0], height=self.size[1])

    def _setAperture(self):
        """Blocks text beyond border using Aperture

        Returns
        -------
        psychopy.visual.Aperture
            The aperture setting viewable area for forms
        """
        return visual.Aperture(win=self.win, name='aperture',
                               units=self.units, shape='square',
                               size=self.size, pos=(0, 0))
    def _getScrollOffet(self):
        """Calculate offset position of items in relation to markerPos

        Returns
        -------
        float
            Offset position of items proportionate to scroll bar
        """
        sizeOffset = (1 - self.scrollbar.markerPos) * (self.size[1]-self.itemPadding)
        maxItemPos = min(self._baseYpositions)
        return (maxItemPos - (self.scrollbar.markerPos * maxItemPos) + sizeOffset)

    def _doLayout(self):
        """Define layout of form"""
        # Define boundaries of form
        self.leftEdge = self.pos[0] - self.size[0]/2.0
        self.rightEdge = self.pos[0] + self.size[0]/2.0
        self.topEdge = self.pos[1] + self.size[1]/2.0


        # For each question, create textstim and rating scale
        for item in self.items:
            # set up the question text
            if ('aLayout' not in item): #assume horizontal if not stated
                item['aLayout'] = "horiz"

            question, qHeight, qWidth = self._setQuestion(item)
            # Position text relative to boundaries defined according to position and size
            question.pos = (self.leftEdge,
                            self.topEdge
                            + self.virtualHeight
                            - qHeight/2 - self.itemPadding)
            response, aHeight, = self._setResponse(item, question)
            # Calculate position of question based on larger qHeight vs aHeight.
            self._baseYpositions.append(self.virtualHeight
                                        - max(aHeight, qHeight)  # Positionining based on larger of the two
                                        + (aHeight/2)            # necessary to offset size-based positioning
                                        - self.textHeight)       # Padding for unaccounted marker size in slider height
            # update height ready for next row
            self.virtualHeight -= max(aHeight, qHeight) + self.itemPadding

        # position a slider on right-hand edge
        self.scrollbar = self._setScrollBar()
        self.scrollbar.markerPos = 1  # Set scrollbar to start position
        self.border = self._setBorder()
        self.aperture = self._setAperture()

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
        upperRange = self.size[1]/2
        lowerRange = -self.size[1]/2
        return (item.pos[1] < upperRange and item.pos[1] > lowerRange)

    def draw(self):
        """Draw items on form within border area"""
        decorations = [self.border]  # add scrollbar if it's needed
        fractionVisible = self.size[1]/(-self.virtualHeight)
        if fractionVisible < 1.0:
            decorations.append(self.scrollbar)

        # draw the box and scrollbar
        for decoration in decorations:
            decoration.draw()
        self.aperture.enable()

        # draw the items
        for element in self._items.keys():
            for idx, items in enumerate(self._items[element]):
                items.pos = (items.pos[0], self.size[1]/2 + self._baseYpositions[idx] - self._getScrollOffet())
                # Only draw if within border range for efficiency
                if self._inRange(items):
                    items.draw()


############################### Above code will need to be embedded rather than hard coded

# Setup the Window
win = visual.Window(
    size=(1024, 768), fullscr=True, screen=0,
    allowGUI=False, allowStencil=True,
    monitor='testMonitor', color=[0, 0, 0], colorSpace='rgb',
    blendMode='avg', useFBO=True)
# store frame rate of monitor if we can measure it
expInfo['frameRate'] = win.getActualFrameRate()
if expInfo['frameRate'] != None:
    frameDur = 1.0 / round(expInfo['frameRate'])
else:
    frameDur = 1.0 / 60.0  # could not measure, so guess

# Initialize components for Routine "trial"
trialClock = core.Clock()
text = visual.TextStim(win=win, name='text',
                       text='Any text\n\nincluding line breaks',
                       font='Arial',
                       pos=(0, 0), height=0.1, wrapWidth=None, ori=0,
                       color='white', colorSpace='rgb', opacity=1,
                       languageStyle='LTR',
                       depth=0.0);
print(visual)
survey = Form(win, excelFile='AQ.xlsx', size=(1, 1), pos=(0.0, 0.0),name="first") #exampleDemographics.xlsx

# Create some handy timers
globalClock = core.Clock()  # to track the time since experiment started
routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine

# ------Prepare to start Routine "trial"-------
t = 0
trialClock.reset()  # clock
frameN = -1
continueRoutine = True
# update component parameters for each repeat
key_resp_2 = event.BuilderKeyResponse()
# keep track of which components have finished
trialComponents = [text, key_resp_2, survey]
for thisComponent in trialComponents:
    if hasattr(thisComponent, 'status'):
        thisComponent.status = NOT_STARTED

# -------Start Routine "trial"-------
while continueRoutine:
    # get current time
    t = trialClock.getTime()
    frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
    # update/draw components on each frame

    survey.draw()

    # *text* updates
    if t >= 0.0 and text.status == NOT_STARTED:
        # keep track of start time/frame for later
        text.tStart = t
        text.frameNStart = frameN  # exact frame index
        #text.setAutoDraw(True)



    # *key_resp_2* updates
    if t >= 0.0 and key_resp_2.status == NOT_STARTED:
        # keep track of start time/frame for later
        key_resp_2.tStart = t
        key_resp_2.frameNStart = frameN  # exact frame index
        key_resp_2.status = STARTED
        # keyboard checking is just starting
        win.callOnFlip(key_resp_2.clock.reset)  # t=0 on next screen flip

        #thisExp.addData('beepbop', "howdy")

        event.clearEvents(eventType='keyboard')
    if key_resp_2.status == STARTED:
        theseKeys = event.getKeys(keyList=['y', 'n', 'left', 'right', 'space'])

        # check for quit:
        if "escape" in theseKeys:
            endExpNow = True
        if len(theseKeys) > 0:  # at least one key was pressed
            key_resp_2.keys = theseKeys[-1]  # just the last key pressed
            key_resp_2.rt = key_resp_2.clock.getTime()
            # a response ends the routine
            continueRoutine = False

    # check if all components have finished
    if not continueRoutine:  # a component has requested a forced-end of Routine
        break
    continueRoutine = False  # will revert to True if at least one component still running
    for thisComponent in trialComponents:
        if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
            continueRoutine = True
            break  # at least one component has not yet finished

    # check for quit (the Esc key)
    if endExpNow or event.getKeys(keyList=["escape"]):
        core.quit()

    # refresh the screen
    if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
        win.flip()

# -------Ending Routine "trial"-------
for thisComponent in trialComponents:
    if hasattr(thisComponent, "setAutoDraw"):
        thisComponent.setAutoDraw(False)
# check responses
if key_resp_2.keys in ['', [], None]:  # No response was made
    key_resp_2.keys = None
thisExp.addData('key_resp_2.keys', key_resp_2.keys)
if key_resp_2.keys != None:  # we had a response
    thisExp.addData('key_resp_2.rt', key_resp_2.rt)
thisExp.nextEntry()
# the Routine "trial" was not non-slip safe, so reset the non-slip timer
routineTimer.reset()
# these shouldn't be strictly necessary (should auto-save)
thisExp.saveAsWideText(filename + '.csv')
thisExp.saveAsPickle(filename)
logging.flush()
# make sure everything is closed down
thisExp.abort()  # or data files will save again on exit
win.close()
core.quit()
