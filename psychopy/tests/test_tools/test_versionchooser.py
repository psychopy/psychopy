# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.versionchooser"""
import os
import sys
import unittest
import subprocess
import shutil
from pathlib import Path

import psychopy
from psychopy.tools.versionchooser import Version, VersionRange, useVersion, versionMap
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
            outfile=scriptFile,
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
            outfile=scriptFile,
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


class TestVersionRange:
    def test_comparisons(self):
        """
        Test that version numbers below the range register as less than.
        """
        cases = [
            # value < range
            {'range': ("2023.1.0", "2023.2.0"), 'value': "2022.2.0",
             'lt': False, 'eq': False, 'gt': True},
            # value == range.first
            {'range': ("2023.1.0", "2023.2.0"), 'value': "2023.1.0",
             'lt': False, 'eq': True, 'gt': False},
            # value in range
            {'range': ("2023.1.0", "2023.2.0"), 'value': "2023.1.5",
             'lt': False, 'eq': True, 'gt': False},
            # value == range.last
            {'range': ("2023.1.0", "2023.2.0"), 'value': "2023.2.0",
             'lt': False, 'eq': True, 'gt': False},
            # value > range
            {'range': ("2023.1.0", "2023.2.0"), 'value': "2024.1.0",
             'lt': True, 'eq': False, 'gt': False},

            # value < range.last with no first
            {'range': (None, "2023.2.0"), 'value': "2022.2.0",
             'lt': False, 'eq': True, 'gt': False},
            # value == range.last with no first
            {'range': (None, "2023.2.0"), 'value': "2023.2.0",
             'lt': False, 'eq': True, 'gt': False},
            # value > range.last with no first
            {'range': (None, "2023.2.0"), 'value': "2024.1.0",
             'lt': True, 'eq': False, 'gt': False},

            # value < range.first with no last
            {'range': ("2023.1.0", None), 'value': "2022.2.0",
             'lt': False, 'eq': False, 'gt': True},
            # value == range.first with no last
            {'range': ("2023.1.0", None), 'value': "2023.1.0",
             'lt': False, 'eq': True, 'gt': False},
            # value > range.first with no last
            {'range': ("2023.1.0", None), 'value': "2024.1.0",
             'lt': False, 'eq': True, 'gt': False},

            # no last or first
            {'range': (None, None), 'value': "2022.2.0",
             'lt': False, 'eq': True, 'gt': False},
            {'range': (None, None), 'value': "2023.1.0",
             'lt': False, 'eq': True, 'gt': False},
            {'range': (None, None), 'value': "2024.1.0",
             'lt': False, 'eq': True, 'gt': False},
        ]

        for case in cases:
            # make VersionRange
            r = VersionRange(
                first=case['range'][0],
                last=case['range'][1]
            )
            # work out le and ge from case values
            case['le'] = case['lt'] or case['eq']
            case['ge'] = case['gt'] or case['eq']
            # confirm that comparisons work as expected
            assert (r > case['value']) == case['gt'], (
                "VersionRange%(range)s > '%(value)s' should be %(gt)s" % case
            )
            assert (r >= case['value']) == case['ge'], (
                "VersionRange%(range)s >= '%(value)s' should be %(ge)s" % case
            )
            assert (case['value'] in r) == case['eq'], (
                "'%(value)s' in VersionRange%(range)s should be %(eq)s" % case
            )
            assert (r <= case['value']) == case['le'], (
                "VersionRange%(range)s <= '%(value)s' should be %(le)s" % case
            )
            assert (r < case['value']) == case['lt'], (
                "VersionRange%(range)s < '%(value)s' should be %(lt)s" % case
            )


class TestGitInstallation(unittest.TestCase):
    def test_git_installed(self):
        # Test if Git is installed on this system.
        try:
            # Attempt to get the Git version
            result = subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # Check if the command was successful
            self.assertTrue(result.returncode == 0, "Git is not installed or not in the PATH.")
        except subprocess.CalledProcessError:
            # If an error occurs, the test should fail
            self.fail("Git is not installed or not in the PATH.")


class TestGitClone(unittest.TestCase):
    def test_git_can_clone_repo(self):
        # Test that Git can clone a repository
        repo_url = "https://github.com/git/git"  # Using a reliable repo that is always available
        target_dir = "temp_repo"

        try:
            # Ensure the target directory does not exist before cloning
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)

            # Run 'git clone' and capture output
            subprocess.run(['git', 'clone', repo_url, target_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            # If Git clone fails for any reason
            self.fail(f"Git clone command failed: {e}")
        except FileNotFoundError:
            # If the 'git' command is not found
            self.fail("Git is not installed on this system.")
        finally:
            # Clean up by removing the cloned directory if it exists
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
