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
        self.known_diffs_file = path.join(self.here, 'known_py_diffs.txt')
        self.new_diff_file    = path.join(self.here, 'tmp_py_diff.tmp')
        
    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        pass
    
    def _file_diff_len(self, file1, file2):
        f1 = len(open(file1).readlines())
        f2 = len(open(file2).readlines())
        d = os.popen('diff -c '+file1+' '+file2).readlines()
        d2 = len([x for x in d if x.startswith('!')]) / 2.  # count of differing lines
        return f1, f2, d2
        
    def _loadSave(self, file):
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
    
    def testExp_LoadCompilePsyexp(self):
        # discover & copy .psyexp demos -> (import XML -> lastrun.py -> py_compile to .pyc)
        # checks:
        # - valid syntax (during _compile)
        # - load->save->load-> consistency
        # - namespace on load from psyexp
        exp = self.exp
        
        # make temp copies of all builder demos:
        for root, dirs, files in os.walk(path.join(exp.prefsPaths['demos'], 'builder')):
            for f in files:
                if f.endswith('.psyexp') and not f.startswith('bart'):
                    shutil.copyfile(path.join(root, f), path.join(self.tmp_dir, f))
        # plus any psyexp in 'here' (testExperiment dir)
        for f in glob.glob(path.join(self.here, '*.psyexp')):
            shutil.copyfile(f, path.join(self.tmp_dir, os.path.basename(f)))
        
        test_psyexp = list(glob.glob(path.join(self.tmp_dir, '*.psyexp')))
        if len(test_psyexp) == 0:
            raise nose.plugins.skip.SkipTest, "No test .psyexp files found (no Builder demos??)"
        
        known_diffs = open(self.known_diffs_file).read()
        diff_in_file_py = ''
        patch = open(self.new_diff_file, 'wb+') # a debug file, with patch info (how two files differ)
        for file in test_psyexp:
            # first load-save:
            file_py, file_psyexp = self._loadSave(file)
            file_pyc = self._compile(file_py)
            sha1_first = sha1hex(file_pyc, file=True)
            
            # second load-save:
            file2_py, file2_psyexp = self._loadSave(file_psyexp)
            file2_pyc = self._compile(file2_py)
            sha1_second = sha1hex(file2_pyc, file=True) # ? need same file name prior to py_compile?
            
            # check for differences:
            patch.write('l1 l2 #diff!: %d  %d  %d' % self._file_diff_len(file_py,file2_py) +
                        '  %s\n' % os.path.basename(file) )
            diff_py = os.popen('diff -c ' + file_py + ' ' + file2_py).read()
            diff_py = '\n'.join(diff_py.splitlines()[2:])
                # first two lines have current time -> fail to match cached, so ignore the lines
            if len(diff_py) and known_diffs.find(diff_py) == -1:
                diff_in_file_py += ' ' + os.path.basename(file) # used for assert
                patch.write(os.path.basename(file) + ' load-save difference in resulting .py files:\n' + diff_py + '\n\n')
            
            diff_psyexp = os.popen('diff -c ' + file_psyexp + ' ' + file2_psyexp).read().strip()
            #assert not diff_psyexp # fails for most demos
            
            diff_pyc = (sha1_first != sha1_second)
            #if diff_pyc:
            #    patch.write(os.path.basename(file) + ': sha1 mismatch for .pyc files:\n' + sha1_first +'   '+ sha1_second + '\n')
        patch.close()
        assert not diff_in_file_py ### see known_py_diffs.txt for viewing and using the diff ###
    
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
            