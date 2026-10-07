# -*- coding: utf-8 -*-
# :Project:  metapensiero.pj -- exceptions transformations
# :Created:  ven 26 feb 2016 15:17:49 CET
# :Authors:  Andrew Schaaf <andrew@andrewschaaf.com>,
#            Alberto Berti <alberto@metapensiero.it>
# :License:  GNU General Public License version 3 or later
#

import ast

from ..js_ast import (
    JSBinOp,
    JSIfStatement,
    JSName,
    JSNewCall,
    JSOpInstanceof,
    JSStatements,
    JSThrowStatement,
    JSTryCatchFinallyStatement,
    JSVarStatement,
)

from .common import _build_call_isinstance


def Try(t, x):
    t.unsupported(x, x.orelse, "'else' block of 'try' statement isn't supported")
    known_exc_types = (ast.Name, ast.Attribute, ast.Tuple, ast.List)
    ename = None
    if x.handlers:
        for h in x.handlers:
            if h.type is not None and not isinstance(h.type, known_exc_types):
                t.warn(x, "Exception type expression might not evaluate to a "
                       "valid type or sequence of types.")
            ename = h.name
        ename = ename or 'e'
        if t.has_child(x.handlers, ast.Raise) and t.has_child(x.finalbody, ast.Return):
            t.warn(x, node, "The re-raise in 'except' body may be masked by the "
                   "return in 'final' body.")
            # see
            # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Control_flow_and_error_handling#The_finally_block

        rhandlers = x.handlers.copy()
        rhandlers.reverse()
        prev_except = stmt =  None
        for ix, h in enumerate(rhandlers):
            body = h.body
            if h.name is not None and h.name != ename:
                # Rename the exception to match the handler
                rename = JSVarStatement([h.name], [ename])
                body = [rename] + h.body

            # if it's  the last except and it's a catchall
            # threat 'except Exception:' as a catchall
            if (ix == 0 and h.type is None or (isinstance(h.type, ast.Name) and
                                   h.type.id == 'Exception')):
                prev_except = JSStatements(*body)
                continue
            else:
                if ix == 0:
                    prev_except = JSThrowStatement(JSName(ename))
                # then h.type is an ast.Name != 'Exception'
                stmt = JSIfStatement(
                    _build_call_isinstance(JSName(ename), h.type),
                    body,
                    prev_except
                )
            prev_except = stmt
        t.ctx['ename'] = ename
        result = JSTryCatchFinallyStatement(x.body, ename, prev_except, x.finalbody)
    else:
        result = JSTryCatchFinallyStatement(x.body, None, None, x.finalbody)
    return result


def Raise(t, x):
    if x.exc is None:
        ename = t.ctx.get('ename')
        t.unsupported(x, not ename, "'raise' has no argument but failed obtaining"
                      " implicit exception")
        res = JSThrowStatement(JSName(ename))
    elif isinstance(x.exc, ast.Call) and isinstance(x.exc.func, ast.Name) and \
         len(x.exc.args) == 1 and x.exc.func.id == 'Exception':
        res = JSThrowStatement(JSNewCall(JSName('Error'), x.exc.args))
    else:
        res = JSThrowStatement(x.exc)

    return res
