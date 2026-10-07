# -*- coding: utf-8 -*-
# :Project:  metapensiero.pj -- public api
# :Created:  ven 26 feb 2016 15:16:13 CET
# :Author:   Alberto Berti <alberto@metapensiero.it>
# :License:  GNU General Public License version 3 or later
#
# Vendored from javascripthon 0.13 (https://github.com/azazel75/metapensiero.pj),
# which is no longer maintained. Only the parts needed by `translates` are kept.

import ast
import logging
import textwrap

from .processor.transforming import Transformer
from .processor.util import Block
from .js_ast import JSStatements
from . import transformations

log = logging.getLogger(__name__)


def translates(src_text, dedent=True, src_filename=None, src_offset=None,
               body_only=False, complete_src=None, enable_es6=False,
               enable_stage3=False):
    """Translate the given Python 3 source text to ES6 Javascript.

    If the string comes from a file, it's possible to specify the filename
    that will be inserted into the output source map. The `src_offset` is the
    ``(line_offset, col_offset)`` tuple of the fragment and it's used to
    relocate the map segments. `map_filename` is the intended file name for
    the output map file that will be added as pragma comment to the output JS.

    Setting `body_only` to a true value will change the evaluation behavior to
    translate only the body of the first statement.
    """
    if isinstance(src_text, (tuple, list)):
        src_lines = src_text
        src_text = ''.join(src_text)
    else:
        src_lines = src_text.splitlines()  # removes \n

    # take into account only the lines with content because only those
    # will be dedented
    src_line_num = 0
    for l in src_lines:
        if not len(l.strip()) == 0:
            src_line_num += 1

    sline_offset, scol_offset = src_offset or (0, 0)
    if dedent:
        # remove indentation so that fragments of files with stuff not
        # at root can be evaluated, or ast will complain
        dedented = textwrap.dedent(src_text)
        if len(dedented) < len(src_text):
            scol_offset += (len(src_text) - len(dedented)) // src_line_num
    else:
        dedented = src_text
    t = Transformer(transformations, JSStatements, es6=enable_es6,
                    stage3=enable_stage3)
    pyast = ast.parse(dedented)
    if body_only and hasattr(pyast, 'body') and len(pyast.body) == 1 \
       and hasattr(pyast.body[0], 'body'):
        # if body_only is true, discard the top level element and and
        # take the first child as top, this will allow to use the body
        # of a function or class as it was a module bosy
        pyast = pyast.body[0]
        # naive check, remove the last statement if it's a return
        if isinstance(pyast.body[-1], ast.Return):
            pyast.body.pop()
    jsast = t.transform_code(pyast)
    dline_offset = dcol_offset = 0
    if t.snippets:
        snipast = t.transform_snippets()
        snipast += jsast
        jsast = snipast
    js_code_block = Block(jsast)
    js_text = js_code_block.read()
    if not src_filename:
        src_filename = '<source>'

    src_map = js_code_block.sourcemap(complete_src or src_text, src_filename,
                                      (sline_offset, scol_offset),
                                      (dline_offset, dcol_offset))
    for t in src_map.tokens:
        log.debug("js: (%d, %d)\t\t py: (%d, %d)\t txt: '%s'",
                  t.dst_line, t.dst_col, t.src_line - sline_offset,
                  t.src_col - scol_offset, t.mapping['text'])
    return js_text, src_map
