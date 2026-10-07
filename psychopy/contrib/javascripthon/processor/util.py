# -*- coding: utf-8 -*-
# :Project:  metapensiero.pj -- transformation utilities
# :Created:  ven 26 feb 2016 15:17:49 CET
# :Authors:  Andrew Schaaf <andrew@andrewschaaf.com>,
#            Alberto Berti <alberto@metapensiero.it>
# :License:  GNU General Public License version 3 or later
#

import ast
import inspect
import re
import textwrap
import os.path

from ..compat import is_py36, assign_types
from . import sourcemaps

IGNORED_NAMES = ('__all__', '__default__')


def delimited(delimiter, arr, dest=None, at_end=False):
    """Similar to ``str.join()``, but returns an array with an option to
    append the delimiter at the end.
    """
    if dest is None:
        dest = []
    if arr:
        dest.append(arr[0])
    for i in range(1, len(arr)):
        dest.append(delimiter)
        dest.append(arr[i])
    if at_end:
        dest.append(delimiter)
    return dest


def delimited_multi_line(node, text, begin=None, end=None, add_space=False):
    """Used to deal with single and multi line literals."""
    begin = begin or ''
    end = end or ''
    if begin and not end:
        end = begin
    sp = ' ' if add_space else ''
    lines = text.splitlines()
    if len(lines) > 1:
        yield node.line(node.part(begin, lines[0].strip()))
        for l in lines[1:-1]:
            yield node.line(l.strip())
        yield node.line(node.part(lines[-1].strip(), end))
    else:
        yield node.part(begin, sp, text, sp, end)


def parent_of(path):
    return os.path.split(os.path.normpath(path))[0]


def body_top_names(body):
    names = set()
    for x in body:
        names |= node_names(x)
    return names


def controlled_ast_walk(node):
    """Walk AST just like ``ast.walk()``, but expect ``True`` on every
    branch to descend on sub-branches.
    """
    if isinstance(node, list):
        l = node.copy()
    elif isinstance(node, tuple):
        l = list(node)
    else:
        l = [node]
    while len(l) > 0:
        popped = l.pop()
        check_children = (yield popped)
        if check_children:
            for n in ast.iter_child_nodes(popped):
                l.append(n)


CODE_BLOCK_STMTS = (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)


def walk_under_code_boundary(node):
    it = controlled_ast_walk(node)
    traverse = None
    try:
        while True:
            subn = it.send(traverse)
            yield subn
            if isinstance(subn, CODE_BLOCK_STMTS):
                traverse = False  # continue traversing sub names
            else:
                traverse = True
    except StopIteration:
        pass


def body_local_names(body):
    """Find the names assigned to in the provided `body`. It doesn't descend
    into function or class subelements."""
    names = set()
    for stmt in body:
        for subn in walk_under_code_boundary(stmt):
            if not isinstance(subn, CODE_BLOCK_STMTS):
                names |= node_names(subn)
    return names


def get_assign_targets(py_node):
    if isinstance(py_node, ast.Assign):
        return py_node.targets
    elif is_py36 and isinstance(py_node, ast.AnnAssign):
        return [py_node.target]
    else:
        raise TypeError('Unsupported assign node type: {}'.format(
            py_node.__class__.__name__))


def node_names(py_node):
    """Extract 'names' from a Python node. Names are all those interesting
    for the enclosing scope.

    Return a set containing them. The nodes considered are the Assign and the
    ones that defines namespaces, the function and class definitions.

    The assignment can be something like:

    .. code:: python
      a = b # 'a' is the target
      a = b = c # 'a' and 'b' are the targets
      a1, a2 = b = c # ('a1', 'a2') and 'b' are the targets

    """
    names = set()
    if isinstance(py_node, assign_types):
        for el in get_assign_targets(py_node):
            if isinstance(el, ast.Name) and el.id not in \
               IGNORED_NAMES:
                names.add(el.id)
            elif isinstance(el, ast.Tuple):
                for elt in el.elts:
                    if isinstance(elt, ast.Name) and elt.id not in \
                       IGNORED_NAMES:
                        names.add(elt.id)
    elif isinstance(py_node, (ast.FunctionDef, ast.ClassDef)):
        names.add(py_node.name)
    return names


def rfilter(r, it, invert=False):
    """
    >>> list(rfilter(r'^.o+$', ['foo', 'bar']))
    ['foo']

    >>> list(rfilter(r'^.o+$', ['foo', 'bar'], invert=True))
    ['bar']

    """
    # Supports Python 2 and 3
    if isinstance(r, str):
        r = re.compile(r)
    try:
        if isinstance(r, unicode):
            r = re.compile
    except NameError:
        pass

    for x in it:
        m = r.search(x)
        ok = False
        if m:
            ok = True
        if invert:
            if not ok:
                yield x
        else:
            if ok:
                yield x


