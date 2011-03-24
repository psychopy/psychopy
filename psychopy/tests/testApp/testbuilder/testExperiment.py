import psychopy.app.builder.experiment
from os import path, unlink
import glob
import py_compile

# Jeremy Gray March 2011

exp = psychopy.app.builder.experiment.Experiment()
here = path.abspath(path.dirname(__file__))

def testExp_AddRoutine():
    exp.addRoutine('instructions')
#    exp.routines['instructions'].AddComponent(
#    exp.Add


def testExp_LoadCompileSavePsyexpFiles():
    tmp_file = path.join(here, 'tmp_lastrun.py')
    test_psyexp = glob.glob(path.join(here, '*psyexp'))
    assert len(test_psyexp) >= 2 # want 2+ demo psyexp files to test; bart.psyexp had a unicode char -> error
    for file in test_psyexp:
        if file.find('bart.psyexp') > -1: continue
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
    unlink(tmp_file)
    unlink(tmp_file+'c')
        
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
    