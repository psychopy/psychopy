from __future__ import print_function
from past.builtins import execfile
from builtins import object

import psychopy.experiment
from psychopy.experiment.components.text import TextComponent
from psychopy.experiment._experiment import RequiredImport
from psychopy.tests.utils import TESTS_FONT
from os import path
import os, shutil, glob, sys
import py_compile
import difflib
from tempfile import mkdtemp
import codecs
from psychopy import core, tests, prefs
import pytest
import locale
from lxml import etree
import numpy
import sys

# Jeremy Gray March 2011

# caveats when comparing files:
# - dicts have no defined order, can load and save differently: use a
#   known-diff file to suppress boring errors.  This situation was
#   addressed in 7e2c72a for stimOut by sorting the keys
# - namespace.makeValid() can change var names from the orig demos,
#   but should not do so from a load-save-load because only the first
#   load should change things

allComponents = psychopy.experiment.getComponents(fetchIcons=False)


def _filterout_legal(lines):
    """Ignore first 5 lines: header info, version, date can differ no problem
    """
    return [line
            for line in lines[5:]
            if not "This experiment was created using PsychoPy3 Experiment Builder (" in line and
            not ("trialList=data.importConditions(" in line and ".xlsx'))" in line)]
        #-This experiment was created using PsychoPy3 Experiment Builder (v1.65.01), August 03, 2011, at 13:14
        #+This experiment was created using PsychoPy3 Experiment Builder (v1.65.02), August 03, 2011, at 13:14
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


