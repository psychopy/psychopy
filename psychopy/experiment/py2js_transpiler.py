#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
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
        # status = STOPPED --> status = PsychoJS.Status.STOPPED
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

        # thisExp --> psychoJS.experiment
        elif node.id == 'thisExp' and isinstance(node.ctx, ast.Load):
            return ast.Attribute(
                value=ast.Name(id='psychoJS', ctx=ast.Load()),
                attr='experiment',
                ctx=ast.Load()
            )

        # win --> psychoJS.window
        elif node.id == 'win' and isinstance(node.ctx, ast.Load):
            return ast.Attribute(
                value=ast.Name(id='psychoJS', ctx=ast.Load()),
                attr='window',
                ctx=ast.Load()
            )

        # event --> psychoJS.eventManager
        elif node.id == 'event' and isinstance(node.ctx, ast.Load):
            return ast.Attribute(
                value=ast.Name(id='psychoJS', ctx=ast.Load()),
                attr='eventManager',
                ctx=ast.Load()
            )

        # _thisDir -->  '.'
        elif node.id == '_thisDir' and isinstance(node.ctx, ast.Load):
            return ast.Constant(
                value='.',
                kind=None
            )
        # return the node by default:
        return node


    def visit_Attribute(self, node):

        node.value = psychoJSTransformer().visit(node.value)

        if isinstance(node.value, ast.Name):
            # os.sep --> '/'
            if node.value.id == 'os' and node.attr == 'sep':
                return ast.Constant(
                    value='/',
                    kind=None
                )

        # return the node by default:
        return node

