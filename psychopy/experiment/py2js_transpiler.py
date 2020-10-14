#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import ast
import sys
import re

try:
    from metapensiero.pj.api import translates
except ImportError:
    pass  # metapensiero not installed

import astunparse


class psychoJSTransformer(ast.NodeTransformer):
    """PsychoJS-specific AST transformer
    """

    def visit_Name(self, node):
        # status = STOPPED => status = PsychoJS.Status.STOPPED
        if node.id in ['STARTED', 'FINISHED', 'STOPPED'] and isinstance(node.ctx, ast.Load):
            return ast.copy_location(
                ast.Attribute(
                    value=ast.Attribute(
                        value=ast.Name(id='PsychoJS', ctx=ast.Load()),
                        attr='Status',
                        ctx=ast.Load()
                    ),
                    attr=node.id,
                    ctx=ast.Load()
                ),
                node)

        # return the node by default:
        return node


class pythonTransformer(ast.NodeTransformer):
    """Python-specific AST transformer
    """

    # builtin python operations that require substitution by specific JavaScript code:
    subtitutableOperations = []

    # operations from the math python module or builtin operations that exist in JavaScript Math:
    directMathOperations = ['abs', 'min', 'max', 'round', 'ceil', 'fabs', 'floor', 'trunc', 'exp', 'log', 'log2', 'pow',
                            'sqrt', 'acos', 'asin', 'atan2', 'cos', 'sin', 'tan', 'acosh', 'asinh', 'atanh', 'cosh',
                            'sinh', 'tanh']

    def visit_BinOp(self, node):

        # formatted strings with %:
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str):
            raise Exception('string formatting using % is not currently supported, please use f-strings instead')

        return node

    def visit_FormattedValue(self, node):

        # unformatted f-strings:
        if not node.format_spec:
            return node

        # formatted f-strings:
        if isinstance(node.format_spec, ast.JoinedStr) and len(node.format_spec.values) > 0 and isinstance(
                node.format_spec.values[0], ast.Str):

            # split the format:
            format = node.format_spec.values[0].s
            match = re.search(r"([0-9]*).([0-9]+)(f|i)", format)
            if not match:
                raise Exception(format + ' format is not currently supported')

            matchGroups = match.groups()
            width = matchGroups[0]
            width = int(width) if width != '' else 1
            precision = matchGroups[1]
            precision = int(precision) if precision != '' else 1
            conversion = matchGroups[2]
            value = node.value

            # prepare the conversion:
            conversionFunc = ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='Number', ctx=ast.Load()),
                    attr='parseFloat' if conversion == 'f' else 'parseInt',
                    ctx=ast.Load()
                ),
                args=[value],
                keywords=[]
            )

            # deal with precision:
            precisionCall = ast.Call(
                func=ast.Attribute(
                    value=conversionFunc,
                    attr='toPrecision',
                    ctx=ast.Load()
                ),
                args=[ast.Num(n=precision)],
                keywords=[]
            )

            # deal with width:
            widthCall = ast.Call(
                func=ast.Name(id='pad', ctx=ast.Load()),
                args=[precisionCall, ast.Num(n=width)],
                keywords=[]
            )

            # return the node:
            node.value = widthCall
            node.conversion = -1
            node.format_spec = None

            return node

        raise Exception('formatted f-string are not all supported at the moment')

    def visit_Call(self, node):

        # if the call node has arguments, transform them first:
        nbArgs = len(node.args)
        for i in range(0, nbArgs):
            node.args[i] = pythonTransformer().visit(node.args[i])

        # operations with module prefix, e.g. a = math.fabs(-1.2)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            prefix = node.func.value.id
            attribute = node.func.attr

            if prefix == 'math':
                return self.mathTransform(attribute, node.args)
            else:
                return node

        # operations without prefix:
        elif isinstance(node.func, ast.Name):
            attribute = node.func.id

            # check whether this is a math operation:
            mathNode = self.mathTransform(attribute, node.args)
            if mathNode:
                return mathNode

        # string.format(args):
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value,
                                                                 ast.Str) and node.func.attr == 'format':
            raise Exception('format() is not supported at the moment, please use f-strings instead')

        # return the node by default:
        return node

    def mathTransform(self, attribute, args):

        # operations from the math python module or builtin operations that exist in JavaScript Math:
        if attribute in self.directMathOperations:
            func = ast.Attribute(
                value=ast.Name(id='Math', ctx=ast.Load()),
                attr=attribute,
                ctx=ast.Load()
            )

            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # substitutable operations, e.g. a = sum(b,c) => a = [b,c].reduce( function(x,y) { return x+y: })
        elif attribute in self.subtitutableOperations:
            # a = sum(b,c) => a = [b,c].reduce( function(x,y) { return x+y: })
            pass  # removed for now in preference for creating the func in utils

        else:
            return None


