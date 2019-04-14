# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.versionchooser"""
from builtins import object
import os
import psychopy
from psychopy.tools.versionchooser import useVersion, psychopyVersion
from psychopy import prefs
from psychopy.experiment import params

USERDIR = prefs.paths['userPrefsDir']
VER_SUBDIR = 'versions'
VERSIONSDIR = os.path.join(USERDIR, VER_SUBDIR)


class _baseVersionChooser(object):
    def test_currentVersion(self):
        vers = useVersion('1.90.0')
        assert(vers == '1.90.0')

    def test_version_folder(self):
        assert(os.path.isdir(VERSIONSDIR))


class Test_Same_Version(_baseVersionChooser):
    def setup(self):
        self.requested = '1.90.0'
        useVersion(self.requested)

    def test_same_version(self):
        assert(psychopy.__version__ == self.requested)


class Test_Older_Version(_baseVersionChooser):
    def setup(self):
        self.requested = '1.90.0'

    def test_older_version(self):
        assert(useVersion(self.requested))

class Test_PsychoPyVersion(object):
    def setup(self):
        self.current = '3.1.0'
        self.params =  {}
        self.params['Use version'] = params.Param(self.current, valType='str', allowedVals=[''])
        self.psychopyVersion = psychopyVersion(self.params, self.current)

    def test_html_version(self):
        assert(self.psychopyVersion.htmlVersion() == ''.join(('-', self.current)))

    def test_current_version(self):
        assert(self.psychopyVersion.current == self.current)

    def test_empty_version(self):
        self.params['Use version'].val = ''
        self.psychopyVersion = psychopyVersion(self.params, self.current)
        assert(self.psychopyVersion.htmlVersion() == '')

    def test_empty_latest_version(self):
        self.params['Use version'].val = 'latest'
        self.psychopyVersion = psychopyVersion(self.params, self.current)
        assert(self.psychopyVersion.htmlVersion() == '')

"""

TODO: Tests to write:

* Fail if git isn't there
* Fail if git can't download repo

"""
