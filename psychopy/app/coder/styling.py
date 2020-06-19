import wx
import wx.stc as stc
import json
import keyword
import builtins
from wx import py
from psychopy.tools.versionchooser import _translate


class StylerMixin:
    lexers = {
        stc.STC_LEX_PYTHON: "python",
        stc.STC_LEX_CPP: "c++",
        stc.STC_LEX_R: "R"
    }

    @property
    def theme(self):
        return self.prefs['theme']

    @theme.setter
    def theme(self, value):
        # Load theme from json file
        try:
            with open("{}//{}.json".format(self.paths['themes'], value), "rb") as fp:
                spec = json.load(fp)
        except:
            with open("{}//{}.json".format(self.paths['themes'], "PsychopyLight"), "rb") as fp:
                spec = json.load(fp)

        # Check that minimum spec is defined
        if 'base' in spec:
            base = spec['base']
            if not (
                all(key in base for key in ['bg', 'fg', 'font'])
            ):
                return
        else:
            return
        # Override base font with user spec if present
        key = 'outputFont' if isinstance(self, PsychopyPyShell) else 'codeFont'
        if self.prefs[key] != "From theme...":
            base['font'] = self.prefs[key]

        if isinstance(self, wx.stc.StyledTextCtrl):
            # Check for language specific spec
            if isinstance(self, wx.stc.StyledTextCtrl):
                if self.GetLexer() in self.lexers:
                    lexer = self.lexers[self.GetLexer()]
                else:
                    lexer = 'invlex'
                if lexer in spec:
                    # If there is lang specific spec, delete subkey...
                    lang = spec[lexer]
                    del spec[lexer]
                    #...and append spec to root, overriding any generic spec
                    spec.update({key: lang[key] for key in lang})
                else:
                    lang = {}
            # Pythonise the universal data (hex -> rgb, tag -> wx int)
            invalid = []
            for key in spec:
                # Check that key is in tag list and full spec is defined, discard if not
                if key in self.tags \
                        and all(subkey in spec[key] for subkey in ['bg', 'fg', 'font']):
                    spec[key]['bg'] = self.hex2rgb(spec[key]['bg'], base['bg'])
                    spec[key]['fg'] = self.hex2rgb(spec[key]['fg'], base['fg'])
                    if not spec[key]['font']:
                        spec[key]['font'] = base['font']
                    spec[key]['size'] = int(self.prefs['codeFontSize'])
                else:
                    invalid += [key]
            for key in invalid:
                del spec[key]
            # Set style from universal data
            for key in spec:
                self.StyleSetBackground(self.tags[key], spec[key]['bg'])
                self.StyleSetForeground(self.tags[key], spec[key]['fg'])
                self.StyleSetSpec(self.tags[key], "face:%(font)s,size:%(size)d" % spec[key])
            # Apply keywords
            for level, val in self.lexkw.items():
                self.SetKeyWords(level, " ".join(val))

            # Make sure there's some spec for margins
            if 'margin' not in spec:
                spec['margin'] = base
            # Set margin colours to match linenumbers if set
            if 'margin' in spec:
                mar = spec['margin']['bg']
            else:
                mar = base['bg']
            self.SetFoldMarginColour(True, mar)
            self.SetFoldMarginHiColour(True, mar)

            # Set wrap point
            self.edgeGuideColumn = self.prefs['edgeGuideColumn']
            self.edgeGuideVisible = self.edgeGuideColumn > 0

            # Set line spacing
            spacing = min(int(self.prefs['lineSpacing'] / 2), 64) # Max out at 64
            self.SetExtraAscent(spacing)
            self.SetExtraDescent(spacing)
        elif isinstance(self, wx.richtext.RichTextCtrl):
            # If dealing with a StdOut, set background from base
            self.SetBackgroundColour(self.hex2rgb(base['bg'], base['bg']))
            # Then construct default styles
            _font = wx.Font(
                int(self.prefs['outputFontSize']),
                wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False,
                faceName=base['font']
            )
            _style = wx.TextAttr(colText=wx.Colour(self.hex2rgb(base['fg'], base['fg'])),
                                 colBack=wx.Colour(self.hex2rgb(base['bg'], base['bg'])),
                                 font=_font)
            # Then style all text as base
            i = 0
            for ln in range(self.GetNumberOfLines()):
                i += self.GetLineLength(ln)+1 # +1 as \n is not included in character count
            self.SetStyle(0, i, _style)

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

    @property
    def tags(self):
        tags = {
            "base": stc.STC_STYLE_DEFAULT,
            "margin": stc.STC_STYLE_LINENUMBER,
            "indent": stc.STC_STYLE_INDENTGUIDE,
            "brace": stc.STC_STYLE_BRACELIGHT,
            "controlchar": stc.STC_STYLE_CONTROLCHAR
        }
        if self.GetLexer() == stc.STC_LEX_PYTHON:
            # Python
            tags.update({
                "operator": stc.STC_P_OPERATOR,
                "keyword": stc.STC_P_WORD,
                "keyword2": stc.STC_P_WORD2,
                "id": stc.STC_P_IDENTIFIER,
                "num": stc.STC_P_NUMBER,
                "char": stc.STC_P_CHARACTER,
                "str": stc.STC_P_STRING,
                "openstr": stc.STC_P_STRINGEOL,
                "decorator": stc.STC_P_DECORATOR,
                "def": stc.STC_P_DEFNAME,
                "class": stc.STC_P_CLASSNAME,
                "comment": stc.STC_P_COMMENTLINE,
                "commentblock": stc.STC_P_COMMENTBLOCK,
                "documentation": stc.STC_P_TRIPLE,
                "documentation2": stc.STC_P_TRIPLEDOUBLE,
                "whitespace": stc.STC_P_DEFAULT
            })
        elif self.GetLexer() == stc.STC_LEX_R:
            # R
            tags.update({
                "operator": stc.STC_R_OPERATOR,
                "keyword": stc.STC_R_BASEKWORD,
                "keyword2": stc.STC_R_KWORD,
                "id": stc.STC_R_IDENTIFIER,
                "num": stc.STC_R_NUMBER,
                "char": stc.STC_R_STRING2,
                "str": stc.STC_R_STRING,
                "infix": stc.STC_R_INFIX,
                "openinfix": stc.STC_R_INFIXEOL,
                "comment": stc.STC_R_COMMENT,
                "whitespace": stc.STC_R_DEFAULT
            })
        elif self.GetLexer() == stc.STC_LEX_CPP:
            # C/C++
            tags.update({
                "operator": stc.STC_C_OPERATOR,
                "keyword": stc.STC_C_WORD,
                "keyword2": stc.STC_C_WORD2,
                "id": stc.STC_C_IDENTIFIER,
                "num": stc.STC_C_NUMBER,
                "char": stc.STC_C_CHARACTER,
                "str": stc.STC_C_STRING,
                "openstr": stc.STC_C_STRINGEOL,
                "class": stc.STC_C_GLOBALCLASS,
                "comment": stc.STC_C_COMMENT,
                "commentblock": stc.STC_C_COMMENTLINE,
                "commentkw": stc.STC_C_COMMENTDOCKEYWORD,
                "commenterror": stc.STC_C_COMMENTDOCKEYWORDERROR,
                "documentation": stc.STC_C_COMMENTLINEDOC,
                "documentation2": stc.STC_C_COMMENTDOC,
                "whitespace": stc.STC_C_DEFAULT
            })
        return tags


    def hex2rgb(self, hex, base=(0, 0, 0, 0)):
        if not isinstance(hex, str):
            return base
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


class PsychopyPyShell(wx.py.shell.Shell, StylerMixin):
    '''Simple class wrapper for Pyshell which uses the Psychopy StylerMixin'''
    def __init__(self, coder):
        msg = _translate('PyShell in PsychoPy - type some commands!')
        wx.py.shell.Shell.__init__(self, coder.shelf, -1, introText=msg + '\n\n', style=wx.BORDER_NONE)
        self.prefs = coder.prefs
        self.paths = coder.paths

        # Set theme to match code editor
        self.theme = self.prefs['theme']