class pythonAddonVisitor(ast.NodeVisitor):
    # operations that require an addon:
    addonOperations = ['list', 'pad']

    def __init__(self):
        self.addons = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in self.addonOperations:
            self.addons.append(node.func.id)


def transformNode(astNode):
    """Transform the input AST

    Args:
        astNode (ast.Node): the input AST

    Returns:
        ast.Node: transformed AST
    """

    # deal with PsychoJS specific changes:
    psychoJSTransformedNode = psychoJSTransformer().visit(astNode)

    # deal with python specific changes:
    pythonBuiltinTransformedNode = pythonTransformer().visit(psychoJSTransformedNode)

    # look for operations requiring an addon:
    visitor = pythonAddonVisitor()
    visitor.visit(psychoJSTransformedNode)

    return pythonBuiltinTransformedNode, visitor.addons


def transformPsychoJsCode(psychoJsCode, addons):
    """Transform the input PsychoJS code.

    Args:
        psychoJsCode (str): the input PsychoJS JavaScript code

    Returns:
        (str) the transformed code
    """

    transformedPsychoJSCode = ''

    # add addons on a need-for basis:
    if 'list' in addons:
        transformedPsychoJSCode += """
        // add-on: list(s: string): string[]
        function list(s) {
            // if s is a string, we return a list of its characters
            if (typeof s === 'string')
                return s.split('');
            else
                // otherwise we return s:
                return s;
        }

        """

    if 'pad' in addons:
        transformedPsychoJSCode += """
        // add-on: pad(n: number, width: number): string
        function pad(n, width) {
            width = width || 2;
            integerPart = Number.parseInt(n);
            decimalPart = (n+'').match(/\.[0-9]*/);
            if (!decimalPart)
                decimalPart = '';
            return (integerPart+'').padStart(width,'0') + decimalPart;
        }

        """

    lines = psychoJsCode.splitlines()

    # remove the initial variable declarations, unless it is for _pj:
    if lines[0].find('var _pj;') == 0:
        transformedPsychoJSCode = 'var _pj;\n'
        startIndex = 1
    else:
        startIndex = 0

    if lines[startIndex].find('var') == 0:
        startIndex += 1

    for index in range(startIndex, len(lines)):
        transformedPsychoJSCode += lines[index]
        transformedPsychoJSCode += '\n'

    return transformedPsychoJSCode


def translatePythonToJavaScript(psychoPyCode):
    """Translate PsychoPy python code into PsychoJS JavaScript code.

    Args:
        psychoPyCode (str): the input PsychoPy python code

    Returns:
        str: the PsychoJS JavaScript code

    Raises:
        (Exception): whenever a step of the translation process failed
    """

    # get the Abstract Syntax Tree (AST)
    # this checks that the code is valid python
    try:
        astNode = ast.parse(psychoPyCode)
    # print('>>> AST node: ' + ast.dump(astNode))
    except Exception as error:
        raise Exception('unable to parse the PsychoPy code into an abstract syntax tree: ' + str(error))

    # transform the AST by making PsychoJS-specific substitutions and dealing with python built-ins:
    try:
        transformedAstNode, addons = transformNode(astNode)
    # print('>>> transformed AST node: ' + ast.dump(transformedAstNode))
    # print('>>> addons: ' + str(addons))
    except Exception as error:
        raise Exception('unable to transform the abstract syntax tree: ' + str(error))

    # turn the transformed AST into code:
    try:
        transformedPsychoPyCode = astunparse.unparse(transformedAstNode)
    # print('>>> transformed PsychoPy code:\n' + transformedPsychoPyCode)
    except Exception as error:
        raise Exception('unable to turn the transformed abstract syntax tree back into code: ' + str(error))

    # translate the python code into JavaScript code:
    try:
        psychoJsCode, psychoJsSourceMap = translates(transformedPsychoPyCode, enable_es6=True)
    # print('>>> PsychoJS code:\n' + psychoJsCode)
    except Exception as error:
        raise Exception(
            'unable to translate the transformed PsychoPy code into PsychoJS JavaScript code: ' + str(error))

    # transform the JavaScript code:
    try:
        transformedPsychoJsCode = transformPsychoJsCode(psychoJsCode, addons)
    except Exception as error:
        raise Exception('unable to transform the PsychoJS JavaScript code: ' + str(error))

    return transformedPsychoJsCode


def main(argv=None):
    """Read PsychoPy code from the command line and translate it into PsychoJS code.
    """

    # other read PsychoPy code from the command line:
    print('Enter PsychoPY code (finish with Ctrl+Z):')
    psychoPyCode = sys.stdin.read()

    # translate it to PsychoJS:
    psychoJSCode = translatePythonToJavaScript(psychoPyCode)
    print('>>> translated PsychoJS code:\n' + psychoJSCode)


if __name__ == "__main__":
    main()
