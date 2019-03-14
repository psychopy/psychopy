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
import esprima
from psychopy.constants import PY3
from psychopy import logging

if PY3:
    from past.builtins import unicode
    from io import StringIO
else:
    from StringIO import StringIO


class NamesJS(dict):
    def __getitem__(self, name):
        try:
            return dict.__getitem__(self, name)
        except:
            return "{}".format(name)


namesJS = NamesJS()
namesJS['sin'] = 'Math.sin'
namesJS['cos'] = 'Math.cos'
namesJS['tan'] = 'Math.tan'
namesJS['pi'] = 'Math.PI'
namesJS['rand'] = 'Math.random'
namesJS['random'] = 'Math.random'


class TupleTransformer(ast.NodeTransformer):
    """ An ast subclass that walks the abstract syntax tree and
    allows modification of nodes.

    This class transforms a tuple to a list.

    :returns node
    """
    def visit_Tuple(self, node):
        return ast.List(node.elts, node.ctx)

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

    # if the code contains a tuple (anywhere), convert parenths to be list.
    # This now works for compounds like `(2*(4, 5))` where the inner
    # parenths becomes a list and the outer parens indicate priority.
    # This works by running an ast transformer class to swap the contents of the tuple
    # into a list for the number of tuples in the expression.
    try:
        syntaxTree = ast.parse(expr)
    except Exception as err:
        logging.error(err)
        syntaxTree = ast.parse(unicode(expr))

    for node in ast.walk(syntaxTree):
        TupleTransformer().visit(node)  # Transform tuples to list
        # for py2 using 'unicode_literals' we don't want
        if isinstance(node, ast.Str) and type(node.s)==bytes:
            node.s = unicode(node.s, 'utf-8')
        elif isinstance(node, ast.Str) and node.s.startswith("u'"):
            node.s = node.s[1:]
        if isinstance(node, ast.Name):
            if node.id == 'undefined':
                continue
            node.id = namesJS[node.id]
    jsStr = unparse(syntaxTree).strip()
    return jsStr

def snippet2js(expr):
    """Convert several lines (e.g. a Code Component) Python to JS"""
    # for now this is just adding ';' onto each line ending so will fail on
    # most code (e.g. if... for... will certainly fail)
    # do nothing for now
    return expr


def findUndeclaredVariables(ast, allUndeclaredVariables):
    """Detect undeclared variables
    """
    undeclaredVariables = []

    for expression in ast:
        if expression.type == 'ExpressionStatement':
            expression = expression.expression
            if expression.type == 'AssignmentExpression' and expression.operator == '=' and expression.left.type == 'Identifier':
                variableName = expression.left.name
                if variableName not in allUndeclaredVariables:
                    undeclaredVariables.append(variableName)
                    allUndeclaredVariables.append(variableName)

        elif expression.type == 'IfStatement':
            if expression.consequent.body is None:
                consequentVariables = findUndeclaredVariables(
                        [expression.consequent], allUndeclaredVariables)
            else:
                consequentVariables = findUndeclaredVariables(
                    expression.consequent.body, allUndeclaredVariables)
            undeclaredVariables.extend(consequentVariables)

    return undeclaredVariables


def addVariableDeclarations(inputProgram):
    """Transform the input program by adding just before each function
    a declaration for its undeclared variables
    """

    # parse Javascript code into abstract syntax tree:
    # NB: esprima: https://media.readthedocs.org/pdf/esprima/4.0/esprima.pdf
    ast = esprima.parseScript(inputProgram, {'range': True, 'tolerant': True})

    # find undeclared vars in functions and declare them before the function
    outputProgram = inputProgram
    offset = 0
    allUndeclaredVariables = []

    for expression in ast.body:
        if expression.type == 'FunctionDeclaration':
            # find all undeclared variables:
            undeclaredVariables = findUndeclaredVariables(expression.body.body,
                                                          allUndeclaredVariables)

            # add declarations (var) just before the function:
            declaration = '\n'.join(['var ' + variable + ';' for variable in
                                     undeclaredVariables]) + '\n'
            startIndex = expression.range[0] + offset
            outputProgram = outputProgram[
                            :startIndex] + declaration + outputProgram[
                                                         startIndex:]
            offset += len(declaration)

    return outputProgram


if __name__ == '__main__':
    for expr in ['sin(t)', 't*5',
                 '(3, 4)', '(5*-2)',  # tuple and not tuple
                 '(1,(2,3), (1,2,3), (-4,-5,-6))', '2*(2, 3)',  # combinations
                 '[1, (2*2)]',  # List with nested operations returns list + nested tuple
                 '(.7, .7)',  # A tuple returns list
                 '(-.7, .7)',  # A tuple with unary operators returns nested lists
                 '[-.7, -.7]',  # A list with unary operators returns list with nested tuple
                 '[-.7, (-.7 * 7)]']:  # List with unary operators and nested tuple with operations returns list + tuple
        print("{} -> {}".format(repr(expr), repr(expression2js(expr))))
