#!/usr/bin/env python

import os, shutil, time
import nose
from tempfile import mkdtemp
from psychopy.contrib import opensslwrap


class test_openssl_wrap():
    def setUp(self):
        self.tmp_dir = mkdtemp(prefix='psychopy-tests-app')
    
    def testPubEncDec(self):    
        opensslwrap._testPubEncDec('secret'+str(time.time())) # does the work
    
    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
