#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import ast
import sys
import re

try:
    from metapensiero.pj.api import translates
except ImportError:
    pass  # metapensiero not installed

import astunparse


namesJS = {
    'sin': 'Math.sin',
    'cos': 'Math.cos',
    'tan': 'Math.tan',
    'pi': 'Math.PI',
    'rand': 'Math.random',
    'random': 'Math.random',
    'sqrt': 'Math.sqrt',
    'abs': 'Math.abs',
    'floor': 'Math.floor',
    'ceil': 'Math.ceil',
    'randint': 'util.randint',
    'range': 'util.range',
    'randchoice': 'util.randchoice',
    'round': 'util.round',  # better than Math.round, supports n DPs arg
    'sum': 'util.sum',
}


class psychoJSTransformer(ast.NodeTransformer):
    """PsychoJS-specific AST transformer
    """

    def visit_Name(self, node):
        if node.id in namesJS:
            node.id = namesJS[node.id]
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
    utilOperations = ['sum', 'average', 'randint', 'range', 'sort', 'shuffle', 'randchoice', 'pad', 'Clock']

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
            substitutedNode = self.substitutionTransform(node.func, node.args, node.keywords)
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
            elif prefix == 'core':
                utilNode = self.utilTransform(attribute, node.args)
                if utilNode:
                    return utilNode

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

    def substitutionTransform(self, func, args, keywords):
        # Substitutions where only the function name changes (see below)
        functionSubsJS = {
            'lower': 'toLowerCase',
            'append': 'push',
            'upper': 'toUpperCase',
            'extend': 'concat',
        }
        # Substitions that become util functions
        utilSubsJS = [
            'index',
            'count'
        ]

        # Substitutions where only the function name changes
        # Examples:
        #   a = 'HELLO'
        #   a.lower() --> a.toLowerCase()
        #
        #   a = [1,2,3]
        #   a.append(4) --> a.push(4)
        #
        #   a = 'hello
        #   a.upper() --> a.toUpperCase()
        #
        # a = [1,2,3]
        # a.extend([4, 5, 6]) --> a.concat([4, 5, 6])
        if func.attr in functionSubsJS:
            func.attr = functionSubsJS[func.attr]
            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # Substitutions where the function is changed to a util.function and the original value becomes an argument
        # a = [1,2,3]
        # a.index(2) --> util.index(a,2)
        # value=Call(func=Attribute(value=Name(id='a', ctx=Load()), attr='index', ctx=Load()), args=[Num(n=2)], keywords=[])
        # value=Call(func=Attribute(value=Name(id='util', ctx=Load()), attr='index', ctx=Load()), args=[Name(id='a', ctx=Load()), Num(n=2)], keywords=[])
        #
        # a = [1,2,3]
        # a.count(2) --> util.count(a,2)
        # value=Call(func=Attribute(value=Name(id='a', ctx=Load()), attr='count', ctx=Load()), args=[Num(n=2)], keywords=[])
        # value=Call(func=Attribute(value=Name(id='util', ctx=Load()), attr='count', ctx=Load()), args=[Name(id='a', ctx=Load()), Num(n=2)], keywords=[])
        elif func.attr in utilSubsJS:
            value = func.value
            func.value = ast.Name(id='util', ctx=ast.Load())
            args = [value, args]
            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # Substitutions where more than one of the function, value, and arguments change
        # a = [1,2,3]
        # a.pop(2) -> a.splice(2, 1);
        # a.pop() -> a.splice(-1, 1);
        # The second argument of splice is the number of elements to delete; pass 1 for functionality equivalent to pop.
        # The default first argument for pop is -1 (remove the last item).
        elif func.attr == 'pop':
            func.attr = 'splice'
            args = args if args else [ast.Constant(value=-1, kind=None)]
            args = [args, [ast.Constant(value=1, kind=None)]]

            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # a = [1, 2, 3, 4]
        # a.insert(0, 5) -> a.splice(0, 0, 5);
        # Note that .insert only inserts a single element, so there should always be exactly two input args).
        elif func.attr == 'insert':
            func.attr = 'splice'
            args = [args[0], [ast.Constant(value=0, kind=None)], args[1]]

            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # a = ['This', 'is', 'a', 'test']
        # ' '.join(a) -> a.join(" ");
        # In this case func.value and args need to be switched.
        elif func.attr == 'join':
            new_args = [ast.Constant(value=func.value.value, kind=None)]
            func.value = args[0]
            
            return ast.Call(
                func=func,
                args=new_args,
                keywords=[]
            )

        # a = "This is a test"
        # a.split() -> a.split(" ")
        # Note that this function translates correctly if there's an input arg; only the default requires modification.
        elif func.attr == 'split' and not args:
            args = [ast.Constant(value=" ", kind=None)]
            return ast.Call(
                func=func,
                args=args,
                keywords=[]
            )

        # a = [3, 7, 9, 0, 1, 5]
        # a.sort(reverse=True) -> a.reverse()
        # This one only needs adjustment if the reverse=True keyword argument is included.
        elif func.attr == 'sort' and keywords and keywords[0].arg == 'reverse' and keywords[0].value.value:
            func.attr = 'reverse'
            return ast.Call(
                func=func,
                args=[],
                keywords=[]
            )

    # Substitutions where the value on which the function is performed (not the function itself) changes
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


def transformPsychoJsCode(psychoJsCode, addons, namespace=[]):
    """Transform the input PsychoJS code.

    Args:
        psychoJsCode (str): the input PsychoJS JavaScript code
        namespace (list): list of varnames which are already defined

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

    for index, thisLine in enumerate(psychoJsCode.splitlines()):
        include = True
        # remove the initial variable declarations, unless it is for _pj:
        if index == 0 and thisLine.find('var _pj;') == 0:
            transformedPsychoJSCode = 'var _pj;\n'
            continue
        # Remove var defs if variable is defined earlier in experiment
        if thisLine.startswith("var "):
            # Get var names
            varNames = thisLine[4:-1].split(", ")
            validVarNames = []
            for varName in varNames:
                if namespace is not None and varName not in namespace:
                    # If var name not is already in namespace, keep it in
                    validVarNames.append(varName)
            # If there are no var names left, remove statement altogether
            if not len(validVarNames):
                include = False
            # Recombine line
            thisLine = f"var {', '.join(validVarNames)};"

        # Append line
        if include:
            transformedPsychoJSCode += thisLine
            transformedPsychoJSCode += '\n'

    return transformedPsychoJSCode


def translatePythonToJavaScript(psychoPyCode, namespace=[]):
    """Translate PsychoPy python code into PsychoJS JavaScript code.

    Args:
        psychoPyCode (str): the input PsychoPy python code
        namespace (list, None): list of varnames which are already defined

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
        transformedPsychoJsCode = transformPsychoJsCode(psychoJsCode, addons, namespace=namespace)
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
