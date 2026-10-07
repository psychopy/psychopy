# -*- coding: utf-8 -*-
# :Project:  metapensiero.pj -- special transformations
# :Created:  ven 26 feb 2016 15:17:49 CET
# :Authors:  Andrew Schaaf <andrew@andrewschaaf.com>,
#            Alberto Berti <alberto@metapensiero.it>
# :License:  GNU General Public License version 3 or later
#

import ast
from unicodedata import lookup
import re

from ..compat import is_str

from ..js_ast import (
    JSAssignmentExpression,
    JSAttribute,
    JSBinOp,
    JSCall,
    JSCommentBlock,
    JSDefaultImport,
    JSDependImport,
    JSDict,
    JSExportDefault,
    JSExpressionStatement,
    JSLiteral,
    JSName,
    JSNamedImport,
    JSNull,
    JSNum,
    JSOpIn,
    JSOpInstanceof,
    JSOpNot,
    JSOpOr,
    JSOpStrongEq,
    JSOpStrongNotEq,
    JSOpTypeof,
    JSPass,
    JSStarImport,
    JSStatements,
    JSStr,
    JSSubscript,
    JSTaggedTemplate,
    JSTemplateLiteral,
    JSThis,
    JSUnaryOp,
)

from .classes import (
    Attribute_super,
    Call_isinstance,
    Call_issubclass,
    Call_super,
    Subscript_super,
)

from .obvious import (
    Assign_all,
    Assign_default,
    Attribute_default,
    BinOp_default,
    Call_default,
    Compare_default,
    Expr_default,
    Name_default,
    Subscript_default,
)

from . import _normalize_name


#### Expr

# docstrings &rarr; comment blocks
def Expr_docstring(t, x):
    if is_str(x.value):
        return JSCommentBlock(x.value.value)


Expr = [Expr_docstring, Expr_default]


# <code>2**3</code> &rarr; <code>Math.pow(2, 3)</code>
def BinOp_pow(t, x):
    if isinstance(x.op, ast.Pow):
        return JSCall(
            JSAttribute(
                JSName('Math'),
                'pow'),
            [x.left, x.right])


BinOp = [BinOp_pow, BinOp_default]


# <code>self</code> &rarr; <code>this</code>
def Name_self(t, x):
    if x.id == 'self':
        return JSThis()


Name = [Name_self, Name_default]


# <code>typeof(x)</code> &rarr; <code>(typeof x)</code>
def Call_typeof(t, x):
    if (isinstance(x.func, ast.Name) and x.func.id == 'typeof'):
        assert len(x.args) == 1
        return JSUnaryOp(JSOpTypeof(), x.args[0])


def Call_callable(t, x):
    """Translate ``callable(foo)`` to ``foo instanceof Function``."""
    if (isinstance(x.func, ast.Name) and x.func.id == 'callable'):
        assert len(x.args) == 1
        return JSBinOp(
            JSBinOp(x.args[0], JSOpInstanceof(), JSName('Function')),
            JSOpOr(),
            JSBinOp(
                JSUnaryOp(JSOpTypeof(), x.args[0]),
                JSOpStrongEq(),
                JSStr('function')
            )
        )


# <code>print(...)</code> &rarr; <code>console.log(...)</code>
def Call_print(t, x):
    if (isinstance(x.func, ast.Name) and x.func.id == 'print'):
        return JSCall(JSAttribute(JSName('console'), 'log'), x.args)


# <code>len(x)</code> &rarr; <code>x.length</code>
def Call_len(t, x):
    if (isinstance(x.func, ast.Name) and x.func.id == 'len' and
        len(x.args) == 1):
        return JSAttribute(x.args[0], 'length')


def Call_str(t, x):
    if (isinstance(x.func, ast.Name) and x.func.id == 'str' and
        len(x.args) == 1):
        return JSCall(JSAttribute(JSName(x.args[0]), 'toString'), [])


def Call_new(t, x):
    """Translate ``Foo(...)`` to ``new Foo(...)`` if function name starts
    with a capital letter.
    """
    def getNameString(x):
        if isinstance(x, ast.Name):
            return x.id
        elif isinstance(x, ast.Attribute):
            return str(x.attr)

    NAME_STRING = getNameString(x.func)

    if (NAME_STRING and re.search(r'^[A-Z]', NAME_STRING)):
        # TODO: generalize args mangling and apply here
        # assert not any([x.keywords, x.starargs, x.kwargs])
        subj = x
    elif isinstance(x.func, ast.Name) and x.func.id == 'new':
        subj = x.args[0]
    else:
        subj = None
    if subj:
        return Call_default(t, subj, operator='new ')


