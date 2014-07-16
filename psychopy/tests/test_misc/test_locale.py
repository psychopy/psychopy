#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import pytest
import locale
from psychopy.app import localization

welcome = u'Welcome to PsychoPy2!'
trans = {'en': welcome,
         'ja': u'PsychoPy2へようこそ！'
         }

@pytest.mark.localization
class TestLocalization(object):
    def setup_class(self):
        self.orig = localization.init()

    def teardown_class(self):
        localization.init(self.orig)

    def test_set(self):
        lang = localization.init('En_US')
        assert lang == 'en'

        for lang in ['En_US', 'Ja_JP', 'ja_JP']:
            setlang = localization.init(lang)
            out = _(welcome)
            assert setlang == lang.lower()[:2]
            assert out == trans[setlang]

        #lo = 'en'
        #localization.init(lo)
        #for lang in ['', None, [], 'junk']:
        #    setlang = localization.init(lang)
        #    assert setlang == lo
