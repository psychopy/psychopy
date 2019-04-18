#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from builtins import str
from builtins import object
import os
import re
import wx.__version__
import psychopy
from psychopy import logging
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.tools.versionchooser import versionOptions, availableVersions, _versionFilter
from psychopy.constants import PY3

# for creating html output folders:
import shutil
import hashlib
import zipfile
import ast  # for doing literal eval to convert '["a","b"]' to a list


def readTextFile(relPath):
    fullPath = os.path.join(thisFolder, relPath)
    with open(fullPath, "r") as f:
        txt = f.read()
    return txt


# used when writing scripts and in namespace:
_numpyImports = ['sin', 'cos', 'tan', 'log', 'log10', 'pi', 'average',
                 'sqrt', 'std', 'deg2rad', 'rad2deg', 'linspace', 'asarray']
_numpyRandomImports = ['random', 'randint', 'normal', 'shuffle']

# this is not a standard component - it will appear on toolbar not in
# components panel

# only use _localized values for label values, nothing functional:
_localized = {'expName': _translate("Experiment name"),
              'Show info dlg':  _translate("Show info dialog"),
              'Enable Escape':  _translate("Enable Escape key"),
              'Experiment info':  _translate("Experiment info"),
              'Data filename':  _translate("Data filename"),
              'Full-screen window':  _translate("Full-screen window"),
              'Window size (pixels)':  _translate("Window size (pixels)"),
              'Screen': _translate('Screen'),
              'Monitor':  _translate("Monitor"),
              'color': _translate("Color"),
              'colorSpace':  _translate("Color space"),
              'Units':  _translate("Units"),
              'blendMode':   _translate("Blend mode"),
              'Show mouse':  _translate("Show mouse"),
              'Save log file':  _translate("Save log file"),
              'Save wide csv file':
                  _translate("Save csv file (trial-by-trial)"),
              'Save csv file': _translate("Save csv file (summaries)"),
              'Save excel file':  _translate("Save excel file"),
              'Save psydat file':  _translate("Save psydat file"),
              'logging level': _translate("Logging level"),
              'Use version': _translate("Use PsychoPy version"),
              'Completed URL': _translate("Completed URL"),
              'Incomplete URL': _translate("Incomplete URL"),
              'Output path': _translate("Output path"),
              'JS libs': _translate("JS libs"),
              'Force stereo': _translate("Force stereo"),
              'Export HTML': _translate("Export HTML")}

thisFolder = os.path.split(__file__)[0]
#
#
# # customize the Proj ID Param class to
# class ProjIDParam(Param):
#     @property
#     def allowedVals(self):
#         from psychopy.app.projects import catalog
#         allowed = list(catalog.keys())
#         # always allow the current val!
#         if self.val not in allowed:
#             allowed.append(self.val)
#         # always allow blank (None)
#         if '' not in allowed:
#             allowed.append('')
#         return allowed
#     @allowedVals.setter
#     def allowedVals(self, allowed):
#         pass

