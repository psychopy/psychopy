#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import pytest
import locale
from psychopy.app import localization
from psychopy.app.localization import _translate

welcome = 'Welcome to PsychoPy2!'
trans = {'en': welcome,
         'ja': 'PsychoPy2へようこそ！'
         }

### needs rewriting since localization.init() no longer sets the locale

@pytest.mark.localization
class XXXTestLocalization(object):
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
