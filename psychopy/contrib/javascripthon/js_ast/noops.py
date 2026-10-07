# -*- coding: utf-8 -*-
# :Project:   metapensiero.pj -- noops
# :Created:   gio 08 feb 2018 00:50:00 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2018 Alberto Berti
#

from .base import JSNode
from ..processor.util import delimited_multi_line


class JSPass(JSNode):
    def emit(self):
        return []


class JSCommentBlock(JSNode):
    def emit(self, text):
        assert text.find('*/') == -1
        yield from self.lines(
            delimited_multi_line(self, text, '/*', '*/', True))
