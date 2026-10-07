# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- Aggregated statements
# :Created:   gio 08 feb 2018 02:53:30 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2018 Alberto Berti
#

import itertools

from .base import JSNode
from .noops import JSCommentBlock
from .statements import JSImport, JSVarStatement


class JSStatements(JSNode):

    def __iadd__(self, other):
        self.transformed_args.extend(other.transformed_args)
        return self

    def emit(self, statements):
        for s in statements:
            yield s

    def squash(self, args):
        for a in args:
            if isinstance(a, JSStatements):
                yield from a.transformed_args
            else:
                yield a

    def reordered_args(self, args):
        """Reorder the args to keep the imports and vars always at the top."""
        args = list(self.squash(args))
        imports = []
        vars_ = []
        others = []
        for a in args:
            if isinstance(a, JSImport):
                imports.append(a)
            elif isinstance(a, JSVarStatement) and \
                 not a.options.get('unmovable', False):
                vars_.append(a)
            else:
                others.append(a)

        others_first = []
        others_after = []
        # if the others start with some comments, put those at the top
        start_trigger = False
        for s in others:
            if isinstance(s, JSCommentBlock) and not start_trigger:
                others_first.append(s)
            else:
                others_after.append(s)
                start_trigger = True

        return itertools.chain(others_first, imports, vars_, others_after)

    def serialize(self):
        for a in self.emit(self.reordered_args(self.transformed_args)):
            yield from self.lines(a.serialize(), delim=True)
