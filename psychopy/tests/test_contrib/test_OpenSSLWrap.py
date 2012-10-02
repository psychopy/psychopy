#!/usr/bin/env python

import shutil, time
from tempfile import mkdtemp
from psychopy.contrib import opensslwrap


class Test_openssl_wrap():
    def set_up(self):
        self.tmp_dir = mkdtemp(prefix='psychopy-tests-app')

    def test_PubEncDec(self):
        opensslwrap._testPubEncDec('secret'+str(time.time())) # does the work

    def tear_down(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
