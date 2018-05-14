#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# python text parser
# this is really just for the purpose of constructing code analysis in
# python scripts

from __future__ import absolute_import, print_function

from builtins import next
from builtins import object
import pyclbr
import tokenize

# xx = pyclbr.readmodule_ex('psychopy.visual')
# #xx = pyclbr.tokenize('psychopy')
# print(xx['makeRadialMatrix'].__doc__)


class tokenBuffer(object):
    # simple buffer to provide mechanism to step backwards through previous
    # tokens

    def __init__(self, token, prev):
        super(tokenBuffer, self).__init__()
        self.tok = token
        self.prev = prev


def getTokensAndImports(buffer):
    # f = open(filename, 'r')
    # gen=tokenize.generate_tokens(f.readline)
    gen = tokenize.generate_tokens(buffer.readline)
    importLines = []
    equalLines = {}
    definedTokens = {}
    prev = None
    for token in gen:
        if token[1] == 'import':
            # runs any line that contains the word import
            importLines.append(token[4].replace('\r', ''))
        elif token[1] == '=':
            equalLines[token[2][0]] = token[4]
            defineStr = ''
            prevTok = prev

            # fetch the name of the object (
            while prevTok is not None:
                if prevTok.tok[0] != 1 and prevTok.tok[1] != '.':
                    prevTok = None  # we have the full name
                else:
                    defineStr = prevTok.tok[1] + defineStr
                    prevTok = prevTok.prev

            # do we have that token already?
            if defineStr in definedTokens:
                continue
            else:
                # try to identify what new token =
                definingStr = ''
                while True:  # fetch the name of the object being defined
                    nextTok = next(gen)
                    if nextTok[0] != 1 and nextTok[1] != '.':
                        break  # we have the full name
                    else:
                        definingStr += nextTok[1]
                definedTokens[defineStr] = {'is': definingStr}

        thisToken = tokenBuffer(token, prev)
        prev = thisToken

    return importLines, definedTokens
