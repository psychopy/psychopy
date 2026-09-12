"""Tests that PsychoPy still works when psychtoolbox is not installed.

Psychtoolbox is an optional dependency - it is used for sound and keyboard
response timing, and PsychoPy is expected to fall back to other libraries
(`iohub` or `event` for the keyboard, `sounddevice` for audio) when it is
absent. Nothing in the test suite currently exercises that fallback, because
the usual test environment always has psychtoolbox installed, so it can break
without anyone noticing: `Keyboard.getKeys()` raised `AttributeError:
'KeyboardDevice' object has no attribute '_buffers'` without psychtoolbox for
a long time before it was reported (gh-7493, fixed in gh-7494).

Two scenarios are covered, because they reach different code:

`default`
    `Keyboard()` with no backend requested. The backend is auto-selected and
    settles on `iohub` or `event`, so the psychtoolbox-only attributes are
    never touched.

`ptb_requested`
    `Keyboard(backend='ptb')` while psychtoolbox is missing - what Builder
    generates for someone whose keyboard preference is `ptb` on a machine
    without psychtoolbox. This is the combination behind gh-7493:
    `KeyboardDevice._backend` is assigned from the requested backend, but
    `_buffers` is only created under ``_backend in ['', 'ptb'] and havePTB``,
    while every later use is guarded by the weaker ``_backend == 'ptb'``.
    When those two conditions disagree the attribute is missing.

Each scenario needs its own interpreter. `KeyboardDevice._backend` is a class
attribute that is only assigned on the first construction, so a `Keyboard()`
built earlier in the process would stop a later `backend='ptb'` from taking
effect. A subprocess is needed anyway: by the time the test suite is running,
`psychopy.clock` has already bound `getTime` to `psychtoolbox.GetSecs`, so
hiding the module in-process would neither undo that nor be safe for the
tests that run afterwards.
"""

import subprocess
import sys

import pytest


# Run in a fresh interpreter with psychtoolbox hidden, for the scenario named
# in argv[1]. Each check appends its own name on success, or
# "<name>: <error>" on failure, so a broken fallback is reported precisely
# rather than as a bare non-zero exit.
_CHILD_SCRIPT = '''
import sys

scenario = sys.argv[1]

class BlockPsychtoolbox:
    """Meta path finder which makes `import psychtoolbox` fail."""
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "psychtoolbox" or fullname.startswith("psychtoolbox."):
            raise ModuleNotFoundError("No module named %r (hidden by test)" % fullname)
        return None

sys.meta_path.insert(0, BlockPsychtoolbox())

results = []

def check(name, fn):
    try:
        fn()
    except Exception as err:
        results.append("%s: %s: %s" % (name, type(err).__name__, err))
    else:
        results.append(name)


def exercise_keyboard(backend):
    """Construct a Keyboard and call the methods an experiment would call.

    Several of these iterate `self._buffers`, which is only created on the
    psychtoolbox path, so they are where the fallback is most likely to break.
    """
    from psychopy.hardware import keyboard
    kb = keyboard.Keyboard() if backend is None else keyboard.Keyboard(backend=backend)
    keys = kb.getKeys()
    assert isinstance(keys, (list, tuple)), "getKeys() returned %r" % type(keys)
    kb.start()
    kb.stop()
    kb.clearEvents()
    kb.device.getState(["a"])
    kb.device.dispatchMessages()


def clock_falls_back():
    from psychopy import clock
    # if this fails, psychtoolbox was not actually hidden and every other
    # check below would be testing the wrong thing
    assert not clock.havePTB, "psychtoolbox was still importable"
    assert isinstance(clock.getTime(), float), "getTime() did not return a float"

def visual_imports():
    import psychopy.visual

def sound_imports():
    import psychopy.sound

def keyboard_backend_is_not_ptb():
    from psychopy.hardware import keyboard
    keyboard.Keyboard()
    backend = keyboard.KeyboardDevice._backend
    assert backend != "ptb", "keyboard backend was still 'ptb'"


if scenario == "default":
    check("clock_falls_back", clock_falls_back)
    check("visual_imports", visual_imports)
    check("sound_imports", sound_imports)
    check("keyboard_api_usable", lambda: exercise_keyboard(None))
    check("keyboard_backend_is_not_ptb", keyboard_backend_is_not_ptb)
elif scenario == "ptb_requested":
    check("clock_falls_back", clock_falls_back)
    # gh-7493: requesting the psychtoolbox backend when psychtoolbox is not
    # installed used to leave `_buffers` unset but `_backend` set to 'ptb'
    check("keyboard_api_usable", lambda: exercise_keyboard("ptb"))
else:
    raise SystemExit("unknown scenario %r" % scenario)

# marked out so they can be picked out of any surrounding library chatter
for line in results:
    print("CHECK|" + line)
'''

# the checks each scenario is expected to report on
_EXPECTED_CHECKS = {
    "default": [
        "clock_falls_back",
        "visual_imports",
        "sound_imports",
        "keyboard_api_usable",
        "keyboard_backend_is_not_ptb",
    ],
    "ptb_requested": [
        "clock_falls_back",
        "keyboard_api_usable",
    ],
}


@pytest.mark.parametrize("scenario", sorted(_EXPECTED_CHECKS))
def test_works_without_psychtoolbox(tmp_path, scenario):
    """PsychoPy should import and take keyboard responses with no psychtoolbox."""
    script = tmp_path / "no_psychtoolbox_child.py"
    script.write_text(_CHILD_SCRIPT, encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "-u", str(script), scenario],
        capture_output=True,
        timeout=300,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")

    if proc.returncode != 0:
        pytest.fail(
            "child interpreter exited with %s\n--- stdout ---\n%s\n--- stderr ---\n%s"
            % (proc.returncode, stdout, stderr)
        )

    results = [line[len("CHECK|"):] for line in stdout.splitlines()
               if line.startswith("CHECK|")]

    # a check which raised is reported as "<name>: <ExcType>: <message>"
    failures = [line for line in results if ":" in line]
    assert not failures, (
        "PsychoPy does not work without psychtoolbox (scenario %r):\n  %s"
        % (scenario, "\n  ".join(failures))
    )

    missing = [name for name in _EXPECTED_CHECKS[scenario] if name not in results]
    assert not missing, (
        "child did not report on %s\n--- stdout ---\n%s\n--- stderr ---\n%s"
        % (missing, stdout, stderr)
    )
