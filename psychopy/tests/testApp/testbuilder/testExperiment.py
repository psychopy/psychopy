import psychopy.app.builder.experiment
from os import path
import os, shutil, glob
import py_compile
import nose
from psychopy.info import _getSha1hexDigest as sha1hex

# Jeremy Gray March 2011

# caveats when comparing files:
# dicts have no defined order, can load and save differently: use a known-diff file to suppress boring errors
# namespace.make_valid() can change var names from the orig demos, but should not do so from a load-save-load
#    because only the first load should change things
# maybe look into python difflib instead of os.popen("diff ...")

exp = psychopy.app.builder.experiment.Experiment()

class TestExpt():
    def setUp(self):
        # something to test:
        self.exp = exp
        
        # dirs and files:
        self.here = path.abspath(path.dirname(__file__))
        self.tmp_dir = path.join(self.here, '.nose.tmp')
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        os.mkdir(self.tmp_dir)
        
    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        pass
    
    def _checkLoadSave(self, file):
        exp = self.exp
        py_file = file+'.py'
        psyexp_file = file+'newXML.psyexp'
            
        # go from psyexp file on disk to internal builder representation:
        exp.loadFromXML(file)
        exp.saveToXML(psyexp_file)
        assert len(exp.namespace.user) # should populate the namespace
        assert not exp.namespace.get_collisions() # ... without duplicates
        
        # generate a script, like 'lastrun.py':
        buff = exp.writeScript() # is a StringIO object
        script = buff.getvalue()
        assert len(str(script)) > 1500 # default empty script is ~2200 chars
        
        # save the script:
        f = open(py_file, 'wb+')
        f.write(script)
        f.close()
        return py_file, psyexp_file
    
    def _compile(self, py_file):
        # compile the temp file to .pyc, catching error msgs (including no file at all):
        py_compile.compile(py_file, doraise=True)
        return py_file + 'c'
    
    def _checkPyDiff(self, file_py, file2_py, known_diffs):
        """return '' for no meaningful diff, or a diff -c patch"""
        # check for differences in lastrun.py versions:
        diff_py_lines = os.popen('diff -c ' + file_py + ' ' + file2_py).readlines()
        if len(diff_py_lines):
            bad_diff = False # not all diffs are bad...
            # different file lengths is a bad sign:
            if len(open(file_py).readlines()) != len(open(file2_py).readlines()):
                bad_diff = True
            # check for mere variation in order within line, if line starts with stimOut=[
            # will fail if there are multiple stimOut lines with different trialLists ==> len(set()) will be > 1 
            if not bad_diff:
                # get all differing lines only, no context:
                diff_py_keylines = [x for x in diff_py_lines if x.startswith('!')] 
                # get only the stimOut lines:
                diff_py_stimOut = [y.replace("'"," ' ").strip() for y in diff_py_keylines
                                     if y.startswith('!     stimOut=[')]
                # stimOut comes from a dict written as a list for trialList, so order can vary, = ok
                diff_py_stimOut_sort = []
                for line in diff_py_stimOut:
                    sp_line = line.split()
                    sp_line.sort() # squash order
                    diff_py_stimOut_sort.append(' '.join(sp_line))
                # for diff lines that start with stimOut, are they all identical except for order of items?
                if len(set(diff_py_stimOut_sort)) > 1: # set() squashes duplicates
                    bad_diff = True
                # are the stimOut lines the only ones that differ? (if so, we're ok)
                if len(diff_py_keylines) != len(diff_py_stimOut):
                    bad_diff = True
            # add another checks here:
            #if not bad_diff:
            #    some_condition = ...
            #    if some_condition:
            #        bad_diff = True
            
            # create a diff file if bad_diff and not already a known-ok-diff:
            if bad_diff:
                diff_py_patch = '\n' + ''.join(diff_py_lines[2:])
                    # NB the first two lines have file names & current time when diff
                    # was run -> will fail to match cached, so ignore them
                if known_diffs.find(diff_py_patch) == -1:
                    patch = open(self.new_diff_file+'_'+os.path.basename(file_py)+'.patch', 'wb+')
                    patch.write(os.path.basename(file_py) + ' load-save difference in resulting .py files:\n' + diff_py_patch + '\n\n')
                    patch.close()
                    
                    return diff_py_patch  # --> final assert will fail
        return ''
    
    def testExp_LoadCompilePsyexp(self):
        """ for each builder demo .psyexp: load-save-load, compile (syntax check), namespace"""
        exp = self.exp
        known_diffs_file   = path.join(self.here, 'known_py_diffs.txt')
        self.new_diff_file = path.join(self.here, 'tmp_py_diff')
        
        # make temp copies of all builder demos:
        for root, dirs, files in os.walk(path.join(exp.prefsPaths['demos'], 'builder')):
            for f in files:
                if f.endswith('.psyexp') and not f.startswith('bart'):
                    shutil.copyfile(path.join(root, f), path.join(self.tmp_dir, f))
        # also copy any psyexp in 'here' (testExperiment dir)
        for f in glob.glob(path.join(self.here, '*.psyexp')):
            shutil.copyfile(f, path.join(self.tmp_dir, os.path.basename(f)))
        test_psyexp = list(glob.glob(path.join(self.tmp_dir, '*.psyexp')))
        if len(test_psyexp) == 0:
            raise nose.plugins.skip.SkipTest, "No test .psyexp files found (no Builder demos??)"
        
        known_diffs = open(known_diffs_file).read()
        diff_in_file_py = '' # will later assert that this is empty
        #diff_in_file_psyexp = ''
        #diff_in_file_pyc = ''
        for file in test_psyexp:
            file_py, file_psyexp = self._checkLoadSave(file)
            file_pyc = self._compile(file_py)
            #sha1_first = sha1hex(file_pyc, file=True)
            
            file2_py, file2_psyexp = self._checkLoadSave(file_psyexp)
            file2_pyc = self._compile(file2_py)
            #sha1_second = sha1hex(file2_pyc, file=True)
            
            # check first against second, filtering out uninteresting diffs; catch diff in any of multiple psyexp files
            diff_in_file_py += self._checkPyDiff(file_py, file2_py, known_diffs)
            #diff_psyexp = os.popen('diff -c ' + file_psyexp + ' ' + file2_psyexp).read().strip()
            #diff_in_file_psyexp += diff_psyexp
            #diff_pyc = (sha1_first != sha1_second)
            #assert not diff_pyc 
        
        assert not diff_in_file_py ### see known_py_diffs.txt for viewing and using the diff ###
        #assert not diff_in_file_psyexp # was failing most times, uninformative
        #assert not diff_in_file_pyc    # oops, was failing every time despite identical .py file
        
    def testExp_AddRoutine(self):
        exp = self.exp
        exp.addRoutine('instructions')
        #exp.routines['instructions'].AddComponent(
        #exp.Add
    
    def testExp_NameSpace(self):
        namespace = self.exp.namespace
        assert namespace.exists('psychopy') == "Psychopy module"
        
        namespace.add('foo')
        assert namespace.exists('foo') == "script variable"
        namespace.add('foo')
        assert namespace.get_collisions() == ['foo']
        
        assert not namespace.is_valid('123')
        assert not namespace.is_valid('a1 23')
        assert not namespace.is_valid('a123$')
        
        assert namespace.make_valid('123') == 'var_123'
        assert namespace.make_valid('123', prefix='wookie') == 'wookie_123'
        assert namespace.make_valid('a a a') == 'a_a_a'
        namespace.add('b')
        assert namespace.make_valid('b') == 'b_2'
        assert namespace.make_valid('a123$') == 'a123_'
        
        assert namespace.make_loop_index('trials') == 'thisTrial'
        assert namespace.make_loop_index('trials_2') == 'thisTrial_2'
        assert namespace.make_loop_index('stimuli') == 'thisStimulus'
            