"""Themes for the editor in Coder."""

import wx
import wx.stc
import builtins
import keyword
import copy

DEFAULT_CARET_FG_COL = "BLACK"

# Keywords for each file type and level
LEXER_KWRDS = dict()
LEXER_KWRDS['Python'] = {
        0: keyword.kwlist + [
            'cdef', 'ctypedef', 'extern', 'cimport', 'cpdef', 'include'],
        1: dir(builtins) + ['self']}
LEXER_KWRDS['C/C++'] = {
        0: ['typedef', 'if', 'else', 'return', 'struct', 'for', 'while', 'do',
            'using', 'namespace', 'union', 'break', 'enum', 'new', 'case',
            'switch', 'continue', 'volatile', 'finally', 'throw', 'try',
            'delete', 'typeof', 'sizeof', 'class', 'volatile'],
        1: ['int', 'float', 'double', 'char', 'short', 'byte', 'void', 'const',
            'unsigned', 'signed', 'NULL', 'true', 'false', 'bool', 'size_t',
            'long', 'long long']}
LEXER_KWRDS['Arduino'] = {
    0: list(LEXER_KWRDS['C/C++'][0]),
    1: list(LEXER_KWRDS['C/C++'][1]) + [
        'BIN', 'HEX', 'OCT', 'DEC', 'INPUT', 'OUTPUT', 'HIGH', 'LOW',
        'INPUT_PULLUP', 'LED_BUILTIN', 'string', 'array']
}

glslTypes = []
baseType = ['', 'i', 'b', 'd']
dim = ['2', '3', '4']
name = ['vec', 'mat']
for i in baseType:
    for j in name:
        for k in dim:
            glslTypes.append(i + j + k)

LEXER_KWRDS['GLSL'] = {
    0: list(LEXER_KWRDS['C/C++'][0]) + [
        'invariant', 'precision', 'highp', 'mediump', 'lowp', 'coherent',
         'restrict', 'readonly', 'writeonly', 'uniform', 'varying', 'layout',
         'in', 'out', 'attribute', 'sampler', 'sampler2D'],
    1: list(LEXER_KWRDS['C/C++'][1]) + glslTypes
}

LEXER_KWRDS['JavaScript'] = {
    0: ['var', 'let', 'import', 'function', 'if', 'else', 'return', 'struct',
        'for', 'while', 'do', 'finally', 'throw', 'try', 'switch', 'case',
        'break'],
    1: ['null', 'false', 'true']
}
LEXER_KWRDS['R'] = {1: ['function', 'for', 'repeat', 'while', 'if', 'else',
                        'break', 'local', 'global'],
                    0: ['NA']}


# Mapping between identifiers and style enums for each lexer. This allows a
# theme to be applied to multiple lexers without needing to specify a theme for
# each one.
LEXER_STYLES = {
    wx.stc.STC_LEX_PYTHON: {
        'default': wx.stc.STC_P_DEFAULT,
        'commentline': wx.stc.STC_P_COMMENTLINE,
        'commentblock': wx.stc.STC_P_COMMENTBLOCK,
        'string': wx.stc.STC_P_STRING,
        'character': wx.stc.STC_P_CHARACTER,
        'number': wx.stc.STC_P_NUMBER,
        'operator': wx.stc.STC_P_OPERATOR,
        'pyidentifier': wx.stc.STC_P_IDENTIFIER,
        'word': wx.stc.STC_P_WORD,
        'word2': wx.stc.STC_P_WORD2,
        'defname': wx.stc.STC_P_DEFNAME,
        'classname': wx.stc.STC_P_CLASSNAME,
        'stringeol': wx.stc.STC_P_STRINGEOL,
        'tripledouble': wx.stc.STC_P_TRIPLEDOUBLE,
        'triple': wx.stc.STC_P_TRIPLE
    },
    wx.stc.STC_LEX_CPP: {
        'default': wx.stc.STC_C_DEFAULT,
        'comment': wx.stc.STC_C_COMMENT,
        'commentline': wx.stc.STC_C_COMMENTLINE,
        'commentdoc': wx.stc.STC_C_COMMENTDOC,
        'commentlinedoc': wx.stc.STC_C_COMMENTLINEDOC,
        'commentdockeyword': wx.stc.STC_C_COMMENTDOCKEYWORD,
        'commentdockeyworderror': wx.stc.STC_C_COMMENTDOCKEYWORDERROR,
        'stringraw': wx.stc.STC_C_STRINGRAW,
        'uuid': wx.stc.STC_C_UUID,
        'string': wx.stc.STC_C_STRING,
        'character': wx.stc.STC_C_CHARACTER,
        'number': wx.stc.STC_C_NUMBER,
        'operator': wx.stc.STC_C_OPERATOR,
        'identifier': wx.stc.STC_C_IDENTIFIER,
        'word': wx.stc.STC_C_WORD,
        'word2': wx.stc.STC_C_WORD2,
        'stringeol': wx.stc.STC_C_STRINGEOL,
        'preprocessor': wx.stc.STC_C_PREPROCESSOR,
        'preprocessorcomment': wx.stc.STC_C_PREPROCESSORCOMMENT,
        'verbatim': wx.stc.STC_C_VERBATIM,
        'tripleverbatim': wx.stc.STC_C_TRIPLEVERBATIM,
        'globalclass': wx.stc.STC_C_GLOBALCLASS
    },
    wx.stc.STC_LEX_R: {
        'default': wx.stc.STC_R_DEFAULT,
        'comment': wx.stc.STC_R_COMMENT,
        'string': wx.stc.STC_R_STRING,
        'character': wx.stc.STC_R_STRING2,
        'number': wx.stc.STC_R_NUMBER,
        'operator': wx.stc.STC_R_OPERATOR,
        'identifier': wx.stc.STC_R_IDENTIFIER,
        'word': wx.stc.STC_R_BASEKWORD,
        'word2': wx.stc.STC_R_KWORD,
        'infix': wx.stc.STC_R_INFIX,
        'infixeol': wx.stc.STC_R_INFIXEOL
    },
}

