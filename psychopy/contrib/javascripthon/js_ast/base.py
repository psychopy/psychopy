# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- base node
# :Created:   mer 07 feb 2018 16:17:02 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2018 Alberto Berti
#

import inspect

from ..processor.util import Line, Part


class TargetNode:
    """This is the common ancestor of all the JS AST nodes."""

    """The associated Python AST node"""
    py_node = None

    """The Transformer instance which is managing this one"""
    transformer = None

    """The final arguments passed to the emit method defined on the
    subclasses"""
    transformed_args = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.options = kwargs

    def __str__(self):
        return ''.join(str(x) for x in self.serialize())

    def _chain(self, items):
        for i in self._expand(items):
            if inspect.isgenerator(i):
                yield from i
            else:
                yield i

    def _expand(self, items):
        for i in items:
            if isinstance(i, TargetNode):
                yield from i.serialize()
            else:
                yield i

    def emit(self):
        """This is the main output definition method. Is reimplemented by the
        subclasses."""

    @classmethod
    def final(cls, *transformed_args, **options):
        tn = cls(**options)
        tn.transformed_args = transformed_args
        return tn

    def line(self, item, indent=False, delim=False, name=None):
        if isinstance(item, Line):
            item.indent += int(indent)
            l = item
        elif isinstance(item, (tuple, list)):
            item = tuple(self._chain(item))
            l = Line(self, item, indent, delim, name)
        else:
            l = Line(self, item, indent, delim, name)
        return l

    def lines(self, items, *, indent=False, delim=False, name=None):
        if not isinstance(items, (tuple, list)):
            items = (items,)
        for i in self._chain(items):
            yield self.line(i, indent=indent, delim=delim, name=name)

    def part(self, *items, name=None):
        it = tuple(self._expand(items))
        if len(it) == 1 and isinstance(it[0], Line):
            result = it[0].item
        else:
            result = Part(self, *it, name=name)
        return result

    def serialize(self):
        for a in self.emit(*self.transformed_args, **self.options):
            yield from a.serialize()


class JSNode(TargetNode):
    pass


class JSStatement(JSNode):
    pass
