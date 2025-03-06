#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""locale handling for PsychoPy experiment scripts, currently Mac 10.10.3+

Purpose: Avoid a unicode-related python crash on Mac 10.10.3 (maybe only
in conda environment?)

Usage: Just import this module at the top of experiment scripts. Should be fast
enough and safe to do for all Builder scripts.

Its unlikely to be widely useful for localizing experiments; that is not its
intended purpose. Few people will want to have the visual display of text in
their experiment vary by locale. If they do, it is easy enough for them to
create multiple versions of an experiment.
"""

import platform
macVer = platform.mac_ver()[0]  # e.g., '10.9.5' or '' for non-Mac

if macVer:
    def _versionTuple(v):
        return tuple(map(int, v.split('.')))
    ver = _versionTuple(macVer)
    if ver > _versionTuple('10.10.2'):
        # set locale and prefs experiment-wide, without saving prefs to disk
        import locale
        from psychopy import prefs
        if not prefs.app['locale']:
            prefs.app['locale'] = u'en_US'
        
        # set the requested locale
        reqLocale = str(prefs.app['locale'])
        reqLocale += '.UTF-8'
        try:
            locale.setlocale(locale.LC_ALL, reqLocale)
        except locale.Error:
            # locale not found, use en_US.UTF-8
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            print('Warning: locale {} not found, using en_US.UTF-8'.format(
                reqLocale))
