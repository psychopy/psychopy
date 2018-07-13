#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Converting code parameters and components from python (PsychoPy)
to JS (ES6/PsychoJS)
"""

import ast
import astunparse

class NamesJS(dict):
    def __getitem__(self, name):
        try:
            return dict.__getitem__(self, name)
        except:
            return "my.{}".format(name)

namesJS = NamesJS()
namesJS['sin'] = 'Math.sin'
namesJS['cos'] = 'Math.cos'
namesJS['tan'] = 'Math.tan'
namesJS['pi'] = 'Math.PI'
namesJS['rand'] = 'Math.random'
namesJS['random'] = 'Math.random'


def expression2js(expr):
    """Convert a short expression (e.g. a Component Parameter) Python to JS"""
    syntaxTree = ast.parse(expr)
    for node in ast.walk(syntaxTree):
        if isinstance(node, ast.Name):
            node.id = namesJS[node.id]
    return astunparse.unparse(syntaxTree).strip()


def snippet2js(expr):
    """Convert several lines (e.g. a Code Component) Python to JS"""
    # for now this is just adding ';' onto each line ending so will fail on
    # most code (e.g. if... for... will certainly fail)
    # do nothing for now
    return expr


if __name__=='__main__':
    for expr in ['sin(t)', 't*5']:
        print("{} -> {}".format(repr(expr), repr(expression2js(expr))))
