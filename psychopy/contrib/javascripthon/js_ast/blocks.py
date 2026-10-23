# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- block statements
# :Created:   gio 08 feb 2018 02:25:23 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2018 Alberto Berti
#

from .base import JSStatement


class JSBlock(JSStatement):
    pass


class JSIfStatement(JSBlock):
    def emit(self, test, body, orelse):
        yield self.line(['if (', test, ') {'])
        yield from self.lines(body, indent=True, delim=True)
        if orelse:
            yield self.line(['} else {'])
            yield from self.lines(orelse, indent=True, delim=True)
            yield self.line('}')
        else:
            yield self.line('}')


class JSWhileStatement(JSBlock):
    def emit(self, test, body):
        yield self.line(['while (', test, ') {'])
        yield from self.lines(body, indent=True, delim=True)
        yield self.line('}')


class JSForStatement(JSBlock):
    def emit(self, left, test, right, body):
        yield self.line(['for (', left, '; ', test, '; ', right, ') {'])
        yield from self.lines(body, indent=True, delim=True)
        yield self.line('}')


class JSForIterableStatement(JSBlock):

    operator = ' of '

    def emit(self, target, source, body):
        yield self.line(['for (var ', self.part(target), self.operator,
                         source, ') {'])
        yield from self.lines(body, indent=True, delim=True)
        yield self.line('}')


class JSForeachStatement(JSForIterableStatement):

    operator = ' in '


class JSForofStatement(JSForIterableStatement):
    pass


class JSTryCatchFinallyStatement(JSBlock):
    def emit(self, try_body, target, catch_body, finally_body):
        assert catch_body or finally_body
        yield self.line('try {')
        yield from self.lines(try_body, indent=True, delim=True)
        if catch_body:
            yield self.line(['} catch(', target, ') {'])
            yield from self.lines(catch_body, indent=True, delim=True)
        if finally_body:
            yield self.line(['} finally {'])
            yield from self.lines(finally_body, indent=True, delim=True)
        yield self.line('}')
