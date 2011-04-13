#!/usr/bin/env python
'''
%		Maximum length sequence assuming 2,3,5 distinct values
%
%       [ms]=MSEQ(baseVal,powerVal[,shift,whichSeq])
%
%       OUTPUT:
%       ms = generated maximum length sequence, of length basisVal^powerVal-1
%
%       INPUT:
%		  baseVal  -nuber of sequence levels (2,3, or 5 allowed)
%		  powerVal -power, so that sequence length is baseVal^powerVal-1
%		  shift    -cyclical shift of the sequence
%		  whichSeq -sequence istantiation to use 
%		  (numer of sequences varies with powerVal - see the code)

% (c) Giedrius T. Buracas, SNL-B, Salk Institute
% Register values are taken from: WDT Davies, System Identification
% for self-adaptive control. Wiley-Interscience, 1970
% When using mseq code for design of FMRI experiments, please, cite:
% G.T.Buracas & G.M.Boynton (2002) Efficient Design of Event-Related fMRI 
% Experiments Using M-sequences. NeuroImage, 16, 801-813.


Python translation from matlab & tests:
  (c) Jeremy R. Gray, April 2011; BSD license
  original from: http://www.mathworks.com/matlabcentral/fileexchange/990-m-sequence-generation-program

script usage:
  import mseq
  print mseq.mseq(2,3,1,1)

command line:
  ./mseq.py 2 3 1 1
run tests with:
  ./mseq.py test
'''

import sys
import numpy as np

def _get_tap(baseVal, powerVal):
    """Given requested base and power, retrieve pre-defined tap values.
       NB: matlab is 1-indexed and python 0-indexed; copied from mseq.m, adjusted elsewhere
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
        raise ValueError, 'M-sequence %.0f^%.0f is not defined by this function' % (baseVal, powerVal)
    
    return tap

def mseq(baseVal, powerVal, shift=1, whichSeq=None):
    """Return an M-sequence.
    """
    tap = _get_tap(baseVal, powerVal)
    bitNum = baseVal ** powerVal - 1
    ms = np.array([0 for i in range(bitNum)])
    
    if not whichSeq:
        whichSeq = np.random.randint(0, len(tap))
    else:
        whichSeq -= 1 # matlab -> python indexing
        if whichSeq >= len(tap) or whichSeq < 0:
            print 'whichSeq wrapping around!'
            whichSeq = whichSeq % len(tap)
    
    # convert tap -> python numpy array; adjust for python 0-indexing
    tap_py = np.array(tap[whichSeq])
    if baseVal == 2: # zeros unless index is in tap
        weights = np.array([int(i+1 in tap_py) for i in range(powerVal)])
    elif baseVal > 2:
        weights = tap_py
    
    register = np.array([1 for i in range(powerVal)])
    for i in range(bitNum):
        ms[i] = (sum(weights*register) + baseVal) % baseVal
        register = np.append(ms[i], register[:-1])
        
    if shift:
        shift = shift % len(ms)
        ms = np.append(ms[shift:], ms[:shift])
        
    if baseVal == 2:     
        ms = ms * 2 - 1
    elif baseVal == 3: 
        ms = map(lambda x: -1 if x == 2 else x, ms)
    elif baseVal == 5: 
        ms = map(lambda x: -1 if x == 4 else x, ms)
        ms = map(lambda x: -2 if x == 3 else x, ms)
    else: # baseVal == 9:
        ms = map(lambda x: -1 if x == 5 else x, ms)
        ms = map(lambda x: -2 if x == 6 else x, ms)
        ms = map(lambda x: -3 if x == 7 else x, ms)
        ms = map(lambda x: -4 if x == 8 else x, ms)
    
    return np.array(ms)

def test():
    print 'testing 2,3,5:'
    powers = {2:range(2,16), 3:range(2,8), 5:range(2,5), 9:[2]}
    for base in [2,3,5]:
        for power in powers[base]:
            tap = _get_tap(base, power)
            for t in tap:
                whichSeq = tap.index(t)
                for shift in [1,4]:
                    ms = mseq(base, power, shift, whichSeq)
                    bitNum = base ** power - 1
                    autoc = [np.corrcoef(ms, np.append(ms[i:], ms[:i]))[1][0] for i in range(1,4)]
                    max_abs_auto = max(map(abs,autoc))
                    print 'mseq(%d,%d,%d,%d)' % (base, power, shift, whichSeq), ms[:10],
                    assert len(ms) == bitNum
                    if bitNum > 10:
                        assert max_abs_auto < 1./(bitNum-2)
                        print "max_abs_autocorr_1234=%.2f < 1/(n-2)" % max_abs_auto
                    else: print
                    if base == 2: assert sum(ms) == 1
                    if base in [3,5]: assert sum(ms) == 0
    assert sum(mseq(3,3) - list([0, -1, 0, -1,  1, -1, -1,  1,  0, -1, -1, -1,  0,  0,  1,  0,  1, -1,  1,  1, -1, 0,  1,  1,  1, 0])) == 0    
    assert sum(mseq(2,5) - list([ 1, -1, -1, -1, 1, -1, -1, 1 ,-1, 1, -1, 1, 1, -1, -1, -1, -1, 1, 1, 1, -1, -1, 1, 1, -1, 1, 1, 1, 1, 1, -1])) == 0
    assert sum(mseq(5,4,1,1)[:10] - list([0, 1, -2, -1, 0, -2, 1, -1, -2, -2])) == 0
    print '2,3,5 ok; skipped 2^%d and higher' % (powers[2][-1] +1)
    
if __name__ == '__main__':
    if 'test' in sys.argv:
        test()
    else:
        try:
            args = map(int, sys.argv[1:])
        except:
            raise ValueError, "expected integer arguments: base, power, shift, which-sequence"
        ms =  mseq(*args)
        print ms
    