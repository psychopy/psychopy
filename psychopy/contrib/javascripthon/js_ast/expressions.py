# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- expressions
# :Created:   gio 08 feb 2018 02:46:38 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2018 Alberto Berti
#

import re

from .base import JSNode
from .operators import JSLeftSideUnaryOp
from ..processor.util import delimited, delimited_multi_line
from .util import _check_keywords


class JSExpression(JSNode):

    def emit(self, expr):
        yield self.part('(', expr, ')')


class JSAssignmentExpression(JSNode):
    def emit(self, left, right):
        yield self.part(left, ' = ', right)


class JSIfExp(JSNode):
    def emit(self, test, body, orelse):
        yield self.part('(', test, ' ? ', body, ' : ', orelse, ')')


class JSCall(JSNode):

    operator = ''

    def emit(self, func, args, kwargs=None, operator=None):
        operator = operator or self.operator
        kwargs = kwargs or []
        arr = [operator, func, '(']
        fargs = args.copy()
        if kwargs:
            fargs.append(kwargs)
        delimited(', ', fargs, dest=arr)
        arr.append(')')
        yield self.part(*arr)


class JSNewCall(JSCall):

    operator = 'new '


class JSAttribute(JSNode):
    def emit(self, obj, s):
        assert re.search(r'^[a-zA-Z$_][a-zA-Z$_0-9]*$', s)
        _check_keywords(self, s)
        yield self.part(obj, '.', s, name=True)


class JSSubscript(JSNode):
    def emit(self, obj, key):
        yield self.part(self.part(obj, name=True), '[',
                        self.part(key, name=True), ']')


class JSKeySubscript(JSNode):
    def emit(self, key):
        yield self.part('[', self.part(key), ']')


class JSBinOp(JSNode):
    def emit(self, left, op, right):
        yield self.part('(', left, ' ', op, ' ', right, ')')


class JSMultipleArgsOp(JSNode):
    def emit(self, binop, conj, *args):
        assert len(args) > 1
        parts = []
        for ix, arg in enumerate(args):
            if isinstance(binop, (tuple, list)):
                op = binop[ix]
            else:
                op = binop
            if ix > 0:
                parts += [' ', conj, ' ']
            parts += ['(', arg[0], ' ', op, ' ', arg[1], ')']
        yield self.part('(', *parts, ')')


class JSUnaryOp(JSNode):
    def emit(self, op, right):
        assert isinstance(op, JSLeftSideUnaryOp)
        yield self.part('(', op, ' ', right, ')')


class JSName(JSNode):
    def emit(self, name):
        _check_keywords(self, name)
        yield self.part(name, name=True)


class JSTaggedTemplate(JSNode):

    def emit(self, value, func):
        text = list(delimited_multi_line(self, value, '`'))
        func = list(func.serialize())
        yield self.part(*func, *text)


class JSTemplateLiteral(JSNode):

    def emit(self, value):
        yield from delimited_multi_line(self, value, '`')


class JSSuper(JSNode):
    def emit(self):
        yield self.part('super')


class JSThis(JSNode):
    def emit(self):
        yield self.part('this')
