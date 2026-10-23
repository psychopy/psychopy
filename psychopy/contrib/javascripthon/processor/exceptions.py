# -*- coding: utf-8 -*-
# :Project:  metapensiero.pj -- exceptions
# :Created:  ven 26 feb 2016 15:17:49 CET
# :Authors:  Andrew Schaaf <andrew@andrewschaaf.com>,
#            Alberto Berti <alberto@metapensiero.it>
# :License:  GNU General Public License version 3 or later
#

import ast


class ProcessorError(Exception):

    def __str__(self):
        py_node = self.args[0]
        if isinstance(py_node, (ast.expr, ast.stmt)):
            lineno = str(py_node.lineno)
            col_offset = str(py_node.col_offset)
        else:
            lineno = 'n. a.'
            col_offset = 'n. a.'
        return "Node type '%s': Line: %s, column: %s" % (type(py_node).__name__,
                                                         lineno,
                                                         col_offset)


class TransformationError(ProcessorError):

    def __str__(self):
        error = super().__str__()
        if len(self.args) > 1:
            error += ". %s" % self.args[1]
        return error


class UnsupportedSyntaxError(TransformationError):
    pass
