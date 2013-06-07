'''
Module with experiment code generation routines
'''

def timeStartTest(component, codeBuffer):
    if not component.params['startVal'].val.strip():
        component.params['startVal'].val = '0.0'
    codeBuffer.writeIndented("if t >= %(startVal)s and %(name)s.status == NOT_STARTED:\n" % (component.params))

def frameNStartTest(component, codeBuffer):
    codeBuffer.writeIndented("if frameN >= %(startVal)s and %(name)s.status == NOT_STARTED:\n" % (component.params))

def conditionStartTest(component, codeBuffer):
    codeBuffer.writeIndented("if (%(startVal)s) and %(name)s.status == NOT_STARTED:\n" % (component.params))

def componentStartStartTest(component, codeBuffer):
    codeBuffer.writeIndented("if %(startVal)s.status == STARTED and %(name)s.status == NOT_STARTED:\n" % (component.params))

def componentFinishStartTest(component, codeBuffer):
    codeBuffer.writeIndented("if %(startVal)s.status == FINISHED and %(name)s.status == NOT_STARTED:\n" % (component.params))

def mouseClickStartTest(component, codeBuffer):
    codeBuffer.writeIndented("if len(%(startVal)s.time) > 0 and %(name)s.status == NOT_STARTED:\n" % (component.params))

def keyPressStartTest(component, codeBuffer):
    codeBuffer.writeIndented("if %(startVal)s.rt != [] and %(name)s.status == NOT_STARTED:\n" % (component.params))

START_TEST = {
    "time (s)": timeStartTest,
    "frame N": frameNStartTest,
    "condition": conditionStartTest,
    "COMPONENT_START": componentStartStartTest,
    "COMPONENT_FINISH": componentFinishStartTest,
    "MOUSE_CLOCK": mouseClickStartTest,
    "KEY_PRESS": keyPressStartTest
}

def timeStopTest(component, codeBuffer):
    codeBuffer.writeIndented("elif %(name)s.status == STARTED and t >= %(stopVal)s:\n" % (component.params))

def durationStopTest(component, codeBuffer):
    if component.params['startType'].val=='time (s)':
        codeBuffer.writeIndented("elif %(name)s.status == STARTED and t >= (%(startVal)s + %(stopVal)s):\n" % (component.params))
    else: #start at frame and end with duratio (need to use approximation)
        codeBuffer.writeIndented("elif %(name)s.status == STARTED and t >= (%(name)s.tStart + %(stopVal)s):\n" % (component.params))

def durationFramesStopTest(component, codeBuffer):
    codeBuffer.writeIndented("elif %(name)s.status == STARTED and frameN >= (%(name)s.frameNStart + %(stopVal)s):\n" % (component.params))

def frameNStopTest(component, codeBuffer):
    codeBuffer.writeIndented("elif %(name)s.status == STARTED and frameN >= %(stopVal)s:\n" % (component.params))

def conditionStopTest(component, codeBuffer):
    codeBuffer.writeIndented("elif %(name)s.status == STARTED and (%(stopVal)s):\n" % (component.params))

def componentStartStopTest(component, codeBuffer):
    codeBuffer.writeIndented("elif %(name)s.status == STARTED and %(stopVal)s.status == STARTED:\n" % (component.params))

def componentFinishStopTest(component, codeBuffer):
    codeBuffer.writeIndented("elif %(name)s.status == STARTED and %(stopVal)s.status == FINISHED:\n" % (component.params))

def mouseClickStopTest(component, codeBuffer):
    codeBuffer.writeIndented("elif %(name)s.status == STARTED and len(%(stopVal)s.time) > 0:\n" % (component.params))

def keyPressStopTest(component, codeBuffer):
    codeBuffer.writeIndented("elif %(name)s.status == STARTED and  %(stopVal)s.rt != []:\n" % (component.params))

STOP_TEST = {
    "time (s)": timeStopTest,
    "frame N": frameNStopTest,
    "duration (s)": durationStopTest,
    "duration (frames)": durationFramesStopTest,
    "condition": conditionStopTest,
    "COMPONENT_START": componentStartStopTest,
    "COMPONENT_FINISH": componentFinishStopTest,
    "MOUSE_CLOCK": mouseClickStopTest,
    "KEY_PRESS": keyPressStopTest
}
