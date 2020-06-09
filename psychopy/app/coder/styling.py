import wx
import wx.stc as stc
import json
import keyword
import builtins


class StylerMixin:
    lexers = {
        stc.STC_LEX_PYTHON: "python",
        stc.STC_LEX_CPP: "c++",
        stc.STC_LEX_R: "R"
    }

    @property
    def theme(self):
        return self.coder.prefs['theme']

    @theme.setter
    def theme(self, value):
        # Load theme from json file
        with open("coder//themes//" + value + ".json", "rb") as fp:
            spec = json.load(fp)

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
        base['tag'] = getattr(stc, base['tag'])
        base['bg'] = self.hex2rgb(base['bg'])
        base['fg'] = self.hex2rgb(base['fg'])
        base['size'] = int(self.coder.prefs['codeFontSize'])
        # Set base colours
        self.StyleSetBackground(base['tag'], base['bg'])
        self.StyleSetForeground(base['tag'], base['fg'])
        self.StyleSetSpec(base['tag'], "face:%(font)s,size:%(size)d" % base)

        # Check that universal spec is defined
        if 'universal' in spec:
            universal = spec['universal']
        else:
            return
        # Pythonise the universal data (hex -> rgb, tag -> wx int)
        for key in universal:
            universal[key]['tag'] = [getattr(stc, tag) for tag in universal[key]['tag']]
            universal[key]['bg'] = self.hex2rgb(universal[key]['bg'], base['bg'])
            universal[key]['fg'] = self.hex2rgb(universal[key]['fg'], base['fg'])
            if not universal[key]['font']:
                universal[key]['font'] = base['font']
            universal[key]['size'] = int(self.coder.prefs['codeFontSize'])
        # Set colours from spec
        for key in universal:
            for tag in universal[key]['tag']:
                self.StyleSetBackground(tag, universal[key]['bg'])
                self.StyleSetForeground(tag, universal[key]['fg'])
                self.StyleSetSpec(tag, "face:%(font)s,size:%(size)d" % universal[key])
        # Apply keywords
        for level, val in self.lexkw.items():
            self.SetKeyWords(level, " ".join(val))

        # Set margin colours to match linenumbers if set
        if 'margin' in universal:
            mar = universal['margin']['bg']
        else:
            mar = base['bg']
        self.SetFoldMarginColour(True, mar)
        self.SetFoldMarginHiColour(True, mar)

        # Check that Psychopy has configuration for this language
        if self.GetLexer() not in self.lexers:
            return
        # Check that json file has spec for this language
        if self.lexers[self.GetLexer()] in spec:
            lang = spec[self.lexers[self.GetLexer()]]
        else:
            return
        # Pythonise language specific data (hex -> rgb, tag -> wx int)
        for key in lang:
            lang[key]['tag'] = getattr(stc, lang[key]['tag'])
            lang[key]['bg'] = self.hex2rgb(lang[key]['bg'], base['bg'])
            lang[key]['fg'] = self.hex2rgb(lang[key]['fg'], base['fg'])
            if not spec[key]['font']:
                lang[key]['font'] = base['font']
        # Set colours from spec
        for key in lang:
            self.StyleSetBackground(lang[key]['tag'], spec[key]['bg'])
            self.StyleSetForeground(lang[key]['tag'], spec[key]['fg'])
            lang[key]['size'] = int(self.coder.prefs['codeFontSize'])
            self.StyleSetSpec(lang[key]['tag'], "face:%(font)s,size:%(size)d" % lang[key])
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
        elif self.GetLexer == stc.STC_LEX_CPP:
            # C/C++
            keywords = baseC
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
        else:
            keywords = {
                0: [],
                1: []
            }
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