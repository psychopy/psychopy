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
from psychopy.constants import PY3
if PY3:
    from io import StringIO
else:
    from StringIO import StringIO

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


class Unparser(astunparse.Unparser):
    """astunparser had buried the future_imports option underneath its init()
    so we need to override that method and change it."""

    def __init__(self, tree, file):
        """Unparser(tree, file=sys.stdout) -> None.
         Print the source for tree to file."""
        self.f = file
        self.future_imports = ['unicode_literals']
        self._indent = 0
        self.dispatch(tree)
        self.f.flush()

def unparse(tree):
    v = StringIO()
    Unparser(tree, file=v)
    return v.getvalue()


def expression2js(expr):
    """Convert a short expression (e.g. a Component Parameter) Python to JS"""
    syntaxTree = ast.parse(expr)
    wasTuple = False
    for node in ast.walk(syntaxTree):
        if isinstance(node, ast.Str) and node.s.startswith("u'"):
            node.s = node.s[1:]
            print(node.s)
        if isinstance(node, ast.Name):
            if node.id == 'undefined':
                continue
            node.id = namesJS[node.id]
        if isinstance(node, ast.Tuple):
            wasTuple = True
    jsStr = unparse(syntaxTree).strip()
    # if the code contained a tuple (anywhere) convert parenths to be list
    # NB this won't be good for compounds like `(2*(4, 5))` where the inner
    # parenths are a list and the outer parens are indicating priority.
    # Would be better to convert a Tuple node into a List node with same
    # and then the JS would work fine!
    if wasTuple:
        jsStr = jsStr.replace('(', '[').replace(')', ']')
    return jsStr


def snippet2js(expr):
    """Convert several lines (e.g. a Code Component) Python to JS"""
    # for now this is just adding ';' onto each line ending so will fail on
    # most code (e.g. if... for... will certainly fail)
    # do nothing for now
    return expr


if __name__=='__main__':
    for expr in ['sin(t)', 't*5',
                 '(3, 4)', '(5*2)',  # tuple and not tuple
                 '(1,(2,3))', '2*(2, 3)']:  # combinations
        print("{} -> {}".format(repr(expr), repr(expression2js(expr))))
