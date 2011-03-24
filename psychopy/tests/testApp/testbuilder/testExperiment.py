import psychopy.app.builder.experiment
from os import path, unlink
import os, shutil, glob
import py_compile
import nose

# Jeremy Gray March 2011

exp = psychopy.app.builder.experiment.Experiment()
here = path.abspath(path.dirname(__file__))

def testExp_AddRoutine():
    exp.addRoutine('instructions')
#    exp.routines['instructions'].AddComponent(
#    exp.Add


def testExp_LoadCompileSavePsyexpFiles():
    """ copy .psyexp demos -> import XML -> lastrun.py -> py_compile to .pyc
    """
    # avoid redundant psyexp scripts; make temp copies of builder demos:
    tmp_dir = path.join(here, 'tmp_load_compile_psyexp')
    tmp_file = path.join(tmp_dir, 'tmp_lastrun.py')
    shutil.rmtree(tmp_dir, ignore_errors=True) # start clean
    os.mkdir(tmp_dir) # muck about in here
    for root, dirs, files in os.walk(path.join(tmp_dir, '../../../../demos/builder')):
        for psy_exp in [f for f in files if f.endswith('.psyexp')]:
            shutil.copyfile(path.join(root, psy_exp), path.join(tmp_dir, psy_exp))
    test_psyexp = glob.glob(path.join(tmp_dir, '*.psyexp')) + glob.glob(path.join(here, '*.psyexp'))
    if len(test_psyexp) == 0:
        # need something to test; found no demos, maybe its a path error here in the test
        raise nose.plugins.skip.SkipTest
    for file in test_psyexp:
        if file.find('bart.psyexp') > -1: continue # ; bart.psyexp had a unicode char -> error
        # go from psyexp file on disk to internal builder representation:
        exp.loadFromXML(path.join(here, file))
        assert len(exp.namespace.user) # should automatically populate the namespace
        assert not exp.namespace.get_collisions() # ... without duplicates
        # from there generate a script:
        buff = exp.writeScript() # is a StringIO object
        script = buff.getvalue()
        assert len(str(script))
        # save the script:
        f = open(tmp_file, 'wb+')
        f.write(script)
        f.close()
        # compile the temp file, catching error msgs (including no file at all):
        py_compile.compile(tmp_file, doraise=True)
    shutil.rmtree(tmp_dir, ignore_errors=True)
        
def testExp_NameSpace():
    assert exp.namespace.exists('psychopy') == "Psychopy module"
    
    exp.namespace.add('foo')
    assert exp.namespace.exists('foo') == "script variable"
    exp.namespace.add('foo')
    assert exp.namespace.get_collisions() == ['foo']
    
    assert not exp.namespace.is_valid('123')
    assert not exp.namespace.is_valid('a1 23')
    assert not exp.namespace.is_valid('a123$')
    
    assert exp.namespace.make_valid('123') == 'var_123'
    assert exp.namespace.make_valid('a a a') == 'a_a_a'
    exp.namespace.add('b')
    assert exp.namespace.make_valid('b') == 'b_2'
    
    assert exp.namespace.make_loop_index('trials') == 'thisTrial'
    assert exp.namespace.make_loop_index('trials_2') == 'thisTrial_2'
    assert exp.namespace.make_loop_index('stimuli') == 'thisStimulus'
    