class TestExpt(object):
    @classmethod
    def setup_class(cls):
        cls.exp = psychopy.experiment.Experiment() # create once, not every test
        cls.tmp_dir = mkdtemp(prefix='psychopy-tests-app')

    def setup(self):
        """This setup is done for each test individually
        """
        self.here = path.abspath(path.dirname(__file__))
        self.known_diffs_file   = path.join(self.here, 'known_py_diffs.txt')
        self.tmp_diffs_file     = path.join(self.here, 'tmp_py_diffs.txt') # not deleted by mkdtemp cleanup

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_xsd(self):
        # get files

        psyexp_files = []

        for root, dirs, files in os.walk(os.path.join(self.exp.prefsPaths['demos'], 'builder')):
            for f in files:
                if f.endswith('.psyexp'):
                    psyexp_files.append(os.path.join(root, f))

        # get schema

        schema_name = path.join(self.exp.prefsPaths['psychopy'], 'experiment', 'experiment.xsd');
        schema_root = etree.parse(schema_name)
        schema = etree.XMLSchema(schema_root)

        # validate files with schema

        for psyexp_file in psyexp_files:
            project_root = etree.parse(psyexp_file)
            schema.assertValid(project_root)

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
        script = self.exp.writeScript()
        assert len(script) > 1500  # default empty script is ~2200 chars

        # save the script:
        with codecs.open(py_file, 'w', 'utf-8-sig') as f:
            f.write(script)

        return py_file, psyexp_file

    def _checkCompile(self, py_file):
        # compile the temp file to .pyc, catching error msgs
        # (including no file at all):
        py_compile.compile(py_file, doraise=True)
        return py_file + 'c'

    def _checkPyDiff(self, file_py, file2_py):
        """return '' for no meaningful diff, or a diff patch"""

        diff_py_lines = _diff_file(file_py, file2_py)[5:] # ignore first five lines --- +++
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
        if not sys.platform.startswith('win'):
            testlocList = ['en_US', 'en_US.UTF-8', 'ja_JP']
        else:
            testlocList = ['USA', 'JPN']

        for file in test_psyexp:
            # test for any diffs using various locale's:
            for loc in ['en_US', 'ja_JP']:
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
                d = self._checkPyDiff(file_py, file2_py)
                if d:
                    diff_in_file_py += os.path.basename(file) + '::' + d
                #diff_psyexp = _diff_file(file_psyexp,file2_psyexp)[2:]
                #diff_in_file_psyexp += diff_psyexp
                #diff_pyc = (sha1_first != sha1_second)
                #assert not diff_pyc
        #locale.setlocale(locale.LC_ALL,'C')

        assert not diff_in_file_py ### see known_py_diffs.txt; potentially a locale issue? ###
        #assert not diff_in_file_psyexp # was failing most times, uninformative
        #assert not diff_in_file_pyc    # oops, was failing every time despite identical .py file

    def test_future(self):
        """An experiment file with made-up params and routines to see whether
        future versions of experiments will get loaded.
        """
        expfile = path.join(self.exp.prefsPaths['tests'], 'data', 'futureParams.psyexp')
        self.exp.loadFromXML(expfile) # reload the edited file
        # we don't test this script but make sure it builds
        script = self.exp.writeScript(expPath=expfile)
        py_file = os.path.join(self.tmp_dir, 'testFutureFile.py')
        # save the script:
        with codecs.open(py_file, 'w', 'utf-8-sig') as f:
            f.write(script)

        #check that files compiles too
        self._checkCompile(py_file)

    def test_loopBlocks(self):
        """An experiment file with made-up params and routines to see whether
        future versions of experiments will get loaded.
        """
        #load the test experiment (with a stims loop, trials loop and blocks loop)
        expfile = path.join(self.exp.prefsPaths['tests'], 'data', 'testLoopsBlocks.psyexp')
        self.exp.loadFromXML(expfile) # reload the edited file
        #alter the settings so the data goes to our tmp dir
        datafileBase = os.path.join(self.tmp_dir, 'testLoopsBlocks')
        datafileBaseRel = os.path.relpath(datafileBase,expfile)
        self.exp.settings.params['Data filename'].val = repr(datafileBaseRel)
        #write the script from the experiment
        script = self.exp.writeScript(expPath=expfile)
        py_file = os.path.join(self.tmp_dir, 'testLoopBlocks.py')

        # save it
        with codecs.open(py_file, 'w', 'utf-8-sig') as f:
            f.write(script.replace("core.quit()", "pass"))
            f.write("del thisExp\n") #garbage collect the experiment so files are auto-saved

        #run the file (and make sure we return to this location afterwards)
        wd = os.getcwd()
        execfile(py_file)
        os.chdir(wd)
        #load the data
        print("searching..." +datafileBase)
        print(glob.glob(datafileBase+'*'))
        f = open(datafileBase+".csv", 'rb')
        dat = numpy.recfromcsv(f, case_sensitive=True)
        f.close()
        assert len(dat)==8 # because 4 'blocks' with 2 trials each (3 stims per trial)

    def test_Run_FastStroopPsyExp(self):
        # start from a psyexp file, loadXML, execute, get keypresses from a emulator thread
        if sys.platform.startswith('linux'):
            pytest.skip("response emulation thread not working on linux yet")

        expfile = path.join(self.exp.prefsPaths['tests'], 'data', 'ghost_stroop.psyexp')
        with codecs.open(expfile, 'r', encoding='utf-8-sig') as f:
            text = f.read()

        # copy conditions file to tmp_dir
        shutil.copyfile(os.path.join(self.exp.prefsPaths['tests'], 'data', 'ghost_trialTypes.xlsx'),
                        os.path.join(self.tmp_dir,'ghost_trialTypes.xlsx'))

        # edit the file, to have a consistent font:
        text = text.replace("'Arial'", "'" + TESTS_FONT +"'")

        expfile = path.join(self.tmp_dir, 'ghost_stroop.psyexp')
        with codecs.open(expfile, 'w', encoding='utf-8-sig') as f:
            f.write(text)

        self.exp.loadFromXML(expfile)  # reload the edited file
        script = self.exp.writeScript()

        # reposition its window out from under splashscreen (can't do easily from .psyexp):
        script = script.replace('fullscr=False,','pos=(40,40), fullscr=False,')
        # Only log errors.
        script = script.replace('logging.console.setLevel(logging.WARNING',
                                'logging.console.setLevel(logging.ERROR')

        lastrun = path.join(self.tmp_dir, 'ghost_stroop_lastrun.py')
        with codecs.open(lastrun, 'w', encoding='utf-8-sig') as f:
            f.write(script)

        # run:
        stdout, stderr = core.shellCall([sys.executable, lastrun], stderr=True)
        assert not stderr

    def test_Exp_AddRoutine(self):
        self.exp.addRoutine('instructions')

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


