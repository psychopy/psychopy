import ast
import inspect

import esprima
import pytest

from psychopy.experiment.components.sound import SoundComponent
from psychopy.experiment.exports import IndentingBuffer
from psychopy.sound._base import _SoundBase
from psychopy.tests.test_experiment.test_components.test_base_components import \
    BaseComponentTests

# stopVal -> the secs the Sound should get: short durations are passed on so a
# tone fades out at that length, anything else plays until stopped (-1)
SECS_CASES = [
    ("1.0", 1.0),        # a short duration
    ("", -1),            # blank: the duration of the media
    ("5", -1),           # longer than 2 s: stopped by the Component
    ("$dur", -1),        # a variable: not known when the script is written
]


class TestSoundComponent(BaseComponentTests):
    comp = SoundComponent

    def _make(self, stopVal):
        comp, rt, exp = self.make_minimal_experiment()
        comp.params['stopVal'].val = stopVal
        return comp

    def _writeUpdate(self, comp, target, updateType="set every repeat"):
        """Code written to update the sound param, e.g. at Routine start."""
        buff = IndentingBuffer(target=target)
        comp.writeParamUpdate(
            buff, comp.params['name'], 'sound', comp.params['sound'],
            updateType, target=target)
        return buff.getvalue()

    @staticmethod
    def _parseCall(code, func):
        """The keyword args of the first call to ``func`` in Python ``code``,
        which must parse."""
        for node in ast.walk(ast.parse(code)):
            if isinstance(node, ast.Call) and getattr(node.func, 'attr', None) == func:
                return {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords
                        if isinstance(kw.value, (ast.Constant, ast.UnaryOp))}, node
        raise AssertionError(f"no call to {func} in:\n{code}")

    @pytest.mark.parametrize("stopVal, secs", SECS_CASES)
    def test_set_sound_python(self, stopVal, secs):
        """The Python update must be valid code, call setSound with arguments
        every backend accepts, and give the same secs as the init code."""
        comp = self._make(stopVal)
        kwargs, call = self._parseCall(self._writeUpdate(comp, "PsychoPy"), "setSound")
        # arguments accepted by setSound (e.g. log=, not logging=)
        inspect.signature(_SoundBase.setSound).bind(
            None, *call.args, **{kw.arg: None for kw in call.keywords})
        assert kwargs["secs"] == secs

        init = IndentingBuffer(target="PsychoPy")
        comp.writeInitCode(init)
        initKwargs, _ = self._parseCall(init.getvalue(), "Sound")
        assert initKwargs["secs"] == secs

    def test_set_sound_every_frame_does_not_log(self):
        kwargs, _ = self._parseCall(
            self._writeUpdate(self._make("1.0"), "PsychoPy", "set every frame"),
            "setSound")
        assert kwargs["log"] is False

    @pytest.mark.parametrize("stopVal, secs", SECS_CASES)
    def test_set_sound_js(self, stopVal, secs):
        """The JS update must be valid code and give the same secs as the init
        code."""
        comp = self._make(stopVal)
        code = self._writeUpdate(comp, "PsychoJS")
        esprima.parseScript(code)  # raises on a syntax error
        assert f"{comp.params['name']}.secs = {secs};" in code

        init = IndentingBuffer(target="PsychoJS")
        comp.writeInitCodeJS(init)
        assert f"secs: {secs}," in init.getvalue()