def Call_import(t, x):
    if (isinstance(x.func, ast.Name) and x.func.id == '__import__'):
        assert len(x.args) == 1 and is_str(x.args[0])
        t.es6_guard(x, "'__import__()' call requires ES6")
        return JSDependImport(x.args[0].value)


def Call_type(t, x):
    if (isinstance(x.func, ast.Name) and x.func.id == 'type'):
        assert len(x.args) == 1
        return JSCall(JSAttribute(JSName('Object'), 'getPrototypeOf'), x.args)


def Call_dict_update(t, x):
    """Convert ``dict(foo).update(bar)`` to ``Object.assign(foo, bar)``.

    Requires ES6

    AST dump::

      Expr(value=Call(args=[Name(ctx=Load(),
                                 id='bar')],
                      func=Attribute(attr='update',
                                     ctx=Load(),
                                     value=Call(args=[Name(ctx=Load(),
                                                           id='foo')],
                                                func=Name(ctx=Load(),
                                                          id='dict'),
                                                keywords=[])),
                      keywords=[]))

    """
    if isinstance(x.func, ast.Attribute) and x.func.attr == 'update' and \
       isinstance(x.func.value, ast.Call) and  \
       isinstance(x.func.value.func, ast.Name) and \
       x.func.value.func.id == 'dict' and len(x.func.value.args) == 1:
        t.es6_guard(x, "dict.update() requires ES6")
        return JSCall(
            JSAttribute(JSName('Object'), 'assign'),
            [x.func.value.args[0]] + x.args
            )


def Call_dict_copy(t, x):
    """Convert ``dict(foo).copy()`` to ``Object.assign({}, foo)``.

    Requires ES6

    AST dump::

      Expr(value=Call(args=[],
                      func=Attribute(attr='copy',
                                     ctx=Load(),
                                     value=Call(args=[Name(ctx=Load(),
                                                           id='foo')],
                                                func=Name(ctx=Load(),
                                                          id='dict'),
                                                keywords=[])),
                      keywords=[]))
    """
    if isinstance(x.func, ast.Attribute) and x.func.attr == 'copy' and \
       isinstance(x.func.value, ast.Call) and  \
       isinstance(x.func.value.func, ast.Name) and \
       x.func.value.func.id == 'dict' and len(x.func.value.args) == 1:
        t.es6_guard(x, "dict.copy() requires ES6")
        return JSCall(
            JSAttribute(JSName('Object'), 'assign'),
            (JSDict([], []), x.func.value.args[0])
            )


def Call_template(t, x):
    if (isinstance(x.func, ast.Name) and x.func.id == 'tmpl') and \
       len(x.args) > 0:
        assert len(x.args) == 1
        assert is_str(x.args[0])
        t.es6_guard(x, "template literals require ES6")
        return JSTemplateLiteral(x.args[0].value)


def Call_tagged_template(t, x):
    if (isinstance(x.func, ast.Name) and x.func.id == '__') and \
       len(x.args) > 0 and t.parent_of(x) is not ast.Attribute:
        assert 3 > len(x.args) >= 1
        assert is_str(x.args[0])
        t.es6_guard(x, "tagged templates require ES6")
        if len(x.args) == 2:
            tag = x.args[1]
        else:
            tag = JSName('__')
        return JSTaggedTemplate(x.args[0].value, tag)


def Call_hasattr(t, x):
    """Translate ``hasattr(foo, bar)`` to ``bar in foo``."""
    if (isinstance(x.func, ast.Name) and x.func.id == 'hasattr') and \
       len(x.args) == 2:
        return JSBinOp(x.args[1], JSOpIn(), x.args[0])


def Call_getattr(t, x):
    """Translate ``getattr(foo, bar, default)`` to ``foo[bar] || default``."""
    if (isinstance(x.func, ast.Name) and x.func.id == 'getattr') and \
       2 <= len(x.args) < 4:
        if len(x.args) == 2:
            res = JSSubscript(x.args[0], x.args[1])
        else:
            res = JSBinOp(
                JSSubscript(x.args[0], x.args[1]),
                JSOpOr(),
                x.args[2]
            )
        return res


def Call_setattr(t, x):
    """Translate ``setattr(foo, bar, value)`` to ``foo[bar] = value``."""
    if (isinstance(x.func, ast.Name) and x.func.id == 'setattr') and \
       len(x.args) == 3:
        return JSExpressionStatement(
            JSAssignmentExpression(
                JSSubscript(x.args[0], x.args[1]),
                x.args[2]
            )
        )


