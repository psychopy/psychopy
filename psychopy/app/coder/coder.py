# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, time, types, re
import wx, wx.stc, wx.aui, wx.richtext
import keyword, os, sys, string, StringIO, glob, platform, io
import threading, traceback, bdb, cPickle
import psychoParser
import introspect, py_compile
from psychopy.app import stdOutRich, dialogs
from psychopy import logging
from wx.html import HtmlEasyPrinting

#advanced prefs (not set in prefs files)
prefTestSubset = ""
analysisLevel=1
analyseAuto=True
runScripts='process'

try:#needed for wx.py shell
    import code
    haveCode=True
except:
    haveCode = False

_localized = {'basic': _translate('basic'), 'input': _translate('input'), 'stimuli': _translate('stimuli'),
              'experiment control': _translate('exp control'),
              'iohub': 'ioHub', # no translation
              'hardware': _translate('hardware'), 'timing': _translate('timing'), 'misc': _translate('misc')}

def toPickle(filename, data):
    """save data (of any sort) as a pickle file

    simple wrapper of the cPickle module in core python
    """
    f = open(filename, 'w')
    cPickle.dump(data,f)
    f.close()

def fromPickle(filename):
    """load data (of any sort) from a pickle file

    simple wrapper of the cPickle module in core python
    """
    f = open(filename)
    contents = cPickle.load(f)
    f.close()
    return contents

class Printer(HtmlEasyPrinting):
    """bare-bones printing, no control over anything

    from http://wiki.wxpython.org/Printing
    """
    def __init__(self):
        HtmlEasyPrinting.__init__(self)

    def GetHtmlText(self, text):
        "Simple conversion of text."

        text = text.replace('&', '&amp;')
        text = text.replace('<P>', '&#60;P&#62;')
        text = text.replace('<BR>', '&#60;BR&#62;')
        text = text.replace('<HR>', '&#60;HR&#62;')
        text = text.replace('<p>', '&#60;p&#62;')
        text = text.replace('<br>', '&#60;br&#62;')
        text = text.replace('<hr>', '&#60;hr&#62;')
        text = text.replace('\n\n', '<P>')
        text = text.replace('\t', '    ')  # tabs -> 4 spaces
        text = text.replace(' ', '&nbsp;')  # preserve indentation
        html_text = text.replace('\n', '<BR>')
        return html_text

    def Print(self, text, doc_name):
        self.SetHeader(doc_name)
        self.PrintText('<HR>' + self.GetHtmlText(text), doc_name)

