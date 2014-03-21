from psychopy.app import psychopyApp
import psychopy.app.builder.experiment
from os import path
import os, shutil, glob, sys
import py_compile
import difflib
from tempfile import mkdtemp
import codecs
from psychopy import core, tests
import pytest
import locale
import wx
import threading
#from psychopy.info import _getSha1hexDigest as sha1hex

# Jeremy Gray March 2011

# caveats when comparing files:
# - dicts have no defined order, can load and save differently: use a
#   known-diff file to suppress boring errors.  This situation was
#   addressed in 7e2c72a for stimOut by sorting the keys
# - namespace.makeValid() can change var names from the orig demos,
#   but should not do so from a load-save-load because only the first
#   load should change things

allComponents = psychopy.app.builder.experiment.getComponents(fetchIcons=False)

def _filterout_legal(lines):
    return [l
            for l in lines
            if not "This experiment was created using PsychoPy2 Experiment Builder (" in l
            and not ("trialList=data.importConditions(" in l and ".xlsx'))" in l) ]
        #-This experiment was created using PsychoPy2 Experiment Builder (v1.65.01), August 03, 2011, at 13:14
        #+This experiment was created using PsychoPy2 Experiment Builder (v1.65.02), August 03, 2011, at 13:14
        #-    trialList=data.importConditions(u'trialTypes.xlsx'))
        #+    trialList=data.importConditions('trialTypes.xlsx'))
        #-    trialList=data.importConditions(u'mainTrials.xlsx'))
        #+    trialList=data.importConditions('mainTrials.xlsx'))

def _diff(a, b):
    """ diff of strings; returns a generator, 3 lines of context by default, - or + for changes """
    return difflib.unified_diff(a, b)

def _diff_file(a, b):
    """ diff of files read as strings, by line; output is similar to git gui diff """
    diff = _diff(open(a).readlines(), open(b).readlines())
    return list(diff)

