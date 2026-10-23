# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- classes
# :Created:   gio 08 feb 2018 02:32:04 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2018 Alberto Berti
#

from .blocks import JSBlock
from .functions import JSFunction


class JSClass(JSBlock):

    def emit(self, name, super_, methods):
        line = ['class ', name]
        if super_ is not None:
            line += [' extends ', super_]
        line += [' {']
        yield self.line(line)
        yield from self.lines(methods, indent=True, delim=True)
        yield self.line('}')


class JSClassMember(JSFunction):

    def with_kind(self, kind, args, body, acc=None, kwargs=None, static=False):
        if static:
            line = ['static ', kind]
        else:
            line = [kind]
        line += self.fargs(args, acc, kwargs)
        line += ['{']
        yield self.line(line)
        yield from self.lines(body, indent=True, delim=True)
        yield self.line('}')


class JSClassConstructor(JSClassMember):

    def emit(self, args, body, acc=None, kwargs=None):
        yield from self.with_kind('constructor', args, body, acc, kwargs)


class JSMethod(JSClassMember):

    def emit(self, name, args, body, acc=None, kwargs=None, static=False):
        yield from self.with_kind(name, args, body, acc, kwargs, static)


class JSAsyncMethod(JSClassMember):

    def emit(self, name, args, body, acc=None, kwargs=None, static=False):
        yield from self.with_kind('async ' + name, args, body, acc, kwargs,
                                  static)


class JSGenMethod(JSClassMember):

    def emit(self, name, args, body, acc=None, kwargs=None, static=False):
        yield from self.with_kind('* ' + name, args, body, acc, kwargs,
                                  static)


class JSGetter(JSClassMember):

    def emit(self, name, body, static=False):
        yield from self.with_kind('get ' + name, [], body, static=static)


class JSSetter(JSClassMember):

    def emit(self, name, arg, body, static=False):
        yield from self.with_kind('set ' + name, [arg], body, static=static)