STYLE_SPEC_LANG = {
    'psychopy': {  # wxPython demo style
        'editor': {  # editor default styles, applied before lexer specific
            'caretFgCol': "BLUE",
            'selFg': "#000000",
            'selBg': "#C0C0C0",
            'edgeGuideCol': "#CDCDCD",  # should be the same as the indent guide
            'default': {
                wx.stc.STC_STYLE_DEFAULT: "face:%(code)s,size:%(size)d",
                wx.stc.STC_STYLE_CONTROLCHAR: "face:%(comment)s",
                wx.stc.STC_STYLE_LINENUMBER: "back:#C0C0C0,face:%(code)s,size:%(small)d",
                wx.stc.STC_STYLE_BRACELIGHT: "fore:#FFFFFF,back:#0000FF,bold",
                wx.stc.STC_STYLE_BRACEBAD: "fore:#000000,back:#FF0000,bold",
                wx.stc.STC_STYLE_INDENTGUIDE: "fore:#CDCDCD",
            }
        },
        'lexerStyles': {
            'default': "fore:#000000,face:%(code)s,size:%(size)d",
            'comment': "fore:#007F00,face:%(comment)s,size:%(size)d",
            'commentline': "fore:#007F00,face:%(comment)s,size:%(size)d",
            'commentblock': "fore:#007F00,face:%(comment)s,size:%(size)d",
            'commentlinedoc': "fore:#007F00,face:%(comment)s,size:%(size)d",
            'commentdockeyword': "fore:#007F00,bold,face:%(comment)s,size:%(size)d",
            'commentdockeyworderror': "fore:#007F00,bold,face:%(comment)s,size:%(size)d",
            'string': "fore:#7F007F,face:%(code)s,size:%(size)d",
            'character': "fore:#7F007F,face:%(code)s,size:%(size)d",
            'triple': "fore:#7F0000,size:%(size)d",
            'tripledouble': "fore:#7F0000,size:%(size)d",
            'number': "fore:#007F7F,size:%(size)d",
            'operator': "bold,size:%(size)d",
            'pyidentifier': "fore:#000000,face:%(code)s,size:%(size)d",
            'identifier': "fore:#000000,face:%(code)s,size:%(size)d",
            'word': "fore:#00007F,bold,size:%(size)d",
            'word2': "fore:#00007F,bold,size:%(size)d",
            'defname': "fore:#007F7F,bold,size:%(size)d",
            'classname': "fore:#0000FF,bold,underline,size:%(size)d",
            'stringeol':
                "fore:#000000,face:%(code)s,back:#E0C0E0,eol,size:%(size)d",
            'preprocessor': "fore:#00007F,size:%(size)d",
            'preprocessorcomment': "fore:#00007F,size:%(size)d",
            'verbatim': "fore:#7F0000,size:%(size)d",
            'tripleverbatim': "fore:#7F0000,size:%(size)d",
            'globalclass': "fore:#0000FF,bold,underline,size:%(size)d"
        }
    },
    'wx': {  # wxPython demo style
        'editor': {  # editor default styles, applied before lexer specific
            'caretFgCol': "BLUE",
            'selFg': "#000000",
            'selBg': "#66CCFF",
            'edgeGuideCol': "#CDCDCD",
            'default': {
                wx.stc.STC_STYLE_DEFAULT: "face:%(code)s,size:%(size)d",
                wx.stc.STC_STYLE_LINENUMBER: 'fore:#000000,back:#99A9C2',
                wx.stc.STC_STYLE_BRACELIGHT: 'fore:#00009D,back:#FFFF00',
                wx.stc.STC_STYLE_INDENTGUIDE: "fore:#CDCDCD",
            }
        },
        'lexerStyles': {
            'default': "fore:#000000,face:%(code)s,size:%(size)d",
            'comment': "fore:#008000,back:#F0FFF0',size:%(size)d",
            'commentline': "fore:#008000,back:#F0FFF0,size:%(size)d",
            'commentblock': "fore:#008000,back:#F0FFF0,size:%(size)d",
            'commentlinedoc': "fore:#008000,back:#F0FFF0,size:%(size)d",
            'commentdockeyword':
                "fore:#008000,back:#F0FFF0,bold,face:%(comment)s,size:%(size)d",
            'commentdockeyworderror':
                "fore:#008000,back:#F0FFF0,bold,face:%(comment)s,size:%(size)d",
            'string': "fore:#800080,face:%(code)s,size:%(size)d",
            'character': "fore:#800080,face:%(code)s,size:%(size)d",
            'triple': "fore:#800080,back:#FFFFEA,size:%(size)d",
            'tripledouble': "fore:#800080,back:#FFFFEA,size:%(size)d",
            'number': "fore:#005cc5,size:%(size)d",
            'operator': "fore:#800000,bold,size:%(size)d",
            'pyidentifier': "fore:#000000,face:%(code)s,size:%(size)d",
            'identifier': "fore:#000000,face:%(code)s,size:%(size)d",
            'word': "fore:#000080,bold,size:%(size)d",
            'word2': "fore:#800080,size:%(size)d",
            'defname': "fore:#008080,bold,size:%(size)d",
            'classname': "fore:#0000FF,bold,size:%(size)d",
            'stringeol':
                "fore:#000000,face:%(code)s,back:#E0C0E0,eol,size:%(size)d",
            'preprocessor': "fore:#00007F,size:%(size)d",
            'preprocessorcomment': "fore:#00007F,size:%(size)d",
            'verbatim': "fore:#7F0000,size:%(size)d",
            'tripleverbatim': "fore:#7F0000,size:%(size)d",
            'globalclass': "fore:#0000FF,bold,underline,size:%(size)d"
        }
    },
    'vc6': {  # wxPython demo style
        'editor': {  # editor default styles, applied before lexer specific
            'caretFgCol': "BLACK",
            'selFg': "WHITE",
            'selBg': "BLUE",
            'edgeGuideCol': "#CDCDCD",
            'default': {
                wx.stc.STC_STYLE_DEFAULT: "face:%(code)s,size:%(size)d",
                wx.stc.STC_STYLE_LINENUMBER: 'fore:#000000,back:#CDCDCD',
                wx.stc.STC_STYLE_BRACELIGHT: 'fore:#00009D,back:#FFFF00',
                wx.stc.STC_STYLE_INDENTGUIDE: "fore:#CDCDCD",
            }
        },
        'lexerStyles': {
            'default': "fore:#000000,face:%(code)s,size:%(size)d",
            'comment': "fore:#008000,size:%(size)d",
            'commentline': "fore:#008000,size:%(size)d",
            'commentblock': "fore:#008000,size:%(size)d",
            'commentlinedoc': "fore:#008000,size:%(size)d",
            'commentdockeyword':
                "fore:#008000,face:%(comment)s,size:%(size)d",
            'commentdockeyworderror':
                "fore:#008000,face:%(comment)s,size:%(size)d",
            'string': "fore:#4C4C4C,face:%(code)s,size:%(size)d",
            'character': "fore:#4C4C4C,face:%(code)s,size:%(size)d",
            'triple': "fore:#4C4C4C,size:%(size)d",
            'tripledouble': "fore:#4C4C4C,size:%(size)d",
            'number': "fore:#000000,size:%(size)d",
            'operator': "fore:#000000,size:%(size)d",
            'pyidentifier': "fore:#000000,face:%(code)s,size:%(size)d",
            'identifier': "fore:#000000,face:%(code)s,size:%(size)d",
            'word': "fore:#0000EE,size:%(size)d",
            'word2': "fore:#0000EE,size:%(size)d",
            'defname': "fore:#000000,size:%(size)d",
            'classname': "fore:#000000,size:%(size)d",
            'stringeol':
                "fore:#000000,face:%(code)s,eol,size:%(size)d",
            'preprocessor': "fore:#0000EE,size:%(size)d",
            'preprocessorcomment': "fore:#0000EE,size:%(size)d",
            'globalclass': "fore:#000000,size:%(size)d"
        }
    },
    'github': {  # github style
        'editor': {  # editor default styles, applied before lexer specific
            'caretFgCol': DEFAULT_CARET_FG_COL,
            'selFg': '#000000',
            'selBg': '#add2fc',
            'edgeGuideCol': "#eeeeee",
            'default': {
                wx.stc.STC_STYLE_DEFAULT: "fore:#000000,face:%(code)s,size:%(size)d",
                wx.stc.STC_STYLE_LINENUMBER: 'fore:#B0B0B0',
                wx.stc.STC_STYLE_BRACELIGHT: 'fore:#000000,back:#f1f8ff',
                wx.stc.STC_STYLE_INDENTGUIDE: "fore:#eeeeee",
                wx.stc.STC_STYLE_BRACEBAD: "fore:#000000,back:#FF0000",
            },
        },
        'lexerStyles': {
            'default': "fore:#000000,face:%(code)s,size:%(size)d",
            'comment': "fore:#969896,face:%(comment)s,size:%(size)d",
            'commentline': "fore:#969896,face:%(comment)s,size:%(size)d",
            'commentblock': "fore:#969896,face:%(comment)s,size:%(size)d",
            'commentlinedoc': "fore:#969896,face:%(comment)s,size:%(size)d",
            'commentdockeyword':
                "fore:#969896,bold,face:%(comment)s,size:%(size)d",
            'commentdockeyworderror':
                "fore:#969896,bold,face:%(comment)s,size:%(size)d",
            'stringraw':
                "fore:#969896,bold,face:%(comment)s,size:%(size)d",
            'string': "fore:#032f62,face:%(code)s,size:%(size)d",
            'character': "fore:#032f62,face:%(code)s,size:%(size)d",
            'triple': "fore:#032f62,face:%(code)s,size:%(size)d",
            'tripledouble': "fore:#032f62,face:%(code)s,size:%(size)d",
            'number': "fore:#005cc5,size:%(size)d",
            'operator': "fore:#005cc5,size:%(size)d",
            'pyidentifier': "face:%(code)s,size:%(size)d",  # this looks ugly
            'identifier': "face:%(code)s,size:%(size)d",
            'word': "fore:#d73a49,size:%(size)d",
            'word2': "fore:#800080,size:%(size)d",
            'defname': "fore:#800080,size:%(size)d",
            'classname': "fore:#e36209,size:%(size)d",
            'stringeol':
                "fore:#000000,face:%(code)s,back:#E0C0E0,eol,size:%(size)d",
            'preprocessor': "fore:#d73a49,size:%(size)d",
            'preprocessorcomment': "fore:#d73a49,size:%(size)d",
            'verbatim': "fore:#032f62,size:%(size)d",
            'tripleverbatim': "fore:#032f62,size:%(size)d",
            'globalclass': "fore:#e36209,size:%(size)d"
        }
    }
}


