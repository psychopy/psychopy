"""Themes for the editor in Coder."""

import wx
import wx.stc
import builtins
import keyword
import copy
import json
import os

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

stylenames = os.listdir("coder//themes")
STYLE_SPEC_LANG = {}
for style in stylenames:
    with open("coder//themes//"+style, "rb") as fp:
        STYLE_SPEC_LANG[style.replace('.json', '')] = json.load(fp)

    STYLE_SPEC_LANG[style.replace('.json', '')]['editor']['default'] = {
            wx.stc.STC_STYLE_DEFAULT: "face:%(code)s,size:%(size)d",
            wx.stc.STC_STYLE_CONTROLCHAR: "face:%(comment)s",
            wx.stc.STC_STYLE_LINENUMBER: "back:#C0C0C0,face:%(code)s,size:%(small)d",
            wx.stc.STC_STYLE_BRACELIGHT: "fore:#FFFFFF,back:#0000FF,bold",
            wx.stc.STC_STYLE_BRACEBAD: "fore:#000000,back:#FF0000,bold",
            wx.stc.STC_STYLE_INDENTGUIDE: "fore:#CDCDCD",
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
