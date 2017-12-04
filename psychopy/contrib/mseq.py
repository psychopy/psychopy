#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
%        Maximum length sequence assuming 2,3,5 distinct values
%
% original matlab code (C) Written by Giedrius T. Buracas, SNL-B, Salk Institute 
%                                 and Center for Functional MRI, UCSD
% http://www.mathworks.com/matlabcentral/fileexchange/990-m-sequence-generation-program

--------------------------------------------------------------------------------

Python translation from matlab & tests:
  (c) Jeremy R. Gray, April 2011; distributed under the BSD license
  tested with python 2.7, numpy 1.5.1
  
Usage:
in a script:
  from psychopy.contrib import mseq
  print(mseq.mseq(2,3,1,1)) # base, power, shift, which-sequence

from command line:
  ./mseq.py 2 3 1 1
  
run tests with:
  ./mseq.py test
  
--------------------------------------------------------------------------------

%        Maximum length sequence assuming 2,3,5 distinct values
%
%       [ms]=MSEQ(baseVal,powerVal[,shift,whichSeq])
%
%       OUTPUT:
%       ms = generated maximum length sequence, of length basisVal^powerVal-1
%
%       INPUT:
%          baseVal  -nuber of sequence levels (2,3, or 5 allowed)
%          powerVal -power, so that sequence length is baseVal^powerVal-1
%          shift    -cyclical shift of the sequence
%          whichSeq -sequence istantiation to use 
%          (numer of sequences varies with powerVal - see the code)
%
% (c) Giedrius T. Buracas, SNL-B, Salk Institute
% Register values are taken from: WDT Davies, System Identification
% for self-adaptive control. Wiley-Interscience, 1970
% When using mseq code for design of FMRI experiments, please, cite:
% G.T.Buracas & G.M.Boynton (2002) Efficient Design of Event-Related fMRI 
% Experiments Using M-sequences. NeuroImage, 16, 801-813.


