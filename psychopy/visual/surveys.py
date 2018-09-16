def initialize():
    global content
    content = {}

    global updateScores
    def updateScores(currentSurvey,currentItem,response):
        content[currentSurvey]["items"][currentItem]["response"] = response
        answers = content[currentSurvey]["items"][currentItem]["answers"].split("|")
        answerValues = content[currentSurvey]["items"][currentItem]["answerValues"].split("|")
        thisValue = answerValues[answers.index(response)]
        content[currentSurvey]["items"][currentItem]["value"] = thisValue
        print(thisValue)

        scoringCols = content[currentSurvey]['scoring'].keys()
        for scoringCol in scoringCols:  #loop through each questionnaire related to that survey and item
            #print(content[currentSurvey]['scoring'][scoringCol])
            if currentItem in content[currentSurvey]['scoring'][scoringCol]['items']:
                #sum up the total
                content[currentSurvey]['scoring'][scoringCol]['items'][ currentItem]["value"] = thisValue

                thisTotal = 0
                theseItems = content[currentSurvey]['scoring'][scoringCol]['items'].keys()
                for thisItem in theseItems:
                    thisTotal = thisTotal+ int(content[currentSurvey]['scoring'][scoringCol]['items'][thisItem]["value"])

                content[currentSurvey]['scoring'][scoringCol]["total"] = thisTotal

                print(scoringCol + " = " + str(content[currentSurvey]['scoring'][scoringCol]["total"]))

