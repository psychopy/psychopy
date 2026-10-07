# -*- coding: utf-8 -*-
# :Project:  metapensiero.pj -- transformation processor
# :Created:  ven 26 feb 2016 15:17:49 CET
# :Authors:  Andrew Schaaf <andrew@andrewschaaf.com>,
#            Alberto Berti <alberto@metapensiero.it>
# :License:  GNU General Public License version 3 or later
#

import ast
import collections
import contextlib
import os
import sys
import string
import textwrap

from ..js_ast import TargetNode

from .exceptions import TransformationError, UnsupportedSyntaxError
from .util import (rfilter, parent_of, obj_source, body_local_names,
                   walk_under_code_boundary)

SNIPPETS_TEMPLATE = """\
def _pj_snippets(container):
%(snippets)s
%(assignments)s
    return container

_pj = {}
_pj_snippets(_pj)

"""

ASSIGN_TEMPLATE = "    container['%(name)s'] = %(name)s"

VAR_TEMPLATE = "_pj_%s"


class Transformer:

    enable_snippets = True
    enable_es6 = False
    enable_let = False
    enable_stage3 = False
    disable_srcmap = False

    """Used in subtransformation to remap a node on a Transformer instance
    to the AST produced by a substransform."""
    remap_to = None

    def __init__(self, py_ast_module, statements_class, snippets=True,
                 es6=False, stage3=False, remap_to=None):
        self.transformations = load_transformations(py_ast_module)
        self.statements_class = statements_class
        self.enable_snippets = snippets
        self.enable_es6 = es6
        self.enable_stage3 = stage3
        self.remap_to = remap_to
        self._init_structs()

    def _init_structs(self):
        self.snippets = set()
        self._globals = set()
        self._args_stack = []
        self._context = collections.ChainMap()
        self._warnings = []

    @property
    def ctx(self):
        return self._context

    def _push_ctx(self, **kwargs):
        self._context = self._context.new_child(kwargs)

    def _pop_ctx(self):
        self._context = self._context.parents

    @contextlib.contextmanager
    def context_for(self, py_node, **kwargs):
        if isinstance(py_node, ast.stmt):
            self._push_ctx(**kwargs)
            yield
            self._pop_ctx()
        else:
            yield

    @classmethod
    def new_from(cls, instance):
        new = cls.__new__(cls)
        new._init_structs()
        new.transformations = instance.transformations
        new.statements_class = instance.statements_class
        for k, v in vars(instance).items():
            if k.startswith('enable_'):
                setattr(new, k, v)
        return new

    def transform_code(self, ast_tree):
        """Convert the given Python AST dump into JavaScript AST."""
        from ..js_ast import JSVarStatement

        top = ast.parse(ast_tree)
        body = top.body
        self._args_stack.clear()

        self.node_parent_map = build_node_parent_map(top)

        local_vars = body_local_names(body)
        self.ctx['vars'] = local_vars
        result = self.statements_class(*body)
        self._finalize_target_node(result)

        local_vars = list(local_vars - self._globals)
        if len(local_vars) > 0:
            local_vars.sort()
            vars = JSVarStatement(local_vars,
                                  [None] * len(local_vars))
            self._finalize_target_node(vars)
            result.transformed_args.insert(0, vars)

        self.node_parent_map = None

        return result

    def parent_of(self, node):
        """Return the parent of the given node."""
        return self.node_parent_map.get(node)

    def parents(self, node, stop_at=None):
        """Return all the parents possibly up an instance of `stop_at`
        class."""
        parent = self.node_parent_map.get(node)
        while parent:
            yield parent
            if stop_at and isinstance(parent, stop_at):
                break
            parent = self.node_parent_map.get(parent)

    def find_parent(self, node, *classes):
        """Retrieve the first parent of the given AST `node` that is an
        instance of the given `classes`.
        """
        parent = self.parent_of(node)
        if parent is not None:
            if isinstance(parent, classes):
                return parent
            else:
                return self.find_parent(parent, *classes)

    def find_child(self, node, cls):
        """Find any child of `node` that is an instance of `cls`. The walk
        will not go down into other code blocks.
        """
        if not isinstance(node, (tuple, list, set)):
            node = (node)
        for n in node:
            for c in walk_under_code_boundary(n):
                if isinstance(c, cls):
                    yield c

    def has_child(self, node, cls):
        """Return true if `node` has any child that is an instance of
        `cls`."""
        wanted = tuple(self.find_child(node, cls))
        return len(wanted) > 0

    def new_name(self):
        """Generate a new name to use in statements."""
        ix = self.ctx.setdefault('gen_name_ix', -1)
        ix += 1
        self.ctx['gen_name_ix'] = ix
        if ix > len(string.ascii_letters):
            raise TransformationError("Reached maximum index for "
                                      "auto-generated variable names")
        return VAR_TEMPLATE % string.ascii_letters[ix]

    def add_snippet(self, func):
        """Add a function to the snippets."""
        self.snippets.add(func)

    def _transform_node(self, in_node):
        """Transform a Python AST node to a JS AST node."""

        if isinstance(in_node, list) or isinstance(in_node, tuple):
            res = [self._transform_node(child) for child in in_node]

        elif isinstance(in_node, ast.AST):
            # prepare a context for the transformation if it's a
            # statement; it's used for example by try...catch stmts to
            # give hints to raise
            with self.context_for(in_node):
                # transformations can come in tuples or lists, take the
                # first one
                for transformation in self.transformations.get(
                        in_node.__class__.__name__, []):
                    out_node = transformation(self, in_node)
                    if out_node is not None:
                        self._finalize_target_node(out_node, py_node=in_node)
                        res = out_node
                        break
                else:
                    raise TransformationError(
                        in_node, "No transformation for the node")

        elif isinstance(in_node, TargetNode):
            self._finalize_target_node(in_node)
            res = in_node
        else:
            # e.g. an integer
            res = in_node
        return res

    def _finalize_target_node(self, tnode, py_node=None):
        tnode.py_node = self.remap_to or py_node or tnode.py_node
        tnode.transformer = self
        if tnode.transformed_args is None:
            tnode.transformed_args = targs = []
            args = collections.deque(tnode.args)
            self._args_stack.append(args)
            while args:
                arg = args.popleft()
                targs.append(self._transform_node(arg))
            self._args_stack.pop()

    def transform_snippets(self):
        snippets = tuple(sorted(self.snippets, key=lambda e: e.__name__))
        srcs = [obj_source(s) for s in snippets]
        src = textwrap.indent('\n'.join(srcs), ' ' * 4)
        names = [s.__name__ for s in snippets]
        assign_src = '\n'.join([ASSIGN_TEMPLATE % {'name': n} for n in names])
        trans_src = SNIPPETS_TEMPLATE % {
            'snippets': src,
            'assignments': assign_src
        }
        t = self.new_from(self)
        t.snippets = None
        t.enable_snippets = False
        t.disable_srcmap = True
        return t.transform_code(trans_src)

    def add_globals(self, *items):
        self._globals |= set(items)

    def _guard(self, test, node, desc):
        if not test:
            raise TransformationError(node, desc)

    def es6_guard(self, node, desc):
        """Raise an exception if es6 isn't enabled."""
        self._guard(self.enable_es6, node, desc)

    def next_args(self):
        return self._args_stack[-1]

    def unsupported(self, py_node, cond, desc):
        """Raise an exception if `cond` is ``True``."""
        if cond:
            raise UnsupportedSyntaxError(py_node, desc)
        return False

    def warn(self, py_node, msg):
        """Append the given message to the warnings."""
        self._warnings.append((py_node, msg))

    def subtransform(self, obj, remap_to=None):
        """Transform a piece of code, either a python object or a string. This
        is done in a new ``Transformer`` with a configuration similar
        to the calling instance.
        """
        if isinstance(obj, str):
            src = textwrap.dedent(obj)
        else:
            src = obj_source(obj)
        t = self.new_from(self)
        t.remap_to = remap_to
        t.snippets = None
        t.enable_snippets = False
        return t.transform_code(src)

    def stage3_guard(self, node, desc):
        """Raise an exception if stage3 isn't enabled."""
        self._guard(self.enable_stage3, node, desc)


