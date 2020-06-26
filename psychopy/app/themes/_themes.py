import wx
import wx.stc as stc
from wx import py
import keyword
import builtins
from pathlib import Path
from psychopy import prefs

thisFolder = Path(__file__).parent


class ThemeMixin:
    lexers = {
        stc.STC_LEX_PYTHON: "python",
        stc.STC_LEX_CPP: "c++",
        stc.STC_LEX_R: "R"
    }
    # these are populated and modified by PsychoPyApp.theme.setter
    mode = ''
    icons = ''
    codeColors = {}
    appColors = {}

    def _applyAppTheme(self, target=None):
        """Applies colorScheme recursively to the target and its children

        Parameters
        ----------
        colorScheme: the new color spec being applied (dict)
        target: the wx object to which being applied
        depth: depth in the tree of wx objects

        """
        if target is None:
            target = self
        appCS = ThemeMixin.appColors
        base = ThemeMixin.codeColors['base']

        # try and set colors for target
        try:
            target.SetBackgroundColour(ThemeMixin.appColors['frame_bg'])
            target.SetForegroundColour(ThemeMixin.appColors['txt_default'])
        except AttributeError:
            pass

        # search for children (set in a second step)
        if isinstance(target, wx.Sizer):
            sizer = target
            children = sizer.Children
        else:
            children = []
            if isinstance(target, wx.richtext.RichTextCtrl):
                base = ThemeMixin.codeColors['base']
                # todo: Add element-specific styling (it must be possible...)
                # If dealing with a StdOut, set background from base
                target.SetBackgroundColour(
                    self.hex2rgb(base['bg'], base['bg']))
                # Then construct default styles
                _font = wx.Font(
                        int(prefs.coder['outputFontSize']),
                        wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_NORMAL, False,
                        faceName=base['font']
                )
                _style = wx.TextAttr(
                        colText=wx.Colour(
                            self.hex2rgb(base['fg'], base['fg'])),
                        colBack=wx.Colour(
                            self.hex2rgb(base['bg'], base['bg'])),
                        font=_font)
                # Then style all text as base
                i = 0
                for ln in range(target.GetNumberOfLines()):
                    i += target.GetLineLength(
                            ln) + 1  # +1 as \n is not included in character count
                target.SetStyle(0, i, _style)
            elif hasattr(target, 'Children'):
                children.extend(target.Children)
            elif hasattr(target, 'immune'):
                pass
            elif hasattr(target, 'paneManager'):
                for pane in target.paneManager.AllPanes:
                    children.append(pane.window)
            elif hasattr(target, 'Sizer') and target.Sizer:
                children.append(target.Sizer)

        # then apply to all children as well
        for c in children:
            if hasattr(c, '_applyAppTheme'):
            # if the object understands themes then request that
                c._applyAppTheme()
            else:
                # if not then use our own recursive method to search
                if hasattr(c, 'Window') and c.Window is not None:
                    self._applyAppTheme(c.Window)
                elif hasattr(c, 'Sizer') and c.Sizer is not None:
                    self._applyAppTheme(c.Sizer)
                # and then apply
                self._applyAppTheme(c)

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
            if hasattr(self, 'filename'):
                if self.filename.endswith('.js'):
                    # JavaScript
                    keywords = {
                        0: ['var', 'let', 'import', 'function', 'if', 'else', 'return', 'struct', 'for', 'while', 'do',
                            'finally', 'throw', 'try', 'switch', 'case', 'break'],
                        1: ['null', 'false', 'true']
                    }
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
            "caret": None,
            "select": None,
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

    def shiftColour(self, col, offset=15):
        """Shift colour up or down by a set amount"""
        if not isinstance(col, wx.Colour):
            return
        if col.GetLuminance() < 0.5:
            newCol = wx.Colour(
                [c+offset for c in col.Get()]
            )
        else:
            newCol = wx.Colour(
                [c - offset for c in col.Get()]
            )

        return newCol


# Create library of "on brand" colours
cLib = {
    'none': [127, 127, 127, 0],
    'black': [0, 0, 0],
    'grey': [102, 102, 110],
    'white': [242, 242, 242],
    'red': [242, 84, 91],
    'green': [108, 204, 116],
    'blue': [2, 169, 234],
    'yellow': [241, 211, 2],
    'orange': [236, 151, 3],
    'purple': [195, 190, 247],
    'darker': {},
    'lighter': {},
    'very': {'lighter': {},
             'darker': {}}
}
# Create light and dark variants of each colour by +-15 to each value
for c in cLib:
     if not c in ['darker', 'lighter', 'none', 'very']:
         cLib['darker'][c] = [max(0, n-15) for n in cLib[c]]
         cLib['lighter'][c] = [min(255, n+15) for n in cLib[c]]
# Create very light and very dark variants of each colour by a further +-30 to each value
for c in cLib['lighter']:
    cLib['very']['lighter'][c] = [min(255, n+30) for n in cLib['lighter'][c]]
for c in cLib['darker']:
    cLib['very']['darker'][c] = [max(0, n-30) for n in cLib['darker'][c]]

