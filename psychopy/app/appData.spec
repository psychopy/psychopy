
lastFrame = string(default='builder-coder-runner')
skipVersion=string(default='')  #skipping any updates of this version
tipIndex = integer(default=0)
flowSize = integer(0,2,default=2)
routineSize = integer(0,2,default=2)
showLoopInfoInFlow = boolean(default=False)
testSubset = string(default='all tests')
lastNewsDate = string(default="2018-12-21T12:00:00.000Z")

[runner]
taskList = list(default=list())  # List of Runner tasks

[coder]
winX = integer(default=100)
winY = integer(default=100)
winH = integer(default=800)
winW = integer(default=600)
auiPerspective = string(default='')
state = option('normal','maxim', default='normal')
fileHistory = list(default=list())  #files in history
prevFiles = list(default=list())  #file open on last save
showIndentGuides = boolean(default=True)
showWhitespace = boolean(default=True)
showEOLs= boolean(default=False)

[builder]
fileHistory = list(default=list())  #files in history
prevFiles = list(default=list())  #file open on last quit

    [[favComponents]]
    ImageComponent = integer(default=20)

    [[frames]]

        [[[__many__]]]
        winX = integer(default=50)
        winY = integer(default=50)
        winH = integer(default=600)
        winW = integer(default=800)
        auiPerspective = string(default='')
        state = option('normal','maxim', default='normal')
        lastOpened = integer(default=0)

    [[defaultFrame]]
    winX = integer(default=50)
    winY = integer(default=50)
    winH = integer(default=600)
    winW = integer(default=800)
    auiPerspective = string(default='')
    state = option('normal','maxim', default='normal')
    lastOpened = integer(default=0)

[projects]
fileHistory = list(default=list())  # files in history
prevFiles = list(default=list())  # file open on last quit
user = string(default='')  # this is OSF user not pavlovia
pavloviaUser = string(default='')