def Call_JS(t, x):
    if (isinstance(x.func, ast.Name) and x.func.id == 'JS') and \
       len(x.args) == 1:
        assert is_str(x.args[0])
        return JSLiteral(x.args[0].value)


def Call_int(t, x):
    # maybe this needs a special keywords mangling for optional "base" param
    if isinstance(x.func, ast.Name) and x.func.id == 'int':
        if t.enable_es6:
            return JSCall(JSAttribute('Number', 'parseInt'), x.args)
        else:
            return JSCall(JSName('parseInt'), x.args)


def Call_float(t, x):
    if isinstance(x.func, ast.Name) and x.func.id == 'float':
        if t.enable_es6:
            return JSCall(JSAttribute('Number', 'parseFloat'), x.args)
        else:
            return JSCall(JSName('parseFloat'), x.args)


Call = [Call_typeof, Call_callable, Call_isinstance, Call_print, Call_len,
        Call_JS, Call_new, Call_super, Call_import, Call_str, Call_type,
        Call_dict_update, Call_dict_copy, Call_tagged_template, Call_template,
        Call_hasattr, Call_getattr, Call_setattr, Call_issubclass,
        Call_int, Call_float, Call_default]


#### Ops

# <code>==</code>
#
# Transform to <code>===</code>
def Eq(t, x):
    return JSOpStrongEq()


Is = Eq


# <code>!=</code>
#
# Transform to <code>!==</code>
def NotEq(t, x):
    return JSOpStrongNotEq()


IsNot = NotEq

#### Import

AT_PREFIX_RE = re.compile(r'^__([a-zA-Z0-9])')
INSIDE_DUNDER_RE = re.compile(r'([a-zA-Z0-9])__([a-zA-Z0-9])')


GEN_PREFIX_RE = re.compile(r'((?:[a-zA-Z][a-z]+)+)_')
SINGLE_WORD_RE = re.compile(r'([A-Z][a-z]+)')


_shortcuts = {
    'at': '@'
}


def _notable_replacer_gen():
    """This is used together with 'GEN_PREFIX_RE' to replace unicode
    symbol names in module prefixes. Some names are shortcut using the
    ``_shortcuts`` map. It's designed to replace matches only if they
    are located at the beginning of the string and if they are
    subsequent to one another. It returns a function to be used with a
    regular expression object ``sub()`` method.
    """
    last_match_end = None

    def replace_notable_name(match):
        nonlocal last_match_end
        # try to replace only if the match is positioned at the start
        # or is following another match
        if ((last_match_end is None and match.start() == 0) or
            (isinstance(last_match_end, int) and
             last_match_end == match.start())):
            last_match_end = match.end()
            prefix = match.group(1)
            low_prefix = prefix.lower()
            if low_prefix in _shortcuts:
                return _shortcuts[low_prefix]
            try:
                prefix = SINGLE_WORD_RE.sub(r' \1', prefix).strip()
                return lookup(prefix)
            except KeyError:
                pass
        return match.group()
    return replace_notable_name


def _replace_identifiers_with_symbols(dotted_str):
    """Replaces two kinds of identifiers with characters. This is used to
    express characters that are used in JS module paths in Python's
    ``import`` statements.

    1. The first replaces ``__`` (a "dunder") with ``@`` if it's at
       the beginning and with ``-`` if it's in the middle of two
       words;
    2. the second replaces notable names ending with an underscore
       like ``tilde_`` with the corresponding character (only at the
       beginning).

    Returns a string with the mangled dotted path
    """
    dotted_str = AT_PREFIX_RE.sub(r'@\1', dotted_str)
    dotted_str = INSIDE_DUNDER_RE.sub(r'\1-\2', dotted_str)

    dotted_str = GEN_PREFIX_RE.sub(_notable_replacer_gen(), dotted_str)

    return dotted_str


def Import(t, x):
    t.es6_guard(x, "'import' statement requires ES6")
    names = []
    for n in x.names:
        names.append(n.asname or n.name)
    t.add_globals(*names)
    result = []
    for n in x.names:
        old_name = n.name
        n.name = _replace_identifiers_with_symbols(n.name)
        t.unsupported(x, (old_name != n.name) and not n.asname,
                      "Invalid module name: {!r}: use 'as' to give "
                      "it a new name.".format(n.name))
        path_module = '/'.join(n.name.split('.'))
        result.append(
            JSStarImport(path_module, n.asname or n.name)
        )
    return JSStatements(*result)


