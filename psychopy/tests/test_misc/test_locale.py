#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import locale
from psychopy import localization
from psychopy.localization import _translate

welcome = u'Welcome to PsychoPy3!'
trans = {'en': welcome,
         'ja': u'PsychoPy3へようこそ！'
         }

### needs rewriting since localization.init() no longer sets the locale

@pytest.mark.localization
class XXXTestLocalization():
    def setup_class(self):
        self.orig = localization.languageID

    def teardown_class(self):
        pass #localization.getID(self.orig)

    def test_set(self):
        lang = localization.getID('En_US')
        assert lang == 'en'

        for lang in ['En_US', 'Ja_JP', 'ja_JP']:
            setlang = localization.getID(lang)
            out = _translate(welcome)
            assert setlang == lang.lower()[:2]
            assert out == trans[setlang]

        #lo = 'en'
        #localization.init(lo)
        #for lang in ['', None, [], 'junk']:
        #    setlang = localization.init(lang)
        #    assert setlang == lo
