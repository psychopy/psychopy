# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- operators
# :Created:   mer 07 feb 2018 17:37:24 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2018 Alberto Berti
#

from .base import JSNode


class JSOperator(JSNode):
    pass


class JSLeftSideUnaryOp(JSOperator):
    pass


class JSOpIn(JSOperator):
    def emit(self):
        yield self.part('in')


class JSOpAnd(JSOperator):
    def emit(self):
        yield self.part('&&')


class JSOpOr(JSOperator):
    def emit(self):
        yield self.part('||')


class JSOpNot(JSLeftSideUnaryOp):
    def emit(self):
        yield self.part('!')


class JSOpInstanceof(JSOperator):
    def emit(self):
        yield self.part('instanceof')


class JSOpTypeof(JSLeftSideUnaryOp):
    def emit(self):
        yield self.part('typeof')


class JSOpAdd(JSOperator):
    def emit(self):
        yield self.part('+')


class JSOpSub(JSOperator):
    def emit(self):
        yield self.part('-')


class JSOpMult(JSOperator):
    def emit(self):
        yield self.part('*')


class JSOpDiv(JSOperator):
    def emit(self):
        yield self.part('/')


class JSOpMod(JSOperator):
    def emit(self):
        yield self.part('%')


class JSOpRShift(JSOperator):
    def emit(self):
        yield self.part('>>')


class JSOpLShift(JSOperator):
    def emit(self):
        yield self.part('<<')


class JSOpBitXor(JSOperator):
    def emit(self):
        yield self.part('^')


class JSOpBitAnd(JSOperator):
    def emit(self):
        yield self.part('&')


class JSOpBitOr(JSOperator):
    def emit(self):
        yield self.part('|')


class JSOpInvert(JSLeftSideUnaryOp):
    def emit(self):
        yield self.part('~')


class JSOpUSub(JSLeftSideUnaryOp):
    def emit(self):
        yield self.part('-')


class JSOpStrongEq(JSOperator):
    def emit(self):
        yield self.part('===')


class JSOpStrongNotEq(JSOperator):
    def emit(self):
        yield self.part('!==')


class JSOpLt(JSOperator):
    def emit(self):
        yield self.part('<')


class JSOpLtE(JSOperator):
    def emit(self):
        yield self.part('<=')


class JSOpGt(JSOperator):
    def emit(self):
        yield self.part('>')


class JSOpGtE(JSOperator):
    def emit(self):
        yield self.part('>=')


JSIs = JSOpStrongEq


class JSRest(JSOperator):
    def emit(self, value):
        yield self.part('...', value)
