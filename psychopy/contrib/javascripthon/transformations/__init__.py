# -*- coding: utf-8 -*-
# :Project:  metapensiero.pj
# :Created:  gio 09 mar 2017 19:43:11 CET
# :Author:   Alberto Berti <alberto@metapensiero.it>
# :License:  GNU General Public License version 3 or later
#

import ast
import logging

from ..compat import is_str
from ..js_ast import JSKeySubscript, JSStr, TargetNode

logger = logging.getLogger(__name__)


def _normalize_name(n):
    if n.startswith('d_'):
        n = n.replace('d_', '$')
    elif n.startswith('dd_'):
        n = n.replace('dd_', '$$')
    # allow to reference names that are Python's keywords by appending
    # a dash to them
    elif not n.startswith('_') and n.endswith('_'):
        n = n[:-1]
    return n

def _normalize_dict_keys(transformer, keys):
    res = []
    for key in keys:
        if isinstance(key, str):
            key = ast.Constant(key)
        elif isinstance(key, JSStr):
            key = ast.Constant(key.args[0])
        if not is_str(key):
            if transformer.enable_es6:
                key = JSKeySubscript(key)
            else:
                if isinstance(key, ast.AST):
                    py_node = key
                elif isinstance(key, TargetNode) and key.py_node is not None:
                    py_node = key.py_node
                else:
                    raise ValueError('Value of type %r cannot '
                                     'be use as key' % type(key))
                transformer.unsupported(py_node, True, 'Value of type %r cannot '
                                        'be use as key' % type(key))
        res.append(key)
    return res
