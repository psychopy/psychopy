import math

def initialize():
    global scoring
    scoring = {}

    global createScoring
    def createScoring(survey_data,surveyName):
        ### prepare dictionary for storing item scores
        scoring[surveyName]["scoring"] = {
            "items":{}
        }
        for i in range(len(survey_data["item_name"])):
            itemName = survey_data["item_name"][i]
            theseAnswers = survey_data["answers"][i]
            theseValues = survey_data["values"][i]
            scoring[surveyName]["items"][itemName] = {
                "response":"",
                "value":0,
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
        thisValue = values[answers.index(response)]
        scoring[currentSurvey]["items"][currentItem]["value"] = thisValue

        scoringCols = list(filter(lambda key: "score:" in key,scoring[currentSurvey]['scoring'].keys()))

        for scoringCol in scoringCols:  #loop through each questionnaire related to that survey and item
            if currentItem in scoring[currentSurvey]["scoring"][scoringCol]['items']:
                #sum up the total
                scoring[currentSurvey]["scoring"][scoringCol]['items'][ currentItem]["value"] = thisValue

                thisTotal = 0
                theseItems = scoring[currentSurvey]['scoring'][scoringCol]['items'].keys()
                for thisItem in theseItems:
                    thisTotal = thisTotal+ int(scoring[currentSurvey]['scoring'][scoringCol]['items'][thisItem]["value"])

                    scoring[currentSurvey]['scoring'][scoringCol]["total"] = thisTotal

                print(scoringCol + " = " + str(scoring[currentSurvey]['scoring'][scoringCol]["total"]))
