#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Language localization for PsychoPy.

Sets the locale upon import, installs global translate function _( ):
    from psychopy import localization
"""

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Author: Jeremy Gray, May 2014

import gettext
import locale
import os, sys
from psychopy import logging, prefs

# Create a dict of locale aliases, usage:
# key = locale.getlocale()[0]
# setlocale(0, aliases[key])
if sys.platform.startswith('win'):
    filename = 'win.txt'
else:
    filename = 'macnix.txt'
path = os.path.join(os.path.dirname(__file__), 'aliases', filename)
aliases = {}
for line in open(path, 'rU').readlines():
    val, key = line.strip().split(' ', 1)
    aliases[key] = val


def init(lang=None):
    """Init language to use for translations: `lang`, pref, or system default.

    On Mac or Linux, `lang` is typically a two-character language code, or 5 char language_CULTURE
    On Windows, `lang` is typically a three-character code
    """
    encoding = 'utf-8'

    if lang:
        current = lang.split('.')
        if len(current) == 1:
            current.append(encoding)
    else:
        current = locale.getlocale()
    if current == (None, None):
        try:
            val = str(prefs.app['locale'])
        except KeyError:
            val = u''
        if val in locale.locale_alias.keys():
            val = locale.locale_alias[val]
        try:
            val = locale.setlocale(locale.LC_ALL, val)
            if '.' in val:
                val, encoding = val.split('.')
        except locale.Error:
            pass
        current = (val, encoding)

    # look for language_CULTURE files first (en_NZ), else just language (en):
    dname = os.path.dirname(__file__)
    fileexpr = os.path.join(dname, "res/messages_%s.mo")
    # use language_Country if available (= more specific than just language)
    if os.path.exists(fileexpr % current[0]):
        lang = current[0]
    else:
        lang = current[0][:2]
    lang = lang[:2].lower() + lang[2:]
    mofile = fileexpr % lang

    try:
        logging.debug("Opening message file %s for locale %s" % (mofile, lang))
        trans = gettext.GNUTranslations(open(mofile, "rU"))
    except IOError:
        logging.debug("Locale for '%s' not found. Using default." % lang)
        trans = gettext.NullTranslations()
        lang = locale.getlocale()[0][:2]  # return value

    # install global _() function, and return code of the installed language:
    trans.install()
    return lang


init()

if __name__ == '__main__':
    print _('Welcome to PsychoPy2!')
