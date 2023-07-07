from psychopy.tools import environmenttools as et


globalVal1 = 1
globalVal2 = 2
globalExec1 = 1
globalExec2 = 2


def testGetFromNames():
    # locals set via normal code
    localVal1 = 1
    localVal2 = 2
    assert et.getFromNames(['localVal1', 'localVal2'], locals()) == [1, 2]
    # locals set via exec
    exec("localExec1 = 1")
    exec("localExec2 = 2")
    assert et.getFromNames(['localExec1', 'localExec2'], locals()) == [1, 2]
    # globals set via normal code
    global globalVal1
    global globalVal2
    assert et.getFromNames(['globalVal1', 'globalVal2'], globals()) == [1, 2]
    # globals set via exec
    exec("global globalExec1")
    exec("global globalExec2")
    assert et.getFromNames(['globalExec1', 'globalExec2'], globals()) == [1, 2]

    # nonexistant locals
    assert et.getFromNames(['nonexistantLocal1', 'nonexistantLocal2'], locals()) == ['nonexistantLocal1', 'nonexistantLocal2']
    # nonexistant globals
    assert et.getFromNames(['nonexistantGlobal1', 'nonexistantGlobal2'], globals()) == ['nonexistantGlobal1', 'nonexistantGlobal2']

    # listlike strings
    assert et.getFromNames("localVal1, localVal2", locals()) == [1, 2]
    assert et.getFromNames("(localVal1, localVal2)", locals()) == [1, 2]
    assert et.getFromNames("[localVal1, localVal2]", locals()) == [1, 2]
    assert et.getFromNames("'localVal1', 'localVal2'", locals()) == [1, 2]
    assert et.getFromNames('"localVal1", "localVal2"', locals()) == [1, 2]
    # single name
    assert et.getFromNames("localVal1", locals()) == [1]


def testSetExecEnvironment():
    # globals
    exec = et.setExecEnvironment(globals())
    exec("execEnvGlobalTest = 1")
    assert globals()['execEnvGlobalTest'] == 1

    # locals
    exec = et.setExecEnvironment(locals())
    exec("execLocalTest = 1")
    assert locals()['execLocalTest'] == 1
