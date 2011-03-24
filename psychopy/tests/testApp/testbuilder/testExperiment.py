import psychopy.app.builder.experiment
from os import path, unlink
import glob
import popen2

exp = psychopy.app.builder.experiment.Experiment()
here = path.abspath(path.dirname(__file__))

#def shellCall(shellCmd):
#    # this had build problems on mac when in psychopy.core but is preferred way to do things
#    import subprocess, shlex
#    stdoutData, stderrData = subprocess.Popen(shlex.split(shellCmd),
#            stdout=subprocess.PIPE, stderr=subprocess.PIPE ).communicate()
#    return stdoutData.strip(), stderrData.strip()

def shellCall(shellCmd):
    stdO,stdI,stdE = popen2.popen3(shellCmd)
    stdOData = stdO.read().strip()
    stdEData = stdE.read().strip()
    stdO.close()
    stdI.close()
    stdE.close()
    return stdOData, stdEData

def testExperiment_AddRoutine():
    exp.addRoutine('instructions')
#    exp.routines['instructions'].AddComponent(
#    exp.Add


def testExp_LoadCompileSave6psyexpFiles():
    target_file = 'tmp_lastrun.py'
    #demos = here.replace('/tests/testApp/testbuilder', '/demos/builder/*/*.psyexp')
    test_psyexp = glob.glob('*psyexp') 
    assert len(test_psyexp) >= 2 # want 2+ demo psyexp files to test; bart.psyexp had a unicode char -> error
    for file in test_psyexp:
        if file.find('bart.psyexp'): continue
        # go from psyexp file on disk to internal builder representation:
        exp.loadFromXML(path.join(here, file))
        assert len(exp.namespace.user) # should automatically populate the namespace
        assert not exp.namespace.get_collisions() # ... without duplicates
        # from there generate a script:
        buff = exp.writeScript() # as StringIO object
        script = buff.getvalue()
        assert len(str(script))
        # save the script to a tmp file:
        f = open(target_file, 'wb+')
        f.write(script)
        f.close()
        # compile the temp file, catching error msgs:
        #unlink(target_file) # ==> no file -> raise error, good
        stdout_contents, syntax_error = shellCall("python -m py_compile "+target_file)
        assert not stdout_contents   # from: "python -m py_compile tmp_lastrun.p"
        assert not syntax_error  # from: "python -m py_compile tmp_lastrun.py"
        #py_compile.compile(target_file) # fails to catch errors
    #unlink(target_file)
    unlink(target_file+'c')
        
def testExp_NameSpace():
    assert exp.namespace.exists('psychopy') == "Psychopy module"
    
    exp.namespace.add('foo')
    assert exp.namespace.exists('foo') == "script variable"
    exp.namespace.add('foo')
    assert exp.namespace.get_collisions() == ['foo']
    
    assert exp.namespace.make_valid('123') == 'var_123'
    assert exp.namespace.make_valid('a a a') == 'a_a_a'
    exp.namespace.add('b')
    assert exp.namespace.make_valid('b') == 'b_2'
    
    assert exp.namespace.make_loop_index('trials') == 'thisTrial'
    assert exp.namespace.make_loop_index('trials_2') == 'thisTrial_2'
    assert exp.namespace.make_loop_index('stimuli') == 'thisStimulus'
    
