#!/usr/bin/env python
# coding: utf-8

"""
Split string in accordance with UAX#14 Unicode line breaking.

Code is based on uniseg 0.7.1 (https://pypi.org/project/uniseg/)
"""

import sys
import re
import pathlib

__all__ = [
    'get_breakable_points',
    'break_units',
]

from builtins import ord as _ord


if sys.maxunicode < 0x10000:
    # narrow unicode build
    def ord(c, index=None):
        if isinstance(c, str):
            return _ord(c[index or 0])
        # if not isinstance(c, unicode):
        #     raise TypeError('must be unicode, not %s' % type(c).__name__)
        i = index or 0
        len_s = len(c)-i
        if len_s:
            value = hi = _ord(c[i])
            i += 1
            if 0xd800 <= hi < 0xdc00:
                if len_s > 1:
                    lo = _ord(c[i])
                    i += 1
                    if 0xdc00 <= lo < 0xe000:
                        value = (hi-0xd800)*0x400+(lo-0xdc00)+0x10000
            if index is not None or i == len_s:
                return value
        raise TypeError('need a single Unicode code point as parameter')

    rx_codepoints = re.compile(r'[\ud800-\udbff][\udc00-\udfff]|.', re.DOTALL)
    
    def code_point(s, index=0):
        
        L = rx_codepoints.findall(s)
        return L[index]
    
    def code_points(s):
        
        return rx_codepoints.findall(s)

else:
    # wide unicode build
    
    def ord(c, index=None):
        return _ord(c if index is None else c[index])
    
    def code_point(s, index=0):
        return s[index or 0]
    
    def code_points(s):
        return list(s)

def _read_uax14_table():
    """Reads in 'LineBreak.txt' as a dictionary of codes

    Reading and parsing the file takes roughly 70ms (macbook pro 2022)
    LineBreak.txt comes from from https://www.unicode.org/reports/tr14/"""
    # read in the LineBreak spec file for UAX14 (takes ~70ms)
    with open(pathlib.Path(__file__).parent / 'LineBreak.txt') as f:
        lb_table = {}
        for row in f.readlines():
            # remove comments
            code = row.split('#')[0].strip()
            if code:  # was it ONLY comments?
                # could be range (02E0..02E4;AL) or single (02DF;BB)
                chars, this_lb = code.split(';')
                if '..' in chars:
                    # range of vals
                    start, stop = [int(val, base=16) for val in chars.split('..')]
                    for charcode in range(start, stop + 1):
                        lb_table[charcode] = this_lb
                else:
                    # single val
                    lb_table[int(chars, base=16)] = this_lb
    return lb_table

line_break_table = _read_uax14_table()

BK = 'BK'   # Mandatory Break
CR = 'CR'   # Carriage Return
LF = 'LF'   # Line Feed
CM = 'CM'   # Combining Mark
NL = 'NL'   # Next Line
SG = 'SG'   # Surrogate
WJ = 'WJ'   # Word Joiner
ZW = 'ZW'   # Zero Width Space
GL = 'GL'   # Non-breaking ("Glue")
SP = 'SP'   # Space
B2 = 'B2'   # Break Opportunity Before and After
BA = 'BA'   # Break After
BB = 'BB'   # Break Before
HY = 'HY'   # Hyphen
CB = 'CB'   # Contingent Break Opportunity
CL = 'CL'   # Close Punctuation
CP = 'CP'   # Close Parenthesis
EX = 'EX'   # Exclamation/Interrogation
IN = 'IN'   # Inseparable
NS = 'NS'   # Nonstarter
OP = 'OP'   # Open Punctuation
QU = 'QU'   # Quotation
IS = 'IS'   # Infix Numeric Separator
NU = 'NU'   # Numeric
PO = 'PO'   # Postfix Numeric
PR = 'PR'   # Prefix Numeric
SY = 'SY'   # Symbols Allowing Break After
AI = 'AI'   # Ambiguous (Alphabetic or Ideographic)
AL = 'AL'   # Alphabetic
CJ = 'CJ'   # Conditional Japanese Starter
H2 = 'H2'   # Hangul LV Syllable
H3 = 'H3'   # Hangul LVT Syllable
HL = 'HL'   # Hebrew Letter
ID = 'ID'   # Ideographic
JL = 'JL'   # Hangul L Jamo
JV = 'JV'   # Hangul V Jamo
JT = 'JT'   # Hangul T Jamo
RI = 'RI'   # Regional Indicator
SA = 'SA'   # Complex Context Dependent (South East Asian)
XX = 'XX'   # Unknown

def line_break(c, index=0):
    code = ord(code_point(c, index))
    if code in line_break_table:
        return line_break_table[code]
    return 'Other'

def break_units(s, breakables):
    """
    Split a sequence at given breakpoint. This returns a generator object.
    So do `list(break_units(s, breakables))` to get the result as a list.
    
    :Parameters:
    
        s:
            A string (or sequence) to be split.

        breakables:
            A sequence of 0/1 of the same length of s. 1 represents that 
            the input sequence is breakable at that point.
            See also get_breakable_points().
    """
    i = 0
    for j, bk in enumerate(breakables):
        if bk:
            if j:
                yield s[i:j]
            i = j
    if s:
        yield s[i:]

