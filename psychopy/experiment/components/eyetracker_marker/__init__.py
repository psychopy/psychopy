from pathlib import Path

from psychopy.experiment.components import getInitVals
from psychopy.experiment.components._base import BaseComponent
from psychopy.experiment.params import Param
from psychopy.localization import _translate


class EyetrackerMarkerComponent(BaseComponent):
    """
    Add a text marker in the hdf5 file
    """
    categories = ['Eyetracking']
    targets = ['PsychoPy']
    version = "2026.2.0"
    iconFile = Path(__file__).parent / 'EyetrackerMarkerComponent.png'
    iconSVG = Path(__file__).parent / 'EyetrackerMarkerComponent.svg'
    tooltip = _translate('Add a text marker in the hdf5 file')
    beta = True

    def __init__(
        self, 
        exp, 
        parentName, 
        # basic
        name='etMarker',
        startType='time (s)', 
        startVal=0.0,
        startEstim='', 
        stopType='duration (s)', 
        stopVal=1.0,
        durationEstim='',
        message="",
        category=""
    ):
        # initialise base class
        BaseComponent.__init__(
            self, 
            exp, 
            parentName, 
            name=name,
            startType=startType, 
            startVal=startVal,
            stopType=stopType, 
            stopVal=stopVal,
            startEstim=startEstim, 
            durationEstim=durationEstim
        )
        # set attributes
        self.type = 'EyetrackerMarker'
        self.url = "https://www.psychopy.org/builder/components/eyetracker_marker"
        self.exp.requireImport(
            importName="SimpleNamespace",
            importFrom="types"
        )
        self.exp.requirePsychopyLibs(['iohub', 'hardware'])
        # remove stop params as they're not relevant
        del self.params['stopVal']
        del self.params['stopType']
        self.params['durationEstim'].val = 0.01
        # reframe start as trigger time
        self.params['startVal'].label = _translate("Send when...")
        self.params['startVal'].hint = _translate("When to send the marker?")
        
        # basic params
        self.params['message'] = Param(
            message, valType="str", inputType="single", categ="Basic",
            updates='set every frame', allowedUpdates=None,
            label=_translate("Text"),
            hint=_translate("Text to send to the eyetracker (128 characters max)")
        )
        self.params['category'] = Param(
            category, valType="str", inputType="single", categ="Basic",
            updates='set every frame', allowedUpdates=None,
            label=_translate("Category"),
            hint=_translate("Optional grouping text for the message (32 characters max)")
        )
    
    def writeInitCode(self, buff):
        inits = getInitVals(self.params, "PsychoPy")
        # create a simple namespace for this Component
        code = (
            "# simple namespace object representing the Eyetracker Marker Component %(name)s\n"
            "%(name)s = SimpleNamespace()\n"
            "%(name)s.status = NOT_STARTED\n"
        )
        buff.writeIndentedLines(code % inits)
    
    def writeFrameCode(self, buff):
        indented = self.writeStartTestCode(buff)
        # send message
        code = (
            "# send message from %(name)s\n"
            "ioServer.sendMessageEvent(text=%(message)s, category=%(category)s)\n"
        )
        buff.writeIndentedLines(code % self.params)
        # close 
        buff.setIndentLevel(-indented, relative=True)
