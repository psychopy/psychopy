# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.versionchooser"""
import os
import sys
from pathlib import Path

import psychopy
from psychopy.tools.versionchooser import Version, useVersion, versionMap
from psychopy import prefs, experiment
from psychopy.scripts.psyexpCompile import generateScript
from psychopy.experiment.components import polygon
from tempfile import mkdtemp

USERDIR = prefs.paths['userPrefsDir']
VER_SUBDIR = 'versions'
VERSIONSDIR = os.path.join(USERDIR, VER_SUBDIR)

pyVersion = Version(".".join(
    [str(sys.version_info.major), str(sys.version_info.minor)]
))


class TestVersionChooser():
    def setup_method(self):
        self.temp = Path(mkdtemp())

    def test_same_version(self):
        # pick a version which works with installed Python
        rVers = versionMap[pyVersion][0]
        # use it
        vers = useVersion(rVers)
        vers = Version(vers)
        # confirm that it is being used
        assert (vers.major, vers.minor) == (rVers.major, rVers.minor)

    def test_version_folder(self):
        assert(os.path.isdir(VERSIONSDIR))

    def test_writing(self):
        # Can't run this test on anything beyond 3.6
        if pyVersion > Version("3.6"):
            return

        # Create simple experiment with a Polygon
        exp = experiment.Experiment()
        rt = experiment.routines.Routine(name="testRoutine", exp=exp)
        exp.addRoutine("testRoutine", rt)
        exp.flow.addRoutine(rt, 0)
        comp = polygon.PolygonComponent(exp=exp, parentName="testRoutine")
        rt.addComponent(comp)
        # Set use version
        exp.settings.params['Use version'].val = "2021.1.4"
        # Save experiment
        exp.saveToXML(str(self.temp / "versionText.psyexp"))

        # --- Python ---
        # Write script
        scriptFile = str(self.temp / "versionText.py")
        generateScript(
            experimentPath=scriptFile,
            exp=exp,
            target="PsychoPy"
        )
        # Read script
        with open(scriptFile, "r") as f:
            script = f.read()
        # Get args passed to comp
        args = script.split(f"{comp.name} = visual.ShapeStim(")[1]
        args = args.split(")")[0]
        # If using 2021.1.4, there shouldn't be any "anchor" arg in ShapeStim, as it wasn't implemented yet
        assert "anchor" not in args, (
            "When compiling Py with useversion 2021.1.4, found 'anchor' argument in ShapeStim; this was not "
            "implemented in requested version."
        )

        # --- JS ---
        # Write script
        scriptFile = str(self.temp / "versionText.js")
        generateScript(
            experimentPath=scriptFile,
            exp=exp,
            target="PsychoJS"
        )
        # Read script
        with open(scriptFile, "r") as f:
            script = f.read()
        # Check for correct version import statement
        assert "import { PsychoJS } from './lib/core-2021.1.4.js'" in script, (
            "When compiling JS with useversion 2021.1.4, could not find version-specific import statement."
        )


"""

TODO: Tests to write:

* Fail if git isn't there
* Fail if git can't download repo

"""
