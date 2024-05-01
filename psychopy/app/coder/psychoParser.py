#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# python text parser
# this is really just for the purpose of constructing code analysis in
# python scripts
import tokenize
import re

# xx = pyclbr.readmodule_ex('psychopy.visual')
# #xx = pyclbr.tokenize('psychopy')
# print(xx['makeRadialMatrix'].__doc__)


class tokenBuffer():
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


def parsePyScript(src, indentSpaces=4):
    """Parse a Python script for the source tree viewer.

    Quick-and-dirty parser for Python files which retrieves declarations in the
    file. Used by the source tree viewer to build a structure tree. This is
    intended to work really quickly so it can handle very large Python files in
    realtime without eating up CPU resources. The parser is very conservative
    and can't handle conditional declarations or nested objects greater than one
    indent level from its parent.

    Parameters
    ----------
    src : str
        Python source code to parse.
    indentSpaces : int
        Indent spaces used by this file, default is 4.

    Returns
    -------
    list
        List of found items.

    """
    foundDefs = []
    for nLine, line in enumerate(src.split('\n')):
        lineno = nLine + 1
        lineFullLen = len(line)
        lineText = line.lstrip()
        lineIndent = int((lineFullLen - len(lineText)) / indentSpaces)  # to indent level

        # filter out defs that are nested in if statements
        if nLine > 0 and foundDefs:
            lastIndent = foundDefs[-1][2]
            if lineIndent - lastIndent > 1:
                continue

        # is definition?
        if lineText.startswith('class ') or lineText.startswith('def '):
            # slice off comment
            lineText = lineText.split('#')[0]
            lineTokens = [
                tok.strip() for tok in re.split(r' |\(|\)', lineText) if tok]
            defType, defName = lineTokens[:2]
            foundDefs.append((defType, defName, lineIndent, lineno))

        # mdc - holding off on showing attributes and imports for now
        # elif lineText.startswith('import ') and lineIndent == 0:
        #     lineText = lineText.split('#')[0]  # clean the line
        #     # check if we have a regular import statement or an 'as' one
        #     if ' as ' not in lineText:
        #         lineTokens = [
        #             tok.strip() for tok in re.split(
        #                 ' |,', lineText[len('import '):]) if tok]
        #
        #         # create a new import declaration for import if a list
        #         for name in lineTokens:
        #             foundDefs.append(('import', name, lineIndent, lineno))
        #     else:
        #         impStmt = lineText[len('import '):].strip().split(' as ')
        #         name, attrs = impStmt
        #
        #         foundDefs.append(('importas', name, lineIndent, lineno, attrs))
        # elif lineText.startswith('from ') and lineIndent == 0:
        #     pass

    return foundDefs
