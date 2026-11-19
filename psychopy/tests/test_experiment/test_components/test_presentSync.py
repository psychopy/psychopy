"""Tests for Components which act at stimulus onset: output Components which
can send data when a frame is presented (`win.callOnPresent`), and timers
reset at the recorded time of a flip (`win.resetClockOnFlip`).
"""
import ast

import pytest

from psychopy.experiment.components.button import ButtonComponent
from psychopy.experiment.components.keyboard import KeyboardComponent
from psychopy.experiment.components.parallelOut import ParallelOutComponent
from psychopy.experiment.components.serialOut import SerialOutComponent
from psychopy.experiment.exports import IndentingBuffer
from psychopy.tests.test_experiment.test_components.test_base_components import \
    BaseComponentTests


def _make(compClass, **params):
    class _Tests(BaseComponentTests):
        comp = compClass

    comp, _, _ = _Tests().make_minimal_experiment()
    for name, val in params.items():
        comp.params[name].val = val
    return comp


def _frameCode(comp):
    buff = IndentingBuffer(target="PsychoPy")
    comp.writeFrameCode(buff)
    code = buff.getvalue()
    ast.parse(code)
    return code


@pytest.mark.parametrize("syncOnset, call", [
    (False, "win.callOnFlip("), (True, "win.callOnPresent("),
])
def test_serial_out_sync_onset(syncOnset, call):
    code = _frameCode(_make(
        SerialOutComponent, syncScreenRefresh=True, syncOnset=syncOnset))
    assert code.count(call) == 2  # start and stop data


def test_serial_out_unsynced_sends_now():
    code = _frameCode(_make(
        SerialOutComponent, syncScreenRefresh=False, syncOnset=True))
    assert "callOnPresent" not in code and "callOnFlip" not in code


@pytest.mark.parametrize("syncOnset, call", [
    (False, "win.callOnFlip("), (True, "win.callOnPresent("),
])
def test_parallel_out_sync_onset(syncOnset, call):
    comp = _make(ParallelOutComponent, syncScreen=True, syncOnset=syncOnset)
    code = _frameCode(comp)
    assert code.count(call) == 2  # start and stop data
    buff = IndentingBuffer(target="PsychoPy")
    comp.writeRoutineEndCode(buff)
    assert call in buff.getvalue()  # stop data at the end of the Routine


@pytest.mark.parametrize("compClass", [SerialOutComponent, ParallelOutComponent])
def test_sync_onset_off_by_default(compClass):
    assert _make(compClass).params['syncOnset'].val is False


@pytest.mark.parametrize("compClass, clockAttr", [
    (KeyboardComponent, "clock"), (ButtonComponent, "buttonClock"),
])
def test_timers_reset_at_flip_time(compClass, clockAttr):
    comp = _make(compClass)
    if 'syncScreenRefresh' in comp.params:
        comp.params['syncScreenRefresh'].val = True
    code = _frameCode(comp)
    name = comp.params['name']
    assert f"win.resetClockOnFlip({name}.{clockAttr})" in code
    assert f"callOnFlip({name}.{clockAttr}.reset)" not in code
