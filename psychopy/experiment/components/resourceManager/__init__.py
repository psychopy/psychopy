from pathlib import Path

from psychopy.alerts import alert
from .._base import BaseComponent
from psychopy.localization import _translate
from ... import getInitVals
from ...params import Param


class ResourceManagerComponent(BaseComponent):
    categories = ['Custom']
    targets = ['PsychoJS']
    iconFile = Path(__file__).parent / "resource_manager.png"
    tooltip = _translate("Pre-load some resources into memory so that components using them can start without having "
                         "to load first")
    beta = True

    def __init__(self, exp, parentName, name='resources',
                 startType='time (s)', startVal=0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 resources=None, actionType='Start and Check',
                 saveStartStop=True, syncScreenRefresh=False,
                 disabled=False):

        BaseComponent.__init__(self, exp, parentName, name=name,
                               startType=startType, startVal=startVal,
                               stopType=stopType, stopVal=stopVal,
                               startEstim=startEstim, durationEstim=durationEstim,
                               saveStartStop=saveStartStop, syncScreenRefresh=syncScreenRefresh,
                               disabled=disabled)
        self.type = 'ResourceManager'
        self.url = "https://www.psychopy.org/builder/components/resourcemanager"

        if not resources:
            resources = []

        self.params['resources'] = Param(resources,
            valType='list', inputType="fileList", categ='Basic', updates='constant',
            hint=_translate("Resources to download/check"),
            direct=False, label=_translate("Resources"))

        self.params['checkAll'] = Param(resources,
            valType='bool', inputType="bool", categ='Basic',
            hint=_translate("When checking these resources, also check for all currently downloading?"),
            label=_translate("Check All"))

        self.params['actionType'] = Param(actionType,
            valType='str', inputType='choice', categ='Basic',
            allowedVals=["Start and Check", "Start Only", "Check Only"],
            hint=_translate("Should this component start an / or check resource preloading?"),
            label=_translate("Preload Actions")
        )

        self.params['stopVal'].label = "Check"

        self.depends.append(
             {"dependsOn": "actionType",  # must be param name
              "condition": "=='Start Only'",  # val to check for
              "param": "stop",  # param property to alter
              "true": "hide",  # what to do with param if condition is True
              "false": "show",  # permitted: hide, show, enable, disable
              }
        )
        self.depends.append(
             {"dependsOn": "actionType",  # must be param name
              "condition": "=='Check Only'",  # val to check for
              "param": "start",  # param property to alter
              "true": "hide",  # what to do with param if condition is True
              "false": "show",  # permitted: hide, show, enable, disable
              }
         )
        self.depends.append(
             {"dependsOn": "actionType",  # must be param name
              "condition": "=='Check Only'",  # val to check for
              "param": "start",  # param property to alter
              "true": "hide",  # what to do with param if condition is True
              "false": "show",  # permitted: hide, show, enable, disable
              }
         )
        self.depends.append(
             {"dependsOn": "checkAll",  # must be param name
              "condition": "==True",  # val to check for
              "param": "resources",  # param property to alter
              "true": "disable",  # what to do with param if condition is True
              "false": "enable",  # permitted: hide, show, enable, disable
              }
         )

    def writeInitCode(self, buff):
        """
        As ResourceManager is not yet implemented in Python, create a placeholder object purely to prevent crashing
        """
        # Get initial values
        inits = getInitVals(self.params, 'PsychoPy')
        # Create dummy object
        code = (
            "%(name)s = core.OnlineOnlyComponent()"
        )
        buff.writeIndentedLines(code % inits)
        # Raise not implemented alert
        alert(4335, strFields={'comp': type(self).__name__})

    def writeInitCodeJS(self, buff):
        # Get initial values
        inits = getInitVals(self.params, 'PsychoJS')
        # Create object
        code = (
            "%(name)s = {\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
            "status: PsychoJS.Status.NOT_STARTED\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            "};\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeFrameCodeJS(self, buff):
        # Get initial values
        inits = getInitVals(self.params, 'PsychoJS')
        # Sub in ALL_RESOURCES if checkAll is ticked
        if inits['checkAll']:
            inits['resources'] = "core.ServerManager.ALL_RESOURCES"
        # Write start code if mode includes start
        if "start" in self.params['actionType'].val.lower():
            code = (
                "// start downloading resources specified by component %(name)s\n"
                "if (t >= %(startVal)s && %(name)s.status === PsychoJS.Status.NOT_STARTED) {\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(1, relative=True)
            code = (
                    "console.log('register and start downloading resources specified by component %(name)s');\n"
                    "psychoJS.serverManager.prepareResources(%(resources)s);\n"
                    "resources.status = PsychoJS.Status.STARTED;\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(-1, relative=True)
            code = (
                "}"
            )
            buff.writeIndentedLines(code % inits)
        # Write check code if mode includes check
        if "check" in self.params['actionType'].val.lower():
            code = (
                "// check on the resources specified by component %(name)s\n"
                "if (t >= %(stopVal)s && %(name)s.status === PsychoJS.Status.STARTED) {\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(1, relative=True)
            code = (
                    "if (psychoJS.serverManager.getResourceStatus(%(resources)s) === core.ServerManager.ResourceStatus.DOWNLOADED) {\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(1, relative=True)
            code = (
                        "console.log('finished downloading resources specified by component %(name)s');\n"
                        "%(name)s.status = PsychoJS.Status.FINISHED;\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(-1, relative=True)
            code = (
                "}"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(-1, relative=True)
            code = (
                "}"
            )
            buff.writeIndentedLines(code % inits)