class OutputSrc:

    def __init__(self, node, name=None):
        self.node = node
        self.src_name = name

    def _gen_mapping(self, text, src_line=None, src_offset=None,
                     dst_offset=None):
        """Generate a single mapping. `dst_line` is absent from signature
        because the part hasn't this information, but is present in the
        returned mapping. `src_line` is adjusted to be 0-based.

        See `Source Map version 3 proposal
        <https://docs.google.com/document/d/1U1RGAehQwRypUTovF1KRlpiOFze0b-_2gc6fAH0KY0k>`_.
        """
        return {
            'src_line': src_line,
            'src_offset': src_offset,
            'dst_line': None,
            'dst_offset': dst_offset,
            'text': text,
            'name': self.src_name if self.src_name is not True else str(self),
            'part': self
        }

    def _pos_in_src(self):
        """Return the position in source of the generated node."""
        py_node = self.node.py_node
        if py_node:
            offset = getattr(py_node, 'col_offset', 0)
            # multi-line comments have an offset of -1
            if offset < 0:
                offset = 0

            # special handling of nodes that are decorable. Those nodes expose
            # a 'lineno' that starts with the first decorator. for now, take
            # the last decorator lineno and add one
            if isinstance(py_node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                    ast.ClassDef)) and py_node.decorator_list:
                result = (py_node.decorator_list[-1].lineno + 1, offset)
            else:
                result = (getattr(py_node, 'lineno', None),
                          offset)
        else:
            result = (None, None)
        return result


class Line(OutputSrc):

    def __init__(self, node, item, indent=False, delim=False, name=None):
        super().__init__(node, name)
        self.indent = int(indent)
        self.delim = delim
        if isinstance(item, (tuple, list)):
            item = Part(node, *item)
        self.item = item

    def __str__(self):
        line = str(self.item)
        if self.delim:
            line += ';'
        if self.indent and line.strip():
            line = (' ' * 4 * self.indent) + line
        line += '\n'
        return line

    def serialize(self):
        yield self

    def src_mappings(self):
        if self.node.transformer.disable_srcmap:
            return
        src_line, src_offset = self._pos_in_src()
        offset = self.indent * 4
        if isinstance(self.item, str):
            if src_line:
                yield self._gen_mapping(self.item, src_line, src_offset,
                                        offset)
        else:
            assert isinstance(self.item, Part)
            for m in self.item.src_mappings():
                m['dst_offset'] += offset
                yield m

    def __repr__(self):
        return '<%s indent: %d, "%s">' % (self.__class__.__name__,
                                          self.indent, str(self))


class Part(OutputSrc):

    def __init__(self, node, *items, name=None):
        super().__init__(node, name)
        self.items = []
        for i in items:
            if isinstance(i, (str, Part)):
                self.items.append(i)
            elif inspect.isgenerator(i):
                self.items.extend(i)
            else:
                self.items.append(str(i))

    def __str__(self):
        return ''.join(str(i) for i in self.items)

    def serialize(self):
        yield self

    def src_mappings(self):
        if self.node.transformer.disable_srcmap:
            return
        # optional position in source file, if this is missing, there's no
        # reason for generate a source mapping. (not all python AST elements
        # can be source located)
        src_line, src_offset = self._pos_in_src()
        # accumulator for string text
        frag = ''
        col = 0
        # for every item that composes this part...
        for i in self.items:
            assert isinstance(i, (str, Part))
            if isinstance(i, str):
                # if it's a string, just add it to the accumulator (usually
                # comma, parens, etc...)
                frag += i
            elif isinstance(i, Part):
                # if the item is a part
                if frag and src_line:
                    # .. and if there is accumulated text and a src location
                    # emit a src mapping for the accumulated text and reset it
                    yield self._gen_mapping(frag, src_line, src_offset, col)
                col += len(frag)
                frag = ''
                psrc = str(i)
                # ... then , ask the subpart to produce a src mapping and
                # maybe relocate it if necessary
                # yield from i._translate_src_mappings(i, src, psrc, col)
                for m in i.src_mappings():
                    m['dst_offset'] += col
                    yield m
                col += len(psrc)
        else:
            # at the end of the loop, if there is still a fragment and a src
            # location, emit a mapping for it
            if frag and src_line:
                yield self._gen_mapping(frag, src_line, src_offset, col)

    def _translate_src_mappings(self, part, src=None, psrc=None, start=None):
        src = src or str(self)
        psrc = psrc or str(part)
        offset = src.find(psrc, start)
        for m in part.src_mappings():
            m['dst_offset'] += offset
            yield m

    def __repr__(self):
        return '<%s, "%s">' % (self.__class__.__name__,
                               str(self))


def linecounter(iterable, start=1):
    count = start
    for line in iterable:
        yield count, line
        count += len(re.findall('\n', str(line)))


class Block(OutputSrc):

    def __init__(self, node):
        super().__init__(None)
        self.lines = list(node.serialize())

    def src_mappings(self, src_offset=None, dst_offset=None):

        sline_offset, scol_offset = src_offset or (0, 0)
        dline_offset, dcol_offset = dst_offset or (0, 0)
        for ix, line in linecounter(self.lines, start=1):
            for m in line.src_mappings():
                m['dst_line'] = ix + dline_offset
                m['dst_offset'] += dcol_offset
                m['src_line'] += sline_offset
                m['src_offset'] += scol_offset
                yield m

    def read(self):
        return ''.join(str(l) for l in self.lines)

    def sourcemap(self, source, src_filename, src_offset=None,
                  dst_offset=None):
        Token = sourcemaps.Token
        tokens = []
        for m in self.src_mappings(src_offset, dst_offset):
            token = Token(m['dst_line'] - 1, m['dst_offset'], src_filename,
                          m['src_line'] - 1, m['src_offset'], m['name'], m)
            tokens.append(token)

        src_map = sourcemaps.SourceMap(
            sources_content={src_filename: source}
        )
        for t in tokens:
            src_map.add_token(t)
        return src_map


def obj_source(obj):
    src = inspect.getsource(obj)
    src = textwrap.dedent(src)
    return src
