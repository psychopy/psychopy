# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- functions
# :Created:   gio 08 feb 2018 02:29:14 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2018 Alberto Berti
#

from .blocks import JSBlock
from ..processor.util import delimited


class JSFunction(JSBlock):

    begin = 'function '
    bet_args_n_body = ''

    def fargs(self, args, acc=None, kwargs=None):
        result = []
        result.append('(')
        js_args = args.copy()
        if kwargs:
            js_args.append(self.part('{', *delimited(', ', kwargs), '}={}'))
        if acc:
            js_args.append(acc)
        delimited(', ', js_args, dest=result)
        result.append(') ')
        return result

    def emit(self, name, args, body, acc=None, kwargs=None):
        line = [self.begin]
        if name is not None:
            line.append(name)
        line += self.fargs(args, acc, kwargs)
        line += self.bet_args_n_body
        line += ['{']
        yield self.line(line, name=str(name))
        yield from self.lines(body, indent=True, delim=True)
        yield self.line('}')


class JSAsyncFunction(JSFunction):

    begin = 'async function '


class JSGenFunction(JSFunction):

    begin = 'function* '


class JSArrowFunction(JSFunction):

    begin = ''
    bet_args_n_body = '=> '

    def emit(self, name, args, body, acc=None, kwargs=None):
        if name:
            # TODO: split this into an assignment + arrow function
            line = [name, ' = ']
        else:
            line = []
        line += self.fargs(args, acc, kwargs)
        line += self.bet_args_n_body
        line += ['{']
        yield self.line(line)
        yield from self.lines(body, indent=True, delim=True)
        if name:
            yield self.line('}', delim=True)
        else:
            yield self.part('}')
