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
import os, sys, glob, codecs
from psychopy import logging, prefs

import wx

# need a wx App for wx.Locale:
try:
    wx.Dialog(None, -1)
except wx._core.PyNoAppError:
    if wx.version() < '2.9':
        tmpApp = wx.PySimpleApp()
    else:
        tmpApp = wx.App(False)

# Get a dict of locale aliases from wx.Locale() -- same cross-platform (Win 7, Mac 10.9)
locale = wx.Locale()
aliases = {}
wxIdFromCode = {}  # int: 0, 2-229
codeFromWxId = {}  # used in directory names e.g. ja_JP; never JPN ala Windows
winmap = {}  # get windows 3-letter code (=val) from canonical form (=key); use only for setting locale (non-wx)
locname = {}  # descriptive name, if available; 5-letter code if not
reverseMap = {}

for i in range(230):
    info = locale.GetLanguageInfo(i)
    if info:
        aliases[info.Description] = info.CanonicalName  # mix of forms: ja or ja_JP
        wxIdFromCode[info.CanonicalName] = i
        codeFromWxId[i] = info.CanonicalName

mappings = os.path.join(os.path.dirname(__file__), 'mappings.txt')
for line in codecs.open(mappings, 'rU', 'utf8').readlines():
    try:
        can, win, name = line.strip().split(' ', 2)  # canonical, windows, name-with-spaces
    except ValueError:
        can, win = line.strip().split(' ', 1)
        name = can
    winmap[can] = win
    locname[can] = name
    reverseMap[name] = can

# what are the available translations? available languages on the OS?
expr = os.path.join(os.path.dirname(__file__), '..', 'locale', '*')
available = sorted(map(os.path.basename, glob.glob(expr)))
sysAvail = [str(l) for l in codeFromWxId.values()  # installed language packs
            if l and locale.IsAvailable(wxIdFromCode[l])]

def getID(lang=None):
    """Get wx ID of language to use for translations: `lang`, pref, or system default.

    `lang` is a 5 char `language_REGION`, eg ja_JP
    """
    if lang:
        val = lang
    else:
        try:
            val = prefs.app['locale']
        except KeyError:
            val = locale.GetLocale()  # wx.Locale, no encoding
        if not val:
            val = codeFromWxId[wx.LANGUAGE_DEFAULT]
    try:
        # out-dated: [can't set wx.Locale here because no app yet] now there is an app
        # here just determine the value to be used when it can be set
        language = wxIdFromCode[val]
    except KeyError:
        logging.error('locale %s not known to wx.Locale, using default' % val)
        language = wx.LANGUAGE_DEFAULT

    return language, val

languageID, lang = getID()
#use lang like this:
#import locale  -- the non-wx version of locale
#
#if sys.platform.startswith('win'):
#        v = winmap[val]
#else: v=val
#locale.setlocale(locale.LC_ALL, (v, 'UTF-8'))

# set locale before splash screen:
if locale.IsAvailable(languageID):
    wxlocale = wx.Locale(languageID)
else:
    wxlocale = wx.Locale(wx.LANGUAGE_DEFAULT)

# ideally rewrite the following using wxlocale only:
path = os.path.join(os.path.dirname(__file__), '..', 'locale', lang, 'LC_MESSAGE') + os.sep
mofile = os.path.join(path, 'messages.mo')
try:
    logging.debug("Opening message catalog %s for locale %s" % (mofile, lang))
    trans = gettext.GNUTranslations(open(mofile, "rb"))
except IOError:
    logging.debug("Locale for '%s' not found. Using default." % lang)
    trans = gettext.NullTranslations()
trans.install(unicode=True)

#__builtins__['_'] = wx.GetTranslation
# this seems to have no effect, needs more investigation:
#path = os.path.join(os.path.dirname(__file__), '..', 'locale', lang, 'LC_MESSAGE') + os.sep
#wxlocale.AddCatalogLookupPathPrefix(path)
