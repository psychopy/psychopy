import pytest
import re
from psychopy import preferences
from psychopy.app._psychopyApp import PsychoPyApp

@pytest.mark.prefs
def testGenerateSpec():
    # Get base spec
    base = open(preferences.__folder__ / "baseNoArch.spec").read()
    # Change theme default for use as a marker
    base = re.sub(r"(?<=theme = string\(default=')PsychopyLight(?='\))", "PsychopyDark", base)
    # Generate spec
    preferences.generateSpec(baseSpec=base)
    darwin = open(preferences.__folder__ / "Darwin.spec").read()
    freeBSD = open(preferences.__folder__ / "FreeBSD.spec").read()
    linux = open(preferences.__folder__ / "Linux.spec").read()
    windows = open(preferences.__folder__ / "Windows.spec").read()
    # Check for marker
    assert all("theme = string(default='PsychopyDark')" in target for target in [darwin, freeBSD, linux, windows])
    assert all("theme = string(default='PsychopyLight')" not in target for target in [darwin, freeBSD, linux, windows])
    # Check generated prefs
    prefs = preferences.Preferences()
    prefs.resetPrefs()
    assert prefs.app['theme'] == "PsychopyDark"
    # Check that the app still loads
    app = PsychoPyApp(0, testMode=True, showSplash=False)
    app.quit()