#### Helpers

def python_ast_names():
    #LATER: do this properly
    return rfilter(r'[A-Z][a-zA-Z]+', dir(ast))


def load_transformations(py_ast_module):
    # transformationsDict = {
    #     'NodeName': [...transformation functions...]
    # }
    d = {}
    ast_names = list(python_ast_names())
    filenames = rfilter(
        r'^[^.]+\.py$',
        os.listdir(parent_of(py_ast_module.__file__)))
    for filename in filenames:
        if filename != '__init__.py':
            mod_name = '%s.%s' % (py_ast_module.__name__,
                                  filename.split('.')[0])
            __import__(mod_name)
            mod = sys.modules[mod_name]
            for name in dir(mod):
                if name in ast_names:
                    assert name not in d
                    value = getattr(mod, name)
                    if not isinstance(value, list) or isinstance(value, tuple):
                        value = [value]
                    d[name] = value
    return d


def build_node_parent_map(top):

    node_parent_map = {}

    def _process_node(node):
        for k in node._fields:
            x = getattr(node, k)
            if not (isinstance(x, list) or isinstance(x, tuple)):
                x = [x]
            for y in x:
                if isinstance(y, ast.AST):
                    node_parent_map[y] = node
                    _process_node(y)

    _process_node(top)

    return node_parent_map
