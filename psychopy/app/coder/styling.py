import wx
import wx.stc as stc
import json
import keyword
import builtins


class StylerMixin:
    lexers = {
        wx.stc.STC_LEX_PYTHON: "python"
    }

    @property
    def theme(self):
        return self.coder.prefs['theme']

    @theme.setter
    def theme(self, value):
        # Load theme from json file
        with open("coder//themes//" + value + ".json", "rb") as fp:
            spec = json.load(fp)
        # Check that Psychopy has configuration for this language
        if self.GetLexer() not in self.lexers:
            return

        # Check that minimum spec is defined
        if 'base' in spec:
            base = spec['base']
            if 'tag' in base \
                    or 'bg' in base \
                    or 'fg' in base \
                    or 'font' in base:
                base = spec['base']
            else:
                return
        else:
            return
        # Pythonise base data (hex -> rgb, tag -> wx int)
        base['tag'] = eval(base['tag'])
        base['bg'] = self.hex2rgb(base['bg'])
        base['fg'] = self.hex2rgb(base['fg'])
        base['size'] = int(self.coder.prefs['codeFontSize'])
        # Set base colours
        self.StyleSetBackground(base['tag'], base['bg'])
        self.StyleSetForeground(base['tag'], base['fg'])
        self.StyleSetSpec(base['tag'], "face:%(font)s,size:%(size)d" % base)

        # Check that margin spec is defined
        if 'margin' in spec:
            margin = spec['margin']
            if 'tag' in margin \
                    or 'bg' in margin \
                    or 'fg' in margin \
                    or 'font' in margin:
                # Pythonise margin data
                margin['tag'] = eval(margin['tag'])
                margin['bg'] = self.hex2rgb(margin['bg'])
                margin['fg'] = self.hex2rgb(margin['fg'])
                if not margin['font']:
                    margin['font'] = base['font']
                # Set margin colours
                self.StyleSetBackground(margin['tag'], margin['bg'])
                self.StyleSetForeground(margin['tag'], margin['fg'])
                margin['size'] = int(self.coder.prefs['codeFontSize'])
                self.StyleSetSpec(margin['tag'], "face:%(font)s,size:%(size)d" % margin)
                # Set fold margin to match lineno margin
                mar = margin['bg']
            else:
                mar = base['bg']
        else:
            mar = base['bg']
        self.SetFoldMarginColour(True, mar)
        self.SetFoldMarginHiColour(True, mar)

        # Check that json file has spec for this language
        if self.lexers[self.GetLexer()] in spec:
            spec = spec[self.lexers[self.GetLexer()]]
        else:
            return

        # Pythonise the json data (hex -> rgb, tag -> wx int)
        for key in spec:
            spec[key]['tag'] = eval(spec[key]['tag'])
            spec[key]['bg'] = self.hex2rgb(spec[key]['bg'], base['bg'])
            spec[key]['fg'] = self.hex2rgb(spec[key]['fg'], base['fg'])
            if not spec[key]['font']:
                spec[key]['font'] = base['font']
        # Set colours from spec
        for key in spec:
            self.StyleSetBackground(spec[key]['tag'], spec[key]['bg'])
            self.StyleSetForeground(spec[key]['tag'], spec[key]['fg'])
            spec[key]['size'] = int(self.coder.prefs['codeFontSize'])
            self.StyleSetSpec(spec[key]['tag'], "face:%(font)s,size:%(size)d" % spec[key])
        # Apply keywords
        for level, val in self.lexkw.items():
            self.SetKeyWords(level, " ".join(val))

    @property
    def lexkw(self):
        baseC = {
            0: ['typedef', 'if', 'else', 'return', 'struct', 'for', 'while', 'do',
                'using', 'namespace', 'union', 'break', 'enum', 'new', 'case',
                'switch', 'continue', 'volatile', 'finally', 'throw', 'try',
                'delete', 'typeof', 'sizeof', 'class', 'volatile'],
            1: ['int', 'float', 'double', 'char', 'short', 'byte', 'void', 'const',
                'unsigned', 'signed', 'NULL', 'true', 'false', 'bool', 'size_t',
                'long', 'long long']
        }
        if self.GetLexer() == stc.STC_LEX_PYTHON:
            # Python
            keywords = {
                0: keyword.kwlist + ['cdef', 'ctypedef', 'extern', 'cimport', 'cpdef', 'include'],
                1: dir(builtins) + ['self']
            }
        # elif self.GetLexer() == stc.STC_LEX_JAVASCRIPT:
        #     # JavaScript
        #     keywords = {
        #         0: ['var', 'let', 'import', 'function', 'if', 'else', 'return', 'struct', 'for', 'while', 'do',
        #             'finally', 'throw', 'try', 'switch', 'case', 'break'],
        #         1: ['null', 'false', 'true']
        #     }
        elif self.GetLexer() == stc.STC_LEX_R:
            # R
            keywords = {
                1: ['function', 'for', 'repeat', 'while', 'if', 'else',
                 'break', 'local', 'global'],
                0: ['NA']
            }
        # elif self.GetLexer == stc.STC_LEX_C:
        #     # C/C++
        #     keywords = baseC
        # elif self.GetLexer() == stc.STC_LEX_ARDUINO:
        #     # Arduino
        #     keywords = {
        #         0: baseC[0],
        #         1: baseC[1] + [
        #             'BIN', 'HEX', 'OCT', 'DEC', 'INPUT', 'OUTPUT', 'HIGH', 'LOW',
        #             'INPUT_PULLUP', 'LED_BUILTIN', 'string', 'array']
        #     }
        # elif self.GetLexer() == stc.STC_LEX_GLSL:
        #     # GLSL
        #     glslTypes = []
        #     baseType = ['', 'i', 'b', 'd']
        #     dim = ['2', '3', '4']
        #     name = ['vec', 'mat']
        #     for i in baseType:
        #         for j in name:
        #             for k in dim:
        #                 glslTypes.append(i + j + k)
        #     keywords = {
        #         0: baseC[0] + ['invariant', 'precision', 'highp', 'mediump', 'lowp', 'coherent',
        #                                 'sampler', 'sampler2D'],
        #         1: baseC[1]
        #     }
        return keywords

    def hex2rgb(self, hex, base=(0, 0, 0, 0)):
        if not isinstance(hex, str):
            raise Exception("Hex code must be a string in format #xxxxxx")
        # Make hex code case irrelevant
        hex = hex.lower()
        # dict of hex -> int conversions
        hexkeys = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
                   'a': 10, 'b': 11, 'c': 12, 'd': 13, 'e': 14, 'f': 15,
                   '#': None}
        # Check that hex is a hex code
        if not all(c in hexkeys.keys() for c in hex) or not len(hex) == 7:
            # Default to transparent if not
            return wx.Colour(base)

        # Convert to rgb
        r = hexkeys[hex[1]] * 16 + hexkeys[hex[2]]
        g = hexkeys[hex[3]] * 16 + hexkeys[hex[4]]
        b = hexkeys[hex[5]] * 16 + hexkeys[hex[6]]
        return wx.Colour(r, g, b, 1)