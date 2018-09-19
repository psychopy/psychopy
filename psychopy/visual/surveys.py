#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Creates a module that manages surveys. This is not currently embedded within the Form class because
    there might be multiple surveys in an experiment, so this scoring method can store multiple Forms' worth of scoring
    information.

        :Authors:
            - 2018: Anthony Haffey
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).


from psychopy import visual

import math

def initialize():


    global thisSurvey
    thisSurvey = {} #this just gets replaced anyway - right?

    global scoring
    scoring = {}

    global completed
    completed = []

    global createScoring
    def createScoring(survey_data,surveyName):

        completed.append(False)

        ### prepare dictionary for storing item scores
        scoring[surveyName]["scoring"] = {
            "items":{}
        }
        for i in range(len(survey_data["item_name"])):

            thisOptional = survey_data["optional"][i]
            if isinstance(thisOptional, float) | isinstance(thisOptional, int):
                if math.isnan(survey_data["optional"][i]) == True:
                    thisValue = 0
                else:
                    print("Error: number instead of 'yes' or 'no' used for 'optional' column")
                    exit()

            elif survey_data["optional"][i].lower() == "no":
                thisValue = "none"  # i.e. trigger fail in checkOptional later
            else:
                thisValue = 0


            itemName = survey_data["item_name"][i]
            theseAnswers = survey_data["answers"][i]
            theseValues = survey_data["values"][i]
            scoring[surveyName]["items"][itemName] = {
                "response":"",
                "value":thisValue,
                "optional":"",
                "answers":theseAnswers,
                "values":theseValues
            }

        ### prepare dictionary for storing scale scores
        scoringCols = list(filter(lambda x: "score:" in x, survey_data.columns))

        for scoringCol in scoringCols:
            scoring[surveyName]["scoring"][scoringCol] = {
                "items": {},
                "total": 0
            }
            for i in range(len(survey_data["item_name"])):
                thisScoreCode = survey_data[scoringCol][i]
                thisItemName = survey_data["item_name"][i]
                if isinstance(thisScoreCode, str):
                    scoring[surveyName]["scoring"][scoringCol]["items"][thisItemName] = {
                        "code": thisScoreCode,
                        "value": 0
                    }
                elif math.isnan(thisScoreCode) == False:
                    scoring[surveyName]["scoring"][scoringCol]["items"][thisItemName] = {
                        "code": thisScoreCode,
                        "value": 0
                    }

    global updateScores
    def updateScores(currentSurvey,currentItem,response):

        #update the appropriate row
        #index which row has the current item

        scoring[currentSurvey]["items"][currentItem]["response"] = response
        answers = scoring[currentSurvey]["items"][currentItem]["answers"].split("|")
        values = scoring[currentSurvey]["items"][currentItem]["values"].split("|")
        valueIndex = answers.index(response)
        thisValue = values[valueIndex]
        scoring[currentSurvey]["items"][currentItem]["value"] = thisValue

        scoringCols = list(filter(lambda key: "score:" in key,scoring[currentSurvey]['scoring'].keys()))

        for scoringCol in scoringCols:  #loop through each questionnaire related to that survey and item
            if currentItem in scoring[currentSurvey]["scoring"][scoringCol]['items']:

                ##identify scoring
                thisCode = scoring[currentSurvey]["scoring"][scoringCol]['items'][currentItem]["code"]
                if type(thisCode) is str:
                    if "r" in thisCode:
                        thisCode = thisCode.lower()
                        thisCode = float(thisCode.replace("r",""))
                        theseValues = values[::-1]
                    else:
                        print("Error: problem with attempt to use reverse scoring - check your spreadsheet")
                        exit()
                else:
                    theseValues = values
                thisValue = thisCode * float(theseValues[valueIndex])

                scoring[currentSurvey]["scoring"][scoringCol]['items'][ currentItem]["value"] = thisValue

                # sum up the total
                thisTotal = 0
                theseItems = scoring[currentSurvey]['scoring'][scoringCol]['items'].keys()
                for thisItem in theseItems:
                    thisValue = scoring[currentSurvey]['scoring'][scoringCol]['items'][thisItem]["value"]
                    if isinstance(thisValue, float) | isinstance(thisValue, int):
                        thisTotal = thisTotal+ int(scoring[currentSurvey]['scoring'][scoringCol]['items'][thisItem]["value"])
                    # else just skip

                scoring[currentSurvey]['scoring'][scoringCol]["total"] = thisTotal
                print(scoringCol + " = " + str(scoring[currentSurvey]['scoring'][scoringCol]["total"])) #keeping this until scoring is completely verified

    global saveScores
    def saveScores(currentSurvey,thisExp):

        ## confirm that the user can proceed, or highlight which questions they still need to complete
        itemsFailed = []
        for i in range(len(thisSurvey._items["response"])):
            try:
                #if completed the item
                updateScores(thisSurvey.name,
                             thisSurvey._items["response"][i].name,
                             thisSurvey._items["response"][i].rating)
                thisSurvey._items["question"][i].color = "black"
            except:
                #means that there's no response
                item = thisSurvey._items["response"][i].name

                if item != "unnamed TextStim":
                    thisItem = scoring[currentSurvey]["items"][item]
                    if thisItem["value"] == "none":
                        itemsFailed.append(thisItem)
                        thisSurvey._items["question"][i].color = "red"


        #Save if completed checks
        if len(itemsFailed) == 0:

            itemNames = scoring[currentSurvey]["items"].keys()
            for itemName in itemNames:
                thisExp.addData(currentSurvey + "_" + itemName + "_response",
                                scoring[currentSurvey]['items'][itemName]["response"])
                thisExp.addData(currentSurvey + "_" + itemName + "_value",
                                scoring[currentSurvey]['items'][itemName]["value"])

            scoringCols = list(filter(lambda key: "score:" in key, scoring[currentSurvey]['scoring'].keys()))
            for scoringCol in scoringCols:  # loop through each questionnaire related to that survey and item
                thisExp.addData(currentSurvey + "_" + scoringCol + "_total",
                                scoring[currentSurvey]['scoring'][scoringCol]["total"])

            completed[sum(completed)] = True #i.e. time to move on
        else:
            print("Cannot proceed, not all necessary questions responded to")
            print(itemsFailed)
        return itemsFailed