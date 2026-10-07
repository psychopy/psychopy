# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- literals
# :Created:   mer 07 feb 2018 17:50:03 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2018 Alberto Berti
#

import json

from .base import JSNode
from ..processor.util import delimited, delimited_multi_line


class JSLiteral(JSNode):
    def emit(self, text):
        yield from self.lines(delimited_multi_line(self, text, '', '', False))


class JSDict(JSLiteral):
    def emit(self, keys, values):
        arr = ['{']
        for i in range(len(keys)):
            if i > 0:
                arr.append(', ')
            arr.append(keys[i])
            arr.append(': ')
            arr.append(values[i])
        arr.append('}')
        yield self.part(*arr)


class JSList(JSLiteral):
    def emit(self, elts):
        arr = ['[']
        delimited(', ', elts, dest=arr)
        arr.append(']')
        yield self.part(*arr)


class JSFalse(JSLiteral):
    def emit(self):
        yield self.part('false')


class JSNull(JSLiteral):
    def emit(self):
        yield self.part('null')


class JSNum(JSLiteral):
    def emit(self, x):
        yield self.part(str(x))


class JSStr(JSLiteral):
    def emit(self, s):
        yield self.part(json.dumps(s))


class JSTrue(JSLiteral):
    def emit(self):
        yield self.part('true')
