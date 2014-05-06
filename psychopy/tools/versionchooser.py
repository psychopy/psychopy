#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Psychopy Version Chooser to specify version within experiment scripts'''

import psychopy     # For currently loaded version
import re           # Version comparison parsing
import subprocess   # Simple git commandline management

VERSIONSDIR = os.path.expanduser('~/.psychopy/versions')

def useVersion(requestedVersion):
    """Manage paths and checkout psychopy libraries for requested versions of psychopy.

    Inputs: 
        * requestedVersion : A string with the requested version of Psychopy to use 
          (NB ">=1.80.04" is allowable.)

    Outputs:
        * Returns True if requested version was successfully loaded.
          Raises a ScriptError if git is needed and not present, or if other psychopy modules
          have already been loaded.

    Usage (at the top of an experiment script):

        from psychopy.versionchooser import useVersion
        useVersion('1.80.04')
        from psychopy import visual, event, ...

    """
    # Sanity Checks
    imported = _psychopyComponentsImported():
    if len(imported):
        raise ScriptError(
            "Please request a version before importing any psychopy modules. "
            "Found: %s" % imported)
    if version_ok(psychopy.__version__, requestedVersion): then return  # No switching needed
    if not _gitPresent():  # Switching required, so make sure `git` is available.
        raise ScriptError("Please install git to specify a version with useVersion()")

    # Setup Requested Version
    requestedPath = _setupRequested(requestedVersion)
    _switchVersionTo(requestedPath)

    # Reload!
    reload psychopy
    # TODO Best way to check for other submodules that have already been imported?

    return True  # Success!

def _versionOk(loaded,requested):
    """Check if loaded version is a valid fit for the requested version."""
    requestComparator,requestVers = _getComparator(requested)
    return eval("'%s' %s '%s'" % (loaded, requestComparator, requestVers))
        # e.g. returns True if loaded > requested '1.80.05' > '1.80.04'

def _comparator(requested):
    comparePat = re.compile('$(<|>|=)*(\d|\.)*')
    search = comparePat.search(requested)
    if search:
        return (search.groups[0], search.groups[1])
    else:
        return ('==', requested)  # Default to identity comparison

def _setupRequested(requestedVersion):
    """Checkout or Clone requested version."""
    repoPath = os.path.join(VERSIONSDIR,'psychopy')
    if os.path.exists(repoPath):
        _checkoutRequested(requestedVersion)
    else:
        _cloneRequested(requestedVersion)

    return repoPath

def _checkoutRequested(requestedVersion):
    """Look for a path matching the request, return it if found or return None for the search"""
    with os.chdir(os.path.join(VERSIONSDIR,'psychopy')):
        cmd = ['git','describe','--always','--tag']
        vers = subprocess.check_output(cmd).split('-')[0]
        if _versionOk(vers,requestedVersion):
            return os.path.join(searchPath,child)
        else:
            _, requestVers = _getComparator(requestedVersion)
            cmd = ['git','checkout',requestVers]
            out = subprocess.check_output(cmd)


def _cloneRequested(requestedVersion):
    """Check out a new copy of the requested version"""
    with os.chdir(VERSIONSDIR):
        cmd = 'git clone https://github.com/psychopy/psychopy'
        print 'Cloning Psychopy Library from Github - this may take a while'
        print cmd
        out = subprocess.check_output(cmd.split())

        _, requestVers = _getComparator(requestedVersion)
        cmd = 'git checkout --tag %s' % requestVers
        print cmd
        out = subprocess.check_output(cmd.split())


def _gitPresent():
    """Check for git on command-line"""
    proc = subprocess.Popen('git --version',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            cwd='.', shell=True)
    gitvers, _ = proc.communicate()
    if gitvers.startswith('git version'):
        return True
    else:
        return False

def _psychopyComponentsImported():
    imported = []
    loaded = dir()
    for mod in psychopy.__all__:
        if mod in dir: imported.append(mod)
    return imported

def _switchVersionTo(requestedPath):
    """Alter sys.path in place to remove current references to psychopy 
       and replace them with ones to the requested path"""
    # Remove Exisitng References
    for p in sys.path:
        if 'psychopy' in sys.path.downcase():
            sys.path.remove(p)
    # And replace them with the correct requested version.
    sys.path = [requestedPath] + sys.path