class TestExpImports(object):
    def setup(self):
        self.exp = psychopy.experiment.Experiment()
        self.exp.requiredImports = []

    def test_requireImportName(self):
        import_ = RequiredImport(importName='foo', importFrom='',
                                 importAs='')
        self.exp.requireImport(importName='foo')

        assert import_ in self.exp.requiredImports

        script = self.exp.writeScript()
        assert 'import foo\n' in script

    def test_requireImportFrom(self):
        import_ = RequiredImport(importName='foo', importFrom='bar',
                                 importAs='')
        self.exp.requireImport(importName='foo', importFrom='bar')

        assert import_ in self.exp.requiredImports

        script = self.exp.writeScript()
        assert 'from bar import foo\n' in script

    def test_requireImportAs(self):
        import_ = RequiredImport(importName='foo', importFrom='',
                                 importAs='baz')
        self.exp.requireImport(importName='foo', importAs='baz')

        assert import_ in self.exp.requiredImports

        script = self.exp.writeScript()
        assert 'import foo as baz\n' in script

    def test_requireImportFromAs(self):
        import_ = RequiredImport(importName='foo', importFrom='bar',
                                 importAs='baz')
        self.exp.requireImport(importName='foo', importFrom='bar',
                               importAs='baz')

        assert import_ in self.exp.requiredImports

        script = self.exp.writeScript()
        assert 'from bar import foo as baz\n' in script

    def test_requirePsychopyLibs(self):
        import_ = RequiredImport(importName='foo', importFrom='psychopy',
                                 importAs='')
        self.exp.requirePsychopyLibs(['foo'])

        assert import_ in self.exp.requiredImports

        script = self.exp.writeScript()
        assert 'from psychopy import locale_setup, foo\n' in script

    def test_requirePsychopyLibs2(self):
        import_0 = RequiredImport(importName='foo', importFrom='psychopy',
                                  importAs='')
        import_1 = RequiredImport(importName='foo', importFrom='psychopy',
                                  importAs='')
        self.exp.requirePsychopyLibs(['foo', 'bar'])

        assert import_0 in self.exp.requiredImports
        assert import_1 in self.exp.requiredImports

        script = self.exp.writeScript()
        assert 'from psychopy import locale_setup, foo, bar\n' in script

    def test_requireImportAndPsychopyLib(self):
        import_0 = RequiredImport(importName='foo', importFrom='psychopy',
                                  importAs='')
        import_1 = RequiredImport(importName='bar', importFrom='',
                                  importAs='')
        self.exp.requirePsychopyLibs(['foo'])
        self.exp.requireImport('bar')

        assert import_0 in self.exp.requiredImports
        assert import_1 in self.exp.requiredImports

        script = self.exp.writeScript()
        assert 'from psychopy import locale_setup, foo\n' in script
        assert 'import bar\n' in script


class TestRunOnce(object):
    def setup(self):
        self.exp = psychopy.experiment.Experiment()

    def test_runOnceSingleLine(self):
        code = 'foo bar baz'
        self.exp.runOnce(code)
        assert code in self.exp._runOnce

        script = self.exp.writeScript()
        assert code + '\n' in script

    def test_runOnceMultiLine(self):
        code = 'foo bar baz\nbla bla bla'
        self.exp.runOnce(code)
        assert code in self.exp._runOnce

        script = self.exp.writeScript()
        assert code + '\n' in script

    def test_runOnceMultipleStatements(self):
        code_0 = 'foo bar baz'
        self.exp.runOnce(code_0)

        code_1 = 'bla bla bla'
        self.exp.runOnce(code_1)

        assert code_0 in self.exp._runOnce
        assert code_1 in self.exp._runOnce

        script = self.exp.writeScript()
        assert (code_0 + '\n' + code_1 + '\n') in script


class TestDisabledComponents(object):
    def setup(self):
        self.exp = psychopy.experiment.Experiment()
        self.exp.addRoutine(routineName='Test Routine')
        self.routine = self.exp.routines['Test Routine']
        self.exp.flow.addRoutine(self.routine, 0)

    def test_component_not_disabled_by_default(self):
        self.text = TextComponent(exp=self.exp, parentName='Test Routine')
        assert self.text.params['disabled'].val is False

    def test_component_is_written_to_script(self):
        self.text = TextComponent(exp=self.exp, parentName='Test Routine')
        self.routine.addComponent(self.text)
        script = self.exp.writeScript()
        assert 'visual.TextStim' in script

    def test_disabled_component_is_not_written_to_script(self):
        self.text = TextComponent(exp=self.exp, parentName='Test Routine')
        self.text.params['disabled'].val = True

        self.routine.addComponent(self.text)
        script = self.exp.writeScript()
        assert 'visual.TextStim' not in script

    def test_disabling_component_does_not_remove_it_from_original_routine(self):
        self.text = TextComponent(exp=self.exp, parentName='Test Routine')
        self.text.params['disabled'].val = True
        self.routine.addComponent(self.text)

        # This drops the disabled component -- if working correctly, only from
        # a copy though, leaving the original unchanged!
        self.exp.writeScript()

        # Original routine should be unchanged.
        assert self.text in self.routine
