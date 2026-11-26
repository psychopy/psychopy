import pytest
from psychopy import data, experiment
from psychopy.contrib.configobj.validate import dottedQuadToNum, numToDottedQuad
from psychopy.contrib.javascripthon import translates
from psychopy.experiment.exports import IndentingBuffer
from psychopy.sound.microphone import Microphone


def test_trialhandler2_get_earlier_trial():
    conds = [{"stim": "a"}, {"stim": "b"}, {"stim": "c"}]
    th = data.TrialHandler2(conds, nReps=1, method="sequential")

    # Before any trial has elapsed, must return None rather than raising IndexError
    assert th.getEarlierTrial(-1) is None
    assert th.getEarlierTrial(1) is None

    next(th)  # trial 0 ('a') is active; no trials have elapsed yet
    assert th.getEarlierTrial(-1) is None

    next(th)  # trial 1 ('b') is active; trial 0 ('a') is in elapsedTrials
    assert th.getEarlierTrial(-1)["stim"] == "a"
    assert th.getEarlierTrial(1)["stim"] == "a"
    assert th.getEarlierTrial(-2) is None

    next(th)  # trial 2 ('c') is active; upcomingTrials is now empty
    assert len(th.upcomingTrials) == 0
    assert th.getEarlierTrial(-1)["stim"] == "b"
    assert th.getEarlierTrial(-2)["stim"] == "a"
    assert th.getEarlierTrial(-3) is None


def test_experiment_handler_add_data_row_bounds():
    exp = data.ExperimentHandler(name="boundsTest", savePickle=False, saveWideText=False)
    exp.addData("x", 10)
    exp.nextEntry()
    exp.addData("x", 20)
    exp.nextEntry()
    assert len(exp.entries) == 2

    # Valid positive and negative row indices
    exp.addData("tag", "first", row=0)
    exp.addData("tag", "second", row=-1)
    assert exp.entries[0]["tag"] == "first"
    assert exp.entries[1]["tag"] == "second"

    # Out-of-bounds positive (row == len(entries)) and negative indices must abort cleanly
    exp.addData("oob", 999, row=2)
    exp.addData("oob", 999, row=5)
    exp.addData("oob", 999, row=-3)
    assert all("oob" not in entry for entry in exp.entries)


def test_routine_default_components_not_shared():
    r1 = data.Routine(name="r1")
    r2 = data.Routine(name="r2")
    r1.components.append("dummy_comp")
    assert r2.components == []


def test_settings_write_devices_code_allows_none_thisexp():
    exp = experiment.Experiment()
    exp.settings.params["keyboardBackend"].val = "ioHub"
    exp.settings.params["Save hdf5 file"].val = True
    buff = IndentingBuffer(target="PsychoPy")
    exp.settings.writeDevicesCode(buff)
    code = buff.getvalue()
    assert "thisExp.dataFileName if thisExp is not None else ''" in code


def test_javascripthon_try_reraise_with_finally_return():
    py_src = (
        "def f():\n"
        "    try:\n"
        "        work()\n"
        "    except Exception:\n"
        "        raise\n"
        "    finally:\n"
        "        return 42\n"
    )
    js_src, _ = translates(py_src)
    assert "finally" in js_src
    assert "return 42" in js_src


def test_configobj_validate_num_to_dotted_quad():
    assert numToDottedQuad(0) == "0.0.0.0"
    assert numToDottedQuad(4294967295) == "255.255.255.255"
    num = dottedQuadToNum("192.168.1.100")
    assert numToDottedQuad(num) == "192.168.1.100"
    with pytest.raises(ValueError):
        numToDottedQuad(4294967296)
    with pytest.raises(ValueError):
        numToDottedQuad(-1)


def test_microphone_set_max_recording_size_docstring():
    assert Microphone.setMaxRecordingSize.__doc__ is not None
    assert Microphone.setMaxRecordingSize.__doc__ == Microphone.maxRecordingSize.__doc__
