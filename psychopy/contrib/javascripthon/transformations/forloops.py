# -*- coding: utf-8 -*-
# :Project:  metapensiero.pj -- for loops transformations
# :Created:  ven 26 feb 2016 15:17:49 CET
# :Authors:  Andrew Schaaf <andrew@andrewschaaf.com>,
#            Alberto Berti <alberto@metapensiero.it>
# :License:  GNU General Public License version 3 or later
#

import ast

from ..js_ast import (
    JSAssignmentExpression,
    JSAttribute,
    JSAugAssignStatement,
    JSBinOp,
    JSCall,
    JSExpressionStatement,
    JSForStatement,
    JSForeachStatement,
    JSForofStatement,
    JSIfStatement,
    JSName,
    JSNum,
    JSOpAdd,
    JSOpLt,
    JSStatements,
    JSSubscript,
    JSVarStatement,
)


def For_range(t, x):
    """Special conversion for ``for name in range(n)``, which detects
    ``range()`` calls and converts the statement to:

    .. code:: javascript

      for (var name = 0, bound = bound; name < bound; name++) {
          // ...
      }

    """
    if (isinstance(x.target, ast.Name) and
        isinstance(x.iter, ast.Call) and
        isinstance(x.iter.func, ast.Name) and
        x.iter.func.id == 'range' and
        1 <= len(x.iter.args) < 4) and (not x.orelse):

        name = x.target
        body = x.body
        if len(x.iter.args) == 1:
            start = JSNum(0)
            bound = x.iter.args[0]
            step = JSNum(1)
        elif len(x.iter.args) == 2:
            start = x.iter.args[0]
            bound = x.iter.args[1]
            step = JSNum(1)
        else:
            start = x.iter.args[0]
            bound = x.iter.args[1]
            step = x.iter.args[2]

        bound_name = t.new_name()

        return JSForStatement(
            JSVarStatement(
                [name.id, bound_name],
                [start, bound]),
            JSBinOp(JSName(name.id), JSOpLt(), JSName(bound_name)),
            JSAugAssignStatement(
                JSName(name.id), JSOpAdd(), step),
            body
        )


def For_dict(t, x):
    """Special ``for name in dict(expr)`` statement translation.

    It detects the ``dict()`` call and converts it to:

    .. code:: javascript

      var dict_ = expr;
      for (var name in dict_) {
          if (dict_.hasOwnProperty(name)) {
          // ...
          }
      }
    """
    if (isinstance(x.iter, ast.Call) and
        isinstance(x.iter.func, ast.Name) and
        x.iter.func.id == 'dict' and
        len(x.iter.args) <= 2) and (not x.orelse):

        t.unsupported(x, not isinstance(x.target, ast.Name),
                      "Target must be a name")

        name = x.target
        expr = x.iter.args[0]
        body = x.body

        dict_ = t.new_name()

        # if not ``dict(foo, True)`` filter out inherited values
        if not (len(x.iter.args) == 2 and
            isinstance(x.iter.args[1], ast.Constant) and
            x.iter.args[1].value):
            body = [
                    JSIfStatement(
                        JSCall(
                            JSAttribute(JSName(dict_), 'hasOwnProperty'),
                            [JSName(name.id)]
                        ),
                        body, None
                    )
                ]
        # set the incoming py_node for the sourcemap
        loop = JSForeachStatement(
            name.id,
            JSName(dict_),
            body
        )
        loop.py_node = x

        return JSStatements(
            JSVarStatement([dict_], [expr], unmovable=True),
            loop
        )


def For_iterable(t, x):
    """Special ``for name in iterable(expr)`` statement translation.

    It detects the ``iterable()`` call and converts it to:

    .. code:: javascript

      var __iterable = expr;
      for (var name of __iterable) {
          ...
      }
    """
    if (isinstance(x.iter, ast.Call) and
        isinstance(x.iter.func, ast.Name) and
        x.iter.func.id == 'iterable' and
        len(x.iter.args) == 1) and (not x.orelse):
        t.es6_guard(x, 'for...of statement requires ES6')

        expr = x.iter.args[0]
        body = x.body
        target = x.target

        # set the incoming py_node for the sourcemap
        return JSForofStatement(
            target,
            expr,
            body,
        )


def For_default(t, x):
    """Assumes that the iteration is over a list.

    Converts something like:

    .. code:: python

      for name in expr:
          #body...

    to:

    .. code:: javascript

      for(var name, arr=expr, ix=0, length=arr.length; ix < length: ix++) {
          name = arr[ix];
          //body ...
      }

    """

    t.unsupported(x, not isinstance(x.target, ast.Name), "Target must be a name,"
                  " Are you sure is only one?")

    name = x.target
    expr = x.iter
    body = x.body

    arr = t.new_name()
    length = t.new_name()
    ix = t.new_name()

    return JSForStatement(
        JSVarStatement(
            [name.id, ix, arr, length],
            [None, JSNum(0), expr,
             JSAttribute(JSName(arr), 'length')],
            unmovable=True
        ),
        JSBinOp(
            JSName(ix),
            JSOpLt(),
            JSName(length)),
        JSExpressionStatement(
            JSAugAssignStatement(
                JSName(ix),
                JSOpAdd(),
                JSNum(1))),
        [
            JSExpressionStatement(
                JSAssignmentExpression(
                    JSName(name.id),
                    JSSubscript(
                        JSName(arr),
                        JSName(ix))))
        ] + body)


For = [For_range, For_dict, For_iterable, For_default]
