#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Language localization for PsychoPy.

Sets the locale value as a wx languageID (int) and initializes gettext translation _():
    from psychopy.app import localization
"""

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Author: Jeremy Gray, July 2014


import gettext
import os, sys
from psychopy import logging, prefs

# Get a dict of locale aliases (cross-platform?) from wx.Locale()
import wx
locale = wx.Locale()
aliases = {}
idFromCode = {}
codeFromId = {}
for i in range(256):
    info = locale.GetLanguageInfo(i)
    if info:
        aliases[info.Description] = info.CanonicalName
        idFromCode[info.CanonicalName] = i
        codeFromId[i] = info.CanonicalName
aliases['English'] = 'en_US'

def getID(lang=None):
    """Get wx ID of language to use for translations: `lang`, pref, or system default.

    `lang` is a two-character language code, or 5 char `language_REGION`
    """
    if lang:
        val = lang
    else:
        try:
            val = prefs.app['locale']
        except KeyError:
            val = locale.GetLocale()
    try:
        # can't set wx.Locale here because no app yet
        language = idFromCode[val]
    except KeyError:
        logging.error('locale %s not known to wx.Locale, using default' % val)
        language = wx.LANGUAGE_DEFAULT
    return language

languageID = getID()

# set locale before splash screen:
wxlocale = wx.Locale(languageID)
lang = codeFromId[languageID]

# ideally rewrite the following using self.locale only (= via wx):
path = os.path.join(os.path.dirname(__file__), '..', 'locale', lang, 'LC_MESSAGE') + os.sep
# try two-letter version if language_REGION not found; wx does this?
if not os.path.exists(path):
    path = path.replace(lang, lang[:2])
mofile = os.path.join(path, 'messages.mo')
try:
    logging.debug("Opening message file %s for locale %s" % (mofile, lang))
    trans = gettext.GNUTranslations(open(mofile, "rb"))
except IOError:
    logging.debug("Locale for '%s' not found. Using default." % lang)
    trans = gettext.NullTranslations()
trans.install(unicode=True)

# this seems to have no effect, needs more investigation:
path = os.path.join(os.path.dirname(__file__), 'locale') + os.sep
wxlocale.AddCatalogLookupPathPrefix(path)

