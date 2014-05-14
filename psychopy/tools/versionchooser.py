#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Psychopy Version Chooser to specify version within experiment scripts'''

import os,sys,re
import subprocess   # Simple git commandline management
from subprocess import CalledProcessError
import psychopy     # For currently loaded version
from psychopy import preferences

_p = preferences.preferences.Preferences()
VERSIONSDIR = os.path.join(_p.paths['userPrefsDir'], 'version')

def useVersion(requestedVersion):
    """Manage paths and checkout psychopy libraries for requested versions of psychopy.

    Inputs: 
        * requestedVersion : A string with the requested version of Psychopy to use 
          (NB Must be an exact version to checkout; ">=1.80.04" is NOT allowable yet.)

    Outputs:
        * Returns True if requested version was successfully loaded.
          Raises a ScriptError if git is needed and not present, or if other psychopy modules
          have already been loaded. Raises a subprocess CalledProcessError if an invalid
          git tag/version was checked out.


    Usage (at the top of an experiment script):

        from psychopy.versionchooser import useVersion
        useVersion('1.80.04')
        from psychopy import visual, event, ...

    """
    # Sanity Checks
    imported = _psychopyComponentsImported()
    if len(imported):
        raise ScriptError(
            "Please request a version before importing any psychopy modules. "
            "Found: %s" % imported)
    if _versionOk(psychopy.__version__, requestedVersion): return  # No switching needed
    if not _gitPresent():  # Switching required, so make sure `git` is available.
        raise ScriptError("Please install git to specify a version with useVersion()")

    # Setup Requested Version
    requestedPath = _setupRequested(requestedVersion)
    _switchVersionTo(requestedPath)

    # Reload!
    reload(psychopy)
    # TODO Best way to check for other submodules that have already been imported?

    return True  # Success!

def _versionOk(loaded,requested):
    """Check if loaded version is a valid fit for the requested version."""
    return loaded == requested
    # requestComparator,requestVers = _getComparator(requested)
    # return eval("'%s' %s '%s'" % (loaded, requestComparator, requestVers))
    #     # e.g. returns True if loaded > requested '1.80.05' > '1.80.04'


def _setupRequested(requestedVersion):
    """Checkout or Clone requested version."""
    if not os.path.exists(VERSIONSDIR): os.mkdir(VERSIONSDIR)
    repoPath = os.path.join(VERSIONSDIR,'psychopy')
    try:
        if os.path.exists(repoPath):
            _checkoutRequested(requestedVersion)
        else:
            _cloneRequested(requestedVersion)
    except CalledProcessError as e:
        if 'did not match any file(s) known to git' in e.output:
            print "'%s' is not a valid Psychopy version." % requestedVersion
            raise
            
    return repoPath

def _checkoutRequested(requestedVersion):
    """Look for a path matching the request, return it if found or return None for the search"""
    prevPath = os.getcwd()
    try:
        os.chdir(os.path.join(VERSIONSDIR,'psychopy'))
        # Grab new tags
        cmd = 'git fetch github'
        print cmd
        out = subprocess.check_output(cmd.split())

        # Check tag of repo
        cmd = 'git describe --always --tag'
        print cmd
        vers = subprocess.check_output(cmd.split()).split('-')[0]

        # Checkout the requested tag if required
        if not _versionOk(vers,requestedVersion):
            cmd = 'git checkout %s' % requestedVersion
            out = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
    finally:
        os.chdir(prevPath)


def _cloneRequested(requestedVersion):
    """Check out a new copy of the requested version"""
    prevPath = os.getcwd()
    try:
        os.chdir(VERSIONSDIR)
        print 'Cloning Psychopy Library from Github - this may take a while'
        cmd = ['git', 'clone', '-o', 'github', 'https://github.com/psychopy/psychopy']
        print ' '.join(cmd)
        out = subprocess.check_output(cmd)
        
        os.chdir('psychopy')
        cmd = ['git', 'checkout', requestedVersion]
        print ' '.join(cmd)
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    finally:
        os.chdir(prevPath)


def _gitPresent():
    """Check for git on command-line"""
    try:
        gitvers = subprocess.check_output(['git','--version'],stderr=subprocess.PIPE)
        if gitvers.startswith('git version'):
            return True
    except OSError:
        return False

def _psychopyComponentsImported():
     return [name for name in globals() if name in psychopy.__all__]


def _switchVersionTo(requestedPath):
    """Alter sys.path in place to preprend new version"""
    # NB When installed with pip/easy_install psychopy will live in
    # a site-packages directory, which should *not* be removed as it may contain
    # other relevant and needed packages.
    # 
    # Instead just prepend the current path to make sure it is loaded first.
    sys.path = [requestedPath] + sys.path

