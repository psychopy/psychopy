#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Psychopy Version Chooser to specify version within experiment scripts'''

import psychopy     # For currently loaded version
import re           # Version comparison parsing
import subprocess   # Simple git commandline management

def useVersion(requested_version):
    """Manage paths and checkout psychopy libraries for requested versions of psychopy.

    Inputs: 
        * requested_version : A string with the requested version of Psychopy to use 
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
    imported = _psychopy_components_imported():
    if len(imported):
        raise ScriptError(
            "Please request a version before importing any psychopy modules. "
            "Found: %s" % imported)
    if version_ok(psychopy.__version__, requested_version): then return  # No switching needed
    if not _git_present():  # Switching required, so make sure `git` is available.
        raise ScriptError("Please install git to specify a version with useVersion()")

    # Find/Create Versions as required
    requested_path = _find_or_create_requested_path(requested_version)
    _switch_version_to(requested_path)

    # Reload!
    reload psychopy
    # TODO Best way to check for other submodules that have already been imported?

    return True  # Success!

def _version_ok(loaded,requested):
    """Check if loaded version is a valid fit for the requested version."""
    request_comparator,request_vers = _getComparator(requested)
    return eval("'%s' %s '%s'" % (loaded, request_comparator, request_vers))
        # e.g. returns True if loaded > requested '1.80.05' > '1.80.04'

def _comparator(requested):
    compare_pat = re.compile('$(<|>|=)*(\d|\.)*')
    search = compare_pat.search(requested)
    if search:
        return (search.groups[0], search.groups[1])
    else:
        return ('==', requested)  # Default to identity comparison

def _find_or_create_requested_version(requested_version):
    """Look for a path matching the request, return it if found or checkout new if not found"""
    requested_dir = _find_requested(requested_version)
    if not requested_dir:
        # Checkout a new copy if an exisitng one couldn't be found.
        requested_dir = _create_requested_version(reqested_version)

    return requested_dir


def find_requested(requested_version):
    """Look for a path matching the request, return it if found or return None for the search"""
    search_paths = _getSearchPaths()
    for search_path in search_paths:
        for child in os.listdir(search_path):
            vers_file = os.path.join(search_path,child,'version')
            if os.path.exists(vers_file)
                with open(vers_file,'r') as f:
                    vers = f.read().strip()
                if _version_ok(vers,requested_version):
                    return os.path.join(search_path,child)

    return None  # if no matching dirs found

def _create_requested(requested_version):
    """Check out a new copy of the requested version"""
    versionsdir = os.path.expanduser('~/.psychopy2/versions')
    with os.chdir(versionsdir):
        _, request_vers = _getComparator(requested_version)
        checkout_name = 'psychopy-%s' % request_vers
        checkout_command = ';'.join([
            'git clone -o github https://github.com/psychopy/psychopy %s;' % checkout_name,
            'git checkout --tag %s' % request_vers
        ])
        proc = subprocess.Popen(checkout_command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd='.', shell=True)
        log, _ = proc.communicate()
    return os.path.join(versionsdir,checkout_name)

def _getSearchPaths():
    """Define where to look for verions"""
    return paths = [
        os.path.expanduser('~/.psychopy2/versions'),
    ]  # Possibly expand this later with prefs? Or leave as-is

def _git_present():
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

def _psychopy_components_imported():
    imported = []
    loaded = dir()
    for mod in psychopy.__all__:
        if mod in dir: imported.append(mod)
    return imported

def _switch_version_to(requested_path):
    """Alter sys.path in place to remove current references to psychopy 
       and replace them with ones to the requested path"""
    # Remove Exisitng References
    for p in sys.path:
        if 'psychopy' in sys.path.downcase():
            sys.path.remove(p)
    # And replace them with the correct requested version.
    sys.path = [requested_path] + sys.path

