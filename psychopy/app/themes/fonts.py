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


lexerNames = {
    "python": stc.STC_LEX_PYTHON,
    "c++": stc.STC_LEX_CPP,
    "r": stc.STC_LEX_R,
    "json": stc.STC_LEX_JSON,
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
                    'break', 'await'],
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
        # Create base attributes
        self._base = {}
        self._caret = {}
        self._margin = {}
        self._select = {}
        # Load theme
        self.load(theme.code)

    def __getitem__(self, item):
        # If theme isn't cached yet, load & cache it
        self.load(theme.code)
        # Return value from theme cache
        return dict.__getitem__(self, theme.code)[item]

    def __getattr__(self, attr):
        # If theme isn't cached yet, load & cache it
        self.load(theme.code)
        # Return value
        return getattr(self, attr)

    def items(self):
        # If theme isn't cached yet, load & cache it
        self.load(theme.code)
        return dict.__getitem__(self, theme.code).items()

    def values(self):
        # If theme isn't cached yet, load & cache it
        self.load(theme.code)
        return dict.__getitem__(self, theme.code).values()

    def keys(self):
        # If theme isn't cached yet, load & cache it
        self.load(theme.code)
        return dict.__getitem__(self, theme.code).keys()

    def __iter__(self):
        # If theme isn't cached yet, load & cache it
        self.load(theme.code)
        return dict.__getitem__(self, theme.code).__iter__()

    @property
    def base(self):
        if theme.code not in self._base:
            self.load(theme.code)
        return self._base[theme.code]

    @base.setter
    def base(self, value):
        self._base[theme.code] = value

    @property
    def caret(self):
        if theme.code not in self._caret:
            self.load(theme.code)
        return self._caret[theme.code]

    @caret.setter
    def caret(self, value):
        self._caret[theme.code] = value

    @property
    def margin(self):
        if theme.code not in self._margin:
            self.load(theme.code)
        return self._margin[theme.code]

    @margin.setter
    def margin(self, value):
        self._margin[theme.code] = value

    @property
    def select(self):
        if theme.code not in self._select:
            self.load(theme.code)
        return self._select[theme.code]

    @select.setter
    def select(self, value):
        self._select[theme.code] = value

    def load(self, name):
        # If already loaded, just set base attributes, don't load again
        if theme.code in self:
            CodeFont.pointSize = self.base.pointSize
            CodeFont.foreColor = self.base.foreColor
            CodeFont.backColor = self.base.backColor
            CodeFont.faceNames = self.base.faceNames
            CodeFont.bold = self.base.bold
            CodeFont.italic = self.base.italic
            return

        cache = {}
        # Load theme from file
        filename = Path(prefs.paths['themes']) / (theme.code + ".json")
        spec = loadSpec(filename)
        # Set base attributes
        self.base = CodeFont(*extractAll(spec['code']['base']))
        CodeFont.pointSize = self.base.pointSize
        CodeFont.foreColor = self.base.foreColor
        CodeFont.backColor = self.base.backColor
        CodeFont.faceNames = self.base.faceNames
        CodeFont.bold = self.base.bold
        CodeFont.italic = self.base.italic
        # Store other non-tag spec
        for attr in ('caret', 'margin', 'select'):
            if attr in spec['code']:
                val = CodeFont(*extractAll(spec['code'][attr]))
            else:
                val = CodeFont()
            setattr(self, attr, val)

        # Find style associated with each tag
        for key, tag in tags.items():
            # Skip None
            if tag is None:
                continue
            elif key.lower() in lexerNames:
                # If tag is a lexer, store in a sub-dict
                lex = lexerNames[key]
                cache[lex] = {}
                # If lexer isn't described in spec, skip
                if key not in spec['code']:
                    continue
                for subkey, subtag in tag.items():
                    # For each subtag, extract font
                    if subkey in spec['code'][key]:
                        # If font is directly specified, use it
                        cache[lex][subtag] = CodeFont(*extractAll(spec['code'][key][subkey]))
                    elif subkey in spec['code']:
                        # If font is not directly specified, use universal equivalent
                        cache[lex][subtag] = CodeFont(*extractAll(spec['code'][subkey]))
            elif key in spec['code']:
                # If tag is a tag, extract font
                cache[tag] = CodeFont(*extractAll(spec['code'][key]))
            else:
                cache[tag] = CodeFont()

        # Store cache
        dict.__setitem__(self, name, cache)


