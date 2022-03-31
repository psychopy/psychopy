import builtins
import keyword
from pathlib import Path

import wx
import wx.stc as stc
import re

from ... import prefs
from . import colors, theme, loadSpec


# STC tags corresponding to words in theme spec
tags = {
    "base": stc.STC_STYLE_DEFAULT,
    "margin": stc.STC_STYLE_LINENUMBER,
    "caret": None,
    "select": None,
    "indent": stc.STC_STYLE_INDENTGUIDE,
    "brace": stc.STC_STYLE_BRACELIGHT,
    "controlchar": stc.STC_STYLE_CONTROLCHAR,
    # Python
    "python": {
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
    },
    # R
    "r": {
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
    },
    # C++
    "c++": {
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
        "whitespace": stc.STC_C_DEFAULT,
        "preprocessor": stc.STC_C_PREPROCESSOR,
        "preprocessorcomment": stc.STC_C_PREPROCESSORCOMMENT
    },
    # JSON
    "json": {
        "operator": stc.STC_JSON_OPERATOR,
        "keyword": stc.STC_JSON_KEYWORD,
        "uri": stc.STC_JSON_URI,
        "compactiri": stc.STC_JSON_COMPACTIRI,
        "error": stc.STC_JSON_ERROR,
        "espacesequence": stc.STC_JSON_ESCAPESEQUENCE,
        "propertyname": stc.STC_JSON_PROPERTYNAME,
        "ldkeyword": stc.STC_JSON_LDKEYWORD,
        "num": stc.STC_JSON_NUMBER,
        "str": stc.STC_JSON_STRING,
        "openstr": stc.STC_JSON_STRINGEOL,
        "comment": stc.STC_JSON_LINECOMMENT,
        "commentblock": stc.STC_JSON_BLOCKCOMMENT,
        "whitespace": stc.STC_JSON_DEFAULT
    }
}


def getLexerKeywords(lexer, filename=""):
    """
    Get the keywords to look for with a given lexer.
    """
    # Keywords common to all C-based languages
    baseC = {
        0: ['typedef', 'if', 'else', 'return', 'struct', 'for', 'while', 'do',
            'using', 'namespace', 'union', 'break', 'enum', 'new', 'case',
            'switch', 'continue', 'volatile', 'finally', 'throw', 'try',
            'delete', 'typeof', 'sizeof', 'class', 'volatile', 'int',
            'float', 'double', 'char', 'short', 'byte', 'void', 'const',
            'unsigned', 'signed', 'NULL', 'true', 'false', 'bool', 'size_t',
            'long', 'long long'],
        1: []
    }
    if lexer == stc.STC_LEX_PYTHON:
        # Python
        keywords = {
            0: keyword.kwlist + ['cdef', 'ctypedef', 'extern', 'cimport', 'cpdef', 'include'],
            1: dir(builtins) + ['self']
        }
    elif lexer == stc.STC_LEX_R:
        # R
        keywords = {
            1: ['function', 'for', 'repeat', 'while', 'if', 'else',
                'break', 'local', 'global'],
            0: ['NA']
        }
    elif lexer == stc.STC_LEX_CPP:
        # C/C++
        keywords = baseC.copy()
        if filename.endswith('.js'):
            # JavaScript
            keywords = {
                0: ['var', 'const', 'let', 'import', 'function', 'if',
                    'else', 'return', 'struct', 'for', 'while', 'do',
                    'finally', 'throw', 'try', 'switch', 'case',
                    'break'],
                1: ['null', 'false', 'true']
            }
        elif any([filename.lower().endswith(ext) for ext in (
                '.glsl', '.vert', '.frag')]):
            # keywords
            keywords[0] += [
                'invariant', 'precision', 'highp', 'mediump', 'lowp',
                'coherent', 'sampler', 'sampler2D', 'layout', 'out',
                'in', 'varying', 'uniform', 'attribute']
            # types
            keywords[0] += [
                'vec2', 'vec3', 'vec4', 'mat2', 'mat3', 'mat4',
                'ivec2', 'ivec3', 'ivec4', 'imat2', 'imat3', 'imat4',
                'bvec2', 'bvec3', 'bvec4', 'bmat2', 'bmat3', 'bmat4',
                'dvec2', 'dvec3', 'dvec4', 'dmat2', 'dmat3', 'dmat4']
            # reserved
            keywords[1] += [
                'gl_Position', 'gl_LightSourceParameters',
                'gl_MaterialParameters', 'gl_LightModelProducts',
                'gl_FrontLightProduct', 'gl_BackLightProduct',
                'gl_FrontMaterial', 'gl_BackMaterial', 'gl_FragColor',
                'gl_ModelViewMatrix', 'gl_ModelViewProjectionMatrix',
                'gl_Vertex', 'gl_NormalMatrix', 'gl_Normal',
                'gl_ProjectionMatrix', 'gl_LightSource']

    # elif lexer stc.STC_LEX_ARDUINO:
    #     # Arduino
    #     keywords = {
    #         0: baseC[0],
    #         1: baseC[1] + [
    #             'BIN', 'HEX', 'OCT', 'DEC', 'INPUT', 'OUTPUT', 'HIGH', 'LOW',
    #             'INPUT_PULLUP', 'LED_BUILTIN', 'string', 'array']
    #     }
    # elif lexer == stc.STC_LEX_GLSL:
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