class TestExpt():

    @classmethod
    def setup_class(cls):
        # print "D: CREATING THE EXP"
        cls.exp = psychopy.app.builder.experiment.Experiment() # create once, not every test

    def setup(self):
        """This setup is done for each test individually
        """
        self.here = path.abspath(path.dirname(__file__))
        self.known_diffs_file   = path.join(self.here, 'known_py_diffs.txt')
        self.tmp_diffs_file     = path.join(self.here, 'tmp_py_diffs.txt') # not deleted by mkdtemp cleanup
        self.tmp_dir = mkdtemp(prefix='psychopy-tests-app')

    def teardown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_missing_dotval(self):
        """search for a builder component gotcha:
            self.params['x'] when you mean self.params['x'].val
        there could well be instances this does not catch
        """
        # find relevant files -- expect problems only in builder/components/:
        files = []
        for root, dirs, tmpfiles in os.walk(path.join(self.exp.prefsPaths['tests'], 'app', 'builder', 'components')):
            for f in tmpfiles:
                file = path.join(root, f)
                if file.endswith('.py') and not file.endswith(__file__):
                    files.append(file)

        # check each line of each relevant file:
        missing_dotval_count = 0
        for file in files:
            contents = open(r''+file+'', 'r').readlines()
            lines = [line for line in enumerate(contents) if (
                     line[1].find("if self.params[") > -1 # this pattern could miss some things
                     and not (line[1].find('].val') > -1 or line[1].find('].updates') > -1) )
                     ]
            #for num, line in lines:
            #    print file, '#'+str(num+1), line.strip()
            missing_dotval_count += len(lines)

        assert missing_dotval_count == 0  # some suspicious lines were found: "if self.param[]" without .val or .updates

    def _checkLoadSave(self, file):
        exp = self.exp
        py_file = file+'.py'
        psyexp_file = file+'newXML.psyexp'

        # go from psyexp file on disk to internal builder representation:
        self.exp.loadFromXML(file)
        self.exp.saveToXML(psyexp_file)
        assert len(self.exp.namespace.user) # should populate the namespace
        assert not self.exp.namespace.getCollisions() # ... without duplicates

        # generate a script, like 'lastrun.py':
        buff = self.exp.writeScript() # is a StringIO object
        script = buff.getvalue()
        assert len(script) > 1500 # default empty script is ~2200 chars

        # save the script:
        f = codecs.open(py_file, 'w', 'utf-8')
        f.write(script)
        f.close()
        return py_file, psyexp_file

    def _checkCompile(self, py_file):
        # compile the temp file to .pyc, catching error msgs (including no file at all):
        py_compile.compile(py_file, doraise=True)
        return py_file + 'c'

    def _checkPyDiff(self, file_py, file2_py):
        """return '' for no meaningful diff, or a diff patch"""

        diff_py_lines = _diff_file(file_py, file2_py)[2:] # ignore first two lines --- +++
        if not len(diff_py_lines):
            return ''

        bad_diff = False # not all diffs are bad...
        # get all differing lines only, no context:
        f1 = _filterout_legal([x[1:] for x in diff_py_lines if x[0] == '+'])
        f2 = _filterout_legal([x[1:] for x in diff_py_lines if x[0] == '-'])
        if len(f1) != len(f2):
            bad_diff = True
        diff_py_keylines = f1 + f2

        # if line starts with stimOut, check for mere variation in order within line = ok
        #     fails for multiple stimOut lines with diff conditionss ==> len(set()) > 1
        if not bad_diff:
            # get only the stimOut lines, ignore leading whitespace:
            diff_py_stimOut = [y.replace("'", " ' ").strip() for y in diff_py_keylines
                                 if y.lstrip().startswith('stimOut')]
            # in Navon demo, stimOut comes from a dict written as a list, for conditions
            diff_py_stimOut_sort = []
            for line in diff_py_stimOut:
                sp_line = line.split()
                sp_line.sort() # squash order
                diff_py_stimOut_sort.append(' '.join(sp_line))
            # for diff lines that start with stimOut, are they same except order?
            if len(set(diff_py_stimOut_sort)) > 1: # set() squashes duplicates
                bad_diff = True
            # are the stimOut lines the only ones that differ? if so, we're ok
            if len(diff_py_keylines) != len(diff_py_stimOut):
                bad_diff = True

        # add another checks here:
        #if not bad_diff:
        #    some_condition = ...
        #    if some_condition:
        #        bad_diff = True

        # create a patch / diff file if bad_diff and not already a known-ok-diff:
        if bad_diff:
            diff_py_patch = ''.join(diff_py_lines)
            known_diffs = open(self.known_diffs_file).read()
            if known_diffs.find(diff_py_patch) < 0:
                patch = open(self.new_diff_file+'_'+path.basename(file_py)+'.patch', 'wb+')
                patch.write(path.basename(file_py) + ' load-save difference in resulting .py files: '
                            + '-'*15 + '\n' + diff_py_patch+'\n' + '-'*80 +'\n\n')
                patch.close()

                return diff_py_patch  # --> final assert will fail
        return ''

    def test_Exp_LoadCompilePsyexp(self):
        #""" for each builder demo .psyexp: load-save-load, compile (syntax check), namespace"""
        exp = self.exp
        self.new_diff_file = self.tmp_diffs_file

        # make temp copies of all builder demos:
        for root, dirs, files in os.walk(path.join(self.exp.prefsPaths['demos'], 'builder')):
            for f in files:
                if (f.endswith('.psyexp') or
                    f.endswith('.xlsx') or
                    f.endswith('.csv') )\
                    and not f.startswith('bart'):
                        shutil.copyfile(path.join(root, f), path.join(self.tmp_dir, f))
        # also copy any psyexp in 'here' (testExperiment dir)
        #for f in glob.glob(path.join(self.here, '*.psyexp')):
        #    shutil.copyfile(f, path.join(self.tmp_dir, path.basename(f)))
        test_psyexp = list(glob.glob(path.join(self.tmp_dir, '*.psyexp')))
        if len(test_psyexp) == 0:
            pytest.skip("No test .psyexp files found (no Builder demos??)")

        diff_in_file_py = '' # will later assert that this is empty
        #diff_in_file_psyexp = ''
        #diff_in_file_pyc = ''

        #savedLocale = '.'.join(locale.getlocale())
        locale.setlocale(locale.LC_ALL, '') # default
        for file in test_psyexp:
            # test for any diffs using various locale's:
            for loc in ['en_US', 'en_US.UTF-8', 'ru_RU', 'ja_JP']:
                try:
                    locale.setlocale(locale.LC_ALL, loc)
                except locale.Error:
                    continue #skip this locale; it isnt installed
                file_py, file_psyexp = self._checkLoadSave(file)
                file_pyc = self._checkCompile(file_py)
                #sha1_first = sha1hex(file_pyc, file=True)

                file2_py, file2_psyexp = self._checkLoadSave(file_psyexp)
                file2_pyc = self._checkCompile(file2_py)
                #sha1_second = sha1hex(file2_pyc, file=True)

                # check first against second, filtering out uninteresting diffs; catch diff in any of multiple psyexp files
                diff_in_file_py += self._checkPyDiff(file_py, file2_py)
                #diff_psyexp = _diff_file(file_psyexp,file2_psyexp)[2:]
                #diff_in_file_psyexp += diff_psyexp
                #diff_pyc = (sha1_first != sha1_second)
                #assert not diff_pyc
        if self.exp.prefsApp['locale']:
            locale.setlocale(locale.LC_ALL, self.exp.prefsApp['locale'])

        assert not diff_in_file_py ### see known_py_diffs.txt; potentially a locale issue? ###
        #assert not diff_in_file_psyexp # was failing most times, uninformative
        #assert not diff_in_file_pyc    # oops, was failing every time despite identical .py file

    def test_Run_FastStroopPsyExp(self):
        # start from a psyexp file, loadXML, execute, get keypresses from a emulator thread

        pytest.skip()  # test is stalling, hangs up before any text is displayed

        if sys.platform.startswith('linux'):
            pytest.skip("response emulation thread not working on linux yet")

        expfile = path.join(self.exp.prefsPaths['tests'], 'data', 'ghost_stroop.psyexp')
        f = codecs.open(file, 'r', 'utf-8')
        text = f.read()
        f.close()

        # copy conditions file to tmp_dir
        shutil.copyfile(os.path.join(self.exp.prefsPaths['tests'], 'data', 'ghost_trialTypes.xlsx'),
                        os.path.join(self.tmp_dir,'ghost_trialTypes.xlsx'))

        # edit the file, to have a consistent font:
        text = text.replace("'Arial'","'"+tests.utils.TESTS_FONT+"'")
        #text = text.replace("Arial",tests.utils.TESTS_FONT) # fails

        expfile = path.join(self.tmp_dir, 'ghost_stroop.psyexp')
        f = codecs.open(expfile, 'w', 'utf-8')
        f.write(text)
        f.close()

        self.exp.loadFromXML(expfile) # reload the edited file
        lastrun = path.join(self.tmp_dir, 'ghost_stroop_lastrun.py')
        script = self.exp.writeScript(expPath=file)

        # reposition its window out from under splashscreen (can't do easily from .psyexp):
        text = script.getvalue().replace('fullscr=False,','pos=(40,40), fullscr=False,')
        f = codecs.open(lastrun, 'w', 'utf-8')
        f.write(text)
        f.close()

        # run:
        stdout, stderr = core.shellCall('python '+lastrun, stderr=True)
        assert not len(stderr), stderr # print stderr if it's greater than zero

    def test_Exp_AddRoutine(self):
        exp = self.exp
        self.exp.addRoutine('instructions')
        #self.exp.routines['instructions'].AddComponent(
        #self.exp.Add

    def test_Exp_NameSpace(self):
        namespace = self.exp.namespace
        assert namespace.exists('psychopy') == "Psychopy module"

        namespace.add('foo')
        assert namespace.exists('foo') == "one of your Components, Routines, or condition parameters"
        namespace.add('foo')
        assert namespace.getCollisions() == ['foo']

        assert not namespace.isValid('123')
        assert not namespace.isValid('a1 23')
        assert not namespace.isValid('a123$')

        assert namespace.makeValid('123') == 'var_123'
        assert namespace.makeValid('123', prefix='wookie') == 'wookie_123'
        assert namespace.makeValid('a a a') == 'a_a_a'
        namespace.add('b')
        assert namespace.makeValid('b') == 'b_2'
        assert namespace.makeValid('a123$') == 'a123_'

        assert namespace.makeLoopIndex('trials') == 'thisTrial'
        assert namespace.makeLoopIndex('trials_2') == 'thisTrial_2'
        assert namespace.makeLoopIndex('stimuli') == 'thisStimulus'

