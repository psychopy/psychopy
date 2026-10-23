# -*- coding: utf-8 -*-
# :Project:  metapensiero.pj -- common transformation functions
# :Authors:  Andrew Schaaf <andrew@andrewschaaf.com>,
#            Alberto Berti <alberto@metapensiero.it>
#            Devan Lai <devan.lai@gmail.com>
# :License:  GNU General Public License version 3 or later
#

import ast
from ..js_ast import (
    JSBinOp,
    JSMultipleArgsOp,
    JSName,
    JSOpInstanceof,
    JSOpOr,
    JSOpStrongEq,
    JSOpTypeof,
    JSStr,
    JSUnaryOp,
)


def _build_call_isinstance(tgt, cls_or_seq):
    """Helper to build the translate the equivalence of ``isinstance(foo, Bar)``
    to ``foo instanceof Bar`` and ``isinstance(Foo, (Bar, Zoo))`` to
    ``foo instanceof Bar || foo instanceof Zoo``.
    """
    if isinstance(cls_or_seq, (ast.Tuple, ast.List, ast.Set)):
        classes = cls_or_seq.elts
        args = tuple((tgt, c) for c in classes)
        return JSMultipleArgsOp(JSOpInstanceof(), JSOpOr(), *args)
    else:
        cls = cls_or_seq
        if isinstance(cls, ast.Name) and cls.id == 'str':
            return JSMultipleArgsOp(
                (JSOpStrongEq(), JSOpInstanceof()),
                JSOpOr(),
                (JSUnaryOp(JSOpTypeof(), tgt), JSStr('string')),
                (tgt, JSName('String'))
            )
        elif isinstance(cls, ast.Name) and cls.id in ['int', 'float']:
            return JSMultipleArgsOp(
                (JSOpStrongEq(), JSOpInstanceof()),
                JSOpOr(),
                (JSUnaryOp(JSOpTypeof(), tgt), JSStr('number')),
                (tgt, JSName('Number'))
            )
        else:
            return JSBinOp(tgt, JSOpInstanceof(), cls)
