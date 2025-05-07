#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Converting code parameters and components from python (PsychoPy)
to JS (ES6/PsychoJS)
"""

import ast
from pathlib import Path

import astunparse
import esprima
from os import path
from psychopy import logging

from io import StringIO
from psychopy.experiment.py2js_transpiler import translatePythonToJavaScript


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
    except Exception:
        try:
            syntaxTree = ast.parse(str(expr))
        except Exception as err:
            logging.error(err)
            return str(expr)

    for node in ast.walk(syntaxTree):
        TupleTransformer().visit(node)  # Transform tuples to list
        # for py2 using 'unicode_literals' we don't want
        if isinstance(node, ast.Str) and type(node.s)==bytes:
            node.s = str(node.s, 'utf-8')
        elif isinstance(node, ast.Str) and node.s.startswith("u'"):
            node.s = node.s[1:]
        if isinstance(node, ast.Name):
            if node.id == 'undefined':
                continue
    jsStr = unparse(syntaxTree).strip()
    if not any(ch in jsStr for ch in ("=",";","\n")):
        try:
            jsStr = translatePythonToJavaScript(jsStr)
            if jsStr.endswith(';\n'):
                jsStr = jsStr[:-2]
        except:
            # If translation fails, just use old translation
            pass
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
        elif expression.type == "ReturnStatement":
            if expression.argument.type == "FunctionExpression":
                consequentVariables = findUndeclaredVariables(
                    expression.argument.body.body, allUndeclaredVariables)
                undeclaredVariables.extend(consequentVariables)
    return undeclaredVariables


def addVariableDeclarations(inputProgram, fileName):
    """Transform the input program by adding just before each function
    a declaration for its undeclared variables
    """

    # parse Javascript code into abstract syntax tree:
    # NB: esprima: https://media.readthedocs.org/pdf/esprima/4.0/esprima.pdf
    fileName = Path(str(fileName))
    try:
        ast = esprima.parseScript(inputProgram, {'range': True, 'tolerant': True})
    except esprima.error_handler.Error as err:
        if fileName:
            logging.error(f"Error parsing JS in {fileName.name}:\n{err}")
        else:
            logging.error(f"Error parsing JS: {err}")
        logging.flush()
        return inputProgram  # So JS can be written to file

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
            funSpacing = ['', '\n'][len(undeclaredVariables) > 0]  # for consistent function spacing
            declaration = funSpacing + '\n'.join(['var ' + variable + ';' for variable in
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
