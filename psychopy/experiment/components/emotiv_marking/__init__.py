# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 11:20:49 2017

@author: mrbki
"""
from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import (BaseComponent, Param, getInitVals,
                                            _translate)
# overwrite (filemode='w') a detailed log of the last run in this dir
# lastLog = logging.LogFile("lastRun.log", level=logging.DEBUG, filemode='w')
from ..emotiv_record import OBJECT_NAME

thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'marker.jpg')
tooltip = _translate('Mark a period of EEG')

_localized = {
    'label': _translate('Marker Label'),
    'value': _translate('Marker Value'),
    'stop_marker': _translate('Stop Marker')
}


class EmotivMarkingComponent(BaseComponent):  # or (VisualComponent)
    def __init__(self, exp, parentName, name='eeg_marker',
                 startType='time (s)', startVal=0.0,
                 stopType='Frame N', stopVal=2,
                 startEstim='', durationEstim='0.1',
                 label='label', value=1,
                 stop_marker=False):
        super(EmotivMarkingComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=0.01)

        msg = _translate(
            "Label of the marker to be inserted")
        self.params['label'] = Param(
            label, valType='str',
            hint=msg,
            label=_localized['label'])

        msg = _translate(
            "Value of the marker to be inserted")
        self.params['value'] = Param(
            value, valType='int',
            hint=msg,
            label=_localized['value'])

        msg = _translate("Check this box to end the marker period")
        self.params['stop_marker'] = Param(
            stop_marker, valType='bool',
            allowedVals=[True, False],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized["stop_marker"])

        self.exp.requirePsychopyLibs(['emotiv'])
        self.exp.requirePsychopyLibs(['visual'])

    def writeInitCode(self, buff):
        # replace variable params with defaults
        inits = getInitVals(self.params, 'PsychoPy')
        code = ('{} = visual.BaseVisualStim('.format(inits['name']) +
                'win=win, name="{}")\n'.format(inits['name'])
                )
        buff.writeIndentedLines(code)

    def writeRoutineStartCode(self, buff):
        pass

    def writeFrameCode(self, buff):
        self.writeStartTestCode(buff)
        code = "{}.status =STARTED\n".format(self.params['name'])
        buff.writeIndented(code)
        self.writeParamUpdates(buff, 'set every frame')
        code = ("{}.inject_marker(value=str({}), label={})\n"
                    .format(OBJECT_NAME,
                            self.params['value'],
                            self.params['label']))
        buff.writeIndented(code)
        code = "{}.start_sent = True\n".format(self.params["name"])
        buff.writeIndented(code)
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ('', None, -1, 'None'):
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            code = "{}.update_marker()\n".format(OBJECT_NAME)
            buff.writeIndented(code)
            code = "{}.status = FINISHED\n".format(self.params['name'])
            buff.writeIndented(code)
            buff.setIndentLevel(-1, relative=True)
        buff.setIndentLevel(-1, relative=True)

# ==============================================================================
#     def writeRoutineEndCode(self, buff):
#         code = "del {}\n".format(self.params['name'])
#         buff.writeIndentedLines(code)
#         pass
# ==============================================================================

# ==============================================================================
#     def writeStartTestCode(self, buff):
#         """Test whether we need to start
#         """
#         lastLog.write('checking whether to start or not')
#         if self.params['startType'].val == 'time (s)':
#             # if startVal is an empty string then set to be 0.0
#             if (isinstance(self.params['startVal'].val, basestring) and
#                     not self.params['startVal'].val.strip()):
#                 self.params['startVal'].val = '0.0'
#             code = ("if t >= %(startVal)s "
#                     "and %(name)s.status == NOT_STARTED:\n")
#         elif self.params['startType'].val == 'frame N':
#             code = ("if frameN >= %(startVal)s "
#                     "and %(name)s.status == NOT_STARTED:\n")
#         elif self.params['startType'].val == 'condition':
#             code = ("if (%(startVal)s) "
#                     "and %(name)s.status == NOT_STARTED:\n")
#         else:
#             msg = "Not a known startType (%(startType)s) for %(name)s"
#             raise CodeGenerationException(msg % self.params)
# 
#         buff.writeIndented(code % self.params)
# 
#         buff.setIndentLevel(+1, relative=True)
#         code = ("# keep track of start time/frame for later\n"
#                 "%(name)s.tStart = t\n"
#                 "%(name)s.frameNStart = frameN  # exact frame index\n")
#         buff.writeIndentedLines(code % self.params)
# 
# ==============================================================================