class Test_ExptComponents():
    """This test fetches all standard components and checks that, with default
    settings, they can be added to a Routine and result in a script that compiles
    """
    def test_all_components(self):
        for compName, compClass in allComponents.items():
            if compName in ['SettingsComponent']:
                continue
            #print "testing with:", compName
            thisComp = compClass(exp=self.exp, parentName='testRoutine', name=compName)
            self._checkCompileWith(thisComp)
    @classmethod
    def setup_class(cls):
        app = psychopyApp._app #this was created already
        app.newBuilderFrame()
        cls.builder = app.builderFrames[-1] # the most recent builder frame created
        cls.exp = cls.builder.exp
        cls.here = path.abspath(path.dirname(__file__))
        cls.tmp_dir = mkdtemp(prefix='psychopy-tests-app')
        cls.exp.addRoutine('testRoutine')
        cls.testRoutine = cls.exp.routines['testRoutine']
        cls.exp.flow.addRoutine(cls.testRoutine, 0)

    def setup(self):
        # dirs and files:
        pass
    def teardown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

#    def _send_OK_after(self):
#        #this is supposed to help with sending button clicks but not working
#        def clickOK():
#            clickEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, wx.ID_OK)
#            self.builder.ProcessEvent(clickEvent)
#            print "D: tried click"
#        wx.CallAfter(clickOK)

    def _checkCompileWith(self, thisComp):
        """Adds the component to the current Routine and makes sure it still
        compiles
        """
        filename = thisComp.params['name'].val+'.py'
        filepath = path.join(self.tmp_dir, filename)

        self.testRoutine.addComponent(thisComp)
        #make sure the mouse code compiles

        # generate a script, similar to 'lastrun.py':
        buff = self.exp.writeScript() # is a StringIO object
        script = buff.getvalue()
        assert len(script) > 1500 # default empty script is ~2200 chars

        # save the script:
        f = codecs.open(filepath, 'w', 'utf-8')
        f.write(script)
        f.close()

        # compile the temp file to .pyc, catching error msgs (including no file at all):
        py_compile.compile(filepath, doraise=True)
        return filepath + 'c'