class ScriptThread(threading.Thread):
    """A subclass of threading.Thread, with a kill()
    method."""
    def __init__(self, target, gui):
        threading.Thread.__init__(self, target=target)
        self.killed = False
        self.gui=gui

    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        self.run = self.__run      # Force the Thread toinstall our trace.
        threading.Thread.start(self)

    def __run(self):
        """Hacked run function, which installs the
        trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup
        #we're done - send the App a message
        self.gui.onProcessEnded(event=None)

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True

class PsychoDebugger(bdb.Bdb):
    #this is based on effbot:
    #http://effbot.org/librarybook/bdb.htm
    def __init__(self):
        bdb.Bdb.__init__(self)
        self.starting = True
    def user_call(self, frame, args):
        name = frame.f_code.co_name or "<unknown>"
        #print "call", name, args
        self.set_continue() # continue

    def user_line(self, frame):
        if self.starting:
            self.starting = False
            self.set_trace() # start tracing
        else:
            # arrived at breakpoint
            name = frame.f_code.co_name or "<unknown>"
            filename = self.canonic(frame.f_code.co_filename)
            print "break at", filename, frame.f_lineno, "in", name
        self.set_continue() # continue to next breakpoint

    def user_return(self, frame, value):
        name = frame.f_code.co_name or "<unknown>"
        print "return from", name, value
        print "returnCont..."
        self.set_continue() # continue

    def user_exception(self, frame, exception):
        name = frame.f_code.co_name or "<unknown>"
        print "exception in", name, exception
        print "excCont..."
        self.set_continue() # continue
    def quit(self):
        self._user_requested_quit = 1
        self.set_quit()
        return 1

class UnitTestFrame(wx.Frame):
    class _unitTestOutRich(stdOutRich.StdOutRich):
        """richTextCtrl window for unit test output"""
        def __init__(self, parent, style, size=None, font=None, fontSize=None):
            stdOutRich.StdOutRich.__init__(self, parent=parent, style=style, size=size)
            self.bad = [150,0,0]
            self.good = [0,150,0]
            self.skip = [170,170,170]
            self.png = []
        def write(self,inStr):
            self.MoveEnd()#always 'append' text rather than 'writing' it
            for thisLine in inStr.splitlines(True):
                if thisLine.startswith('OK'):
                    self.BeginBold()
                    self.BeginTextColour(self.good)
                    self.WriteText("OK")
                    self.EndTextColour()
                    self.EndBold()
                    self.WriteText(thisLine[2:]) # for OK (SKIP=xx)
                    self.parent.status = 1
                elif thisLine.startswith('#####'):
                    self.BeginBold()
                    self.WriteText(thisLine)
                    self.EndBold()
                elif thisLine.find('FAIL') > -1 or thisLine.find('ERROR')>-1:
                    self.BeginTextColour(self.bad)
                    self.WriteText(thisLine)
                    self.EndTextColour()
                    self.parent.status = -1
                elif thisLine.find('SKIP')>-1:
                    self.BeginTextColour(self.skip)
                    self.WriteText(thisLine.strip())
                    # show the new image, double size for easier viewing:
                    if thisLine.strip().endswith('.png'):
                        newImg = thisLine.split()[-1]
                        img = os.path.join(self.parent.paths['tests'], 'data', newImg)
                        self.png.append(wx.Image(img, wx.BITMAP_TYPE_ANY))
                        self.MoveEnd()
                        self.WriteImage(self.png[-1])
                    self.MoveEnd()
                    self.WriteText('\n')
                    self.EndTextColour()
                else:#line to write as simple text
                    self.WriteText(thisLine)
                if thisLine.find('Saved copy of actual frame')>-1:
                    # show the new images, double size for easier viewing:
                    newImg = [f for f in thisLine.split() if f.find('_local.png')>-1]
                    newFile = newImg[0]
                    origFile = newFile.replace('_local.png', '.png')
                    img = os.path.join(self.parent.paths['tests'], origFile)
                    self.png.append(wx.Image(img, wx.BITMAP_TYPE_ANY))
                    self.MoveEnd()
                    self.WriteImage(self.png[-1])
                    self.MoveEnd()
                    self.WriteText('= '+origFile+';   ')
                    img = os.path.join(self.parent.paths['tests'], newFile)
                    self.png.append(wx.Image(img, wx.BITMAP_TYPE_ANY))
                    self.MoveEnd()
                    self.WriteImage(self.png[-1])
                    self.MoveEnd()
                    self.WriteText('= '+newFile+'; ')

            self.MoveEnd()#go to end of stdout so user can see updated text
            self.ShowPosition(self.GetLastPosition() )
    def __init__(self, parent=None, ID=-1, title=_translate('PsychoPy unit testing'), files=[], app=None):
        self.app = app
        self.frameType='unittest'
        self.prefs = self.app.prefs
        self.paths = self.app.prefs.paths
        #deduce the script for running the tests
        try:
            import pytest
            havePytest=True
        except:
            havePytest=False
        if havePytest:
            self.runpyPath = os.path.join(self.prefs.paths['tests'], 'run.py')
        else:
            self.runpyPath = os.path.join(self.prefs.paths['tests'], 'runPytest.py')#run the standalone version
        if sys.platform != 'win32':
            self.runpyPath = self.runpyPath.replace(' ','\ ')
        #setup the frame
        self.IDs = self.app.IDs
        wx.Frame.__init__(self, parent, ID, title, pos=(450,45)) # to right, so Cancel button is clickable during a long test
        self.scriptProcess=None
        self.runAllText = 'all tests'
        border = 10
        self.status = 0 # outcome of the last test run: -1 fail, 0 not run, +1 ok

        #create menu items
        menuBar = wx.MenuBar()
        self.menuTests=wx.Menu()
        menuBar.Append(self.menuTests, _translate('&Tests'))
        self.menuTests.Append(wx.ID_APPLY,   _translate("&Run tests\t%s") % self.app.keys['runScript'])
        wx.EVT_MENU(self, wx.ID_APPLY,  self.onRunTests)
        self.menuTests.Append(self.IDs.stopFile, _translate("&Cancel running test\t%s") %
                              self.app.keys['stopScript'], _translate("Quit a test in progress"))
        wx.EVT_MENU(self, self.IDs.stopFile,  self.onCancelTests)
        self.menuTests.AppendSeparator()
        self.menuTests.Append(wx.ID_CLOSE,   _translate("&Close tests panel\t%s") % self.app.keys['close'])
        wx.EVT_MENU(self, wx.ID_CLOSE,  self.onCloseTests)
        self.menuTests.Append(self.IDs.openCoderView, _translate("Go to &Coder view\t%s") %
                              self.app.keys['switchToCoder'], _translate("Go to the Coder view"))
        wx.EVT_MENU(self, self.IDs.openCoderView,  self.app.showCoder)
        #-------------quit
        self.menuTests.AppendSeparator()
        self.menuTests.Append(wx.ID_EXIT, _translate("&Quit\t%s") % self.app.keys['quit'], _translate("Terminate PsychoPy"))
        wx.EVT_MENU(self, wx.ID_EXIT, self.app.quit)
        item = self.menuTests.Append(wx.ID_PREFERENCES, text = _translate("&Preferences"))
        self.Bind(wx.EVT_MENU, self.app.showPrefs, item)
        self.SetMenuBar(menuBar)

        #create controls
        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.outputWindow=self._unitTestOutRich(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.EXPAND|wx.GROW,
            size=wx.Size(750,500), font=self.prefs.coder['outputFont'],
            fontSize=self.prefs.coder['outputFontSize'])

        knownTests = glob.glob(os.path.join(self.paths['tests'], 'test*'))
        knownTestList = [t.split(os.sep)[-1] for t in knownTests if t.endswith('.py') or os.path.isdir(t)]
        self.knownTestList = [self.runAllText] + knownTestList
        self.testSelect = wx.Choice(parent=self, id=-1, pos=(border,border), choices=self.knownTestList)
        self.testSelect.SetToolTip(wx.ToolTip(_translate("Select the test(s) to run, from:\npsychopy/tests/test*")))
        prefTestSubset = self.prefs.appData['testSubset']
        # preselect the testGroup in the drop-down menu for display:
        if prefTestSubset in self.knownTestList:
            self.testSelect.SetStringSelection(prefTestSubset)

        self.btnRun = wx.Button(parent=self,label=_translate("Run tests"))
        self.btnRun.Bind(wx.EVT_BUTTON, self.onRunTests)
        self.btnCancel = wx.Button(parent=self,label=_translate("Cancel"))
        self.btnCancel.Bind(wx.EVT_BUTTON, self.onCancelTests)
        self.btnCancel.Disable()
        self.Bind(wx.EVT_END_PROCESS, self.onTestsEnded)

        self.chkCoverage=wx.CheckBox(parent=self,label=_translate("Coverage Report"))
        self.chkCoverage.SetToolTip(wx.ToolTip(_translate("Include coverage report (requires coverage module)")))
        self.chkCoverage.Disable()
        self.chkAllStdOut=wx.CheckBox(parent=self,label=_translate("ALL stdout"))
        self.chkAllStdOut.SetToolTip(wx.ToolTip(_translate("Report all printed output & show any new rms-test images")))
        self.chkAllStdOut.Disable()
        wx.EVT_IDLE(self, self.onIdle)
        self.SetDefaultItem(self.btnRun)

        #arrange controls
        buttonsSizer.Add(self.chkCoverage, 0, wx.LEFT|wx.RIGHT|wx.TOP, border=border)
        buttonsSizer.Add(self.chkAllStdOut, 0, wx.LEFT|wx.RIGHT|wx.TOP, border=border)
        buttonsSizer.Add(self.btnRun, 0, wx.LEFT|wx.RIGHT|wx.TOP, border=border)
        buttonsSizer.Add(self.btnCancel, 0, wx.LEFT|wx.RIGHT|wx.TOP, border=border)
        self.sizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.sizer.Add(buttonsSizer, 0, wx.ALIGN_RIGHT)
        self.sizer.Add(self.outputWindow, 0, wx.ALL|wx.EXPAND|wx.GROW, border=border)
        self.SetSizerAndFit(self.sizer)
        self.Show()

    def onRunTests(self, event=None):
        """Run the unit tests
        """
        self.status = 0

        #create process
        self.scriptProcess=wx.Process(self) #self is the parent (which will receive an event when the process ends)
        self.scriptProcess.Redirect()#catch the stdout/stdin
        #include coverage report?
        if self.chkCoverage.GetValue(): coverage=' cover'
        else: coverage=''
        #print ALL output?
        if self.chkAllStdOut.GetValue(): allStdout=' -s'
        else: allStdout=''
        #what subset of tests? (all tests == '')
        tselect = self.knownTestList[self.testSelect.GetCurrentSelection()]
        if tselect == self.runAllText: tselect = ''
        testSubset = tselect
        #self.prefs.appData['testSubset'] = tselect # in onIdle

        # launch the tests using wx.Execute():
        self.btnRun.Disable()
        self.btnCancel.Enable()
        if sys.platform=='win32':
            testSubset = ' '+testSubset
            command = '"%s" -u "%s" %s%s%s' %(sys.executable, self.runpyPath,
                coverage, allStdout, testSubset)# the quotes allow file paths with spaces
            print command
            self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC, self.scriptProcess)
            #self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC| wx.EXEC_NOHIDE, self.scriptProcess)
        else:
            testSubset = ' '+testSubset.replace(' ','\ ')
            command = '%s -u %s%s%s%s' %(sys.executable, self.runpyPath,
                coverage, allStdout, testSubset)# the quotes would break a unix system command
            self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC| wx.EXEC_MAKE_GROUP_LEADER, self.scriptProcess)
        msg = "\n##### Testing: %s%s%s%s   #####\n\n" % (self.runpyPath, coverage, allStdout, testSubset)
        self.outputWindow.write(msg)
        if self.app.prefs.general['units'] != 'norm' and testSubset.find('testVisual') > -1:
            self.outputWindow.write("Note: default window units = '%s' (in prefs); for visual tests 'norm' is recommended.\n\n" % self.app.prefs.general['units'])

    def onCancelTests(self, event=None):
        if self.scriptProcess != None:
            self.scriptProcess.Kill(self.scriptProcessID, wx.SIGTERM, wx.SIGKILL)
        self.scriptProcess = None
        self.scriptProcessID = None
        self.outputWindow.write("\n --->> cancelled <<---\n\n")
        self.status = 0
        self.onTestsEnded()
    def onIdle(self, event=None):
        # auto-save last selected subset:
        self.prefs.appData['testSubset'] = self.knownTestList[self.testSelect.GetCurrentSelection()]
        if self.scriptProcess!=None:
            if self.scriptProcess.IsInputAvailable():
                stream = self.scriptProcess.GetInputStream()
                text = stream.read()
                self.outputWindow.write(text)
            if self.scriptProcess.IsErrorAvailable():
                stream = self.scriptProcess.GetErrorStream()
                text = stream.read()
                self.outputWindow.write(text)
    def onTestsEnded(self, event=None):
        self.onIdle()#so that any final stdout/err gets written
        self.outputWindow.flush()
        self.btnRun.Enable()
        self.btnCancel.Disable()
    def onURL(self, evt):
        """decompose the URL of a file and line number"""
        # "C:\\Program Files\\wxPython2.8 Docs and Demos\\samples\\hangman\\hangman.py", line 21,
        tmpFilename, tmpLineNumber = evt.GetString().rsplit('", line ',1)
        filename = tmpFilename.split('File "',1)[1]
        lineNumber = int(tmpLineNumber.split(',')[0])
        self.app.coder.gotoLine(filename,lineNumber)
    def onCloseTests(self, evt):
        self.Destroy()

class FileDropTarget(wx.FileDropTarget):
    """On Mac simply setting a handler for the EVT_DROP_FILES isn't enough.
    Need this too.
    """
    def __init__(self, coder):
        wx.FileDropTarget.__init__(self)
        self.coder = coder
    def OnDropFiles(self, x, y, filenames):
        for filename in filenames:
            if os.path.isfile(filename):
                if filename.lower().endswith('.psyexp'):
                    self.coder.app.newBuilderFrame(fileName=filename)
                else:
                    self.coder.setCurrentDoc(filename)

class CodeEditor(wx.stc.StyledTextCtrl):
    # this comes mostly from the wxPython demo styledTextCtrl 2
    def __init__(self, parent, ID, frame,
                 pos=wx.DefaultPosition, size=wx.Size(100,100),#set the viewer to be small, then it will increase with wx.aui control
                 style=0):
        wx.stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)
        #JWP additions
        self.notebook=parent
        self.coder = frame
        self.UNSAVED=False
        self.filename=""
        self.fileModTime=None # for checking if the file was modified outside of CodeEditor
        self.AUTOCOMPLETE = True
        self.autoCompleteDict={}
        #self.analyseScript()  #no - analyse after loading so that window doesn't pause strangely
        self.locals = None #this will contain the local environment of the script
        self.prevWord=None
        #remove some annoying stc key commands
        self.CmdKeyClear(ord('['), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord(']'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('/'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('/'), wx.stc.STC_SCMOD_CTRL|wx.stc.STC_SCMOD_SHIFT)

        self.SetLexer(wx.stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist))

        self.SetProperty("fold", "1")
        self.SetProperty("tab.timmy.whinge.level", "4")#4 means 'tabs are bad'; 1 means 'flag inconsistency'
        self.SetMargins(0,0)
        self.SetUseTabs(False)
        self.SetTabWidth(4)
        self.SetIndent(4)
        self.SetViewWhiteSpace(self.coder.appData['showWhitespace'])
        #self.SetBufferedDraw(False)
        self.SetViewEOL(self.coder.appData['showEOLs'])
        self.SetEOLMode(wx.stc.STC_EOL_LF)
        self.SetUseAntiAliasing(True)
        #self.SetUseHorizontalScrollBar(True)
        #self.SetUseVerticalScrollBar(True)

        #self.SetEdgeMode(wx.stc.STC_EDGE_BACKGROUND)
        #self.SetEdgeMode(wx.stc.STC_EDGE_LINE)
        #self.SetEdgeColumn(78)

        # Setup a margin to hold fold markers
        self.SetMarginType(2, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, wx.stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        #
        self.SetIndentationGuides(self.coder.appData['showIndentGuides'])

        # Like a flattened tree control using square headers
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPEN,    wx.stc.STC_MARK_BOXMINUS,          "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDER,        wx.stc.STC_MARK_BOXPLUS,           "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERSUB,     wx.stc.STC_MARK_VLINE,             "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERTAIL,    wx.stc.STC_MARK_LCORNER,           "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEREND,     wx.stc.STC_MARK_BOXPLUSCONNECTED,  "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_TCORNER,           "white", "#808080")

        self.Bind(wx.EVT_DROP_FILES, self.coder.filesDropped)
        self.Bind(wx.stc.EVT_STC_MODIFIED, self.onModified)
        #self.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)

        self.setFonts()
        self.SetDropTarget(FileDropTarget(coder = self.coder))

    def setFonts(self):

        """Make some styles,  The lexer defines what each style is used for, we
        just have to define what each style looks like.  This set is adapted from
        Scintilla sample property files."""

        if wx.Platform == '__WXMSW__':
            faces = { 'size' : 10}
        elif wx.Platform == '__WXMAC__':
            faces = { 'size' : 14}
        else:
            faces = { 'size' : 12}
        if self.coder.prefs['codeFontSize']:
            faces['size'] = int(self.coder.prefs['codeFontSize'])
        faces['small']=faces['size']-2
        # Global default styles for all languages
        faces['code'] = self.coder.prefs['codeFont']#,'Arial']#use arial as backup
        faces['comment'] = self.coder.prefs['commentFont']#,'Arial']#use arial as backup
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:%(code)s,size:%(size)d" % faces)
        self.StyleClearAll()  # Reset all to be like the default

        # Global default styles for all languages
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:%(code)s,size:%(size)d" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,  "back:#C0C0C0,face:%(code)s,size:%(small)d" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_CONTROLCHAR, "face:%(comment)s" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT,  "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD,    "fore:#000000,back:#FF0000,bold")

        # Python styles
        # Default
        self.StyleSetSpec(wx.stc.STC_P_DEFAULT, "fore:#000000,face:%(code)s,size:%(size)d" % faces)
        # Comments
        self.StyleSetSpec(wx.stc.STC_P_COMMENTLINE, "fore:#007F00,face:%(comment)s,size:%(size)d" % faces)
        # Number
        self.StyleSetSpec(wx.stc.STC_P_NUMBER, "fore:#007F7F,size:%(size)d" % faces)
        # String
        self.StyleSetSpec(wx.stc.STC_P_STRING, "fore:#7F007F,face:%(code)s,size:%(size)d" % faces)
        # Single quoted string
        self.StyleSetSpec(wx.stc.STC_P_CHARACTER, "fore:#7F007F,face:%(code)s,size:%(size)d" % faces)
        # Keyword
        self.StyleSetSpec(wx.stc.STC_P_WORD, "fore:#00007F,bold,size:%(size)d" % faces)
        # Triple quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLE, "fore:#7F0000,size:%(size)d" % faces)
        # Triple double quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLEDOUBLE, "fore:#7F0000,size:%(size)d" % faces)
        # Class name definition
        self.StyleSetSpec(wx.stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:%(size)d" % faces)
        # Function or method name definition
        self.StyleSetSpec(wx.stc.STC_P_DEFNAME, "fore:#007F7F,bold,size:%(size)d" % faces)
        # Operators
        self.StyleSetSpec(wx.stc.STC_P_OPERATOR, "bold,size:%(size)d" % faces)
        # Identifiers
        self.StyleSetSpec(wx.stc.STC_P_IDENTIFIER, "fore:#000000,face:%(code)s,size:%(size)d" % faces)
        # Comment-blocks
        self.StyleSetSpec(wx.stc.STC_P_COMMENTBLOCK, "fore:#7F7F7F,size:%(size)d" % faces)
        # End of line where string is not closed
        self.StyleSetSpec(wx.stc.STC_P_STRINGEOL, "fore:#000000,face:%(code)s,back:#E0C0E0,eol,size:%(size)d" % faces)

        self.SetCaretForeground("BLUE")

    def OnKeyPressed(self, event):
        #various stuff to handle code completion and tooltips
        #enable in the _-init__
        if self.CallTipActive():
            self.CallTipCancel()
        keyCode = event.GetKeyCode()

        #handle some special keys
        if keyCode== ord('[') and (wx.MOD_CONTROL == event.GetModifiers()):
            self.indentSelection(-4)
            #if there are no characters on the line then also move caret to end of indentation
            txt, charPos = self.GetCurLine()
            if charPos==0: self.VCHome()#if caret is at start of line then move to start of text instead
        if keyCode== ord(']') and (wx.MOD_CONTROL == event.GetModifiers()):
            self.indentSelection(4)
            #if there are no characters on the line then also move caret to end of indentation
            txt, charPos = self.GetCurLine()
            if charPos==0: self.VCHome()#if caret is at start of line then move to start of text instead

        if keyCode== ord('/') and (wx.MOD_CONTROL == event.GetModifiers()):
            self.commentLines()
        if keyCode== ord('/') and (wx.MOD_CONTROL|wx.MOD_SHIFT == event.GetModifiers()):
            self.uncommentLines()

        #do code completion
        if self.AUTOCOMPLETE:
            #get last word any previous word (if there was a dot instead of space)
            isAlphaNum = (keyCode in range(65,91) or keyCode in range(97,123))
            isDot = (keyCode==46)
            prevWord = None
            if isAlphaNum:#any alphanum
                #is character key
                key = chr(keyCode)
                #if keyCode == 32 and event.ControlDown(): #Ctrl-space
                pos = self.GetCurrentPos()
                prevStartPos = startPos = self.WordStartPosition(pos, True)
                currWord = self.GetTextRange(startPos, pos)+key

                #check if this is an attribute of another class etc...
                while self.GetCharAt(prevStartPos-1)==46:#then previous char was .
                    prevStartPos = self.WordStartPosition(prevStartPos-1, True)
                    prevWord = self.GetTextRange(prevStartPos, startPos-1)

            #slightly different if this char is itself a dot
            elif isDot: #we have a '.' so look for methods/attributes
                pos = self.GetCurrentPos()
                prevStartPos=startPos = self.WordStartPosition(pos, True)
                prevWord = self.GetTextRange(startPos, pos)
                currWord=''
                while self.GetCharAt(prevStartPos-1)==46:#then previous char was .
                    prevStartPos = self.WordStartPosition(prevStartPos-1, True)
                    prevWord = self.GetTextRange(prevStartPos, pos-1)

            self.AutoCompSetIgnoreCase(True)
            self.AutoCompSetAutoHide(True)
            #try to get attributes for this object
            event.Skip()
            if isAlphaNum or isDot:

                if True:#use our own dictionary
                    #after a '.' show attributes
                    subList=[]#by default
                    if prevWord: #did we get a word?
                        if prevWord in self.autoCompleteDict.keys(): #is it in dictionary?
                            attrs = self.autoCompleteDict[prevWord]['attrs']
                            if type(attrs)==list and len(attrs)>=1: #does it have known attributes?
                                subList = [ s for s in attrs if string.find(s.lower(), currWord.lower()) != -1 ]
                    #for objects show simple completions
                    else:#there was no preceding '.'
                        if len(currWord)>1 and len(self.autoCompleteDict.keys())>1: #start trying after 2 characters
                            subList = [ s for s in self.autoCompleteDict.keys() if string.find(s.lower(), currWord.lower()) != -1 ]
                else:#use introspect (from wxpython's py package)
                    pass#
                #if there were any reasonable matches then show them
                if len(subList)>0:
                    subList.sort()
                    self.AutoCompShow(len(currWord)-1, " ".join(subList))

        if keyCode == wx.WXK_RETURN and not self.AutoCompActive():
            #prcoess end of line and then do smart indentation
            event.Skip(False)
            self.CmdKeyExecute(wx.stc.STC_CMD_NEWLINE)
            self.smartIdentThisLine()
            return #so that we don't reach the skip line at end

        event.Skip()
    def smartIdentThisLine(self):
        startLineNum = self.LineFromPosition(self.GetSelectionStart())
        endLineNum = self.LineFromPosition(self.GetSelectionEnd())
        prevLine = self.GetLine(startLineNum-1)
        prevIndent = self.GetLineIndentation(startLineNum-1)

        #set the indent
        self.SetLineIndentation(startLineNum, prevIndent)
        #self.LineEnd() #move cursor to end of line - is good if user is starting a new line but not if they hit shift-tab
        #self.SetPosition(startLineNum+prevIndent)#move the cursor to the end of the indented section
        self.VCHome()

        #check for a colon to signal an indent decrease
        prevLogical = string.split(prevLine, '#')[0]
        prevLogical = string.strip(prevLogical)
        if len(prevLogical)>0 and prevLogical[-1]== ':':
            self.CmdKeyExecute(wx.stc.STC_CMD_TAB)

    def smartIndent(self):
        #find out about current positions and indentation
        startLineNum = self.LineFromPosition(self.GetSelectionStart())
        endLineNum = self.LineFromPosition(self.GetSelectionEnd())
        prevLine = self.GetLine(startLineNum-1)
        prevIndent = self.GetLineIndentation(startLineNum-1)
        startLineIndent = self.GetLineIndentation(startLineNum)

        #calculate how much we need to increment/decrement the current lines
        incr = prevIndent-startLineIndent
        #check for a colon to signal an indent decrease
        prevLogical = string.split(prevLine, '#')[0]
        prevLogical = string.strip(prevLogical)
        if len(prevLogical)>0 and prevLogical[-1]== ':':
            incr = incr+4

        #set each line to the correct indentation
        for lineNum in range(startLineNum, endLineNum+1):
            thisIndent = self.GetLineIndentation(lineNum)
            self.SetLineIndentation(lineNum, thisIndent+incr)
    def shouldTrySmartIndent(self):
        #used when the user presses tab key to decide whether to insert a tab char
        #or whether to smart indent text

        #if some text has been selected then use indentation
        if len(self.GetSelectedText())>0:
            return True

        #test whether any text precedes current pos
        lineText, posOnLine = self.GetCurLine()
        textBeforeCaret = lineText[:posOnLine]
        if textBeforeCaret.split()==[]:
            return True
        else:
            return False

    def indentSelection(self, howFar=4):
        #Indent or outdent current selection by 'howFar' spaces
        #(which could be positive or negative int).
        startLineNum = self.LineFromPosition(self.GetSelectionStart())
        endLineNum = self.LineFromPosition(self.GetSelectionEnd())
        #go through line-by-line
        for lineN in range(startLineNum, endLineNum+1):
            newIndent = self.GetLineIndentation(lineN) + howFar
            if newIndent<0:newIndent=0
            self.SetLineIndentation(lineN, newIndent)
    def MacOpenFile(self, evt):
        logging.debug('PsychoPyCoder: got MacOpenFile event')

    def OnUpdateUI(self, evt):
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()

        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in "[]{}()" and styleBefore == wx.stc.STC_P_OPERATOR:

            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)

            if charAfter and chr(charAfter) in "[]{}()" and styleAfter == wx.stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)
            #pt = self.PointFromPosition(braceOpposite)
            #self.Refresh(True, wxRect(pt.x, pt.y, 5,5))
            #print pt
            #self.Refresh(False)


        if self.coder.prefs['showSourceAsst']:
            #check current word including .
            if charBefore== ord('('):
                startPos = self.WordStartPosition(caretPos-2, True)
                endPos = caretPos-1
            else:
                startPos = self.WordStartPosition(caretPos, True)
                endPos = self.WordEndPosition(caretPos, True)
            #extend starPos back to beginngin of class separated by .
            while self.GetCharAt(startPos-1)==ord('.'):
                startPos = self.WordStartPosition(startPos-1, True)
            #now retrieve word
            currWord = self.GetTextRange(startPos, endPos)

            #lookfor word in dictionary
            if currWord in self.autoCompleteDict.keys():
                helpText = self.autoCompleteDict[currWord]['help']
                thisIs = self.autoCompleteDict[currWord]['is']
                thisType = self.autoCompleteDict[currWord]['type']
                thisAttrs = self.autoCompleteDict[currWord]['attrs']
                if type(thisIs)==str:#if this is a module
                    searchFor = thisIs
                else:
                    searchFor = currWord
            else:
                helpText = None
                thisIs=None
                thisAttrs=None
                thisType=None
                searchFor = currWord


            if self.prevWord != currWord:
                #if we have a class or function then use introspect (because it retrieves args as well as __doc__)
                if thisType is not 'instance':
                    wd, kwArgs, helpText = introspect.getCallTip(searchFor, locals=self.locals)
                #then pass all info to sourceAsst
                self.updateSourceAsst(currWord, thisIs, helpText, thisType, thisAttrs)#for an instance inclue known attrs

                self.prevWord = currWord#update for next time

    def updateSourceAsst(self,currWord, thisIs, helpText, thisType=None, knownAttrs=None):
            #update the source assistant window
            sa = self.coder.sourceAsstWindow
            assert isinstance(sa, wx.richtext.RichTextCtrl)
            # clear the buffer
            sa.Clear()

            #add current symbol
            sa.BeginBold()
            sa.WriteText('Symbol: ')
            sa.BeginTextColour('BLUE')
            sa.WriteText(currWord+'\n')
            sa.EndTextColour()
            sa.EndBold()

            #add expected type
            sa.BeginBold()
            sa.WriteText('is: ')
            sa.EndBold()
            if thisIs: sa.WriteText(str(thisIs)+'\n')
            else: sa.WriteText('\n')

            #add expected type
            sa.BeginBold()
            sa.WriteText('type: ')
            sa.EndBold()
            if thisIs: sa.WriteText(str(thisType)+'\n')
            else: sa.WriteText('\n')

            #add help text
            sa.BeginBold()
            sa.WriteText('Help:\n')
            sa.EndBold()
            if helpText: sa.WriteText(helpText+'\n')
            else: sa.WriteText('\n')

            #add attrs
            sa.BeginBold()
            sa.WriteText('Known methods:\n')
            sa.EndBold()
            if knownAttrs:
                if len(knownAttrs)>500:
                    sa.WriteText('\ttoo many to list (i.e. more than 500)!!\n')
                else:
                    for thisAttr in knownAttrs:
                        sa.WriteText('\t'+thisAttr+'\n')
            else: sa.WriteText('\n')

    def OnMarginClick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())

                if self.GetFoldLevel(lineClicked) & wx.stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)


    def FoldAll(self):
        lineCount = self.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & wx.stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & wx.stc.STC_FOLDLEVELHEADERFLAG and \
               (level & wx.stc.STC_FOLDLEVELNUMBERMASK) == wx.stc.STC_FOLDLEVELBASE:

                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.HideLines(lineNum+1, lastChild)

            lineNum = lineNum + 1



    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & wx.stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)

                    line = self.Expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1

        return line


    def commentLines(self):
        #used for the comment/uncomment machinery from ActiveGrid
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = self.GetLine(lineNo)
            if (len(lineText) > 1 and lineText[0] == '#') or (len(lineText) > 2 and lineText[:2] == '##'):
                newText = newText + lineText
            else:
                newText = newText + "#" + lineText
        self._ReplaceSelectedLines(newText)
    def uncommentLines(self):
        #used for the comment/uncomment machinery from ActiveGrid
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = self.GetLine(lineNo)
            if len(lineText) >= 2 and lineText[:2] == "#":
                lineText = lineText[2:]
            elif len(lineText) >= 1 and lineText[:1] == "#":
                lineText = lineText[1:]
            newText = newText + lineText
        self._ReplaceSelectedLines(newText)
    def _GetSelectedLineNumbers(self):
        #used for the comment/uncomment machinery from ActiveGrid
        selStart, selEnd = self._GetPositionsBoundingSelectedLines()
        return range(self.LineFromPosition(selStart), self.LineFromPosition(selEnd))
    def _GetPositionsBoundingSelectedLines(self):
        #used for the comment/uncomment machinery from ActiveGrid
        startPos = self.GetCurrentPos()
        endPos = self.GetAnchor()
        if startPos > endPos:
            temp = endPos
            endPos = startPos
            startPos = temp
        if endPos == self.PositionFromLine(self.LineFromPosition(endPos)):
            endPos = endPos - 1  # If it's at the very beginning of a line, use the line above it as the ending line
        selStart = self.PositionFromLine(self.LineFromPosition(startPos))
        selEnd = self.PositionFromLine(self.LineFromPosition(endPos) + 1)
        return selStart, selEnd
    def _ReplaceSelectedLines(self, text):
        #used for the comment/uncomment machinery from ActiveGrid
        if len(text) == 0:
            return
        selStart, selEnd = self._GetPositionsBoundingSelectedLines()
        self.SetSelection(selStart, selEnd)
        self.ReplaceSelection(text)
        self.SetSelection(selStart + len(text), selStart)

    def analyseScript(self):
        #analyse the file
        buffer = StringIO.StringIO()
        buffer.write(self.GetText())
        buffer.seek(0)
        try:
            importStatements, tokenDict = psychoParser.getTokensAndImports(buffer)
            successfulParse=True
        except:
            successfulParse=False
        buffer.close()

        if successfulParse: #if we parsed the tokens then process them

            #import the libs used by the script
            if self.coder.modulesLoaded:
                for thisLine in importStatements:
                    #check what file we're importing from
                    tryImport=ALLOW_MODULE_IMPORTS
                    words = string.split(thisLine)
                    for word in words:#don't import from files in this folder (user files)
                        if os.path.isfile(word+'.py'):
                            tryImport=False
                    if tryImport:
                        try:#it might not import
                            exec(thisLine)
                        except:
                            pass
                    self.locals = locals()#keep a track of our new locals
                self.autoCompleteDict = {}

            #go through imported symbols (using dir())
            #loop through to appropriate level of module tree getting all possible symbols
            symbols = dir()
            #remove some tokens that are just from here
            symbols.remove('self')
            symbols.remove('buffer')
            symbols.remove('tokenDict')
            symbols.remove('successfulParse')
            for thisSymbol in symbols:
                #create an actual obj from the name
                exec('thisObj=%s' %thisSymbol)
                #(try to) get the attributes of the object
                try:
                    newAttrs = dir(thisObj)
                except:
                    newAttrs=[]

                #only dig deeper if we haven't exceeded the max level of analysis
                if thisSymbol.find('.') < analysisLevel:
                    #we should carry on digging deeper
                    for thisAttr in newAttrs:
                        #by appending the symbol it will also get analysed!
                        symbols.append(thisSymbol+'.'+thisAttr)

                #but (try to) add data for all symbols including this level
                try:
                    self.autoCompleteDict[thisSymbol]={'is':thisObj,
                        'type':type(thisObj),
                        'attrs':newAttrs,
                        'help':thisObj.__doc__}
                except:
                    pass#not sure what happened - maybe no __doc__?

            #add keywords
            for thisName in keyword.kwlist[:]:
                self.autoCompleteDict[thisName]={'is':'Keyword','type':'Keyword', 'attrs':None, 'help':None}
            self.autoCompleteDict['self']={'is':'self','type':'self', 'attrs':None, 'help':None}

            #then add the tokens (i.e. instances) from this script
            for thisKey in tokenDict:
                #the default is to have no fields filled
                thisObj= thisIs = thisHelp = thisType = thisAttrs = None
                keyIsStr = tokenDict[thisKey]['is']
                try:
                    exec('thisObj=%s' %keyIsStr)
                    if type(thisObj)==types.FunctionType:
                        thisIs = 'returned from functon'
                    else:
                        thisIs = str(thisObj)
                        thisType = 'instance'
                        thisHelp = thisObj.__doc__
                        thisAttrs = dir(thisObj)
                except:
                    pass
                self.autoCompleteDict[thisKey]={'is':thisIs,
                    'type':thisType,
                    'attrs':thisAttrs,
                    'help':thisHelp}

    def onModified(self, event):
        #update the UNSAVED flag and the save icons
        notebook = self.GetParent()
        mainFrame = notebook.GetParent()
        mainFrame.setFileModified(True)
    def DoFindNext(self, findData, findDlg=None):
        #this comes straight from wx.py.editwindow  (which is a subclass of STC control)
        backward = not (findData.GetFlags() & wx.FR_DOWN)
        matchcase = (findData.GetFlags() & wx.FR_MATCHCASE) != 0
        end = self.GetLength()
        textstring = self.GetTextRange(0, end)
        findstring = findData.GetFindString()
        if not matchcase:
            textstring = textstring.lower()
            findstring = findstring.lower()
        if backward:
            start = self.GetSelection()[0]
            loc = textstring.rfind(findstring, 0, start)
        else:
            start = self.GetSelection()[1]
            loc = textstring.find(findstring, start)

        # if it wasn't found then restart at begining
        if loc == -1 and start != 0:
            if backward:
                start = end
                loc = textstring.rfind(findstring, 0, start)
            else:
                start = 0
                loc = textstring.find(findstring, start)

        # was it still not found?
        if loc == -1:
            dlg = dialogs.MessageDialog(self, message=_translate('Unable to find "%s"') %findstring,type='Info')
            dlg.ShowModal()
            dlg.Destroy()
        else:
            # show and select the found text
            line = self.LineFromPosition(loc)
            #self.EnsureVisible(line)
            self.GotoLine(line)
            self.SetSelection(loc, loc + len(findstring))
        if findDlg:
            if loc == -1:
                wx.CallAfter(findDlg.SetFocus)
                return
            else:
                findDlg.Close()

class CoderFrame(wx.Frame):
    def __init__(self, parent, ID, title, files=[], app=None):
        self.app = app
        self.frameType='coder'
        self.appData = self.app.prefs.appData['coder']#things the user doesn't set like winsize etc
        self.prefs = self.app.prefs.coder#things about the coder that get set
        self.appPrefs = self.app.prefs.app
        self.paths = self.app.prefs.paths
        self.IDs = self.app.IDs
        self.currentDoc=None
        self.ignoreErrors = False
        self.fileStatusLastChecked = time.time()
        self.fileStatusCheckInterval = 5 * 60 #sec
        self.showingReloadDialog = False

        if self.appData['winH']==0 or self.appData['winW']==0:#we didn't have the key or the win was minimized/invalid
            self.appData['winH'], self.appData['winW'] =wx.DefaultSize
            self.appData['winX'],self.appData['winY'] =wx.DefaultPosition
        if self.appData['winY'] < 20:
            self.appData['winY'] = 20
        wx.Frame.__init__(self, parent, ID, title,
                         (self.appData['winX'], self.appData['winY']),
                         size=(self.appData['winW'],self.appData['winH']))

        #self.panel = wx.Panel(self)
        self.Hide()#ugly to see it all initialise
        #create icon
        if sys.platform=='darwin':
            pass#doesn't work and not necessary - handled by application bundle
        else:
            iconFile = os.path.join(self.paths['resources'], 'psychopy.ico')
            if os.path.isfile(iconFile):
                self.SetIcon(wx.Icon(iconFile, wx.BITMAP_TYPE_ICO))
        wx.EVT_CLOSE(self, self.closeFrame)#NB not the same as quit - just close the window
        wx.EVT_IDLE(self, self.onIdle)

        if 'state' in self.appData and self.appData['state']=='maxim':
            self.Maximize()
        #initialise some attributes
        self.modulesLoaded=False #will turn true when loading thread completes
        self.findDlg = None
        self.findData = wx.FindReplaceData()
        self.findData.SetFlags(wx.FR_DOWN)
        self.importedScripts={}
        self.scriptProcess=None
        self.scriptProcessID=None
        self.db = None#debugger
        self._lastCaretPos=None

        #setup statusbar
        self.makeToolbar()#must be before the paneManager for some reason
        self.makeMenus()
        self.CreateStatusBar()
        self.SetStatusText("")
        self.fileMenu = self.editMenu = self.viewMenu = self.helpMenu = self.toolsMenu = None

        #setup universal shortcuts
        accelTable = self.app.makeAccelTable()
        self.SetAcceleratorTable(accelTable)

        #make the pane manager
        self.paneManager = wx.aui.AuiManager()

        #create an editor pane
        self.paneManager.SetFlags(wx.aui.AUI_MGR_RECTANGLE_HINT)
        self.paneManager.SetManagedWindow(self)
        #make the notebook
        self.notebook = wx.aui.AuiNotebook(self, -1, size=wx.Size(600,600),
            style= wx.aui.AUI_NB_TOP | wx.aui.AUI_NB_TAB_SPLIT | wx.aui.AUI_NB_SCROLL_BUTTONS | \
                wx.aui.AUI_NB_TAB_MOVE | wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB | wx.aui.AUI_NB_WINDOWLIST_BUTTON)

        self.paneManager.AddPane(self.notebook, wx.aui.AuiPaneInfo().
                          Name("Editor").Caption(_translate("Editor")).
                          CenterPane(). #'center panes' expand to fill space
                          CloseButton(False).MaximizeButton(True))

        self.notebook.SetFocus()
        self.notebook.SetDropTarget(FileDropTarget(coder = self))

        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.fileClose)
        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.pageChanged)
        #self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.pageChanged)
        self.SetDropTarget(FileDropTarget(coder = self))
        self.Bind(wx.EVT_DROP_FILES, self.filesDropped)
        self.Bind(wx.EVT_FIND, self.OnFindNext)
        self.Bind(wx.EVT_FIND_NEXT, self.OnFindNext)
        self.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)
        self.Bind(wx.EVT_END_PROCESS, self.onProcessEnded)

        #take files from arguments and append the previously opened files
        if files not in [None, []]:
            for filename in files:
                if not os.path.isfile(filename): continue
                self.setCurrentDoc(filename, keepHidden=True)

        #create the shelf for shell and output views
        self.shelf = wx.aui.AuiNotebook(self, -1, size=wx.Size(600,600),
            style= wx.aui.AUI_NB_TOP | wx.aui.AUI_NB_TAB_SPLIT | wx.aui.AUI_NB_SCROLL_BUTTONS | \
                wx.aui.AUI_NB_TAB_MOVE)
        self.paneManager.AddPane(self.shelf,
                                 wx.aui.AuiPaneInfo().
                                 Name("Shelf").Caption(_translate("Shelf")).
                                 RightDockable(True).LeftDockable(True).CloseButton(False).
                                 Bottom())

        #create output viewer
        self._origStdOut = sys.stdout#keep track of previous output
        self._origStdErr = sys.stderr

        self.outputWindow = stdOutRich.StdOutRich(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.VSCROLL,
            font=self.prefs['outputFont'], fontSize=self.prefs['outputFontSize'])
        self.outputWindow.write(_translate('Welcome to PsychoPy2!') + '\n')
        self.outputWindow.write("v%s\n" %self.app.version)
        self.shelf.AddPage(self.outputWindow, _translate('Output'))

        if haveCode:
            useDefaultShell = True
            if self.prefs['preferredShell'].lower()=='ipython':
                try:
                    import IPython.gui.wx.ipython_view
                    #IPython shell is nice, but crashes if you draw stimuli
                    self.shell = IPython.gui.wx.ipython_view.IPShellWidget(parent=self,
                        background_color='WHITE',
                        )
                    useDefaultShell = False
                except:
                    logging.warn(_translate('IPython failed as shell, using pyshell (IPython v0.12 can fail on wx)'))
            if useDefaultShell:
                from wx import py
                self.shell = py.shell.Shell(self.shelf, -1, introText=_translate('PyShell in PsychoPy - type some commands!')+'\n\n')
            self.shelf.AddPage(self.shell, _translate('Shell'))

        #add help window
        self.sourceAsstWindow = wx.richtext.RichTextCtrl(self,-1, size=wx.Size(300,300),
                                          style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.paneManager.AddPane(self.sourceAsstWindow,
                                 wx.aui.AuiPaneInfo().BestSize((600,600)).
                                 Name("SourceAsst").Caption(_translate("Source Assistant")).
                                 RightDockable(True).LeftDockable(True).CloseButton(False).
                                 Right())
        #will we show the pane straight away?
        if self.prefs['showSourceAsst']:
            self.paneManager.GetPane('SourceAsst').Show()
        else:self.paneManager.GetPane('SourceAsst').Hide()
        self.unitTestFrame=None

        #self.SetSizer(self.mainSizer)#not necessary for aui type controls
        if self.appData['auiPerspective'] and \
            'Shelf' in self.appData['auiPerspective']:#
                self.paneManager.LoadPerspective(self.appData['auiPerspective'])
                self.paneManager.GetPane('Shelf').Caption(_translate("Shelf"))
                self.paneManager.GetPane('SourceAsst').Caption(_translate("Source Assistant"))
                self.paneManager.GetPane('Editor').Caption(_translate("Editor"))
        else:
            self.SetMinSize(wx.Size(400, 600)) #min size for the whole window
            self.Fit()
            self.paneManager.Update()
        self.SendSizeEvent()

    def makeMenus(self):
        #---Menus---#000000#FFFFFF--------------------------------------------------
        menuBar = wx.MenuBar()
        #---_file---#000000#FFFFFF--------------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, _translate('&File'))

        #create a file history submenu
        self.fileHistory = wx.FileHistory(maxFiles=10)
        self.recentFilesMenu = wx.Menu()
        self.fileHistory.UseMenu(self.recentFilesMenu)
        for filename in self.appData['fileHistory']: self.fileHistory.AddFileToHistory(filename)
        self.Bind(
            wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9
            )

        #add items to file menu
        self.fileMenu.Append(wx.ID_NEW,     _translate("&New\t%s") %self.app.keys['new'])
        self.fileMenu.Append(wx.ID_OPEN,    _translate("&Open...\t%s") %self.app.keys['open'])
        self.fileMenu.AppendSubMenu(self.recentFilesMenu,_translate("Open &Recent"))
        self.fileMenu.Append(wx.ID_SAVE,    _translate("&Save\t%s") %self.app.keys['save'], _translate("Save current file"))
        self.fileMenu.Append(wx.ID_SAVEAS,  _translate("Save &as...\t%s") %self.app.keys['saveAs'], _translate("Save current python file as..."))
        self.fileMenu.Append(self.IDs.filePrint,  _translate("Print\t%s") %self.app.keys['print'])
        self.fileMenu.Append(wx.ID_CLOSE,   _translate("&Close file\t%s") %self.app.keys['close'], _translate("Close current python file"))
        wx.EVT_MENU(self, wx.ID_NEW,  self.fileNew)
        wx.EVT_MENU(self, wx.ID_OPEN,  self.fileOpen)
        wx.EVT_MENU(self, wx.ID_SAVE,  self.fileSave)
        wx.EVT_MENU(self, wx.ID_SAVEAS,  self.fileSaveAs)
        wx.EVT_MENU(self, wx.ID_CLOSE,  self.fileClose)
        wx.EVT_MENU(self, self.IDs.filePrint,  self.filePrint)
        item = self.fileMenu.Append(wx.ID_PREFERENCES, text = _translate("&Preferences\t%s") %self.app.keys['preferences'])
        self.Bind(wx.EVT_MENU, self.app.showPrefs, item)
        #-------------quit
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(wx.ID_EXIT, _translate("&Quit\t%s") %self.app.keys['quit'], _translate("Terminate the program"))
        wx.EVT_MENU(self, wx.ID_EXIT, self.quit)

        #---_edit---#000000#FFFFFF--------------------------------------------------
        self.editMenu = wx.Menu()
        menuBar.Append(self.editMenu, _translate('&Edit'))
        self.editMenu.Append(wx.ID_CUT, _translate("Cu&t\t%s") %self.app.keys['cut'])
        wx.EVT_MENU(self, wx.ID_CUT,  self.cut)
        self.editMenu.Append(wx.ID_COPY, _translate("&Copy\t%s") %self.app.keys['copy'])
        wx.EVT_MENU(self, wx.ID_COPY,  self.copy)
        self.editMenu.Append(wx.ID_PASTE, _translate("&Paste\t%s") %self.app.keys['paste'])
        wx.EVT_MENU(self, wx.ID_PASTE,  self.paste)
        self.editMenu.Append(wx.ID_DUPLICATE, _translate("&Duplicate\t%s") %self.app.keys['duplicate'], _translate("Duplicate the current line (or current selection)"))
        wx.EVT_MENU(self, wx.ID_DUPLICATE,  self.duplicateLine)

        self.editMenu.AppendSeparator()
        self.editMenu.Append(self.IDs.showFind, _translate("&Find\t%s") %self.app.keys['find'])
        wx.EVT_MENU(self, self.IDs.showFind, self.OnFindOpen)
        self.editMenu.Append(self.IDs.findNext, _translate("Find &Next\t%s") %self.app.keys['findAgain'])
        wx.EVT_MENU(self, self.IDs.findNext, self.OnFindNext)

        self.editMenu.AppendSeparator()
        self.editMenu.Append(self.IDs.comment, _translate("Comment\t%s") %self.app.keys['comment'], _translate("Comment selected lines"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, self.IDs.comment,  self.commentSelected)
        self.editMenu.Append(self.IDs.unComment, _translate("Uncomment\t%s") %self.app.keys['uncomment'], _translate("Un-comment selected lines"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, self.IDs.unComment,  self.uncommentSelected)
        self.editMenu.Append(self.IDs.foldAll, _translate("Toggle fold\t%s") %self.app.keys['fold'], _translate("Toggle folding of top level"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, self.IDs.foldAll,  self.foldAll)

        self.editMenu.AppendSeparator()
        self.editMenu.Append(self.IDs.indent, _translate("Indent selection\t%s") %self.app.keys['indent'], _translate("Increase indentation of current line"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, self.IDs.indent,  self.indent)
        self.editMenu.Append(self.IDs.dedent, _translate("Dedent selection\t%s") %self.app.keys['dedent'], _translate("Decrease indentation of current line"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, self.IDs.dedent,  self.dedent)
        self.editMenu.Append(self.IDs.smartIndent, _translate("SmartIndent\t%s") %self.app.keys['smartIndent'], _translate("Try to indent to the correct position w.r.t  last line"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, self.IDs.smartIndent,  self.smartIndent)

        self.editMenu.AppendSeparator()
        self.editMenu.Append(wx.ID_UNDO, _translate("Undo\t%s") %self.app.keys['undo'], _translate("Undo last action"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, wx.ID_UNDO,  self.undo)
        self.editMenu.Append(wx.ID_REDO, _translate("Redo\t%s") %self.app.keys['redo'], _translate("Redo last action"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, wx.ID_REDO,  self.redo)

        #self.editMenu.Append(ID_UNFOLDALL, "Unfold All\tF3", "Unfold all lines", wx.ITEM_NORMAL)
        #wx.EVT_MENU(self, ID_UNFOLDALL,  self.unfoldAll)
        #---_tools---#000000#FFFFFF--------------------------------------------------
        self.toolsMenu = wx.Menu()
        menuBar.Append(self.toolsMenu, _translate('&Tools'))
        self.toolsMenu.Append(self.IDs.monitorCenter, _translate("Monitor Center"), _translate("To set information about your monitor"))
        wx.EVT_MENU(self, self.IDs.monitorCenter,  self.app.openMonitorCenter)
        #self.analyseAutoChk = self.toolsMenu.AppendCheckItem(self.IDs.analyzeAuto, "Analyse on file save/open", "Automatically analyse source (for autocomplete etc...). Can slow down the editor on a slow machine or with large files")
        #wx.EVT_MENU(self, self.IDs.analyzeAuto,  self.setAnalyseAuto)
        #self.analyseAutoChk.Check(self.prefs['analyseAuto'])
        #self.toolsMenu.Append(self.IDs.analyzeNow, "Analyse now\t%s" %self.app.keys['analyseCode'], "Force a reananalysis of the code now")
        #wx.EVT_MENU(self, self.IDs.analyzeNow,  self.analyseCodeNow)

        self.toolsMenu.Append(self.IDs.runFile, _translate("Run\t%s") %self.app.keys['runScript'], _translate("Run the current script"))
        wx.EVT_MENU(self, self.IDs.runFile,  self.runFile)
        self.toolsMenu.Append(self.IDs.stopFile, _translate("Stop\t%s") %self.app.keys['stopScript'], _translate("Stop the current script"))
        wx.EVT_MENU(self, self.IDs.stopFile,  self.stopFile)

        self.toolsMenu.AppendSeparator()
        self.toolsMenu.Append(self.IDs.openUpdater, _translate("PsychoPy updates..."), _translate("Update PsychoPy to the latest, or a specific, version"))
        wx.EVT_MENU(self, self.IDs.openUpdater,  self.app.openUpdater)
        self.toolsMenu.Append(self.IDs.benchmarkWizard, _translate("Benchmark wizard"), _translate("Check software & hardware, generate report"))
        wx.EVT_MENU(self, self.IDs.benchmarkWizard,  self.app.benchmarkWizard)

        if self.appPrefs['debugMode']:
            self.toolsMenu.Append(self.IDs.unitTests, _translate("Unit &testing...\tCtrl-T"),
                _translate("Show dialog to run unit tests"))
            wx.EVT_MENU(self, self.IDs.unitTests, self.onUnitTests)

        #---_view---#000000#FFFFFF--------------------------------------------------
        self.viewMenu = wx.Menu()
        menuBar.Append(self.viewMenu, _translate('&View'))

        #indent guides
        self.indentGuideChk= self.viewMenu.AppendCheckItem(self.IDs.toggleIndentGuides,
            _translate("&Indentation guides\t%s") %self.app.keys['toggleIndentGuides'],
            _translate("Shows guides in the editor for your indentation level"))
        self.indentGuideChk.Check(self.appData['showIndentGuides'])
        wx.EVT_MENU(self, self.IDs.toggleIndentGuides,  self.setShowIndentGuides)
        #whitespace
        self.showWhitespaceChk= self.viewMenu.AppendCheckItem(self.IDs.toggleWhitespace,
            _translate("&Whitespace\t%s") %self.app.keys['toggleWhitespace'],
            _translate("Show whitespace characters in the code"))
        self.showWhitespaceChk.Check(self.appData['showWhitespace'])
        wx.EVT_MENU(self, self.IDs.toggleWhitespace, self.setShowWhitespace)
        #EOL markers
        self.showEOLsChk= self.viewMenu.AppendCheckItem(self.IDs.toggleEOLs,
            _translate("Show &EOLs\t%s") %self.app.keys['toggleEOLs'],
            _translate("Show End Of Line markers in the code"))
        self.showEOLsChk.Check(self.appData['showEOLs'])
        wx.EVT_MENU(self, self.IDs.toggleEOLs, self.setShowEOLs)

        self.viewMenu.AppendSeparator()
        #output window
        self.outputChk= self.viewMenu.AppendCheckItem(self.IDs.toggleOutput, _translate("Show &Output/Shell\t%s") %self.app.keys['toggleOutputPanel'],
                                                  _translate("Shows the output and shell panes (and starts capturing stdout)"))
        self.outputChk.Check(self.prefs['showOutput'])
        wx.EVT_MENU(self, self.IDs.toggleOutput,  self.setOutputWindow)
        #source assistant
        self.sourceAsstChk= self.viewMenu.AppendCheckItem(self.IDs.toggleSourceAsst, _translate("&Source Assistant"),
                                                  _translate("Provides help functions and attributes of classes in your script"))
        self.sourceAsstChk.Check(self.prefs['showSourceAsst'])
        wx.EVT_MENU(self, self.IDs.toggleSourceAsst,  self.setSourceAsst)
        self.viewMenu.AppendSeparator()
        self.viewMenu.Append(self.IDs.openBuilderView, _translate("Go to &Builder view\t%s") %self.app.keys['switchToBuilder'], _translate("Go to the Builder view"))
        wx.EVT_MENU(self, self.IDs.openBuilderView,  self.app.showBuilder)
        #        self.viewMenu.Append(self.IDs.openShell, "Go to &IPython Shell\t%s" %self.app.keys['switchToShell'], "Go to a shell window for interactive commands")
        #        wx.EVT_MENU(self, self.IDs.openShell,  self.app.showShell)
        #self.viewMenu.Append(self.IDs.openIPythonNotebook, "Go to &IPython notebook", "Open an IPython notebook (unconnected in a browser)")
        #wx.EVT_MENU(self, self.IDs.openIPythonNotebook,  self.app.openIPythonNotebook)

        self.demosMenu = wx.Menu()
        self.demos={}
        menuBar.Append(self.demosMenu, _translate('&Demos'))
        #for demos we need a dict where the event ID will correspond to a filename
        #add folders
        for folder in glob.glob(os.path.join(self.paths['demos'],'coder','*')):
            #if it isn't a folder either then skip it
            if not os.path.isdir(folder): continue
            #otherwise create a submenu
            folderDisplayName = os.path.split(folder)[-1]
            if folderDisplayName in _localized.keys():
                folderDisplayName = _localized[folderDisplayName]
            submenu = wx.Menu()
            self.demosMenu.AppendSubMenu(submenu, folderDisplayName)

            #find the files in the folder (search two levels deep)
            demoList = glob.glob(os.path.join(folder, '*.py'))
            demoList += glob.glob(os.path.join(folder, '*', '*.py'))
            demoList += glob.glob(os.path.join(folder, '*', '*', '*.py'))

            demoList.sort(key=str.lower)
            demoIDs = map(lambda _makeID: wx.NewId(), range(len(demoList)))

            for n in range(len(demoList)):
                self.demos[demoIDs[n]] = demoList[n]
            for thisID in demoIDs:
                shortname = self.demos[thisID].split(os.path.sep)[-1]
                if shortname == "run.py":
                    # file is just "run" so get shortname from directory name instead
                    shortname = self.demos[thisID].split(os.path.sep)[-2]
                if shortname.startswith('_'):
                    continue  # remove any 'private' files
                submenu.Append(thisID, shortname)
                wx.EVT_MENU(self, thisID, self.loadDemo)
        #also add simple demos to root
        self.demosMenu.AppendSeparator()
        for filename in glob.glob(os.path.join(self.paths['demos'],'coder','*.py')):
            junk, shortname = os.path.split(filename)
            if shortname.startswith('_'):
                continue  # remove any 'private' files
            thisID = wx.NewId()
            self.demosMenu.Append(thisID, shortname)
            self.demos[thisID] = filename
            wx.EVT_MENU(self, thisID, self.loadDemo)

        #---_help---#000000#FFFFFF--------------------------------------------------
        self.helpMenu = wx.Menu()
        menuBar.Append(self.helpMenu, _translate('&Help'))
        self.helpMenu.Append(self.IDs.psychopyHome, _translate("&PsychoPy Homepage"), _translate("Go to the PsychoPy homepage"))
        wx.EVT_MENU(self, self.IDs.psychopyHome, self.app.followLink)
        self.helpMenu.Append(self.IDs.coderTutorial, _translate("&PsychoPy Coder Tutorial"), _translate("Go to the online PsychoPy tutorial"))
        wx.EVT_MENU(self, self.IDs.coderTutorial, self.app.followLink)
        self.helpMenu.Append(self.IDs.psychopyReference, _translate("&PsychoPy API (reference)"), _translate("Go to the online PsychoPy reference manual"))
        wx.EVT_MENU(self, self.IDs.psychopyReference, self.app.followLink)
        self.helpMenu.AppendSeparator()
        self.helpMenu.Append(wx.ID_ABOUT, _translate("&About..."), _translate("About PsychoPy"))#on mac this will move to appication menu
        wx.EVT_MENU(self, wx.ID_ABOUT, self.app.showAbout)

        self.SetMenuBar(menuBar)

    def makeToolbar(self):
        #---toolbar---#000000#FFFFFF----------------------------------------------
        self.toolbar = self.CreateToolBar( (wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT))

        if sys.platform == 'win32' or sys.platform.startswith('linux'):
            if self.appPrefs['largeIcons']: toolbarSize=32
            else: toolbarSize=16
        else:
            toolbarSize = 32  # mac: 16 either doesn't work, or looks really bad with wx3
        self.toolbar.SetToolBitmapSize((toolbarSize,toolbarSize))
        new_bmp = wx.Bitmap(os.path.join(self.paths['resources'], 'filenew%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        open_bmp = wx.Bitmap(os.path.join(self.paths['resources'], 'fileopen%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        save_bmp = wx.Bitmap(os.path.join(self.paths['resources'], 'filesave%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        saveAs_bmp = wx.Bitmap(os.path.join(self.paths['resources'], 'filesaveas%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        undo_bmp = wx.Bitmap(os.path.join(self.paths['resources'], 'undo%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        redo_bmp = wx.Bitmap(os.path.join(self.paths['resources'], 'redo%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        stop_bmp = wx.Bitmap(os.path.join(self.paths['resources'], 'stop%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        run_bmp = wx.Bitmap(os.path.join(self.paths['resources'], 'run%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        preferences_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'preferences%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        monitors_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'monitors%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        colorpicker_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'color%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)

        ctrlKey = 'Ctrl+'  # show key-bindings in tool-tips in an OS-dependent way
        if sys.platform == 'darwin': ctrlKey = 'Cmd+'
        self.toolbar.AddSimpleTool(self.IDs.tbFileNew, new_bmp, (_translate("New [%s]") %self.app.keys['new']).replace('Ctrl+', ctrlKey), _translate("Create new python file"))
        self.toolbar.Bind(wx.EVT_TOOL, self.fileNew, id=self.IDs.tbFileNew)
        self.toolbar.AddSimpleTool(self.IDs.tbFileOpen, open_bmp, (_translate("Open [%s]") % self.app.keys['open']).replace('Ctrl+', ctrlKey), _translate("Open an existing file"))
        self.toolbar.Bind(wx.EVT_TOOL, self.fileOpen, id=self.IDs.tbFileOpen)
        self.toolbar.AddSimpleTool(self.IDs.tbFileSave, save_bmp, (_translate("Save [%s]") % self.app.keys['save']).replace('Ctrl+', ctrlKey), _translate("Save current file"))
        self.toolbar.EnableTool(self.IDs.tbFileSave, False)
        self.toolbar.Bind(wx.EVT_TOOL, self.fileSave, id=self.IDs.tbFileSave)
        self.toolbar.AddSimpleTool(self.IDs.tbFileSaveAs, saveAs_bmp, (_translate("Save As... [%s]") % self.app.keys['saveAs']).replace('Ctrl+', ctrlKey), _translate("Save current python file as..."))
        self.toolbar.Bind(wx.EVT_TOOL, self.fileSaveAs, id=self.IDs.tbFileSaveAs)
        self.toolbar.AddSimpleTool(self.IDs.tbUndo, undo_bmp, (_translate("Undo [%s]") % self.app.keys['undo']).replace('Ctrl+', ctrlKey), _translate("Undo last action"))
        self.toolbar.Bind(wx.EVT_TOOL, self.undo, id=self.IDs.tbUndo)
        self.toolbar.AddSimpleTool(self.IDs.tbRedo, redo_bmp, (_translate("Redo [%s]") % self.app.keys['redo']).replace('Ctrl+', ctrlKey), _translate("Redo last action"))
        self.toolbar.Bind(wx.EVT_TOOL, self.redo, id=self.IDs.tbRedo)
        self.toolbar.AddSeparator()
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(self.IDs.tbPreferences, preferences_bmp, _translate("Preferences"),  _translate("Application preferences"))
        self.toolbar.Bind(wx.EVT_TOOL, self.app.showPrefs, id=self.IDs.tbPreferences)
        self.toolbar.AddSimpleTool(self.IDs.tbMonitorCenter, monitors_bmp, _translate("Monitor Center"),  _translate("Monitor settings and calibration"))
        self.toolbar.Bind(wx.EVT_TOOL, self.app.openMonitorCenter, id=self.IDs.tbMonitorCenter)
        self.toolbar.AddSimpleTool(self.IDs.tbColorPicker, colorpicker_bmp, _translate("Color Picker -> clipboard"),  _translate("Color Picker -> clipboard"))
        self.toolbar.Bind(wx.EVT_TOOL, self.app.colorPicker, id=self.IDs.tbColorPicker)
        self.toolbar.AddSeparator()
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(self.IDs.tbRun, run_bmp, (_translate("Run [%s]") % self.app.keys['runScript']).replace('Ctrl+', ctrlKey),  _translate("Run current script"))
        self.toolbar.Bind(wx.EVT_TOOL, self.runFile, id=self.IDs.tbRun)
        self.toolbar.AddSimpleTool(self.IDs.tbStop, stop_bmp, (_translate("Stop [%s]") % self.app.keys['stopScript']).replace('Ctrl+', ctrlKey),  _translate("Stop current script"))
        self.toolbar.Bind(wx.EVT_TOOL, self.stopFile, id=self.IDs.tbStop)
        self.toolbar.EnableTool(self.IDs.tbStop,False)
        self.toolbar.Realize()

    def onIdle(self, event):
        #check the script outputs to see if anything has been written to stdout
        if self.scriptProcess is not None:
            if self.scriptProcess.IsInputAvailable():
                stream = self.scriptProcess.GetInputStream()
                text = stream.read()
                self.outputWindow.write(text)
            if self.scriptProcess.IsErrorAvailable():
                stream = self.scriptProcess.GetErrorStream()
                text = stream.read()
                self.outputWindow.write(text)
        #check if we're in the same place as before
        if hasattr(self.currentDoc, 'GetCurrentPos') and (self._lastCaretPos!=self.currentDoc.GetCurrentPos()):
            self.currentDoc.OnUpdateUI(evt=None)
            self._lastCaretPos=self.currentDoc.GetCurrentPos()
        if time.time() - self.fileStatusLastChecked > self.fileStatusCheckInterval and \
                not self.showingReloadDialog:
            if not self.expectedModTime(self.currentDoc):
                self.showingReloadDialog = True
                dlg = dialogs.MessageDialog(self,
                        message=_translate("'%s' was modified outside of PsychoPy:\n\nReload (without saving)?") % (os.path.basename(self.currentDoc.filename)),
                        type='Warning')
                if dlg.ShowModal() == wx.ID_YES:
                    self.SetStatusText(_translate('Reloading file'))
                    self.fileReload(event, filename=self.currentDoc.filename,checkSave=False)
                self.showingReloadDialog = False
                self.SetStatusText('')
                try: dlg.destroy()
                except: pass
            self.fileStatusLastChecked = time.time()

    def pageChanged(self,event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        self.currentDoc = self.notebook.GetPage(new)
        self.setFileModified(self.currentDoc.UNSAVED)
        self.SetLabel('%s - PsychoPy Coder' %self.currentDoc.filename)
        if not self.expectedModTime(self.currentDoc):
            """dial = wx.MessageDialog(None, "'%s' was modified outside of PsychoPy\n\nReload (without saving)?" % (os.path.basename(self.currentDoc.filename)),
                'Warning', wx.YES_NO | wx.ICON_EXCLAMATION)
            resp = dial.ShowModal() # nicer look but fails to accept a response (!)"""
            dlg = dialogs.MessageDialog(self,
                    message=_translate("'%s' was modified outside of PsychoPy:\n\nReload (without saving)?") % (os.path.basename(self.currentDoc.filename)),
                    type='Warning')
            if  dlg.ShowModal() == wx.ID_YES:
                self.SetStatusText(_translate('Reloading file'))
                self.fileReload(event, filename=self.currentDoc.filename,checkSave=False)
                self.setFileModified(False)
            self.SetStatusText('')
            try: dlg.destroy()
            except: pass

        #event.Skip()
    def filesDropped(self, event):
        fileList = event.GetFiles()
        for filename in fileList:
            if os.path.isfile(filename):
                if filename.lower().endswith('.psyexp'):
                    self.app.newBuilderFrame(filename)
                else:
                    print filename
                    self.setCurrentDoc(filename)
    def OnFindOpen(self, event):
        #open the find dialog if not already open
        if self.findDlg is not None:
            return
        win = wx.Window.FindFocus()
        self.findDlg = wx.FindReplaceDialog(win, self.findData, "Find",
                                            wx.FR_NOWHOLEWORD)
        self.findDlg.Show()

    def OnFindNext(self, event):
        #find the next occurence of text according to last find dialogue data
        if not self.findData.GetFindString():
            self.OnFindOpen(event)
            return
        self.currentDoc.DoFindNext(self.findData, self.findDlg)
        if self.findDlg is not None:
            self.OnFindClose(None)

    def OnFindClose(self, event):
        self.findDlg.Destroy()
        self.findDlg = None
    def OnFileHistory(self, evt=None):
        # get the file based on the menu ID
        fileNum = evt.GetId() - wx.ID_FILE1
        path = self.fileHistory.GetHistoryFile(fileNum)
        self.setCurrentDoc(path)#load the file
        # add it back to the history so it will be moved up the list
        self.fileHistory.AddFileToHistory(path)

    def gotoLine(self, filename=None, line=0):
        #goto a specific line in a specific file and select all text in it
        self.setCurrentDoc(filename)
        self.currentDoc.EnsureVisible(line)
        self.currentDoc.GotoLine(line)
        endPos = self.currentDoc.GetCurrentPos()

        self.currentDoc.GotoLine(line-1)
        stPos = self.currentDoc.GetCurrentPos()

        self.currentDoc.SetSelection(stPos,endPos)

    def getOpenFilenames(self):
        """Return the full filename of each open tab"""
        names=[]
        for ii in range(self.notebook.GetPageCount()):
            names.append(self.notebook.GetPage(ii).filename)
        return names

    def quit(self, event):
        self.app.quit()
    def checkSave(self):
        """Loop through all open files checking whether they need save
        """
        for ii in range(self.notebook.GetPageCount()):
            doc = self.notebook.GetPage(ii)
            filename=doc.filename
            if doc.UNSAVED:
                self.notebook.SetSelection(ii) #fetch that page and show it
                #make sure frame is at front
                self.Show(True)
                self.Raise()
                self.app.SetTopWindow(self)
                #then bring up dialog
                dlg = dialogs.MessageDialog(self,message=_translate('Save changes to %s before quitting?') %filename, type='Warning')
                resp = dlg.ShowModal()
                sys.stdout.flush()
                dlg.Destroy()
                if resp  == wx.ID_CANCEL:
                    return 0 #return, don't quit
                elif resp == wx.ID_YES:
                    self.fileSave() #save then quit
                elif resp == wx.ID_NO:
                    pass #don't save just quit
        return 1

    def closeFrame(self, event=None, checkSave=True):
        """Close open windows, update prefs.appData (but don't save) and either
        close the frame or hide it
        """
        if len(self.app.builderFrames)==0 and sys.platform!='darwin':
            if not self.app.quitting:
                self.app.quit(event) #send the event so it can be vetoed if neded
                return#app.quit() will have closed the frame already

        if checkSave:
            if self.checkSave()==0:#check all files before initiating close of any
                return 0 #this signals user cancelled

        wasShown = self.IsShown()
        self.Hide()#ugly to see it close all the files independently

        sys.stdout = self._origStdOut#discovered during __init__
        sys.stderr = self._origStdErr

        #store current appData
        self.appData['prevFiles'] = []
        currFiles = self.getOpenFilenames()
        for thisFileName in currFiles:
            self.appData['prevFiles'].append(thisFileName)
        #get size and window layout info
        if self.IsIconized():
            self.Iconize(False)#will return to normal mode to get size info
            self.appData['state']='normal'
        elif self.IsMaximized():
            self.Maximize(False)#will briefly return to normal mode to get size info
            self.appData['state']='maxim'
        else:
            self.appData['state']='normal'
        self.appData['auiPerspective'] = self.paneManager.SavePerspective()
        self.appData['winW'], self.appData['winH']=self.GetSize()
        self.appData['winX'], self.appData['winY']=self.GetPosition()
        if sys.platform=='darwin':
            self.appData['winH'] -= 39#for some reason mac wxpython <=2.8 gets this wrong (toolbar?)
        self.appData['fileHistory']=[]
        for ii in range(self.fileHistory.GetCount()):
            self.appData['fileHistory'].append(self.fileHistory.GetHistoryFile(ii))

        self.paneManager.UnInit()#as of wx3.0 the AUI manager needs to be uninitialised explicitly

        self.app.allFrames.remove(self)
        self.Destroy()
        self.app.coder=None

    def filePrint(self, event=None):
        pr = Printer()
        docName = self.currentDoc.filename
        text = open(docName, 'r').read()
        pr.Print(text, docName)

    def fileNew(self, event=None, filepath=""):
        self.setCurrentDoc(filepath)
    def fileReload(self, event, filename=None, checkSave=False):
        if filename is None:
            return # should raise an exception

        docId = self.findDocID(filename)

        if docId == -1:
            return

        doc = self.notebook.GetPage(docId)

        # is the file still there
        if os.path.isfile(filename):
            doc.SetText(open(filename).read().decode('utf8'))
            doc.fileModTime = os.path.getmtime(filename)
            doc.EmptyUndoBuffer()
            doc.Colourise(0, -1)
            doc.UNSAVED = False
        else:
            # file was removed after we found the changes, lets keep give the user
            # a chance to save his file.
            self.UNSAVED = True

        # if this is the active document we
        if doc == self.currentDoc:
            self.toolbar.EnableTool(self.IDs.tbFileSave, doc.UNSAVED)


    def findDocID(self, filename):
        #find the ID of the current doc
        for ii in range(self.notebook.GetPageCount()):
            if self.notebook.GetPage(ii).filename == filename:
                return ii
        return -1
    def setCurrentDoc(self, filename, keepHidden=False):
        #check if this file is already open
        docID=self.findDocID(filename)
        if docID>=0:
            self.currentDoc = self.notebook.GetPage(docID)
            self.notebook.SetSelection(docID)
        else:#create new page and load document
            #if there is only a placeholder document then close it
            if len(self.getOpenFilenames())==1 and len(self.currentDoc.GetText())==0 and \
                    self.currentDoc.filename.startswith('untitled'):
                self.fileClose(self.currentDoc.filename)

            #create an editor window to put the text in
            p = self.currentDoc = CodeEditor(self.notebook,-1, frame=self)

            #load text from document
            if os.path.isfile(filename):
                with open(filename, 'rU') as f:
                    self.currentDoc.SetText(f.read().decode('utf8'))
                    self.currentDoc.newlines = f.newlines
                self.currentDoc.fileModTime = os.path.getmtime(filename)
                self.fileHistory.AddFileToHistory(filename)
            else:
                self.currentDoc.SetText("")
            self.currentDoc.EmptyUndoBuffer()
            self.currentDoc.Colourise(0, -1)

            # line numbers in the margin
            self.currentDoc.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
            self.currentDoc.SetMarginWidth(1, 32)
            #set name for an untitled document
            if filename=="":
                filename=shortName='untitled.py'
                allFileNames=self.getOpenFilenames()
                n=1
                while filename in allFileNames:
                    filename=shortName='untitled%i.py' %n
                    n+=1
            else:
                path, shortName = os.path.split(filename)
            self.notebook.AddPage(p, shortName)
            if isinstance(self.notebook, wx.Notebook):
                self.notebook.ChangeSelection(len(self.getOpenFilenames())-1)
            elif isinstance(self.notebook, wx.aui.AuiNotebook):
                self.notebook.SetSelection(len(self.getOpenFilenames())-1)
            self.currentDoc.filename=filename
            self.setFileModified(False)
            self.currentDoc.SetFocus()
        self.SetLabel('%s - PsychoPy Coder' %self.currentDoc.filename)
        if analyseAuto and len(self.getOpenFilenames())>0:
            self.SetStatusText(_translate('Analyzing code'))
            self.currentDoc.analyseScript()
            self.SetStatusText('')
        if not keepHidden:
            self.Show()#if the user had closed the frame it might be hidden
    def fileOpen(self, event):
        #get path of current file (empty if current file is '')
        if hasattr(self.currentDoc, 'filename'):
            initPath = os.path.split(self.currentDoc.filename)[0]
        else:
            initPath=''
        dlg = wx.FileDialog(
            self, message=_translate("Open file ..."),
            defaultDir=initPath, style=wx.OPEN
            )

        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            self.SetStatusText(_translate('Loading file'))
            if os.path.isfile(newPath):
                if newPath.lower().endswith('.psyexp'):
                    self.app.newBuilderFrame(fileName=newPath)
                else:
                    self.setCurrentDoc(newPath)
                    self.setFileModified(False)

        self.SetStatusText('')
        #self.fileHistory.AddFileToHistory(newPath)#thisis done by setCurrentDoc
    def expectedModTime(self, doc):
        # check for possible external changes to the file, based on mtime-stamps
        if doc is None:
            return True#we have no file loaded
        if not os.path.exists(doc.filename): # files that don't exist DO have the expected mod-time
            return True
        actualModTime = os.path.getmtime(doc.filename)
        expectedModTime = doc.fileModTime
        if actualModTime != expectedModTime:
            print 'File %s modified outside of the Coder (IDE).' % doc.filename
            return False
        return True

    def fileSave(self,event=None, filename=None, doc=None):
        """Save a ``doc`` with a particular ``filename``.
        If ``doc`` is ``None`` then the current active doc is used. If the ``filename`` is
        ``None`` then the ``doc``'s current filename is used or a dlg is presented to
        get a new filename.
        """
        if self.currentDoc.AutoCompActive():
            self.currentDoc.AutoCompCancel()

        if doc is None:
            doc=self.currentDoc
        if filename is None:
            filename = doc.filename
        if filename.startswith('untitled'):
            self.fileSaveAs(filename)
            #self.setFileModified(False) # done in save-as if saved; don't want here if not saved there
        else:
            # here detect odd conditions, and set failToSave = True to try 'Save-as' rather than 'Save'
            failToSave = False
            if not self.expectedModTime(doc) and os.path.exists(doc.filename):
                dlg = dialogs.MessageDialog(self,
                        message=_translate("File appears to have been modified outside of PsychoPy:\n   %s\nOK to overwrite?") % (os.path.basename(doc.filename)),
                        type='Warning')
                if dlg.ShowModal() != wx.ID_YES:
                    print "'Save' was canceled.",
                    failToSave = True
                try: dlg.destroy()
                except: pass
            if os.path.exists(doc.filename) and not os.access(doc.filename,os.W_OK):
                dlg = dialogs.MessageDialog(self,
                        message=_translate("File '%s' lacks write-permission:\nWill try save-as instead.") % (os.path.basename(doc.filename)),
                        type='Info')
                dlg.ShowModal()
                failToSave = True
                try: dlg.destroy()
                except: pass
            try:
                if failToSave: raise
                self.SetStatusText(_translate('Saving file'))
                newlines = None # system default, os.linesep
                try:
                    # this will fail when doc.newlines was not set (new file)
                    if self.prefs['newlineConvention'] == 'keep':
                        if doc.GetText().lstrip(u'\ufeff').startswith("#!"):
                            # document has shebang (ignore byte-order-marker)
                            newlines = '\n'
                        elif doc.newlines == '\r\n':
                            # document had '\r\n' newline on load
                            newlines = '\r\n'
                        else:
                            # None, \n, tuple
                            newlines = '\n'
                    elif self.prefs['newlineConvention'] == 'dos':
                        newlines = '\r\n'
                    elif self.prefs['newlineConvention'] == 'unix':
                        newlines = '\n'
                except:
                    pass

                with io.open(filename,'w', encoding='utf-8', newline=newlines) as f:
                    f.write(doc.GetText())
                self.setFileModified(False)
                doc.fileModTime = os.path.getmtime(filename) # JRG
            except:
                print "Unable to save %s... trying save-as instead." % os.path.basename(doc.filename)
                self.fileSaveAs(filename)

        if analyseAuto and len(self.getOpenFilenames())>0:
            self.SetStatusText(_translate('Analyzing current source code'))
            self.currentDoc.analyseScript()
        #reset status text
        self.SetStatusText('')
        self.fileHistory.AddFileToHistory(filename)

    def fileSaveAs(self,event, filename=None, doc=None):
        """Save a ``doc`` with a new ``filename``, after presenting a dlg to get a new
        filename.

        If ``doc`` is ``None`` then the current active doc is used.

        If the ``filename`` is not ``None`` then this will be the initial value
        for the filename in the dlg.
        """
        #cancel autocomplete if active
        if self.currentDoc.AutoCompActive():
            self.currentDoc.AutoCompCancel()

        if doc is None:
            doc = self.currentDoc
            docId=self.notebook.GetSelection()
        else:
            docId = self.findDocID(doc.filename)
        if filename is None:
            filename = doc.filename
        initPath, filename = os.path.split(filename)#if we have an absolute path then split it
        #set wildcards
        if sys.platform=='darwin':
            wildcard=_translate("Python scripts (*.py)|*.py|Text file (*.txt)|*.txt|Any file (*.*)|*")
        else:
            wildcard=_translate("Python scripts (*.py)|*.py|Text file (*.txt)|*.txt|Any file (*.*)|*.*")
        #open dlg
        dlg = wx.FileDialog(
            self, message=_translate("Save file as ..."), defaultDir=initPath,
            defaultFile=filename, style=wx.SAVE, wildcard=wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            # if the file already exists, query whether it should be overwritten (default = yes)
            dlg2 = dialogs.MessageDialog(self,
                        message=_translate("File '%s' already exists.\n    OK to overwrite?") % (newPath),
                        type='Warning')
            if not os.path.exists(newPath) or dlg2.ShowModal() == wx.ID_YES:
                doc.filename = newPath
                self.fileSave(event=None, filename=newPath, doc=doc)
                path, shortName = os.path.split(newPath)
                self.notebook.SetPageText(docId, shortName)
                self.setFileModified(False)
                doc.fileModTime = os.path.getmtime(doc.filename) # JRG: 'doc.filename' should = newPath = dlg.getPath()
                try: dlg2.destroy()
                except: pass
            else:
                print "'Save-as' canceled; existing file NOT overwritten.\n"
        try: #this seems correct on PC, but can raise errors on mac
            dlg.destroy()
        except:
            pass
    def fileClose(self, event, filename=None, checkSave=True):
        if self.currentDoc is None:
            self.closeFrame()  # so a coder window with no files responds like the builder window to self.keys.close
            return
        if filename is None:
            filename = self.currentDoc.filename
        self.currentDoc = self.notebook.GetPage(self.notebook.GetSelection())
        if self.currentDoc.UNSAVED and checkSave:
            sys.stdout.flush()
            dlg = dialogs.MessageDialog(self,message=_translate('Save changes to %s before quitting?') %filename,type='Warning')
            resp = dlg.ShowModal()
            sys.stdout.flush()
            dlg.Destroy()
            if resp  == wx.ID_CANCEL:
                return -1 #return, don't quit
            elif resp == wx.ID_YES:
                #save then quit
                self.fileSave(None)
            elif resp == wx.ID_NO:
                pass #don't save just quit
        #remove the document and its record
        currId = self.notebook.GetSelection()
        #if this was called by AuiNotebookEvent, then page has closed already
        if not isinstance(event, wx.aui.AuiNotebookEvent):
            self.notebook.DeletePage(currId)
            newPageID = self.notebook.GetSelection()
        else:
            newPageID = self.notebook.GetSelection()-1
        #set new current doc
        if newPageID <0:
            self.currentDoc = None
            self.SetLabel("PsychoPy v%s (Coder)" %self.app.version)
        else:
            self.currentDoc = self.notebook.GetPage(newPageID)
            self.setFileModified(self.currentDoc.UNSAVED)#set to current file status
        #return 1
    def _runFileAsImport(self):
        fullPath = self.currentDoc.filename
        path, scriptName = os.path.split(fullPath)
        importName, ext = os.path.splitext(scriptName)
        #set the directory and add to path
        os.chdir(path)  # try to rewrite to avoid doing chdir in the coder
        sys.path.insert(0, path)

        #update toolbar
        self.toolbar.EnableTool(self.IDs.tbRun,False)
        self.toolbar.EnableTool(self.IDs.tbStop,True)

        #do an 'import' on the file to run it
        if importName in sys.modules: #delete the sys reference to it (so we think its a new import)
            sys.modules.pop(importName)
        exec('import %s' %(importName)) #or run first time


    def _runFileInDbg(self):
        #setup a debugger and then runFileAsImport
        fullPath = self.currentDoc.filename
        path, scriptName = os.path.split(fullPath)
        #importName, ext = os.path.splitext(scriptName)
        #set the directory and add to path
        os.chdir(path)  # try to rewrite to avoid doing chdir in the coder

        self.db = PsychoDebugger()
        #self.db.set_break(fullPath, 8)
        #print self.db.get_file_breaks(fullPath)
        self.db.runcall(self._runFileAsImport)

    def _runFileAsProcess(self):
        fullPath = self.currentDoc.filename
        path, scriptName = os.path.split(fullPath)
        #importName, ext = os.path.splitext(scriptName)
        #set the directory and add to path
        os.chdir(path)  # try to rewrite to avoid doing chdir in the coder; do through wx.Shell?
        self.scriptProcess=wx.Process(self) #self is the parent (which will receive an event when the process ends)
        self.scriptProcess.Redirect()#catch the stdout/stdin

        if sys.platform=='win32':
            command = '"%s" -u "%s"' %(sys.executable, fullPath)# the quotes allow file paths with spaces
            #self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC, self.scriptProcess)
            self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC| wx.EXEC_NOHIDE, self.scriptProcess)
        else:
            fullPath = fullPath.replace(' ','\ ')
            pythonExec = sys.executable.replace(' ','\ ')
            command = '%s -u %s' %(pythonExec, fullPath)# the quotes would break a unix system command
            self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC, self.scriptProcess)
        self.toolbar.EnableTool(self.IDs.tbRun,False)
        self.toolbar.EnableTool(self.IDs.tbStop,True)

    def runFile(self, event):
        """Runs files by one of various methods
        """
        fullPath = self.currentDoc.filename
        filename = os.path.split(fullPath)[1]
        #does the file need saving before running?
        if self.currentDoc.UNSAVED:
            sys.stdout.flush()
            dlg = dialogs.MessageDialog(self,message=_translate('Save changes to %s before running?') %filename,type='Warning')
            resp = dlg.ShowModal()
            sys.stdout.flush()
            dlg.Destroy()
            if resp  == wx.ID_CANCEL: return -1 #return, don't run
            elif resp == wx.ID_YES: self.fileSave(None)#save then run
            elif resp == wx.ID_NO:   pass #just run

        if sys.platform in ['darwin']:
            print "\033" #restore normal text color for coder output window (stdout); doesn't fix the issue
        else:
            print

        #check syntax by compiling - errors printed (not raised as error)
        try:
            py_compile.compile(fullPath, doraise=False)
        except Exception, e:
            print "Problem compiling: %s" %e

        #provide a running... message; long fullPath --> no # are displayed unless you add some manually
        print ("##### Running: %s #####" %(fullPath)).center(80,"#")

        self.ignoreErrors = False
        self.SetEvtHandlerEnabled(False)
        wx.EVT_IDLE(self, None)

        #try to run script
        try:# try to capture any errors in the script
            if runScripts == 'thread':
                self.thread = ScriptThread(target= self._runFileAsImport, gui=self)
                self.thread.start()
            elif runScripts=='process':
                self._runFileAsProcess()

            elif runScripts=='dbg':
                #create a thread and run file as debug within that thread
                self.thread = ScriptThread(target= self._runFileInDbg, gui=self)
                self.thread.start()
            elif runScripts=='import':
                #simplest possible way, but fragile
                #USING import of scripts (clunky)
                if importName in sys.modules: #delete the sys reference to it
                    sys.modules.pop(importName)
                exec('import %s' %(importName)) #or run first time
                    #NB execfile() would be better doesn't run the import statements properly!
                    #functions defined in the script have a separate namespace to the main
                    #body of the script(!?)
                    #execfile(thisFile)
        except SystemExit:#this is used in psychopy.core.quit()
            pass
        except: #report any errors that came up
            if self.ignoreErrors:
                pass
            else:
                #traceback.print_exc()
                #tb = traceback.extract_tb(sys.last_traceback)
                #for err in tb:
                #    print '%s, line:%i,function:%s\n%s' %tuple(err)
                print ''#print a new line

        self.SetEvtHandlerEnabled(True)
        wx.EVT_IDLE(self, self.onIdle)

    def stopFile(self, event):
        self.toolbar.EnableTool(self.IDs.tbRun,True)
        self.toolbar.EnableTool(self.IDs.tbStop,False)
        self.app.terminateHubProcess()
        if runScripts in ['thread','dbg']:
            #killing a debug context doesn't really work on pygame scripts because of the extra
            if runScripts == 'dbg':self.db.quit()
            try:
                pygame.display.quit()#if pygame is running then try to kill it
            except:
                pass
            self.thread.kill()
            self.ignoreErrors = False#stop listening for errors if the script has ended
        elif runScripts=='process':
            success = wx.Kill(self.scriptProcessID,wx.SIGTERM) #try to kill it gently first
            if success[0] != wx.KILL_OK:
                wx.Kill(self.scriptProcessID,wx.SIGKILL) #kill it aggressively


    def copy(self, event):
        foc= self.FindFocus()
        foc.Copy()
        #if isinstance(foc, CodeEditor):
        #    self.currentDoc.Copy()#let the text ctrl handle this
        #elif isinstance(foc, StdOutRich):

    def duplicateLine(self,event):
        self.currentDoc.LineDuplicate()
    def cut(self, event):
        self.currentDoc.Cut()#let the text ctrl handle this
    def paste(self, event):
        foc= self.FindFocus()
        if hasattr(foc, 'Paste'): foc.Paste()
    def undo(self, event):
        self.currentDoc.Undo()
    def redo(self, event):
        self.currentDoc.Redo()
    def commentSelected(self,event):
        self.currentDoc.commentLines()
    def uncommentSelected(self, event):
        self.currentDoc.uncommentLines()
    def foldAll(self, event):
        self.currentDoc.FoldAll()
    #def unfoldAll(self, event):
        #self.currentDoc.ToggleFoldAll(expand = False)
    def setOutputWindow(self, event=None, value=None):
        #show/hide the output window (from the view menu control)
        if value is None:
            value=self.outputChk.IsChecked()
        if value:
            #show the pane
            self.prefs['showOutput']=True
            self.paneManager.GetPane('Shelf').Show()
            #will we actually redirect the output?
            if not self.app.testMode:#don't if we're doing py.tests or we lose the output
                sys.stdout = self.outputWindow
                sys.stderr = self.outputWindow
        else:
            #show the pane
            self.prefs['showOutput']=False
            self.paneManager.GetPane('Shelf').Hide()
            sys.stdout = self._origStdOut#discovered during __init__
            sys.stderr = self._origStdErr
        self.app.prefs.saveUserPrefs()#includes a validation

        self.paneManager.Update()
    def setShowIndentGuides(self, event):
        #show/hide the source assistant (from the view menu control)
        newVal = self.indentGuideChk.IsChecked()
        self.appData['showIndentGuides']=newVal
        for ii in range(self.notebook.GetPageCount()):
            self.notebook.GetPage(ii).SetIndentationGuides(newVal)
    def setShowWhitespace(self, event):
        newVal = self.showWhitespaceChk.IsChecked()
        self.appData['showWhitespace']=newVal
        for ii in range(self.notebook.GetPageCount()):
            self.notebook.GetPage(ii).SetViewWhiteSpace(newVal)
    def setShowEOLs(self, event):
        newVal = self.showEOLsChk.IsChecked()
        self.appData['showEOLs']=newVal
        for ii in range(self.notebook.GetPageCount()):
            self.notebook.GetPage(ii).SetViewEOL(newVal)
    def setSourceAsst(self, event):
        #show/hide the source assistant (from the view menu control)
        if not self.sourceAsstChk.IsChecked():
            self.paneManager.GetPane("SourceAsst").Hide()
            self.prefs['showSourceAsst']=False
        else:
            self.paneManager.GetPane("SourceAsst").Show()
            self.prefs['showSourceAsst']=True
        self.paneManager.Update()
    def analyseCodeNow(self, event):
        self.SetStatusText(_translate('Analyzing code'))
        if self.currentDoc is not None:
            self.currentDoc.analyseScript()
        else:
            print 'Open a file from the File menu, or drag one onto this app, or open a demo from the Help menu'

        self.SetStatusText(_translate('ready'))
    #def setAnalyseAuto(self, event):
        ##set autoanalysis (from the check control in the tools menu)
        #if self.analyseAutoChk.IsChecked():
        #    self.prefs['analyseAuto']=True
        #else:
        #    self.prefs['analyseAuto']=False
    def loadDemo(self, event):
        self.setCurrentDoc( self.demos[event.GetId()] )
    def tabKeyPressed(self,event):
        #if several chars are selected then smartIndent
        #if we're at the start of the line then smartIndent
        if self.currentDoc.shouldTrySmartIndent():
            self.smartIndent(event = None)
        else:
            #self.currentDoc.CmdKeyExecute(wx.stc.STC_CMD_TAB)
            pos = self.currentDoc.GetCurrentPos()
            self.currentDoc.InsertText(pos ,'\t')
            self.currentDoc.SetCurrentPos(pos+1)
            self.currentDoc.SetSelection(pos+1, pos+1)
    def smartIndent(self, event):
        self.currentDoc.smartIndent()
    def indent(self, event):
        self.currentDoc.indentSelection(4)
    def dedent(self, event):
        self.currentDoc.indentSelection(-4)
    def setFileModified(self, isModified):
        #changes the document flag, updates save buttons
        self.currentDoc.UNSAVED=isModified
        self.toolbar.EnableTool(self.IDs.tbFileSave, isModified)#disabled when not modified
        #self.fileMenu.Enable(self.fileMenu.FindItem('&Save\tCtrl+S"'), isModified)
    def onProcessEnded(self, event):
        self.onIdle(event=None)#this is will check the stdout and stderr for any last messages
        self.scriptProcess=None
        self.scriptProcessID=None
        self.toolbar.EnableTool(self.IDs.tbRun,True)
        self.toolbar.EnableTool(self.IDs.tbStop,False)
    def onURL(self, evt):
        """decompose the URL of a file and line number"""
        # "C:\\Program Files\\wxPython2.8 Docs and Demos\\samples\\hangman\\hangman.py", line 21,
        tmpFilename, tmpLineNumber = evt.GetString().rsplit('", line ',1)
        filename = tmpFilename.split('File "',1)[1]
        lineNumber = int(tmpLineNumber.split(',')[0])
        self.gotoLine(filename,lineNumber)
    def onUnitTests(self, evt=None):
        """Show the unit tests frame
        """
        if self.unitTestFrame:
            self.unitTestFrame.Raise()
        else:
            self.unitTestFrame=UnitTestFrame(app = self.app)
#        UnitTestFrame.Show()