class SettingsComponent(object):
    """This component stores general info about how to run the experiment
    """

    def __init__(self, parentName, exp, expName='', fullScr=True,
                 winSize=(1024, 768), screen=1, monitor='testMonitor',
                 showMouse=False, saveLogFile=True, showExpInfo=True,
                 expInfo="{'participant':'', 'session':'001'}",
                 units='height', logging='exp',
                 color='$[0,0,0]', colorSpace='rgb', enableEscape=True,
                 blendMode='avg',
                 saveXLSXFile=False, saveCSVFile=False,
                 saveWideCSVFile=True, savePsydatFile=True,
                 savedDataFolder='',
                 useVersion='',
                 filename=None, exportHTML='on Sync'):
        self.type = 'Settings'
        self.exp = exp  # so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual', 'gui'])
        self.parentName = parentName
        self.url = "http://www.psychopy.org/builder/settings.html"

        # if filename is the default value fetch the builder pref for the
        # folder instead
        if filename is None:
            filename = ("u'xxxx/%s_%s_%s' % (expInfo['participant'], expName,"
                        " expInfo['date'])")
        if filename.startswith("u'xxxx"):
            folder = self.exp.prefsBuilder['savedDataFolder'].strip()
            filename = filename.replace("xxxx", folder)

        # params
        self.params = {}
        self.order = ['expName', 'Show info dlg', 'Experiment info',
                      'Data filename',
                      'Save excel file', 'Save csv file',
                      'Save wide csv file', 'Save psydat file',
                      'Save log file', 'logging level',
                      'Monitor', 'Screen', 'Full-screen window',
                      'Window size (pixels)',
                      'color', 'colorSpace', 'Units', 'HTML path']
        # basic params
        self.params['expName'] = Param(
            expName, valType='str', allowedTypes=[],
            hint=_translate("Name of the entire experiment (taken by default"
                            " from the filename on save)"),
            label=_localized["expName"])
        self.params['Show info dlg'] = Param(
            showExpInfo, valType='bool', allowedTypes=[],
            hint=_translate("Start the experiment with a dialog to set info"
                            " (e.g.participant or condition)"),
            label=_localized["Show info dlg"], categ='Basic')
        self.params['Enable Escape'] = Param(
            enableEscape, valType='bool', allowedTypes=[],
            hint=_translate("Enable the <esc> key, to allow subjects to quit"
                            " / break out of the experiment"),
            label=_localized["Enable Escape"])
        self.params['Experiment info'] = Param(
            expInfo, valType='code', allowedTypes=[],
            hint=_translate("The info to present in a dialog box. Right-click"
                            " to check syntax and preview the dialog box."),
            label=_localized["Experiment info"], categ='Basic')
        self.params['Use version'] = Param(
            useVersion, valType='str',
            # search for options locally only by default, otherwise sluggish
            allowedVals=_versionFilter(versionOptions(), wx.__version__)
                        + ['']
                        + _versionFilter(availableVersions(), wx.__version__),
            hint=_translate("The version of PsychoPy to use when running "
                            "the experiment."),
            label=_localized["Use version"], categ='Basic')
        self.params['Force stereo'] = Param(
            enableEscape, valType='bool', allowedTypes=[],
            hint=_translate("Force audio to stereo (2-channel) output"),
            label=_localized["Force stereo"])

        # screen params
        self.params['Full-screen window'] = Param(
            fullScr, valType='bool', allowedTypes=[],
            hint=_translate("Run the experiment full-screen (recommended)"),
            label=_localized["Full-screen window"], categ='Screen')
        self.params['Window size (pixels)'] = Param(
            winSize, valType='code', allowedTypes=[],
            hint=_translate("Size of window (if not fullscreen)"),
            label=_localized["Window size (pixels)"], categ='Screen')
        self.params['Screen'] = Param(
            screen, valType='num', allowedTypes=[],
            hint=_translate("Which physical screen to run on (1 or 2)"),
            label=_localized["Screen"], categ='Screen')
        self.params['Monitor'] = Param(
            monitor, valType='str', allowedTypes=[],
            hint=_translate("Name of the monitor (from Monitor Center). Right"
                            "-click to go there, then copy & paste a monitor "
                            "name here."),
            label=_localized["Monitor"], categ="Screen")
        self.params['color'] = Param(
            color, valType='str', allowedTypes=[],
            hint=_translate("Color of the screen (e.g. black, $[1.0,1.0,1.0],"
                            " $variable. Right-click to bring up a "
                            "color-picker.)"),
            label=_localized["color"], categ='Screen')
        self.params['colorSpace'] = Param(
            colorSpace, valType='str',
            hint=_translate("Needed if color is defined numerically (see "
                            "PsychoPy documentation on color spaces)"),
            allowedVals=['rgb', 'dkl', 'lms', 'hsv', 'hex'],
            label=_localized["colorSpace"], categ="Screen")
        self.params['Units'] = Param(
            units, valType='str', allowedTypes=[],
            allowedVals=['use prefs', 'deg', 'pix', 'cm', 'norm', 'height',
                         'degFlatPos', 'degFlat'],
            hint=_translate("Units to use for window/stimulus coordinates "
                            "(e.g. cm, pix, deg)"),
            label=_localized["Units"], categ='Screen')
        self.params['blendMode'] = Param(
            blendMode, valType='str',
            allowedTypes=[], allowedVals=['add', 'avg'],
            hint=_translate("Should new stimuli be added or averaged with "
                            "the stimuli that have been drawn already"),
            label=_localized["blendMode"], categ='Screen')
        self.params['Show mouse'] = Param(
            showMouse, valType='bool', allowedTypes=[],
            hint=_translate("Should the mouse be visible on screen?"),
            label=_localized["Show mouse"], categ='Screen')

        # data params
        self.params['Data filename'] = Param(
            filename, valType='code', allowedTypes=[],
            hint=_translate("Code to create your custom file name base. Don"
                            "'t give a file extension - this will be added."),
            label=_localized["Data filename"], categ='Data')
        self.params['Save log file'] = Param(
            saveLogFile, valType='bool', allowedTypes=[],
            hint=_translate("Save a detailed log (more detailed than the "
                            "excel/csv files) of the entire experiment"),
            label=_localized["Save log file"], categ='Data')
        self.params['Save wide csv file'] = Param(
            saveWideCSVFile, valType='bool', allowedTypes=[],
            hint=_translate("Save data from loops in comma-separated-value "
                            "(.csv) format for maximum portability"),
            label=_localized["Save wide csv file"], categ='Data')
        self.params['Save csv file'] = Param(
            saveCSVFile, valType='bool', allowedTypes=[],
            hint=_translate("Save data from loops in comma-separated-value "
                            "(.csv) format for maximum portability"),
            label=_localized["Save csv file"], categ='Data')
        self.params['Save excel file'] = Param(
            saveXLSXFile, valType='bool', allowedTypes=[],
            hint=_translate("Save data from loops in Excel (.xlsx) format"),
            label=_localized["Save excel file"], categ='Data')
        self.params['Save psydat file'] = Param(
            savePsydatFile, valType='bool', allowedVals=[True],
            hint=_translate("Save data from loops in psydat format. This is "
                            "useful for python programmers to generate "
                            "analysis scripts."),
            label=_localized["Save psydat file"], categ='Data')
        self.params['logging level'] = Param(
            logging, valType='code',
            allowedVals=['error', 'warning', 'data', 'exp', 'info', 'debug'],
            hint=_translate("How much output do you want in the log files? "
                            "('error' is fewest messages, 'debug' is most)"),
            label=_localized["logging level"], categ='Data')

        # HTML output params
        # self.params['OSF Project ID'] = ProjIDParam(
        #     '', valType='str', # automatically updates to allow choices
        #     hint=_translate("The ID of this project (e.g. 5bqpc)"),
        #     label="OSF Project ID", categ='Online')
        self.params['HTML path'] = Param(
            'html', valType='str', allowedTypes=[],
            hint=_translate("Place the HTML files will be saved locally "),
            label="Output path", categ='Online')
        self.params['JS libs'] = Param(
            'packaged', valType='str', allowedVals=['packaged'],
            hint=_translate("Should we package a copy of the JS libs or use"
                            "remote copies (http:/www.psychopy.org/js)?"),
            label="JS libs", categ='Online')
        self.params['Completed URL'] = Param(
            '', valType='str',
            hint=_translate("Where should participants be redirected after the experiment on completion\n"
                            " INSERT COMPLETION URL E.G.?"),
            label="Completed URL", categ='Online')
        self.params['Incomplete URL'] = Param(
            '', valType='str',
            hint=_translate("Where participants are redirected if they do not complete the task\n"
                            " INSERT INCOMPLETION URL E.G.?"),
            label="Incomplete URL", categ='Online')


        self.params['exportHTML'] = Param(
            exportHTML, valType='str',
            allowedVals=['on Save', 'on Sync', 'manually'],
            hint=_translate("When to export experiment to the HTML folder."),
            label=_localized["Export HTML"], categ='Online')

    def getInfo(self):
        """Rather than converting the value of params['Experiment Info']
        into a dict from a string (which can lead to errors) use this function
        :return: expInfo as a dict
        """
        
        infoStr = self.params['Experiment info'].val.strip()
        if len(infoStr) == 0:
            return {}
        try:
            infoDict = ast.literal_eval(infoStr)
            # check for strings of lists: "['male','female']"
            for key in infoDict:
                val = infoDict[key]
                if (hasattr(val, 'startswith')
                        and val.startswith('[') and val.endswith(']')):
                    try:
                        infoDict[key] = ast.literal_eval(val)
                    except (ValueError, SyntaxError):
                        logging.warning("Tried and failed to parse {!r}"
                                        "as a list of values."
                                        .format(val))
                elif val in ['True', 'False']:
                    infoDict[key] = ast.literal_eval(val)

        except (ValueError, SyntaxError):
            """under Python3 {'participant':'', 'session':02} raises an error because 
            ints can't have leading zeros. We will check for those and correct them
            tests = ["{'participant':'', 'session':02}",
                    "{'participant':'', 'session':02}",
                    "{'participant':'', 'session': 0043}",
                    "{'participant':'', 'session':02, 'id':009}",
                    ]
                    """

            def entryToString(match):
                entry = match.group(0)
                digits = re.split(r": *", entry)[1]
                return ':{}'.format(repr(digits))

            # 0 or more spaces, 1-5 zeros, 0 or more digits:
            pattern = re.compile(r": *0{1,5}\d*")
            try:
                infoDict = eval(re.sub(pattern, entryToString, infoStr))
            except SyntaxError:  # still a syntax error, possibly caused by user
                msg = ('Builder Expt: syntax error in '
                              '"Experiment info" settings (expected a dict)')
                logging.error(msg)
                raise AttributeError(msg)
        return infoDict

    def getType(self):
        return self.__class__.__name__

    def getShortType(self):
        return self.getType().replace('Component', '')

    def getSaveDataDir(self):
        if 'Saved data folder' in self.params:
            # we have a param for the folder (deprecated since 1.80)
            saveToDir = self.params['Saved data folder'].val.strip()
            if not saveToDir:  # it was blank so try preferences
                saveToDir = self.exp.prefsBuilder['savedDataFolder'].strip()
        else:
            saveToDir = os.path.dirname(self.params['Data filename'].val)
        return saveToDir or u'data'

    def writeUseVersion(self, buff):
        if self.params['Use version'].val:
            code = ('\nimport psychopy\n'
                    'psychopy.useVersion({})\n\n')
            val = repr(self.params['Use version'].val)
            buff.writeIndentedLines(code.format(val))

    def writeInitCode(self, buff, version, localDateTime):

        buff.write(
            '#!/usr/bin/env python\n'
            '# -*- coding: utf-8 -*-\n'
            '"""\nThis experiment was created using PsychoPy3 Experiment '
            'Builder (v%s),\n'
            '    on %s\n' % (version, localDateTime) +
            'If you publish work using this script please cite the PsychoPy '
            'publications:\n'
            '    Peirce, JW (2007) PsychoPy - Psychophysics software in '
            'Python.\n'
            '        Journal of Neuroscience Methods, 162(1-2), 8-13.\n'
            '    Peirce, JW (2009) Generating stimuli for neuroscience using '
            'PsychoPy.\n'
            '        Frontiers in Neuroinformatics, 2:10. doi: 10.3389/'
            'neuro.11.010.2008\n"""\n'
            "\nfrom __future__ import absolute_import, division\n")

        self.writeUseVersion(buff)

        psychopyImports = []
        customImports = []
        for import_ in self.exp.requiredImports:
            if import_.importFrom == 'psychopy':
                psychopyImports.append(import_.importName)
            else:
                customImports.append(import_)

        buff.write(
            "from psychopy import locale_setup, "
            "%s\n" % ', '.join(psychopyImports) +
            "from psychopy.constants import (NOT_STARTED, STARTED, PLAYING,"
            " PAUSED,\n"
            "                                STOPPED, FINISHED, PRESSED, "
            "RELEASED, FOREVER)\n"
            "import numpy as np  # whole numpy lib is available, "
            "prepend 'np.'\n"
            "from numpy import (%s,\n" % ', '.join(_numpyImports[:7]) +
            "                   %s)\n" % ', '.join(_numpyImports[7:]) +
            "from numpy.random import %s\n" % ', '.join(_numpyRandomImports) +
            "import os  # handy system and path functions\n" +
            "import sys  # to get file system encoding\n"
            "\n")

        # Write custom import statements, line by line.
        for import_ in customImports:
            importName = import_.importName
            importFrom = import_.importFrom
            importAs = import_.importAs

            statement = ''
            if importFrom:
                statement += "from %s " % importFrom

            statement += "import %s" % importName

            if importAs:
                statement += " as %s" % importAs

            statement += "\n"
            buff.write(statement)

        buff.write("\n")

        # Write "run once" code.
        if self.exp._runOnce:
            buff.write("\n".join(self.exp._runOnce))
            buff.write("\n\n")

    def prepareResourcesJS(self):
        """Sets up the resources folder and writes the info.php file for PsychoJS
        """

        join = os.path.join

        def copyTreeWithMD5(src, dst):
            """Copies the tree but checks SHA for each file first
            """
            # despite time to check the md5 hashes this func gives speed-up
            # over about 20% over using shutil.rmtree() and copytree()
            for root, subDirs, files in os.walk(src):
                relPath = os.path.relpath(root, src)
                for thisDir in subDirs:
                    if not os.path.isdir(join(root, thisDir)):
                        os.makedirs(join(root, thisDir))
                for thisFile in files:
                    copyFileWithMD5(join(root, thisFile),
                                    join(dst, relPath, thisFile))

        def copyFileWithMD5(src, dst):
            """Copies a file but only if doesn't exist or SHA is diff
            """
            if os.path.isfile(dst):
                with open(dst, 'r') as f:
                    dstMD5 = hashlib.md5(f.read()).hexdigest()
                with open(src, 'r') as f:
                    srcMD5 = hashlib.md5(f.read()).hexdigest()
                if srcMD5 == dstMD5:
                    return  # already matches - do nothing
                # if we got here then the file exists but not the same
                # delete and replace. TODO: In future this should check date
                os.remove(dst)
            # either didn't exist or has been deleted
            folder = os.path.split(dst)[0]
            if not os.path.isdir(folder):
                os.makedirs(folder)
            shutil.copy2(src, dst)

        # write info.php file
        folder = os.path.dirname(self.exp.expPath)
        if not os.path.isdir(folder):
            os.mkdir(folder)
        # get OSF projcet info if there was a project id
        # projLabel = self.params['OSF Project ID'].val
        # these are all blank unless we find a valid proj
        # osfID = osfName = osfToken = ''
        # osfHtmlFolder = ''
        # osfDataFolder = 'data'
        # is email a defined parameter for this version
        if 'email' in self.params:
            email = repr(self.params['email'].val)
        else:
            email = "''"
        # populate resources folder
        resFolder = join(folder, 'resources')
        if not os.path.isdir(resFolder):
            os.mkdir(resFolder)
        resourceFiles = self.exp.getResourceFiles()

        for srcFile in resourceFiles:
            dstAbs = os.path.normpath(join(resFolder, srcFile['rel']))
            dstFolder = os.path.split(dstAbs)[0]
            if not os.path.isdir(dstFolder):
                os.makedirs(dstFolder)
            shutil.copy2(srcFile['abs'], dstAbs)

    def writeInitCodeJS(self, buff, version, localDateTime, modular=True):
        # create resources folder
        self.prepareResourcesJS()
        jsFilename = os.path.basename(os.path.splitext(self.exp.filename)[0])

        # decide if we need anchored useVersion or leave plain
        if self.params['Use version'].val not in ['', 'latest']:
            versionStr = "-{}".format(self.params['Use version'])
        else:
            versionStr = ''

        # html header
        template = readTextFile("JS_htmlHeader.tmpl")
        header = template.format(
            name=jsFilename,
            version=versionStr,
            params=self.params)
        jsFile = self.exp.expPath
        folder = os.path.dirname(jsFile)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(os.path.join(folder, "index.html"), 'wb') as html:
            html.write(header.encode())
        html.close()

        # Write header comment
        starLen = "*"*(len(jsFilename) + 9)
        code = ("/%s \n"
               " * %s Test *\n" 
               " %s/\n\n")
        buff.writeIndentedLines(code % (starLen, jsFilename.title(), starLen))

        # Write imports if modular
        if modular:
            code = ("import {{ PsychoJS }} from 'https://pavlovia.org/lib/core{version}.js';\n"
                    "import * as core from 'https://pavlovia.org/lib/core{version}.js';\n"
                    "import {{ TrialHandler }} from 'https://pavlovia.org/lib/data{version}.js';\n"
                    "import {{ Scheduler }} from 'https://pavlovia.org/lib/util{version}.js';\n"
                    "import * as util from 'https://pavlovia.org/lib/util{version}.js';\n"
                    "import * as visual from 'https://pavlovia.org/lib/visual{version}.js';\n"
                    "import {{ Sound }} from 'https://pavlovia.org/lib/sound{version}.js';\n"
                    "\n").format(version=versionStr)
            buff.writeIndentedLines(code)

        # Write window code
        self.writeWindowCodeJS(buff)
        code = ("\n// store info about the experiment session:\n"
                "let expName = '%s';  // from the Builder filename that created this script\n"
                "let expInfo = %s;\n"
                "\n" % (jsFilename, self.getInfo()))
        buff.writeIndentedLines(code)

    def writeExpSetupCodeJS(self, buff, version):

        # write the code to set up experiment
        buff.setIndentLevel(0, relative=False)
        template = readTextFile("JS_setupExp.tmpl")
        setRedirectURL = ''
        if len(self.params['Completed URL'].val) or len(self.params['Incomplete URL'].val):
            setRedirectURL = ("psychoJS.setRedirectUrls({completedURL}, {incompleteURL});\n"
                              .format(completedURL=self.params['Completed URL'],
                                      incompleteURL=self.params['Incomplete URL']))
        # check where to save data variables
        # if self.params['OSF Project ID'].val:
        #     saveType = "OSF_VIA_EXPERIMENT_SERVER"
        #     projID = "'{}'".format(self.params['OSF Project ID'].val)
        # else:
        #     saveType = "EXPERIMENT_SERVER"
        #     projID = 'undefined'
        code = template.format(
                        params=self.params,
                        name=self.params['expName'].val,
                        loggingLevel=self.params['logging level'].val.upper(),
                        setRedirectURL=setRedirectURL,
                        version=version,
                        )
        buff.writeIndentedLines(code)

    def writeStartCode(self, buff, version):

        if not PY3:
            decodingInfo = ".decode(sys.getfilesystemencoding())"
        else:
            decodingInfo = ""
        code = ("# Ensure that relative paths start from the same directory "
                "as this script\n"
                "_thisDir = os.path.dirname(os.path.abspath(__file__))"
                "{decoding}\n"
                "os.chdir(_thisDir)\n\n"
                "# Store info about the experiment session\n"
                "psychopyVersion = '{version}'\n".format(decoding=decodingInfo,
                                                         version=version))
        buff.writeIndentedLines(code)

        if self.params['expName'].val in [None, '']:
            buff.writeIndented("expName = 'untitled.py'\n")
        else:
            code = ("expName = %s  # from the Builder filename that created"
                    " this script\n")
            buff.writeIndented(code % self.params['expName'])

        if PY3:  # in Py3 dicts are chrono-sorted
            sorting = "False"
        else:  # in Py2, with no natural order, at least be alphabetical
            sorting = "True"
        expInfoDict = self.getInfo()
        buff.writeIndented("expInfo = %s\n" % repr(expInfoDict))
        if self.params['Show info dlg'].val:
            buff.writeIndentedLines(
                "dlg = gui.DlgFromDict(dictionary=expInfo, "
                "sortKeys={}, title=expName)\n"
                "if dlg.OK == False:\n"
                "    core.quit()  # user pressed cancel\n"
                .format(sorting)
            )
        buff.writeIndentedLines(
            "expInfo['date'] = data.getDateStr()  # add a simple timestamp\n"
            "expInfo['expName'] = expName\n"
            "expInfo['psychopyVersion'] = psychopyVersion")
        level = self.params['logging level'].val.upper()

        saveToDir = self.getSaveDataDir()
        buff.writeIndentedLines("\n# Data file name stem = absolute path +"
                                " name; later add .psyexp, .csv, .log, etc\n")
        # deprecated code: before v1.80.00 we had 'Saved data folder' param
        # fairly fixed filename
        if 'Saved data folder' in self.params:
            participantField = ''
            for field in ('participant', 'Participant', 'Subject', 'Observer'):
                if field in expInfoDict:
                    participantField = field
                    self.params['Data filename'].val = (
                        repr(saveToDir) + " + os.sep + '%s_%s' % (expInfo['" +
                        field + "'], expInfo['date'])")
                    break
            if not participantField:
                # no participant-type field, so skip that part of filename
                self.params['Data filename'].val = repr(
                    saveToDir) + " + os.path.sep + expInfo['date']"
            # so that we don't overwrite users changes doing this again
            del self.params['Saved data folder']

        # now write that data file name to the script
        if not self.params['Data filename'].val:  # i.e., the user deleted it
            self.params['Data filename'].val = (
                repr(saveToDir) +
                " + os.sep + u'psychopy_data_' + data.getDateStr()")
        # detect if user wanted an absolute path -- else make absolute:
        filename = self.params['Data filename'].val.lstrip('"\'')
        # (filename.startswith('/') or filename[1] == ':'):
        if filename == os.path.abspath(filename):
            buff.writeIndented("filename = %s\n" %
                               self.params['Data filename'])
        else:
            buff.writeIndented("filename = _thisDir + os.sep + %s\n" %
                               self.params['Data filename'])

        # set up the ExperimentHandler
        code = ("\n# An ExperimentHandler isn't essential but helps with "
                "data saving\n"
                "thisExp = data.ExperimentHandler(name=expName, version='',\n"
                "    extraInfo=expInfo, runtimeInfo=None,\n"
                "    originPath=%s,\n")
        buff.writeIndentedLines(code % repr(self.exp.expPath))

        code = ("    savePickle=%(Save psydat file)s, saveWideText=%(Save "
                "wide csv file)s,\n    dataFileName=filename)\n")
        buff.writeIndentedLines(code % self.params)

        if self.params['Save log file'].val:
            code = ("# save a log file for detail verbose info\nlogFile = "
                    "logging.LogFile(filename+'.log', level=logging.%s)\n")
            buff.writeIndentedLines(code % level)
        buff.writeIndented("logging.console.setLevel(logging.WARNING)  "
                           "# this outputs to the screen, not a file\n")

        if self.exp.settings.params['Enable Escape'].val:
            buff.writeIndentedLines("\nendExpNow = False  # flag for 'escape'"
                                    " or other condition => quit the exp\n")

    def writeWindowCode(self, buff):
        """Setup the window code.
        """
        buff.writeIndentedLines("\n# Setup the Window\n")
        # get parameters for the Window
        fullScr = self.params['Full-screen window'].val
        # if fullscreen then hide the mouse, unless its requested explicitly
        allowGUI = (not bool(fullScr)) or bool(self.params['Show mouse'].val)
        allowStencil = False
        # NB routines is a dict:
        for thisRoutine in list(self.exp.routines.values()):
            # a single routine is a list of components:
            for thisComp in thisRoutine:
                if thisComp.type == 'Aperture':
                    allowStencil = True
                if thisComp.type == 'RatingScale':
                    allowGUI = True  # to have a mouse

        requestedScreenNumber = int(self.params['Screen'].val)
        nScreens = 10
        # try:
        #     nScreens = wx.Display.GetCount()
        # except Exception:
        #     # will fail if application hasn't been created (e.g. in test
        #     # environments)
        #     nScreens = 10
        if requestedScreenNumber > nScreens:
            logging.warn("Requested screen can't be found. Writing script "
                         "using first available screen.")
            screenNumber = 0
        else:
            # computer has 1 as first screen
            screenNumber = requestedScreenNumber - 1

        size = self.params['Window size (pixels)']
        winType = self.exp.prefsGeneral['winType']

        code = ("win = visual.Window(\n    size=%s, fullscr=%s, screen=%s, "
                "\n    winType='%s', allowGUI=%s, allowStencil=%s,\n")
        vals = (size, fullScr, screenNumber, winType, allowGUI, allowStencil)
        buff.writeIndented(code % vals)

        code = ("    monitor=%(Monitor)s, color=%(color)s, "
                "colorSpace=%(colorSpace)s,\n")
        if self.params['blendMode'].val:
            code += "    blendMode=%(blendMode)s, useFBO=True, \n"

        if self.params['Units'].val != 'use prefs':
            code += "    units=%(Units)s"
        code = code.rstrip(', \n') + ')\n'
        buff.writeIndentedLines(code % self.params)

        # Import here to avoid circular dependency!
        from psychopy.experiment._experiment import RequiredImport
        microphoneImport = RequiredImport(importName='microphone',
                                          importFrom='psychopy',
                                          importAs='')
        if microphoneImport in self.exp.requiredImports:  # need a pyo Server
            buff.writeIndentedLines("\n# Enable sound input/output:\n"
                                    "microphone.switchOn()\n")

        code = ("# store frame rate of monitor if we can measure it\n"
                "expInfo['frameRate'] = win.getActualFrameRate()\n"
                "if expInfo['frameRate'] != None:\n"
                "    frameDur = 1.0 / round(expInfo['frameRate'])\n"
                "else:\n"
                "    frameDur = 1.0 / 60.0  # could not measure, so guess\n")
        buff.writeIndentedLines(code)

    def writeWindowCodeJS(self, buff):
        """Setup the JS window code.
        """
        # Replace instances of 'use prefs'
        units = self.params['Units'].val
        if units == 'use prefs':
            units = 'height'

        code = ("// init psychoJS:\n"
                "var psychoJS = new PsychoJS({{\n"
                "  debug: true\n"
                "}});\n\n"
                "// open window:\n"
                "psychoJS.openWindow({{\n"
                "  fullscr: {fullScr},\n"
                "  color: new util.Color({params[color]}),\n"
                "  units: '{units}'\n"
                "}});\n").format(fullScr=str(self.params['Full-screen window']).lower(),
                                 params=self.params,
                                 units=units)
        buff.writeIndentedLines(code)

    def writeEndCode(self, buff):
        """Write code for end of experiment (e.g. close log file).
        """
        code = ('\n# Flip one final time so any remaining win.callOnFlip() \n'
                '# and win.timeOnFlip() tasks get executed before quitting\n'
                'win.flip()\n\n')
        buff.writeIndentedLines(code)

        buff.writeIndented("# these shouldn't be strictly necessary "
                           "(should auto-save)\n")
        if self.params['Save wide csv file'].val:
            buff.writeIndented("thisExp.saveAsWideText(filename+'.csv')\n")
        if self.params['Save psydat file'].val:
            buff.writeIndented("thisExp.saveAsPickle(filename)\n")
        if self.params['Save log file'].val:
            buff.writeIndented("logging.flush()\n")
        code = ("# make sure everything is closed down\n"
                "thisExp.abort()  # or data files will save again on exit\n"
                "win.close()\n"
                "core.quit()\n")
        buff.writeIndentedLines(code)

    def writeEndCodeJS(self, buff):

        endLoopInteration = ("\nfunction endLoopIteration(thisScheduler, thisTrial) {\n"
                    "  // ------Prepare for next entry------\n"
                    "  return function () {\n"
                    "    // ------Check if user ended loop early------\n"
                    "    if (currentLoop.finished) {\n"
                    "      thisScheduler.stop();\n"
                    "    } else if (typeof thisTrial === 'undefined' || !('isTrials' in thisTrial) || thisTrial.isTrials) {\n"
                    "      psychoJS.experiment.nextEntry();\n"
                    "    }\n"
                    "  return Scheduler.Event.NEXT;\n"
                    "  };\n"
                    "}\n")
        buff.writeIndentedLines(endLoopInteration)

        recordLoopIterationFunc = ("\nfunction importConditions(loop) {\n"
                    "  const trialIndex = loop.getTrialIndex();\n"
                    "  return function () {\n"
                    "    loop.setTrialIndex(trialIndex);\n"
                    "    psychoJS.importAttributes(loop.getCurrentTrial());\n"
                    "    return Scheduler.Event.NEXT;\n"
                    "    };\n"
                    "}\n")
        buff.writeIndentedLines(recordLoopIterationFunc)
        quitFunc = ("\nfunction quitPsychoJS(message, isCompleted) {\n"
                    "  psychoJS.window.close();\n"
                    "  psychoJS.quit({message: message, isCompleted: isCompleted});\n\n"
                    "  return Scheduler.Event.QUIT;\n"
                    "}")
        buff.writeIndentedLines(quitFunc)
        buff.setIndentLevel(-1)