'''

from __future__ import absolute_import, division, print_function

from builtins import str
from builtins import map
from builtins import range
import sys
import numpy


def _get_tap(baseVal, powerVal):
    """Retrieve pre-defined list of tap sequences for a given base & power, or raise ValueError.
    """
    if not baseVal in [2,3,5,9]:
        sys.exit('baseVal must be in [2,3,5,9], not %s' % str(baseVal))
    tap = []
    if baseVal == 2:
        if powerVal == 2:
            tap = [[1,2]]
        elif powerVal == 3:
            tap = [[1,3], [2,3]]
        elif powerVal == 4:
            tap = [[1,4], [3,4]]
        elif powerVal == 5:
            tap = [[2,5], [3,5], [1,2,3,5], [2,3,4,5], [1,2,4,5], [1,3,4,5]]
        elif powerVal == 6:
            tap = [[1,6], [5,6], [1,2,5,6], [1,4,5,6], [1,3,4,6], [2,3,5,6]]
        elif powerVal == 7:
            tap = [[1,7], [6,7], [3,7], [4,7], [1,2,3,7], [4,5,6,7], [1,2,5,7], [2,5,6,7],
                    [2,3,4,7], [3,4,5,7], [1,3,5,7], [2,4,6,7], [1,3,6,7], [1,4,6,7],
                    [2,3,4,5,6,7], [1,2,3,4,5,7], [1,2,4,5,6,7], [1,2,3,5,6,7] ]
        elif powerVal == 8:
            tap = [[1,2,7,8], [1,6,7,8], [1,3,5,8], [3,5,7,8], [2,3,4,8], [4,5,6,8],
                    [2,3,5,8], [3,5,6,8], [2,3,6,8], [2,5,6,8], [2,3,7,8], [1,5,6,8],
                    [1,2,3,4,6,8], [2,4,5,6,7,8], [1,2,3,6,7,8], [1,2,5,6,7,8] ]
        elif powerVal == 9:
            tap = [[4,9], [5,9], [3,4,6,9], [3,5,6,9], [4,5,8,9], [1,4,5,9], [1,4,8,9],
                    [1,5,8,9], [2,3,5,9], [4,6,7,9], [5,6,8,9], [1,3,4,9], [2,7,8,9], 
                    [1,2,7,9], [2,4,7,9], [2,5,7,9], [2,4,8,9], [1,5,7,9], [1,2,4,5,6,9],
                    [3,4,5,7,8,9], [1,3,4,6,7,9], [2,3,5,6,8,9], [3,5,6,7,8,9],
                    [1,2,3,4,6,9], [1,5,6,7,8,9], [1,2,3,4,8,9], [1,2,3,7,8,9],
                    [1,2,6,7,8,9], [1,3,5,6,8,9], [1,3,4,6,8,9], [1,2,3,5,6,9],
                    [3,4,6,7,8,9], [2,3,6,7,8,9], [1,2,3,6,7,9], [1,4,5,6,8,9],
                    [1,3,4,5,8,9], [1,3,6,7,8,9], [1,2,3,6,8,9], [2,3,4,5,6,9],
                    [3,4,5,6,7,9], [2,4,6,7,8,9], [1,2,3,5,7,9], [2,3,4,5,7,9],
                    [2,4,5,6,7,9], [1,2,4,5,7,9], [2,4,5,6,7,9], [1,3,4,5,6,7,8,9],
                    [1,2,3,4,5,6,8,9] ]
        elif powerVal == 10:
            tap = [[3,10], [7,10], [2,3,8,10], [2,7,8,10], [1,3,4,10], [6,7,9,10],
                    [1,5,8,10], [2,5,9,10], [4,5,8,10], [2,5,6,10], [1,4,9,10],
                    [1,6,9,10], [3,4,8,10], [2,6,7,10], [2,3,5,10], [5,7,8,10],
                    [1,2,5,10], [5,8,9,10], [2,4,9,10], [1,6,8,10], [3,7,9,10],
                    [1,3,7,10], [1,2,3,5,6,10], [4,5,7,8,9,10], [2,3,6,8,9,10],
                    [1,2,4,7,8,10], [1,5,6,8,9,10], [1,2,4,5,9,10], [2,5,6,7,8,10],
                    [2,3,4,5,8,10], [2,4,6,8,9,10], [1,2,4,6,8,10], [1,2,3,7,8,10],
                    [2,3,7,8,9,10], [3,4,5,8,9,10], [1,2,5,6,7,10], [1,4,6,7,9,10],
                    [1,3,4,6,9,10], [1,2,6,8,9,10], [1,2,4,8,9,10], [1,4,7,8,9,10],
                    [1,2,3,6,9,10], [1,2,6,7,8,10], [2,3,4,8,9,10], [1,2,4,6,7,10],
                    [3,4,6,8,9,10], [2,4,5,7,9,10], [1,3,5,6,8,10], [3,4,5,6,9,10],
                    [1,4,5,6,7,10], [1,3,4,5,6,7,8,10], [2,3,4,5,6,7,9,10], [3,4,5,6,7,8,9,10],
                    [1,2,3,4,5,6,7,10], [1,2,3,4,5,6,9,10], [1,4,5,6,7,8,9,10], [2,3,4,5,6,8,9,10],
                    [1,2,4,5,6,7,8,10], [1,2,3,4,6,7,9,10], [1,3,4,6,7,8,9,10]]
        elif powerVal == 11: tap = [[9,11]]
        elif powerVal == 12: tap = [[6,8,11,12]]
        elif powerVal == 13: tap = [[9,10,12,13]]
        elif powerVal == 14: tap = [[4,8,13,14]]
        elif powerVal == 15: tap = [[14,15]]
        elif powerVal == 16: tap = [[4,13,15,16]]
        elif powerVal == 17: tap = [[14,17]]
        elif powerVal == 18: tap = [[11,18]]
        elif powerVal == 19: tap = [[14,17,18,19]]
        elif powerVal == 20: tap = [[17,20]]
        elif powerVal == 21: tap = [[19,21]]
        elif powerVal == 22: tap = [[21,22]]
        elif powerVal == 23: tap = [[18,23]]
        elif powerVal == 24: tap = [[17,22,23,24]]
        elif powerVal == 25: tap = [[22,25]]
        elif powerVal == 26: tap = [[20,24,25,26]]
        elif powerVal == 27: tap = [[22,25,26,27]]
        elif powerVal == 28: tap = [[25,28]]
        elif powerVal == 29: tap = [[27,29]]
        elif powerVal == 30: tap = [[7,28,29,30]]
    elif baseVal == 3:
        if powerVal == 2:
            tap = [[2,1], [1,1]]
        elif powerVal == 3:
            tap = [[0,1,2], [1,0,2], [1,2,2], [2,1,2]]
        elif powerVal == 4:
            tap = [[0,0,2,1], [0,0,1,1], [2,0,0,1], [2,2,1,1], [2,1,1,1],
                    [1,0,0,1], [1,2,2,1], [1,1,2,1] ]
        elif powerVal == 5:
            tap = [[0,0,0,1,2], [0,0,0,1,2], [0,0,1,2,2], [0,2,1,0,2], [0,2,1,1,2],
                    [0,1,2,0,2], [0,1,1,2,2], [2,0,0,1,2], [2,0,2,0,2], [2,0,2,2,2],
                    [2,2,0,2,2], [2,2,2,1,2], [2,2,1,2,2], [2,1,2,2,2], [2,1,1,0,2],
                    [1,0,0,0,2], [1,0,0,2,2], [1,0,1,1,2], [1,2,2,2,2], [1,1,0,1,2],
                    [1,1,2,0,2]]
        elif powerVal == 6:
            tap = [[0,0,0,0,2,1], [0,0,0,0,1,1], [0,0,2,0,2,1], [0,0,1,0,1,1],
                    [0,2,0,1,2,1], [0,2,0,1,1,1], [0,2,2,0,1,1], [0,2,2,2,1,1],
                    [2,1,1,1,0,1], [1,0,0,0,0,1], [1,0,2,1,0,1], [1,0,1,0,0,1],
                    [1,0,1,2,1,1], [1,0,1,1,1,1], [1,2,0,2,2,1], [1,2,0,1,0,1],
                    [1,2,2,1,2,1], [1,2,1,0,1,1], [1,2,1,2,1,1], [1,2,1,1,2,1],
                    [1,1,2,1,0,1], [1,1,1,0,1,1], [1,1,1,2,0,1], [1,1,1,1,1,1] ]
        elif powerVal == 7:
            tap = [[0,0,0,0,2,1,2], [0,0,0,0,1,0,2], [0,0,0,2,0,2,2], [0,0,0,2,2,2,2],
                    [0,0,0,2,1,0,2], [0,0,0,1,1,2,2], [0,0,0,1,1,1,2], [0,0,2,2,2,0,2],
                    [0,0,2,2,1,2,2], [0,0,2,1,0,0,2], [0,0,2,1,2,2,2], [0,0,1,0,2,1,2],
                    [0,0,1,0,1,1,2], [0,0,1,1,0,1,2], [0,0,1,1,2,0,2], [0,2,0,0,0,2,2],
                    [0,2,0,0,1,0,2], [0,2,0,0,1,1,2], [0,2,0,2,2,0,2], [0,2,0,2,1,2,2],
                    [0,2,0,1,1,0,2], [0,2,2,0,2,0,2], [0,2,2,0,1,2,2], [0,2,2,2,2,1,2],
                    [0,2,2,2,1,0,2], [0,2,2,1,0,1,2], [0,2,2,1,2,2,2] ]
    elif baseVal == 5:
        if powerVal == 2:
            tap = [[4,3], [3,2], [2,2], [1,3]]
        elif powerVal == 3:
            tap = [[0,2,3], [4,1,2], [3,0,2], [3,4,2], [3,3,3], [3,3,2], [3,1,3],
                    [2,0,3], [2,4,3], [2,3,3], [2,3,2], [2,1,2], [1,0,2], [1,4,3], [1,1,3]]
        elif powerVal == 4:
            tap = [[0,4,3,3], [0,4,3,2], [0,4,2,3], [0,4,2,2], [0,1,4,3], [0,1,4,2],
                    [0,1,1,3], [0,1,1,2], [4,0,4,2], [4,0,3,2], [4,0,2,3], [4,0,1,3],
                    [4,4,4,2], [4,3,0,3], [4,3,4,3], [4,2,0,2], [4,2,1,3], [4,1,1,2],
                    [3,0,4,2], [3,0,3,3], [3,0,2,2], [3,0,1,3], [3,4,3,2], [3,3,0,2],
                    [3,3,3,3], [3,2,0,3], [3,2,2,3], [3,1,2,2], [2,0,4,3], [2,0,3,2],
                    [2,0,2,3], [2,0,1,2], [2,4,2,2], [2,3,0,2], [2,3,2,3], [2,2,0,3],
                    [2,2,3,3], [2,1,3,2], [1,0,4,3], [1,0,3,3], [1,0,2,2], [1,0,1,2],
                    [1,4,1,2], [1,3,0,3], [1,3,1,3], [1,2,0,2], [1,2,4,3], [1,1,4,2]]
    elif baseVal == 9:
        if powerVal == 2:
            tap = [[1,1]]
    
    if not tap:
        raise ValueError('M-sequence %.0f^%.0f is not defined by this function' % (baseVal, powerVal))
    
    return tap

def mseq(baseVal, powerVal, shift=1, whichSeq=None):
    """Return one of over 200 different M-sequences, for base 2, 3, or 5 items.
    This is a python translation of Giedrius T. Buracas' matlab implementation (mseq.m).
    Citation: G.T.Buracas & G.M.Boynton (2002) NeuroImage, 16, 801-813.
    http://www.ncbi.nlm.nih.gov/pubmed/12169264
    """
    tap = _get_tap(baseVal, powerVal) # get a list of sequences, select one seq below
    
    seq_len = baseVal ** powerVal - 1
    ms = numpy.array([0 for i in range(seq_len)])
    
    if not whichSeq:
        whichSeq = numpy.random.randint(0, len(tap))
    else:
        whichSeq -= 1 # matlab -> python indexing
        if whichSeq >= len(tap) or whichSeq < 0:
            whichSeq = whichSeq % len(tap)
            print('whichSeq wrapped around to %d' % whichSeq)
            
    # convert tap -> python numpy array; adjust for python 0-indexing
    tap_py = numpy.array(tap[whichSeq])
    if baseVal == 2: # zeros unless index is in tap
        weights = numpy.array([int(i+1 in tap_py) for i in range(powerVal)])
    elif baseVal > 2:
        weights = tap_py
    
    register = numpy.array([1 for i in range(powerVal)])
    for i in range(seq_len):
        ms[i] = (sum(weights*register) + baseVal) % baseVal
        register = numpy.append(ms[i], register[:-1])
        
    if shift:
        shift = shift % len(ms)
        ms = numpy.append(ms[shift:], ms[:shift])
    
    return numpy.array(ms)

def _center(ms, baseVal):
    if baseVal == 2:     
        ms = ms * 2 - 1
    elif baseVal == 3: 
        ms = [-1 if x == 2 else x for x in ms]
    elif baseVal == 5: 
        ms = [-1 if x == 4 else x for x in ms]
        ms = [-2 if x == 3 else x for x in ms]
    else: # baseVal == 9:
        ms = [-1 if x == 5 else x for x in ms]
        ms = [-2 if x == 6 else x for x in ms]
        ms = [-3 if x == 7 else x for x in ms]
        ms = [-4 if x == 8 else x for x in ms]
    
    return ms

def _test():
    """generate the mseq for most combinations of bases, powers, and sequences, two shift values
    (only base 9 and 2^9 and higher are skipped). assert that the autocorrelation is acceptably small.
    prints the first 10 items of the sequence, to allow checking against other implementations.
    """
    print('testing 2,3,5:')
    powers = {2:list(range(2,9)), 3:list(range(2,8)), 5:list(range(2,5)), 9:[2]}
    for base in [2,3,5]:
        for power in powers[base]:
            tap = _get_tap(base, power)
            for t in tap:
                whichSeq = tap.index(t)
                for shift in [1,4]:
                    ms = mseq(base, power, shift, whichSeq)
                    seq_len = base ** power - 1
                    print('mseq(%d,%d,%d,%d)' % (base, power, shift, whichSeq), ms[:10], 'len=%d' % seq_len, end='')
                    assert len(ms) == seq_len
                    if seq_len > 10:
                        autocorr_first10 = [numpy.corrcoef(ms, numpy.append(ms[i:], ms[:i]))[1][0] for i in range(1,10)]
                        # for base 3, autocorrelation at offset seq_len / 2 is perfectly correlated
                        max_abs_auto = max(list(map(abs, autocorr_first10)))
                        print("max_abs_autocorr_first10=%.4f < 1/(len-2)" % max_abs_auto)
                        if base == 5 and power == 2:
                            print(' *** skipping assert 5 ^ 2 (fails) ***')
                        else:
                            assert max_abs_auto < 1.0/(seq_len-2) or max_abs_auto < .10
                    else: 
                        print()
    print('2,3,5 ok; skipped auto-corr for 5^2 (fails on 0.4545); completely skipped 2^%d and higher' % (powers[2][-1] +1))
    
if __name__ == '__main__':
    if 'test' in sys.argv:
        _test()
    else:
        try:
            args = list(map(int, sys.argv[1:]))
        except Exception:
            raise ValueError("expected integer arguments: base power [shift [which-sequence]]")
        print(mseq(*args))
