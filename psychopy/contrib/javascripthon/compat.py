# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- compatibility
# :Created:   lun 30 mar 2020, 01:48:33
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2020 Alberto Berti
#

import ast
import sys

is_py36 = sys.version_info >= (3, 6)

is_py39 = sys.version_info >= (3, 9)

if is_py36:
    assign_types = (ast.Assign, ast.AnnAssign)
else:
    assign_types = (ast.Assign,)


def is_str(node):
    """Is `node` a string literal? Replaces ``isinstance(node, ast.Str)``,
    as ``ast.Str`` was removed in Python 3.14."""
    return isinstance(node, ast.Constant) and isinstance(node.value, str)
