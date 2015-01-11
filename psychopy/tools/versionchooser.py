#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Psychopy Version Chooser to specify version within experiment scripts'''

import os,sys,re
import subprocess   # Simple git commandline management
from subprocess import CalledProcessError
import psychopy     # For currently loaded version
from psychopy import prefs as _p
from psychopy import logging, tools

USERDIR = _p.paths['userPrefsDir']
VERSIONSDIR = os.path.join(USERDIR, 'versions')

def useVersion(requestedVersion):
    """Manage paths and checkout psychopy libraries for requested versions of psychopy.

    Inputs:
        * requestedVersion : A string with the requested version of PsychoPy to use
          (NB Must be an exact version to checkout; ">=1.80.04" is NOT allowable yet.)

    Outputs:
        * Returns True if requested version was successfully loaded.
          Raises a RuntimeError if git is needed and not present, or if other psychopy modules
          have already been loaded. Raises a subprocess CalledProcessError if an invalid
          git tag/version was checked out.


    Usage (at the top of an experiment script):

        from psychopy.tools.versionchooser import useVersion
        useVersion('1.80.04')
        from psychopy import visual, event, ...

    """
    # Sanity Checks
    imported = _psychopyComponentsImported()
    if len(imported):
        raise RuntimeError(
            "Please request a version before importing any psychopy modules. "
            "Found: %s" % imported)
    if _versionOk(psychopy.__version__, requestedVersion):
        return  # No switching needed
    if not _gitPresent():  # Switching required, so make sure `git` is available.
        raise RuntimeError("Please install git to specify a version with useVersion()")

    # Setup Requested Version
    requestedPath = _setupRequested(requestedVersion)
    _switchVersionTo(requestedPath)

    # Reload!
    reload(psychopy)
    reload(logging)
    if requestedVersion>="1.80":
        reload(tools) #this is just because this file is withint tools!
    print "Now using PsychoPy library version: ", psychopy.__version__
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
    if not os.path.exists(_p.paths['userPrefsDir']):
        os.mkdir(_p.paths['userPrefsDir'])
    try:
        if os.path.exists(VERSIONSDIR):
            _checkoutRequested(requestedVersion)
        else:
            _cloneRequested(requestedVersion)
    except CalledProcessError as e:
        if 'did not match any file(s) known to git' in e.output:
            logging.error("'%s' is not a valid Psychopy version." % requestedVersion)
            raise
    return VERSIONSDIR

def getCurrentTag():
    """Returns the current tag name from the version repository
    """
    cmd = 'git describe --always --tag'
    vers = subprocess.check_output(cmd.split(), cwd=VERSIONSDIR).split('-')[0]
    return vers

def _checkoutRequested(requestedVersion):
    """Look for a tag matching the request, return it if found or return None for the search"""
    # Check tag of repo
    if getCurrentTag()==requestedVersion: #nothing to do!
        return 1

    # See if the tag already exists in repos (no need for internet)
    cmd = 'git tag'
    if requestedVersion not in subprocess.check_output(['git','tag'], cwd=VERSIONSDIR):
        # Grab new tags
        logging.info("Couldn't find version %r locally. Trying github..." %(requestedVersion))
        cmd = 'git fetch github'
        out = subprocess.check_output(cmd.split())
        #after fetching from github check if it's there now!
        versions = subprocess.check_output(['git','tag'], cwd=VERSIONSDIR)
        if requestedVersion not in versions:
            logging.error("%r is not a valid version. Please choose one of:  %r" %(requestedVersion, versions.split()))
            return 0

    # Checkout the requested tag
    cmd = 'git checkout %s' % requestedVersion
    out = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT, cwd=VERSIONSDIR)
    logging.debug(out)
    return 1

def _cloneRequested(requestedVersion):
    """Check out a new copy of the requested version"""

    print 'Cloning Psychopy Library from Github - this may take a while'
    cmd = ['git', 'clone', '-o', 'github', 'https://github.com/psychopy/versions', 'versions']
    print ' '.join(cmd)
    out = subprocess.check_output(cmd, cwd=USERDIR)

    cmd = ['git', 'checkout', requestedVersion]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=VERSIONSDIR)
    logging.debug(out)


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

