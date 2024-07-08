#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import os
import sys
import pathlib

__version__ = (pathlib.Path(__file__).parent/"VERSION").read_text(encoding="utf-8").strip()
__version__ = (pathlib.Path(__file__).parent/"GIT_SHA").read_text(encoding="utf-8").strip()
__license__ = 'GPL v3'
__author__ = 'Open Science Tools Ltd'
__author_email__ = 'support@opensciencetools.org'
__maintainer_email__ = 'support@opensciencetools.org'
__url__ = 'https://www.psychopy.org/'
__download_url__ = 'https://github.com/psychopy/psychopy/releases/'
__build_platform__ = 'n/a'

__all__ = ["gui", "misc", "visual", "core",
           "event", "data", "sound", "microphone"]

# for developers the following allows access to the current git sha from
# their repository
if __git_sha__ == 'n/a':
    from subprocess import check_output, PIPE
    # see if we're in a git repo and fetch from there
    try:
        thisFileLoc = os.path.split(__file__)[0]
        output = check_output(['git', 'rev-parse', '--short', 'HEAD'],
                              cwd=thisFileLoc, stderr=PIPE)
    except Exception:
        output = False
    if output:
        __git_sha__ = output.strip()  # remove final linefeed

# update preferences and the user paths
if 'installing' not in locals():
    from psychopy.preferences import prefs
    import site

    # Configure the environment to use our custom site-packages location for
    # user-installed packages. In the future, this will be configured outside of
    # the running environment, but for now, we need to do it here.
    useDefaultSite = False
    if 'PSYCHOPYNOPACKAGES' in os.environ:
        # Custom environment variable for people using PsychoPy as a library,
        # who don't want to use the custom site-packages location. If set to 1,
        # this will disable the custom site-packages location. Packages will be
        # installed in the default, system dependent user's site-packages 
        # location.
        useDefaultSite = os.environ['PSYCHOPYNOPACKAGES'] == '1'

    # configure environment for custom site-packages location
    if not useDefaultSite:
        env = os.environ.copy()
        if 'PYTHONPATH' in env:  # append entries to existing PYTHONPATH
            _userSitePackages = str(prefs.paths['userPackages'])
            if _userSitePackages not in env['PYTHONPATH']:
                env['PYTHONPATH'] = os.pathsep.join([
                    env['PYTHONPATH'], _userSitePackages])
            _userPackages = str(prefs.paths['packages'])
            if _userPackages not in env['PYTHONPATH']:
                env['PYTHONPATH'] = os.pathsep.join([
                    env['PYTHONPATH'], _userPackages]) 
        else:
            env['PYTHONPATH'] = os.pathsep.join([
                str(prefs.paths['userPackages']), 
                str(prefs.paths['packages'])])

        # set user site packages
        env['PYTHONUSERBASE'] = prefs.paths['packages']

        # update environment, pass this to sub-processes (e.g. pip)
        os.environ.update(env)

        # make sure site knows about our custom user site-packages
        site.USER_SITE = prefs.paths['userPackages']
        site.ENABLE_USER_SITE = True
        # site.main()

        # add paths from main plugins/packages (installed by plugins manager)
        site.addsitedir(prefs.paths['userPackages'])  # user site-packages
        site.addsitedir(prefs.paths['userInclude'])  # user include
        site.addsitedir(prefs.paths['packages'])  # base package dir

        _envPath = os.environ.get('PATH', None)
        if _envPath is not None:
            # add user include path to system PATH (for C extensions)
            if str(prefs.paths['userInclude']) not in _envPath:
                os.environ['PATH'] = os.pathsep.join([
                    os.environ['PATH'], str(prefs.paths['userInclude'])])
            # add scripts path for user packages to system PATH
            if str(prefs.paths['userScripts']) not in _envPath:
                os.environ['PATH'] = os.pathsep.join([
                    os.environ['PATH'], str(prefs.paths['userScripts'])])

        if sys.platform == 'darwin' and sys._framework:
            # add scripts path for user packages to system PATH
            fwBinPath = os.path.join(sys.prefix, 'bin')
            if fwBinPath not in os.environ['PATH']:
                os.environ['PATH'] = os.pathsep.join([
                    fwBinPath, os.environ['PATH']])
    
    # add paths from general preferences
    for _pathName in prefs.general['paths']:
        sys.path.append(_pathName)
    
    # Add paths from individual plugins/packages (installed by plugins manager),
    # this is to support legacy plugins that don't use the customized user 
    # site-packages location. This will be removed in the future.
    import pathlib as _pathlib
    for _pathName in _pathlib.Path(prefs.paths['packages']).glob("*"):
        if _pathName.is_dir():
            sys.path.append(str(_pathName))

    from psychopy.tools.versionchooser import useVersion, ensureMinimal


if sys.version_info.major < 3:
    raise ImportError("psychopy does not support Python2 installations. "
                      "The last version to support Python2.7 was PsychoPy "
                      "2021.2.x")

# import readline here to get around an issue with sounddevice
# issues GH-2230 GH-2344 GH-2662
try:
    import readline
except ImportError:
    pass  # all that will happen is the stderr/stdout might get redirected