def applyStyleSpec(editor, theme, lexer, faces):
    """Apply a theme based on the specified lexer.

    Parameters
    ----------
    editor : CodeEditor
        Styled Text control to apply the theme to.
    theme : str
        Name of the theme to use.
    lexer : int
        Lexer identifier.
    faces : dict
        Faces for fonts to use.

    """
    try:
        styles = STYLE_SPEC_LANG[theme]
    except KeyError:
        styles = STYLE_SPEC_LANG['psychopy']  # use default

    # apply default style
    editor.StyleSetSpec(
        wx.stc.STC_STYLE_DEFAULT, "face:%(code)s,size:%(size)d" % faces)
    editor.StyleClearAll()

    # set the cursor
    try:
        editor.SetCaretForeground(styles['editor']['caretFgCol'])
    except KeyError:
        editor.SetCaretForeground(DEFAULT_CARET_FG_COL)

    # set selection background according to theme
    try:
        editor.SetSelForeground(True, styles['editor']['selFg'])
    except KeyError:
        editor.SetSelForeground(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

    try:
        editor.SetSelBackground(True, styles['editor']['selBg'])
    except KeyError:
        editor.SetSelBackground(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))

    # apply the default editor styles
    for enum, style in styles['editor']['default'].items():
        if style is None:
            continue  # if None, use default
        editor.StyleSetSpec(enum, style % faces)

    try:
        edgeGuideCol = styles['editor']['edgeGuideCol']
        editor.SetEdgeColour(edgeGuideCol)
    except KeyError:
        pass

    # set all the code styles
    lexerStyles = styles['lexerStyles']

    for key, style in lexerStyles.items():
        try:
            enum = LEXER_STYLES[lexer][key]
            editor.StyleSetSpec(enum, style % faces)
        except KeyError:
            pass

    # set keywords
    ftype = editor.getFileType()
    try:
        kwrds = LEXER_KWRDS[ftype]
    except KeyError:
        return

    for level, vals in kwrds.items():
        editor.SetKeyWords(level, " ".join(vals))
