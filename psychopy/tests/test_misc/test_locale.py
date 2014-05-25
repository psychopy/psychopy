#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import pytest
import locale
from psychopy import localization

welcome = u'Welcome to PsychoPy2!'
trans = {'en': welcome,
         'ja': 'PsychoPy2 へようこそ！'
         }

@pytest.mark.localization
class TestLocalization(object):
    def setup_class(self):
        self.orig = localization.init()

    def teardown_class(self):
        localization.init(self.orig)

    def test_set(self):
        lang = localization.init('En')
        assert lang == 'en'

        for lang in ['En', 'Ja', 'ja']:
            setlang = localization.init(lang)
            out = _(welcome)
            assert setlang == lang.lower()
            assert out == trans[setlang]

        lo = 'en'
        localization.init(lo)
        for lang in ['', None, [], 'junk']:
            setlang = localization.init(lang)
            assert setlang == lo