class pythonTransformer(ast.NodeTransformer):
    """Python-specific AST transformer
    """

    # operations from the math python module or builtin operations that exist in JavaScript Math:
    directMathOperations = ['abs', 'min', 'max', 'round', 'ceil', 'fabs', 'floor', 'trunc',
                            'exp', 'log', 'log2', 'pow', 'sqrt', 'acos', 'asin', 'atan2', 'cos',
                            'sin', 'tan', 'acosh', 'asinh', 'atanh', 'cosh', 'sinh', 'tanh',
                            'random']

    # operation from the math python module or builtin operations that are available
    # in util/Util.js:
    utilOperations = ['sum', 'average', 'randint', 'range', 'sort', 'shuffle', 'randchoice', 'pad']

    def visit_BinOp(self, node):

        # transform the left and right arguments of the binary operation:
        node.left = pythonTransformer().visit(node.left)
        node.right = pythonTransformer().visit(node.right)

        # formatted strings with %
        # note: we have extended the pythong syntax slightly, to accommodate both tuples and lists
        # so both '%_%' % (1,2) and '%_%' % [1,2] are successfully transpiled
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str):
            # transform the node into an f-string node:
            stringFormat = node.left.value
            stringTuple = node.right.elts if (
              isinstance(node.right, ast.Tuple) or isinstance(node.right, ast.List))\
                else [node.right]

            values = []
            tupleIndex = 0
            while True:
                # TODO deal with more complicated formats, such as %.3f
                match = re.search(r'%.', stringFormat)
                if match is None:
                    break
                values.append(ast.Constant(value=stringFormat[0:match.span(0)[0]], kind=None))
                values.append(
                    self.visit_FormattedValue(
                        ast.FormattedValue(
                            value=stringTuple[tupleIndex],
                            conversion=-1,
                            format_spec=None
                        )
                    )
                )
                stringFormat = stringFormat[match.span(0)[1]:]
                tupleIndex += 1

            return ast.JoinedStr(values)

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
                    attr='toFixed',
                    ctx=ast.Load()
                ),
                args=[ast.Constant(value=precision, kind=None)],
                keywords=[]
            )

            # deal with width:
            widthCall = ast.Call(
                func=ast.Name(id='pad', ctx=ast.Load()),
                args=[precisionCall, ast.Constant(value=width, kind=None)],
                keywords=[]
            )

            # return the node:
            node.value = self.visit_Call(widthCall)
            node.conversion = -1
            node.format_spec = None

            return node

        raise Exception('formatted f-string are not all supported at the moment')

    def visit_Call(self, node):
        # transform the node arguments:
        nbArgs = len(node.args)
        for i in range(0, nbArgs):
            node.args[i] = pythonTransformer().visit(node.args[i])

        # transform the node func:
        node.func = pythonTransformer().visit(node.func)

        # substitutable transformation, e.g. Vector.append(5) --> Vector.push(5):
        if isinstance(node.func, ast.Attribute):  # and isinstance(node.func.value, ast.Name):
            substitutedNode = self.substitutionTransform(node.func, node.args)
            if substitutedNode:
                return substitutedNode

        # operations with module prefix, e.g. a = math.fabs(-1.2)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            prefix = node.func.value.id
            attribute = node.func.attr

            if prefix == 'math':
                mathNode = self.mathTransform(attribute, node.args)
                if mathNode:
                    return mathNode

        # operations without prefix:
        if isinstance(node.func, ast.Name):
            attribute = node.func.id

            # check whether this is a math operation:
            mathNode = self.mathTransform(attribute, node.args)
            if mathNode:
                return mathNode

            # check whether we have code for it in util/Util:
            utilNode = self.utilTransform(attribute, node.args)
            if utilNode:
                return utilNode

        # string.format(args):
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value,
                                                               ast.Str) and node.func.attr == 'format':
            raise Exception('format() is not supported at the moment, please use f-strings instead')

        # return the node by default:
        return node


    def substitutionTransform(self, func, args):

        # a = 'HELLO'
        # a.lower() --> a.toLowerCase()
        if func.attr == 'lower':
            func.attr = 'toLowerCase'
            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # a = [1,2,3]
        # a.append(4) --> a.push(4)
        # value=Call(func=Attribute(value=Name(id='a', ctx=Load()), attr='append', ctx=Load()), args=[Num(n=4)], keywords=[])
        if func.attr == 'append':
            func.attr = 'push'
            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # a = 'hello
        # a.upper() --> a.toUpperCase()
        # value=Call(func=Attribute(value=Name(id='a', ctx=Load()), attr='append', ctx=Load()), args=[Num(n=4)], keywords=[])
        if func.attr == 'upper':
            func.attr = 'toUpperCase'
            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # a = [1,2,3]
        # a.extend([4, 5, 6]) --> a.concat([4, 5, 6])
        if func.attr == 'extend':
            func.attr = 'concat'
            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # a = [1,2,3]
        # a.index(2) --> util.index(a,2)
        # value=Call(func=Attribute(value=Name(id='a', ctx=Load()), attr='index', ctx=Load()), args=[Num(n=2)], keywords=[])
        # value=Call(func=Attribute(value=Name(id='util', ctx=Load()), attr='index', ctx=Load()), args=[Name(id='a', ctx=Load()), Num(n=2)], keywords=[])
        elif func.attr == 'index':
            value = func.value
            func.value = ast.Name(id='util', ctx=ast.Load())
            args = [value, args]
            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # a = [1,2,3]
        # a.count(2) --> util.count(a,2)
        # value=Call(func=Attribute(value=Name(id='a', ctx=Load()), attr='count', ctx=Load()), args=[Num(n=2)], keywords=[])
        # value=Call(func=Attribute(value=Name(id='util', ctx=Load()), attr='count', ctx=Load()), args=[Name(id='a', ctx=Load()), Num(n=2)], keywords=[])
        elif func.attr == 'count':
            value = func.value
            func.value = ast.Name(id='util', ctx=ast.Load())
            args = [value, args]
            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        elif isinstance(func.value, ast.Name):
            # webbrowser.open('https://pavlovia.org') --> window.open('https://pavlovia.org')
            if func.value.id == 'webbrowser':
                func.value.id = 'window'
                return ast.Call(
                    func=func,
                    args=args,
                    keywords=[]
                )

        return None


    def utilTransform(self, attribute, args):

        # operations from the math python module or builtin operations that are available
        # in util/Util.js:
        if attribute in self.utilOperations:
            func = ast.Attribute(
                value=ast.Name(id='util', ctx=ast.Load()),
                attr=attribute,
                ctx=ast.Load()
            )

            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )


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


class pythonAddonVisitor(ast.NodeVisitor):
    # operations that require an addon:
    addonOperations = ['list']

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

    lines = psychoJsCode.splitlines()

    # remove the initial variable declarations, unless it is for _pj:
    if lines[0].find('var _pj;') == 0:
        transformedPsychoJSCode = 'var _pj;\n'
        startIndex = 1
    else:
        startIndex = 0

    if lines[startIndex].find('var ') == 0:
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
