# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from os import path
from .._base import BaseComponent, Param, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'eyeRecord.png')
tooltip = _translate('EyeTrackerRecord: Start / Stop eye tracker recording.')


class EyeRecordComponent(BaseComponent):
    """A class used to start / stop recording on an ioHub supported
    Eye Tracker."""
    categories = ['Responses']

    def __init__(self, exp, parentName, name='eye_record',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 save='final'):
        self.type = 'EyeRecord'
        self.url = "http://www.psychopy.org/builder/components/eyeRecord.html"
        self.parentName = parentName
        self.exp = exp  # so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['iohub'])
        # params
        self.params = {}
        self.order = []  # first param after the name

        # TODO: Determine proper params for EyeRecord component.
        # Thoughts on eye record specific params, input on how any of these
        # could be merged into more standard Builder component params is welcome:
        #
        # * Start Record: Specify if and when the component should start eyetracker recording.
        #       - No
        #       - Start of Routine
        #       - Based on some condition
        #
        # * Stop Record: Specify if and when the component should stop eyetracker recording.
        #       - No
        #       - End of Routine
        #       - Based on some condition
        #
        # * startType & startVal: When should eye samples start to be used. See below.
        #       Note: These are different fields than 'Start Record'. For example:
        #             a component could start recording when routine starts but only
        #             start using sample data when some stim has been shown.
        #
        #  * stopType & stopVal: When should eye samples stop being used. See below.
        #       Note: These are different fields than 'Stop Record'. For example:
        #             a component may never want to stop recording, but may stop
        #             using sample data after some condition has occurred.
        #
        # * Force End Routine: What eye state conditions should force the
        #   routine to end?
        #       - Gaze position:
        #            - enters an area of the screen
        #            - exits an area of the screen
        #         where the 'area' could be specified using:
        #           - stim component name (to use stim.contains())
        #           - screen coords:
        #               - rect: left, top, right, bottom
        #               - circle: center, radius
        #       - Pupil Size:
        #           - > some value
        #           - < some value
        #       - Sample Status:
        #           - OK vs. Missing
        #       - Duration: How long should these Force End Routine conditions
        #                   be true before ending the routine. Specified in
        #                   # consecutive samples or time duration.

        # Issues / Considerations:
            # 1. Binocular vs. Monocular recording: Should binoc data be combined / averaged
            #    so EyeRecord Component only ever needs to deal with a single
            #    gaze pos, pupil size, & status.
            # 2. Eye Event Types: I assume EyeRecord only ever uses eye sample
            #    events. Other events, like fixations, saccades, blinks, are ignored.
            # 3. How will gaze contingent stim be supported? Is something needed
            #    in this component type, or will the stim component that is to
            #    move with gaze position have it's position param set to some equation that uses
            #    the eyetracker.getLastGazePosition() method.


        # standard params (can ignore)
        msg = _translate(
            "Name of this component (alpha-numeric or _, no spaces)")
        self.params['name'] = Param(
            name, valType='code', allowedTypes=[],
            hint=msg,
            label="Name")

        self.params['startType'] = Param(
            startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint=_translate("How do you want to define your start point?"))

        self.params['stopType'] = Param(
            stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)',
                         'frame N', 'condition'],
            hint=_translate("How do you want to define your end point?"))

        self.params['startVal'] = Param(
            startVal, valType='code', allowedTypes=[],
            hint=_translate("When does the component start?"))

        self.params['stopVal'] = Param(
            stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=_translate("When does the component end? (blank is endless)"))

        msg = _translate("(Optional) expected start (s), purely for "
                         "representing in the timeline")
        self.params['startEstim'] = Param(
            startEstim, valType='code', allowedTypes=[],
            hint=msg)

        msg = _translate("(Optional) expected duration (s), purely for "
                         "representing in the timeline")
        self.params['durationEstim'] = Param(
            durationEstim, valType='code', allowedTypes=[],
            hint=msg)

        # Eye tracker config will be set in the ioHub Config file
        # specified in the Experiment settings dialog -> ioHub tab.
        # So no config file needs to be specified here.
        # useful params for the eyetracker - keep to a minimum if possible! ;-)
        #self.params['Config file'] = Param(
        #    configFile, valType='str',
        #    hint=_translate("How do you want to define your start point?"))

        # This controls saving of some eye sample data to PsychoPy output files
        # only. All eye tracker events collected while the device is recording
        # are saved to the ioHub HDF5 file.
        msg = _translate(
            "How often should the eyetracker state (x,y,"
            "pupilsize...) be stored? On every video frame, every click "
            "or just at the end of the Routine?")
        self.params['saveState'] = Param(
            save, valType='str',
            allowedVals=['final', 'every frame', 'never'],
            hint=msg,
            label="Save eyetracker state")

    def writeStartCode(self, buff):
        if self.exp.iohub_codegen is None:
            print("ioHub must be enabled to use this component type.")
        else:
            if not self.exp.iohub_codegen.get('eyetracker'):
                self.exp.iohub_codegen['eyetracker'] = True
                buff.writeIndented("# Create iohub_eyetracker device variable\n")
                code = (
                        "try:\n"
                        "    iohub_eyetracker = iohub_server.devices.tracker\n"
                        "except Exception:\n"
                        "    # No eye tracker config found in iohub_config.yaml\n"
                        "    from psychopy.gui.qtgui import criticalDlg, hideWindow\n"
                        "    hideWindow(win)\n"
                        "    dlg_ = criticalDlg('ioHub Eye Tracker Not Configured',\n"
                        "                'No Eye Tracker config found in the the '\n"
                        "                'ioHub settings file:\\n'\n"
                        "                %(ioHubConfigFile)s\n"
                        "                '\\n\\n'\n"
                        "                'Update the ioHub settings file with an '\n"
                        "                'eye tracker configuration\\nor remove '\n"
                        "                'all Eye Tracker Components from your project.'\n"
                        "                '\\n\\nPress OK to exit demo.')\n"
                        "    iohub_server.quit()\n"
                        "    core.quit()\n"%self.exp.settings.params)
                buff.writeIndentedLines(code)

            if not self.exp.iohub_codegen.get('eyerecord'):
                self.exp.iohub_codegen['eyerecord'] = True
                code = ("\n\n"
                         "# Create an 'EyeRecordRuntime' class for the EyeRecord\n"
                         "# Component type. Each instance of an EyeRecord\n"
                         "# component in the experiment will create an instance \n"
                         "# of this class.\n"
                         "class EyeRecordRuntime:\n"
                         "    pass\n")
                buff.writeIndentedLines(code)

    def writeInitCode(self, buff):
        code = ("# (name)s: Create EyeRecordRuntime instance to track data\n"
                "# and have attributes added to it by other parts of the code.\n"
                "%(name)s = EyeRecordRuntime()\n"
                "%(name)s.status=NOT_STARTED\n\n")
        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """
        # create some lists to store recorded values positions and events if we
        # need more than one
        code = "# setup some python lists for storing info about the %(name)s\n" % self.params
        buff.writeIndented(code)
        # a list of vals for each val, rather than a scalar
        if self.params['saveState'].val in ['every frame', 'on click']:
            code = ("%(name)s.time = []\n"
                    "%(name)s.x = []\n"
                    "%(name)s.y = []\n"
                    "%(name)s.pupil = []\n"
                    "%(name)s.status = []\n")
            buff.writeIndentedLines(code % self.params)

        buff.writeIndentedLines("# Start eye tracker recording\n"
                                "# TODO: User should be able to decide if"
                                "recording should start or not.\n")
        buff.writeIndentedLines("iohub_eyetracker.setRecordingState(True)\n")

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("# *%s* updates\n" % self.params['name'])

        # test for whether we're just starting to record
        # writes an if statement to determine whether to draw etc
        self.writeStartTestCode(buff)
        code = ("%(name)s.status = STARTED\n"
                "# clear events, TODO: Make this optional\n"
                "iohub_eyetracker.clearEvents()\n")
        buff.writeIndentedLines(code % self.params)

        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)

            code = ("%(name)s.status = STOPPED\n")
            buff.writeIndentedLines(code % self.params)

            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)

        # if STARTED and not STOPPED!
        code = "if %(name)s.status == STARTED:  # only update if started and not stopped!\n" % self.params
        buff.writeIndented(code)

        buff.setIndentLevel(1, relative=True)  # to get out of the if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        code = ("#%(name)s.x, %(name)s.y = eyetracker.getPosition()\n"
                "#%(name)s.pupil = eyetracker.getPupilSize()\n"
                "pass\n")
        buff.writeIndentedLines(code % self.params)

        # actual each-frame checks
        if self.params['saveState'].val in ['every frame']:
            code = ("#x, y = eyetracker.getPosition()\n"
                    "#%(name)s.x.append(x)\n"
                    "#%(name)s.y.append(y)\n"
                    "#%(name)s.pupil.append(eyetracker.getPupilSize())\n")
            buff.writeIndented(code % self.params)

        # dedent
        # 'if' statement of the time test and button check
        buff.setIndentLevel(-dedentAtEnd, relative=True)

    def writeRoutineEndCode(self, buff):
        # some shortcuts
        name = self.params['name'].val
        # do this because the param itself is not a string!
        store = self.params['saveState'].val
        # check if we're in a loop (so saving is possible)
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = None

        # if store=='final' then update value
        if store == 'final' and currLoop != None:
            code = ("# get info about the %(name)s\n"
                    "# %(name)s.x, %(name)s.y = eyetracker.getPosition()\n"
                    "# x, y = %(name)s.getPos()\n"
                    "# %(name)s.pupil = eyetracker.getPupilSize()\n")
            buff.writeIndentedLines(code % self.params)

        # then push to psychopy data file if store='final','every frame'
        if store != 'never' and currLoop != None:
            buff.writeIndented("# save %(name)s data\n" % self.params)
            for property in ['x', 'y', 'pupil']:
                buff.writeIndented(
                    "# %s.addData('%s.%s', %s.%s)\n" %
                    (currLoop.params['name'], name, property, name, property))

        # make sure eyetracking stops recording (in case it hsn't stopped
        # already)
        buff.writeIndentedLines("# Stop eye tracker recording\n"
                                "# TODO: User should be able to "
                                "decide if recording should stop or not.\n")

        buff.writeIndentedLines("iohub_eyetracker.setRecordingState(False)\n")

    def writeExperimentEndCode(self, buff):
        pass
