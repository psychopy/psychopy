# -*- coding: utf-8 -*-
# :Project:  metapensiero.pj -- comprehensions transformations
# :Created:  ven 26 feb 2016 15:17:49 CET
# :Authors:  Andrew Schaaf <andrew@andrewschaaf.com>,
#            Alberto Berti <alberto@metapensiero.it>
# :License:  GNU General Public License version 3 or later
#

import ast

from ..js_ast import (
    JSAttribute,
    JSAugAssignStatement,
    JSBinOp,
    JSCall,
    JSExpressionStatement,
    JSForStatement,
    JSFunction,
    JSIfStatement,
    JSList,
    JSName,
    JSNum,
    JSOpAdd,
    JSOpLt,
    JSReturnStatement,
    JSSubscript,
    JSThis,
    JSVarStatement,
)

#### ListComp
# Transform
# <pre>[EXPR for NAME in LIST]</pre>
# or
# <pre>[EXPR for NAME in LIST if CONDITION]</pre>
def ListComp(t, x):

    assert len(x.generators) == 1
    assert len(x.generators[0].ifs) <= 1
    assert isinstance(x.generators[0], ast.comprehension)
    assert isinstance(x.generators[0].target, ast.Name)

    EXPR = x.elt
    NAME = x.generators[0].target
    LIST = x.generators[0].iter
    if len(x.generators[0].ifs) == 1:
        CONDITION = x.generators[0].ifs[0]
    else:
        CONDITION = None

    __new = t.new_name()
    __old = t.new_name()
    __i = t.new_name()
    __bound = t.new_name()

    # Let's construct the result from the inside out:
    #<pre>__new.push(EXPR);</pre>
    push = JSExpressionStatement(
            JSCall(
                JSAttribute(
                    JSName(__new),
                    'push'),
                [EXPR]))

    # If needed, we'll wrap that with:
    #<pre>if (CONDITION) {
    #    <i>...push...</i>
    #}</pre>
    if CONDITION:
        pushIfNeeded = JSIfStatement(
                CONDITION,
                push,
                None)
    else:
        pushIfNeeded = push

    # Wrap with:
    #<pre>for(
    #        var __i = 0, __bound = __old.length;
    #        __i &lt; __bound;
    #        __i++) {
    #    var NAME = __old[__i];
    #    <i>...pushIfNeeded...</i>
    #}</pre>
    forloop = JSForStatement(
                    JSVarStatement(
                        [__i, __bound],
                        [0, JSAttribute(
                                JSName(__old),
                                'length')]),
                    JSBinOp(JSName(__i), JSOpLt(), JSName(__bound)),
                    JSAugAssignStatement(JSName(__i), JSOpAdd(), JSNum(1)),
                    [
                        JSVarStatement(
                            [NAME.id],
                            [JSSubscript(
                                JSName(__old),
                                JSName(__i))]),
                        pushIfNeeded])

    # Wrap with:
    #<pre>function() {
    #    var __new = [], __old = LIST;
    #    <i>...forloop...</i>
    #    return __new;
    #}
    func = JSFunction(
        None,
        [],
        [
            JSVarStatement(
                [__new, __old],
                [JSList([]), LIST]),
            forloop,
            JSReturnStatement(
                JSName(__new))])

    # And finally:
    #<pre>((<i>...func...</i>).call(this))</pre>
    invoked = JSCall(
            JSAttribute(
                func,
                'call'),
            [JSThis()])

    return invoked