class CodeFont:
    # Defaults are defined at class level, so they can change with theme
    pointSize = 12
    foreColor = "#000000"
    backColor = "#FFFFFF"
    faceNames = ["JetBrains Mono", "Monaco", "Consolas"]
    bold = False
    italic = False

    def __init__(self, pointSize=None, foreColor=None, backColor=None, faceNames=None, bold=None, italic=None):
        # Set point size
        if pointSize in (None, ""):
            pointSize = CodeFont.pointSize
        self.pointSize = pointSize
        # Set foreground color
        if foreColor in (None, ""):
            foreColor = CodeFont.foreColor
        self.foreColor = foreColor
        # Set background color
        if backColor in (None, ""):
            backColor = CodeFont.backColor
        self.backColor = backColor
        # Set font face
        if faceNames in (None, ""):
            faceNames = CodeFont.faceNames
        self.faceNames = faceNames
        # Set bold
        if bold in (None, ""):
            bold = CodeFont.bold
        self.bold = bold
        # Set italic
        if italic in (None, ""):
            italic = CodeFont.italic
        self.italic = italic

        # Make wx.FontInfo object
        info = wx.FontInfo(self.pointSize).Bold(self.bold).Italic(self.italic)
        # Make wx.Font object
        self.obj = wx.Font(info)

        # Choose face from list
        # Try faces sequentially until one works
        success = False
        for name in self.faceNames:
            success = self.obj.SetFaceName(name)
            if success:
                break
        # If nothing worked, use the default monospace
        if not success:
            self.obj = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)

    def __repr__(self):
        return (
            f"<{type(self).__name__}: "
            f"pointSize={self.pointSize}, "
            f"foreColor={self.foreColor}, backColor={self.backColor}, "
            f"faceName={self.obj.GetFaceName()}, bold={self.bold}, italic={self.italic}"
            f">"
        )


def extractAll(val):
    pointSize = int(prefs.coder['codeFontSize'])
    foreColor = extractColor(val['fg'])
    backColor = extractColor(val['bg'])
    faceNames = extractFaceNames(val['font'])
    bold, italic = extractFontStyle(val['font'])

    return pointSize, foreColor, backColor, faceNames, bold, italic


def extractFaceNames(val):
    # Make sure val is a list
    if isinstance(val, str):
        # Get rid of any perentheses
        val = re.sub("[\(\)\[\]]", "", val)
        # Split by comma
        val = val.split(",")
    # Clear style markers
    val = [p for p in val if val not in ("bold", "italic")]

    # Add fallback font
    val += CodeFont.faceNames

    return val


def extractFontStyle(val):
    bold = "bold" in val
    italic = "italic" in val

    return bold, italic


def extractColor(val):
    val = str(val)
    # If val is blank, return None so further down the line we know to sub in defaults
    if val in ("None", ""):
        return None
    # Split value according to operators, commas and spaces
    val = val.replace("+", " + ").replace("-", " - ").replace("\\", " \\ ")
    parts = re.split(r"[\\\s,\(\)\[\]]", val)
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
        if re.fullmatch(r"#[\dabcdefABCDEF]{6}", part):
            part = part.replace("#", "")
            vals = [int(part[i:i+2], 16) for i in range(0, len(part), 2)] + [255]
            color = colors.BaseColor(*vals)
    # Apply modifier
    color = color + modifier
    # Apply alpha
    color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha=alpha)

    return color


coderTheme = CodeTheme()

