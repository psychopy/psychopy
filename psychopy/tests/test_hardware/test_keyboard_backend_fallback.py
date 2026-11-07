"""Tests that asking for the 'ptb' keyboard backend degrades safely.

`KeyboardDevice._backend` is assigned from the backend the caller asked for,
but the psychtoolbox buffers are only created under
``_backend in ['', 'ptb'] and havePTB``, while every later use of them is
guarded by the weaker ``_backend == 'ptb'``. When psychtoolbox is missing
those two conditions disagree: `_backend` says 'ptb' but the buffers were
never made.

That mismatch first showed up as `AttributeError: 'KeyboardDevice' object has
no attribute '_buffers'` (gh-7493). gh-7494 stopped the crash by defaulting
`_buffers` to `{}` for every backend, but left `_backend` still reporting
'ptb', which turned the crash into silent data loss: `dispatchMessages()`
takes the 'ptb' branch, iterates an empty `_buffers`, and never falls through
to the backend that would actually collect key presses.

Builder writes the keyboard backend into generated scripts from the user's
preferences, so `Keyboard(backend='ptb')` on a machine without psychtoolbox
is a realistic combination rather than a contrived one.

This runs in a subprocess: `psychtoolbox` has to be hidden before `psychopy`
imports it, and `KeyboardDevice._backend` is a class attribute assigned only
on the first construction, so a `Keyboard` built earlier in the process would
stop a later `backend='ptb'` from taking effect.
"""

import subprocess
import sys

import pytest


# Ask for the psychtoolbox backend with psychtoolbox unavailable, then feed in a
# key press the way pyglet's handler would and check it still comes back out.
_WITHOUT_PSYCHTOOLBOX = '''
import sys

class BlockPsychtoolbox:
    """Meta path finder which makes `import psychtoolbox` fail."""
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "psychtoolbox" or fullname.startswith("psychtoolbox."):
            raise ModuleNotFoundError("No module named %r (hidden by test)" % fullname)
        return None

sys.meta_path.insert(0, BlockPsychtoolbox())

from psychopy import core, event
from psychopy.hardware import keyboard

kb = keyboard.Keyboard(backend="ptb")

assert not keyboard.havePTB, "psychtoolbox was still importable"
assert keyboard.KeyboardDevice._backend != "ptb", (
    "backend stayed 'ptb' with no psychtoolbox; key presses would be discarded")

# push a key press into the event backend's buffer, as its pyglet handler does
event._keyBuffer.append(("a", None, core.getTime()))
keys = kb.getKeys(waitRelease=False)
assert keys, "key press was silently discarded"

# on the event backend KeyPress.name carries the (key, time) pair returned by
# event.getKeys(timeStamped=True) rather than a bare string
name = keys[0].name
if not isinstance(name, str):
    name = name[0]
assert name == "a", "unexpected key %r" % (keys[0].name,)

print("RESULT|ok|%s" % keyboard.KeyboardDevice._backend)
'''


@pytest.mark.keyboard
def test_ptb_backend_falls_back_without_psychtoolbox(tmp_path):
    """Requesting 'ptb' with no psychtoolbox should use a backend that works."""
    script = tmp_path / "without_psychtoolbox.py"
    script.write_text(_WITHOUT_PSYCHTOOLBOX, encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "-u", str(script)],
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

    assert any(line.startswith("RESULT|ok|") for line in stdout.splitlines()), stdout
