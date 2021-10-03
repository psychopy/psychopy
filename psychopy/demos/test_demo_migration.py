#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Migration helper script for Coder demos: test the conversion

  For all demos (there are ~70 or so total):
    compare updated style script against existing script
    ignore things that we intend to change, including:
      initial comment about the demo
      whitespace, upper/lower case, use of underscore (in var names, but doesn't check that specifically)
      myWin -> win
      PatchStim -> GratingStim
      win.close() present / absent
      core.quit() present / absent
      leading comment
      shebang, encoding
"""
from __future__ import absolute_import, print_function

import glob, os
import io


def get_contents(f1, f2):
    with io.open(f1, 'r', encoding='utf-8-sig') as f:
        f1r = f.read()
    with io.open(f2, 'r', encoding='utf-8-sig') as f:
        f2r = f.read()

    return f1r, f2r

def remove_shbang(f1, f2):
    if f1.startswith('#!'):
        f1 = f1.split('\n', 1)[1]
    if f2.startswith('#!'):
        f2 = f2.split('\n', 1)[1]
    return f1, f2

def remove_encoding(f1, f2):
    if f1.startswith('# -*- coding:'):
        f1 = f1.split('\n', 1)[1]
    if f2.startswith('# -*- coding:'):
        f2 = f2.split('\n', 1)[1]
    return f1, f2

def remove_licence_future(f1, f2):
    license = '# The contents of this file are in the public domain.'
    future = 'from __future__ import division'
    return f1.replace(license, '').replace(future, ''), f2.replace(license, '').replace(future, '')

def remove_first_comment(f1, f2):
    # call after remove_shbang
    # ignore blank lines
    # remove lines starting with #
    # ignore multi-line """ or ''' comments

    f1s = [line for line in f1.splitlines() if line.strip() and not line.strip().startswith('#')]
    f2s = [line for line in f2.splitlines() if line.strip() and not line.strip().startswith('#')]
    
    if not f1s or not f2s:
        return f1, f2
    for delim in ['"""', "'''"]:
        for f in (f1s, f2s):
            if delim in f[0]:
                if len(f[0].split(delim)) == 2:
                    f.pop(0)
                    while not delim in f[0]:
                        f.pop(0)
                f.pop(0)
        
    return '\n'.join(f1s), '\n'.join(f2s)

def remove_semicolon(f1, f2):
    lines = f1.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            continue
        if line.strip().endswith(';'):
            lines[i] = line.strip('; ')
    f1 = '\n'.join(lines)
    
    lines = f2.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            continue
        if line.strip().endswith(';'):
            lines[i] = line.strip('; ')
    f2 = '\n'.join(lines)
    
    return f1, f2

def replace_PatchStim(f1, f2):
    return f1.replace('PatchStim', 'GratingStim'), f2.replace('PatchStim', 'GratingStim')

def replace_myWin_win(f1, f2):
    f1, f2 = f1.replace('myWin', 'win'), f2.replace('myWin', 'win')
    if 'iohub' in f1:
        f1 = f1.replace('window', 'win')
    if 'iohub' in f2:
        f2 = f2.replace('window', 'win')
    return f1.replace('win.update()', 'win.flip'), f2.replace('win.update()', 'win.flip')
    
def remove_core_quit(f1, f2):
    return f1.replace('core.quit()', ''), f2.replace('core.quit()', '')

def remove_win_close(f1, f2):
    return f1.replace('win.close()', ''), f2.replace('win.close()', '')

def flatten_content(f1, f2):
    f1r = f1.replace(' ', '').replace('\n', '').replace('_', '')
    f2r = f2.replace(' ', '').replace('\n', '').replace('_', '')
    return f1r.lower().strip(), f2r.lower().strip()

def replace_xrange(f1, f2):
    return f1.replace('xrange', 'range'), f2.replace('xrange', 'range')
    
def process_files(f1, f2):
    """Compare contents, ignoring differences in eoln, whitespace,underline, caps
    and various code conventions (win, myWin)
    """
    f = get_contents(f1, f2)
    if not len(f[0].strip()) and not len(f[1].strip()):
        return True, True
    f = remove_shbang(*f)
    f = remove_encoding(*f)
    f = remove_licence_future(*f)
    f = remove_first_comment(*f)  # do after license_future
    f = replace_PatchStim(*f)
    f = replace_xrange(*f)
    f = replace_myWin_win(*f)
    f = remove_semicolon(*f)
    f = remove_win_close(*f)
    f = remove_core_quit(*f)
    f = flatten_content(*f)
    return f

if __name__ == '__main__':
    dirs = [d for d in glob.glob('coder/*') if os.path.isdir(d)]
    print('all pass unless noted')
    for d in dirs:
        p = glob.glob(d+'/*.py')
        for f1 in p:
            if '__init__.py' in f1:
                continue
            f2 = f1.replace('coder/', 'coder_updated/')
            t1, t2 = process_files(f1, f2)
            if not t1 == t2:
                print('FAILED', f1)
                t = t1[0]
                i = 0
                while t2.startswith(t):
                    i += 1
                    t += t1[i]
                print('    ' + t[:-1] + ' |---')
                #print t1, '\n', t2
                