def _preprocess_boundaries(s):
    prev_prop = None
    i = 0
    for c in code_points(s):
        prop = line_break(c)
        if prop in (BK, CR, LF, SP, NL, ZW):
            yield (i, prop)
            prev_prop = None
        elif prop == CM:
            if prev_prop is None:
                yield (i, prop)
                prev_prop = prop
        else:
            yield (i, prop)
            prev_prop = prop
        i += len(c)

def get_breakable_points(s):
    """
    Returns a generator object that yields 1 if the next character is
    breakable, otherwise yields 0.
    Do `list(get_breakable_points(s))` to get a list of breakable points.
    
    :Parameters:
    
        s:
            Sentence to be parsed.
    """
    if not s:
        return
    
    primitive_boundaries = list(_preprocess_boundaries(s))
    prev_prev_lb = None
    prev_lb = None
    for i, (pos, lb) in enumerate(primitive_boundaries):
        next_pos, __ = (primitive_boundaries[i+1]
                        if i<len(primitive_boundaries)-1 else (len(s), None))
        
        if lb == AI:
            lb = AL
        
        if lb == CJ:
            lb = NS

        if lb in (CM, XX, SA):
            lb = AL
        # LB4
        if pos == 0:
            do_break = False
        elif prev_lb == BK:
            do_break = True
        # LB5
        elif prev_lb in (CR, LF, NL):
            do_break = not (prev_lb == CR and lb == LF)
        # LB6
        elif lb in (BK, CR, LF, NL):
            do_break = False
        # LB7
        elif lb in (SP, ZW):
            do_break = False
        # LB8
        elif ((prev_prev_lb == ZW and prev_lb == SP) or (prev_lb == ZW)):
            do_break = True
        # LB11
        elif lb == WJ or prev_lb == WJ:
            do_break = False
        # LB12
        elif prev_lb == GL:
            do_break = False
        # LB12a
        elif prev_lb not in (SP, BA, HY) and lb == GL:
            do_break = False
        # LB13
        elif lb in (CL, CP, EX, IS, SY):
            do_break = False
        # LB14
        elif (prev_prev_lb == OP and prev_lb == SP) or prev_lb == OP:
            do_break = False
        # LB15
        elif ((prev_prev_lb == QU and prev_lb == SP and lb == OP)
              or (prev_lb == QU and lb == OP)):
            do_break = False
        # LB16
        elif ((prev_prev_lb in (CL, CP) and prev_lb == SP and lb == NS)
              or (prev_lb in (CL, CP) and lb == NS)):
            do_break = False
        # LB17
        elif ((prev_prev_lb == B2 and prev_lb == SP and lb == B2)
              or (prev_lb == B2 and lb == B2)):
            do_break = False
        # LB18
        elif prev_lb == SP:
            do_break = True
        # LB19
        elif lb == QU or prev_lb == QU:
            do_break = False
        # LB20
        elif lb == CB or prev_lb == CB:
            do_break = True
        # LB21
        elif lb in (BA, HY, NS) or prev_lb == BB:
            do_break = False
        # LB22
        elif prev_lb in (AL, HL, ID, IN, NU) and lb == IN:
            do_break = False
        # LB23
        elif ((prev_lb == ID and lb == PO)
              or (prev_lb in (AL, HL) and lb == NU)
              or (prev_lb == NU and lb in (AL, HL))):
            do_break = False
        # LB24
        elif ((prev_lb == PR and lb == ID)
              or (prev_lb == PR and lb in (AL, HL))
              or (prev_lb == PO and lb in (AL, HL))):
            do_break = False
        # LB25
        elif ((prev_lb == CL and lb == PO)
              or (prev_lb == CP and lb == PO)
              or (prev_lb == CL and lb == PR)
              or (prev_lb == CP and lb == PR)
              or (prev_lb == NU and lb == PO)
              or (prev_lb == NU and lb == PR)
              or (prev_lb == PO and lb == OP)
              or (prev_lb == PO and lb == NU)
              or (prev_lb == PR and lb == OP)
              or (prev_lb == PR and lb == NU)
              or (prev_lb == HY and lb == NU)
              or (prev_lb == IS and lb == NU)
              or (prev_lb == NU and lb == NU)
              or (prev_lb == SY and lb == NU)):
            do_break = False
        # LB26
        elif ((prev_lb == JL and lb in (JL, JV, H2, H3))
              or (prev_lb in (JV, H2) and lb in (JV, JT))
              or (prev_lb in (JT, H3) and lb == JT)):
            do_break = False
        # LB27
        elif ((prev_lb in (JL, JV, JT, H2, H3) and lb in (IN, PO))
              or (prev_lb == PR and lb in (JL, JV, JT, H2, H3))):
            do_break = False
        # LB28
        elif prev_lb in (AL, HL) and lb in (AL, HL):
            do_break = False
        # LB29
        elif prev_lb == IS and lb in (AL, HL):
            do_break = False
        # LB30
        elif ((prev_lb in (AL, HL, NU) and lb == OP)
              or (prev_lb == CP and lb in (AL, HL, NU))):
            do_break = False
        # LB30a
        elif prev_lb == lb == RI:
            do_break = False
        else:
            do_break = True
        for j in range(next_pos-pos):
            yield int(j==0 and do_break)
        prev_prev_lb = prev_lb
        prev_lb = lb
