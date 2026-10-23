# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- statements
# :Created:   gio 08 feb 2018 01:47:43 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2018 Alberto Berti
#

from .base import JSStatement
from .util import _check_keywords
from ..processor.util import delimited


class JSVarDeclarer(JSStatement):

    def with_kind(self, kind, keys, values):
        for key in keys:
            _check_keywords(self, key)
        assert len(keys) > 0
        assert len(keys) == len(values)

        arr = ['%s ' % kind]
        for i in range(len(keys)):
            if i > 0:
                arr.append(', ')
            arr.append(keys[i])
            if values[i] is not None:
                arr.append(' = ')
                arr.append(values[i])
        yield self.part(*arr)


class JSVarStatement(JSVarDeclarer):
    def emit(self, keys, values, unmovable=False):
        yield from self.with_kind('var', keys, values)


class JSLetStatement(JSVarDeclarer):
    def emit(self, keys, values, unmovable=True):
        yield from self.with_kind('let', keys, values)


class JSAugAssignStatement(JSStatement):
    def emit(self, target, op, value):
        yield self.part(target, ' ', op, '= ', value, name=str(target))


class JSReturnStatement(JSStatement):
    def emit(self, value):
        if value:
            result = self.line(['return ', value], delim=True)
        else:
            result = self.line('return', delim=True)
        yield result


class JSBreakStatement(JSStatement):
    def emit(self):
        yield self.part('break')


class JSContinueStatement(JSStatement):
    def emit(self):
        yield self.part('continue')


class JSDeleteStatement(JSStatement):
    def emit(self, value):
        yield self.line(['delete ', value], delim=True)


class JSThrowStatement(JSStatement):
    def emit(self, obj):
        yield self.line(['throw ', obj], delim=True)


class JSYield(JSStatement):

    def emit(self, expr):
        yield self.part('yield ', expr)


class JSYieldStar(JSStatement):

    def emit(self, expr):
        yield self.part('yield* ', expr)


class JSAwait(JSStatement):

    def emit(self, value):
        yield self.part('await ', value)


class JSImport(JSStatement):
    pass


class JSDependImport(JSImport):
    def emit(self, module):
        yield self.line(['System.import(', "'", module, "'", ')'], delim=True)


class JSNamedImport(JSImport):
    def emit(self, module, names):
        js_names = []
        for name, alias in sorted(names):
            if alias:
                js_names.append(self.part(name, ' as ', alias))
            else:
                js_names.append(self.part(name))

        yield self.line(['import {', *delimited(', ', js_names),
                         "} from '", module, "'"], delim=True)


class JSStarImport(JSImport):
    def emit(self, module, name):
        yield self.line(['import * as ', name, " from '", module, "'"],
                        delim=True)


class JSDefaultImport(JSImport):
    def emit(self, module, alias):
        yield self.line(['import ', alias, " from '", module, "'"], delim=True)


class JSExport(JSStatement):
    def emit(self, names):
        yield self.line(['export ', '{', *delimited(', ', names), '}'],
                        delim=True)


class JSExportDefault(JSExport):
    def emit(self, name):
        yield self.line(['export default ', name], delim=True)


class JSExpressionStatement(JSStatement):
    def emit(self, value):
        yield self.part(value)