class CodeTheme(dict):
    def __init__(self):
        dict.__init__(self)
        self.load(theme.code)

    def __getitem__(self, item):
        # If theme isn't cached yet, load & cache it
        if theme.code not in self:
            self.load(theme.code)
        # Return value from theme cache
        return dict.__getitem__(self, theme.code)[item]

    def load(self, name):
        cache = {}
        # Load theme from file
        filename = Path(__file__).parent / "spec" / (theme.code + ".json")
        spec = loadSpec(filename)
        # Go through each tag in the code dict
        for key, style in spec['code'].items():
            # Skip if key doesn't correspond to an stc tag
            if key not in tags:
                continue
            # Get tag
            tag = tags[key]
            # If tag is a dict, this means it's a langauge so we need to look for sub-items
            if isinstance(tag, dict):
                for subkey, substyle in style.items():
                    cache[tag[subkey]] = CodeFont(substyle)
            # Otherwise, it points to a single style which we should store
            else:
                cache[tag] = CodeFont(style)
        # Store cache
        dict.__setitem__(self, name, cache)


class CodeFont(wx.Font):
    def __init__(self, spec):
        # Make FontInfo object to initialise with
        info = wx.FontInfo(prefs.coder['codeFontSize'])
        # Set style
        if 'font' in spec:
            bold, italic = self.getFontStyle(spec['font'])
            info.Bold(bold)
            info.Italic(italic)
        # Initialise from info
        wx.Font.__init__(self, info)
        # Set face name
        if 'font' in spec:
            # Get font families
            names = self.getFontName(spec['font'])
            # Try faces sequentially until one works
            success = False
            for name in names:
                success = self.SetFaceName(name)
                if success:
                    break
            # If nothing worked, use the default monospace
            if not success:
                self.SetFaceName(wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT).GetFaceName())

        # Store foreground color
        if 'fg' in spec:
            self.fg = self.getColor(spec['fg'])
        else:
            self.fg = colors.app['text']
        # Store background color
        if 'bg' in spec:
            self.bg = self.getColor(spec['fg'])
        else:
            self.bg = colors.app['tab_bg']

    @staticmethod
    def getFontName(val):
        # Make sure val is a list
        if isinstance(val, str):
            # Get rid of any perentheses
            val = re.sub("[()[]]", "", val)
            # Split by comma
            val = val.split(",")
        # Clear style markers
        val = [p for p in val if val not in ("bold", "italic")]

        return val

    @staticmethod
    def getFontStyle(val):
        bold = "bold" in val
        italic = "italic" in val

        return bold, italic

    @staticmethod
    def getColor(val):
        val = str(val)
        # Split value according to operators, commas and spaces
        val = val.replace("+", " + ").replace("-", " - ").replace("\\", " \\ ")
        parts = re.split(r"[\\\s,()[]]", val)
        parts = [p for p in parts if p]
        # Set assumed values
        color = colors.scheme['black']
        modifier = +0
        alpha = 255
        for i, part in enumerate(parts):
            # If value is a named psychopy color, get it
            if part in colors.scheme:
                color = colors.scheme[part]
            # If assigned an operation, store it for application
            if part == "+" and i < len(parts) and parts[i+1].isnumeric():
                modifier = int(parts[i+1])
            if part == "-" and i < len(parts) and parts[i+1].isnumeric():
                modifier = -int(parts[i+1])
            if part == "*" and i < len(parts) and parts[i + 1].isnumeric():
                alpha = int(parts[i + 1])
            # If given a hex value, make a color from it
            if re.fullmatch(r"#(\dabcdefABCDEF){6}", part):
                part = part.replace("#", "")
                vals = [int(part[i:i+2], 16) for i in range(0, len(part), 2)] + [255]
                color = colors.BaseColor(*vals)
        # Apply modifier
        color = color + modifier
        # Apply alpha
        color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha=alpha)

        return color


coderTheme = CodeTheme()