# Create light and dark colour schemes
cs_light = {
    'txt_default': cLib['black'],
    # Toolbar
    'toolbar_bg': cLib['darker']['white'],
    'tool_hover': cLib['very']['darker']['white'],
    # Frame
    'frame_bg': cLib['white'],
    'grippers': cLib['darker']['white'],
    'note_bg': cLib['white'],
    'tab_face': cLib['white'],
    'tab_active': cLib['lighter']['white'],
    'tab_txt': cLib['lighter']['black'],
    'docker_face': cLib['very']['darker']['white'],
    'docker_txt': cLib['black'],
    # Plate Buttons
    'platebtn_bg': cLib['white'],
    'platebtn_txt': cLib['black'],
    'platebtn_hover': cLib['red'],
    'platebtn_hovertxt': cLib['white'],
    ## Builder
    # Routine canvas
    'rtcanvas_bg': cLib['lighter']['white'],
    'time_grid': cLib['very']['darker']['white'],
    'time_txt': cLib['grey'],
    'rtcomp_txt': cLib['black'],
    'rtcomp_bar': cLib['blue'],
    'rtcomp_force': cLib['orange'],
    'rtcomp_distxt': cLib['very']['darker']['white'],
    'rtcomp_disbar': cLib['very']['darker']['white'],
    'isi_bar': cLib['red'] + [75],
    'isi_txt': cLib['lighter']['white'],
    'isi_disbar': cLib['grey'] + [75],
    'isi_distxt': cLib['lighter']['white'],
    # Component panel
    'cpanel_bg': cLib['white'],
    'cbutton_hover': cLib['darker']['white'],
    # Flow panel
    'fpanel_bg': cLib['white'],
    'fpanel_ln': cLib['very']['lighter']['grey'],
    'frt_slip': cLib['blue'],
    'frt_nonslip': cLib['green'],
    'frt_txt': cLib['lighter']['white'],
    'loop_face': cLib['grey'],
    'loop_txt': cLib['lighter']['white'],
    'fbtns_face': cLib['darker']['white'],
    'fbtns_txt': cLib['black'],
    ## Coder
    # Source Assistant
    'src_bg': cLib['white'],
    # Source Assistant: Structure
    'struct_bg': cLib['white'],
    'struct_txt': cLib['black'],
    'struct_hover': cLib['red'],
    'struct_hovertxt': cLib['white'],
    # Source Assistant: File Browser
    'brws_bg': cLib['white'],
    'brws_txt': cLib['black'],
    'brws_hover': cLib['red'],
    'brws_hovertxt': cLib['white']
    # Shell
    }
cs_dark = {
    'txt_default': cLib['white'],
    # Toolbar
    'toolbar_bg': cLib['darker']['grey'],
    'tool_hover': ['grey'],
    # Frame
    'frame_bg': cLib['darker']['grey'],
    'grippers': cLib['darker']['grey'],
    'note_bg': cLib['grey'],
    'tab_face': cLib['grey'],
    'tab_active': cLib['lighter']['grey'],
    'tab_txt': cLib['lighter']['white'],
    'docker_face': cLib['very']['darker']['grey'],
    'docker_txt': cLib['white'],
    # Plate Buttons
    'platebtn_bg': cLib['grey'],
    'platebtn_txt': cLib['white'],
    'platebtn_hover': cLib['red'],
    'platebtn_hovertxt': cLib['white'],
    ## Builder
    # Routine canvas
    'rtcanvas_bg': cLib['lighter']['grey'],
    'time_grid': cLib['very']['lighter']['grey'],
    'time_txt': cLib['darker']['white'],
    'rtcomp_txt': cLib['white'],
    'rtcomp_bar': cLib['blue'],
    'rtcomp_force': cLib['orange'],
    'rtcomp_distxt': cLib['grey'],
    'rtcomp_disbar': cLib['grey'],
    'isi_bar': cLib['red'] + [75],
    'isi_txt': cLib['lighter']['white'],
    'isi_disbar': cLib['grey'] + [75],
    'isi_distxt': cLib['lighter']['white'],
    # Component panel
    'cpanel_bg': cLib['grey'],
    'cbutton_hover': cLib['lighter']['grey'],
    # Flow panel
    'fpanel_bg': cLib['darker']['grey'],
    'fpanel_ln': cLib['lighter']['grey'],
    'frt_slip': cLib['blue'],
    'frt_nonslip': cLib['green'],
    'frt_txt': cLib['lighter']['white'],
    'loop_face': cLib['darker']['white'],
    'loop_txt': cLib['black'],
    'fbtns_face': cLib['grey'],
    'fbtns_txt': cLib['white'],
    ## Coder
    # Source Assistant
    'src_bg': cLib['grey'],
    # Source Assistant: Structure
    'struct_txt': cLib['white'],
    'struct_hover': cLib['red'],
    'struct_hovertxt': cLib['white'],
    # Source Assistant: File Browser
    'brws_txt': cLib['white'],
    'brws_hover': cLib['red'],
    'brws_hovertxt': cLib['white']
    # Shell
    }