def ImportFrom(t, x):
    names = []
    for n in x.names:
        names.append(n.asname or n.name)
    if x.module == '__globals__':
        assert x.level == 0
        # assume a fake import to import js stuff from root object
        t.add_globals(*names)
        result = JSPass()
    else:
        t.es6_guard(x, "'import from' statement requires ES6")
        t.add_globals(*names)
        result = JSPass()
        if x.module:
            mod = tuple(_normalize_name(frag) for frag in
                        _replace_identifiers_with_symbols(x.module).split('.'))
            path_module = '/'.join(mod)
            if x.level == 1:
                # from .foo import bar
                path_module = './' + path_module
            elif x.level > 1:
                # from ..foo import bar
                # from ...foo import bar
                path_module = '../' * (x.level - 1) + path_module
            if len(x.names) == 1 and x.names[0].name == '__default__':
                t.unsupported(x, x.names[0].asname is None,
                              "Default import must declare an 'as' clause.")
                result = JSDefaultImport(path_module, x.names[0].asname)
            else:
                result = JSNamedImport(path_module,
                                       [(n.name, n.asname) for n in x.names])
        else:
            assert x.level > 0
            result = []
            for n in x.names:
                if x.level == 1:
                    # from . import foo
                    imp = JSStarImport('./' + n.name, n.asname or n.name)
                else:
                    # from .. import foo
                    imp = JSStarImport('../' * (x.level - 1) + n.name,
                                       n.asname or n.name)
                if len(x.names) == 1:
                    imp.py_node = x
                else:
                    imp.py_node = n
                result.append(imp)
            result = JSStatements(*result)
    return result


def Compare_in(t, x):
    if not isinstance(x.ops[0], (ast.NotIn, ast.In)):
        return
    if t.enable_snippets:
        from ..snippets import _in, in_es6
        if t.enable_es6:
            t.add_snippet(in_es6)
            sname = 'in_es6'
        else:
            t.add_snippet(_in)
            sname = '_in'
        result = JSCall(JSAttribute('_pj', sname), [x.left, x.comparators[0]])
        if isinstance(x.ops[0], ast.NotIn):
            result = JSUnaryOp(JSOpNot(), result)
        return result


Compare = [Compare_in, Compare_default]


def Subscript_slice(t, x):

    if isinstance(x.slice, ast.Slice):
        slice = x.slice
        t.unsupported(x, slice.step and slice.step != 1,
                      "Slice step is unsupported")
        args = []
        if slice.lower:
            args.append(slice.lower)
        else:
            args.append(JSNum(0))
        if slice.upper:
            args.append(slice.upper)

        return JSCall(JSAttribute(x.value, 'slice'), args)


Subscript = [Subscript_slice, Subscript_super, Subscript_default]


def Attribute_list_append(t, x):
    """Convert ``list(foo).append(bar)`` to ``foo.push(bar)``.

    AST dump::

      Expr(value=Call(args=[Name(ctx=Load(),
                                 id='bar')],
                      func=Attribute(attr='append',
                                     ctx=Load(),
                                     value=Call(args=[Name(ctx=Load(),
                                                           id='foo')],
                                                func=Name(ctx=Load(),
                                                          id='list'),
                                                keywords=[])),
                      keywords=[]))
    """
    if x.attr == 'append' and isinstance(x.value, ast.Call) and \
       isinstance(x.value.func, ast.Name) and x.value.func.id == 'list' and \
       len(x.value.args) == 1:
        return JSAttribute(x.value.args[0], 'push')


Attribute = [Attribute_super, Attribute_list_append, Attribute_default]


def Assert(t, x):
    """Convert ``assert`` statement to just a snippet function call."""
    if t.enable_snippets:
        from ..snippets import _assert
        t.add_snippet(_assert)
        return JSCall(JSAttribute('_pj', '_assert'),
                      [x.test, x.msg or JSNull()])


def Assign_default_(t, x):
    if len(x.targets) == 1 and isinstance(x.targets[0], ast.Name) and \
       x.targets[0].id == '__default__':
        t.es6_guard(x, "'__default__' assignment requires ES6")
        t.unsupported(x.value, isinstance(x.value, (ast.Tuple, ast.List)),
                      "Only one symbol can be exported using '__default__'.")
        if is_str(x.value):
            return JSExportDefault(x.value.value)
        else:
            return JSExportDefault(x.value)


Assign = [Assign_all, Assign_default_, Assign_default]
