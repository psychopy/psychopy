#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
%        Maximum length sequence assuming distinct values = baseVal
%
% original matlab code (C) Written by Giedrius T. Buracas, SNL-B, Salk Institute 
%                                 and Center for Functional MRI, UCSD

--------------------------------------------------------------------------------

Python translation from matlab:
  (c) Jeremy R. Gray, April 2011; distributed under the BSD license
  tested with python 2.7, numpy 1.5.1
  lines in this file that start with % or #% are from GTB's matlab code
  
Usage:
in a script:
    from psychopy.contrib import mseqSearch
    mseqSearch.mseqSearch(3,3)       # (baseVal, powerVal)
    mseqSearch.mseq_search(5,4,1,60) # (baseVal, powerVal, shift, timeout)
  returns a numpy.array(): m-sequence, or ['timed out']
  
from command line:
    ./mseqSearch.py 3 4       # 3^4
    ./mseqSearch.py 3 4 1 10  # 3^4, shift 1, timeout after 10 seconds
  prints an m-sequence, time taken, and the first 10 auto-correlation values
  
--------------------------------------------------------------------------------

%        Maximum length sequence assuming distinct values = baseVal
%
%       [ms]=mseqSearch(powerVal,baseVal)
%
%       OUTPUT:
%         ms:  generated maximum length sequence, of length basisVal^powerVal-1
%              such that all values occur with equal frequency except zero
%
%       INPUT:
%          baseVal:  any prime number up to 31
%         powerVal: an integer
%       NB: the algorithm is performing search in m-sequence register space
%         so the calculation time grows with baseVal and powerVal
%         Tested on Matlab 7.9.0 (R2009b)
%
% Copyright (c) 2010, Giedrius Buracas
% All rights reserved.
%
%Redistribution and use in source and binary forms, with or without 
%modification, are permitted provided that the following conditions are 
%met:
%
%    * Redistributions of source code must retain the above copyright 
%      notice, this list of conditions and the following disclaimer.
%    * Redistributions in binary form must reproduce the above copyright 
%      notice, this list of conditions and the following disclaimer in 
%      the documentation and/or other materials provided with the distribution
%      
%THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
%AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
%IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
%ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
%LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
%CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
%SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
%INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
%CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
%ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
%POSSIBILITY OF SUCH DAMAGE.
"""

import numpy
import sys
import time

digits = "0123456789abcdefghijklmnopqrstuvwxyz"

def _dec2base(n, base):
    """convert positive decimal integer n to equivalent in another base (2-36)
    http://code.activestate.com/recipes/65212-convert-from-decimal-to-any-base-number/
    """
    if n < 0 or base < 2 or base > 36:
        return ""
    s = ""
    while True:
        r = n % base
        s = digits[r] + s
        n = n // base
        if n == 0:
            break
    return s

def mseqSearch(baseVal, powerVal, shift=0, max_time=10):
    """search for an M-sequence, default time-out after 10 seconds
    """
    if not baseVal in [2,3,5,7,11,13,17,19,23,29]:
        raise ValueError("base must be a prime number < 30")
    
    seqLen = baseVal**powerVal-1
    register = numpy.array([1 for i in range(powerVal)])
    regLen = len(register) # == powerVal
    tap = numpy.array([0 for i in range(regLen)])
    
    isM = False #% is m-sequence?
    count = 0
    t0 = time.time()
    ms = numpy.array([0 for i in range(seqLen*2)])
    weights = []
    while not isM and count < seqLen * 4:
        noContinue = False
        count += 1
        #% now generate taps incrementally 
        tap = _dec2base(count, baseVal).zfill(regLen)
        weights = numpy.array([int(tap[i], baseVal) for i in range(regLen)])
        
        for seq in range(2*regLen, 2*seqLen-2, 2):
            ms[:seq] = [0 for i in range(seq)]
            for i in range(seq):
                #% calculating next digit with modulo powerVal arithmetic
                #% updating the register
                ms[i] = (sum(weights*register) + baseVal) % baseVal
                register = numpy.append(ms[i], register[:-1])
            
            foo = sum(ms[:seq//2] == ms[seq//2:seq])
            if foo == seq//2: # first half same as last half
                noContinue = True
                register = numpy.array([1 for i in range(powerVal)])
                break
            if time.time() - t0 > max_time:
                return ['timed out at %d sec' % max_time]
                
        if not noContinue:
            for i in range(seqLen*2):
                #% calculating next digit with modulo powerVal arithmetic
                ms[i] = (sum(weights*register) + baseVal) % baseVal
                #% updating the register
                register = numpy.append(ms[i], register[:-1])
        foo = sum(ms[:seqLen] == ms[seqLen:])
        if foo == seqLen: # first half same as last half
            isM = True
        
    ms = ms[:seqLen]
    if shift:
        shift = shift % len(ms)
        ms = numpy.append(ms[shift:], ms[:shift])
    if not isM:
        ms = []
        
    return ms

def _abs_auto(ms):
    """return absolute value of auto-correlations for lags 1 to 10
    """
    num_acs = min(11, len(ms))
    if num_acs:
        auto_corrs = [numpy.corrcoef(ms, numpy.append(ms[i:], ms[:i]))[1][0] for i in range(1,num_acs)]
        return list(map(abs, auto_corrs))
    
def test():
    print('no tests; auto-correlations are computed for each sequence generated')

if __name__=='__main__':
    if 'test' in sys.argv:
        test()
    else:
        try:
            args = list(map(int, sys.argv[1:]))
        except Exception:
            raise ValueError("expected 2-4 integer arguments: base power " +\
                "[shift [max time to search in sec]]")
        if not args[0] in [2,3,5,7,11,13,17,19,23,29]:
            raise ValueError("base must be a prime number < 30")
        t0 = time.time()
        ms = mseqSearch(*args)
        t1 = time.time() - t0
        print(ms, '\ntime: %.3f' % t1, 'sec')
        if len(ms) > 1:
            ac_10 = _abs_auto(ms) # list of auto-correlations
            print('seq length:', len(ms), '\nauto-corr, first %d: ' % len(ac_10), end='')
            for a in ac_10:
                print("%.3f" % a, end='')
            print()
            assert max(ac_10) < 1./(len(ms) - 3) or max(ac_10) < .10
