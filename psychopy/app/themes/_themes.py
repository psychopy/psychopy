import wx
import wx.lib.agw.aui as aui
import wx.stc as stc
from wx import py
import keyword
import builtins
from pathlib import Path
from psychopy import prefs
import psychopy
import json

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
    appColors = {
        "text": [],
        "frame_bg": [],
        "docker_bg": [],
        "docker_fg": [],
        "panel_bg": [],
        "tab_bg": [],
        "bmpbutton_bg_hover": [],
        "bmpbutton_fg_hover": [],
        "txtbutton_bg_hover": [],
        "txtbutton_fg_hover": [],
        "rt_timegrid": [],
        "rt_comp": [],
        "rt_comp_force": [],
        "rt_comp_disabled": [],
        "rt_static": [],
        "rt_static_disabled": [],
        "fl_routine_fg": [],
        "fl_routine_bg_slip": [],
        "fl_routine_bg_nonslip": [],
        "fl_flowline_bg": [],
        "fl_flowline_fg": []
    }

    def _applyAppTheme(self, target=None):
        """Applies colorScheme recursively to the target and its children

        Parameters
        ----------
        colorScheme: the new color spec being applied (dict)
        target: the wx object to which being applied
        depth: depth in the tree of wx objects

        """

        # Define subfunctions to handle different object types
        def applyToToolbar(target):
            target.SetBackgroundColour(ThemeMixin.appColors['frame_bg'])

        def applyToFrame(target):
            target.SetBackgroundColour(ThemeMixin.appColors['frame_bg'])
            target.SetForegroundColour(ThemeMixin.appColors['text'])
            if hasattr(target, 'GetAuiManager'):
                target.GetAuiManager().SetArtProvider(PsychopyDockArt())
                target.GetAuiManager().Update()

        def applyToPanel(target):
            target.SetBackgroundColour(ThemeMixin.appColors['panel_bg'])
            target.SetForegroundColour(ThemeMixin.appColors['text'])

        def applyToNotebook(target):
            target.SetArtProvider(PsychopyTabArt())
            target.GetAuiManager().SetArtProvider(PsychopyDockArt())
            for index in range(target.GetPageCount()):
                page = target.GetPage(index)
                page.SetBackgroundColour(ThemeMixin.appColors['tab_bg'])
                page._applyAppTheme()

        def applyToCodeEditor(target):
            spec = ThemeMixin.codeColors
            base = spec['base']

            # Check that key is in tag list
            invalid = []
            for key in spec:
                if key not in self.tags:
                    invalid += [key]
            for key in invalid:
                del spec[key]

            # Check for language specific spec
            if target.GetLexer() in self.lexers:
                lexer = self.lexers[target.GetLexer()]
            else:
                lexer = 'invlex'
            if lexer in spec:
                # If there is lang specific spec, delete subkey...
                lang = spec[lexer]
                del spec[lexer]
                # ...and append spec to root, overriding any generic spec
                spec.update({key: lang[key] for key in lang})
            else:
                lang = {}

            # Override base font with user spec if present
            key = 'outputFont' if isinstance(target, wx.py.shell.Shell) else 'codeFont'
            if prefs.coder[key] != "From Theme...":
                base['font'] = prefs.coder[key]

            # Set style for undefined lexers
            for key in [getattr(wx._stc, item) for item in dir(wx._stc) if item.startswith("STC_LEX")]:
                target.StyleSetBackground(key, base['bg'])
                target.StyleSetForeground(key, base['fg'])
                target.StyleSetSpec(key, "face:%(font)s,size:%(size)d" % base)
            # Set style from universal data
            for key in spec:
                if target.tags[key] is not None:
                    target.StyleSetBackground(target.tags[key], spec[key]['bg'])
                    target.StyleSetForeground(target.tags[key], spec[key]['fg'])
                    target.StyleSetSpec(target.tags[key], "face:%(font)s,size:%(size)d" % spec[key])
            # Apply keywords
            for level, val in target.lexkw.items():
                target.SetKeyWords(level, " ".join(val))

            # Set margin
            target.SetFoldMarginColour(True, spec['margin']['bg'])
            target.SetFoldMarginHiColour(True, spec['margin']['bg'])
            # Set caret colour
            target.SetCaretForeground(spec['caret']['fg'])
            target.SetCaretLineBackground(spec['caret']['bg'])
            target.SetCaretWidth(1 + ('bold' in spec['caret']['font']))
            # Set selection colour
            target.SetSelForeground(True, spec['select']['fg'])
            target.SetSelBackground(True, spec['select']['bg'])
            # Set wrap point
            target.edgeGuideColumn = target.prefs['edgeGuideColumn']
            target.edgeGuideVisible = target.edgeGuideColumn > 0
            # Set line spacing
            spacing = min(int(target.prefs['lineSpacing'] / 2), 64)  # Max out at 64
            target.SetExtraAscent(spacing)
            target.SetExtraDescent(spacing)

        def applyToRichText(target):
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

        # Define dict linking object types to subfunctions
        handlers = {
            wx.Frame: applyToFrame,
            wx.Panel: applyToPanel,
            aui.AuiNotebook: applyToNotebook,
            psychopy.app.coder.coder.BaseCodeEditor: applyToCodeEditor,
            wx.richtext.RichTextCtrl: applyToRichText,
            wx.py.shell.Shell: applyToCodeEditor,
            wx.ToolBar: applyToToolbar
        }

        # If no target supplied, default to using self
        if target is None:
            target = self
        appCS = ThemeMixin.appColors
        base = ThemeMixin.codeColors['base']
        # Abort if target is immune
        if hasattr(target, 'immune'):
            return

        # Style target
        for thisType in handlers:
            if isinstance(target, thisType):
                handlers[thisType](target)
            else:
                # try and set colors for target
                try:
                    target.SetBackgroundColour(ThemeMixin.appColors['panel_bg'])
                    target.SetForegroundColour(ThemeMixin.appColors['text'])
                except AttributeError:
                    pass

        # search for children (set in a second step)
        if isinstance(target, wx.Sizer):
            sizer = target
            children = sizer.Children
        else:
            children = []
            if isinstance(target, wx.richtext.RichTextCtrl):
                applyToRichText(target)
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

    def setCodeColors(self, theme):
        try:
            with open("{}//{}.json".format(self.prefs.paths['themes'], theme), "rb") as fp:
                spec = json.load(fp)
            # Check that minimum spec is defined
            if 'base' in spec:
                base = spec['base']
                if not (
                        all(key in base for key in ['bg', 'fg', 'font'])
                ):
                    raise Exception
            else:
                raise Exception
        except:
            with open("{}//{}.json".format(self.prefs.paths['themes'], "PsychopyLight"), "rb") as fp:
                spec = json.load(fp)
            base = spec['base']

        # Make sure there's some spec for margins
        if 'margin' not in spec:
            spec['margin'] = base
        # Make sure there's some spec for caret
        if 'caret' not in spec:
            spec['caret'] = base
        # Make sure there's some spec for selection
        if 'select' not in spec:
            spec['select'] = base
            spec['select']['bg'] = self.shiftColour(base['bg'], 30)

        # Pythonise the universal data (hex -> rgb, tag -> wx int)
        invalid = []
        for key in spec:
            # Check that full spec is defined, discard if not
            if all(subkey in spec[key] for subkey in ['bg', 'fg', 'font']):
                spec[key]['bg'] = self.hex2rgb(spec[key]['bg'], base['bg'])
                spec[key]['fg'] = self.hex2rgb(spec[key]['fg'], base['fg'])
                if not spec[key]['font']:
                    spec[key]['font'] = base['font']
                spec[key]['size'] = int(self.prefs.coder['codeFontSize'])
            else:
                invalid += [key]
        for key in invalid:
            del spec[key]

        # we have a valid theme so continue
        for key in spec:
            self.codeColors[key] = spec[key]  # class attribute for all mixin subclasses
        self.mode = spec['app'] if 'app' in spec else 'light'
        self.icons = spec['icons'] if 'icons' in spec else 'modern'

    def setAppColors(self, theme):
        try:
            with open("{}//app//{}.json".format(prefs.paths['themes'], theme), "rb") as fp:
                spec = json.load(fp)
        except:
            with open("{}//app//{}.json".format(prefs.paths['themes'], "light"), "rb") as fp:
                spec = json.load(fp)

        hexchars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                    'a', 'b', 'c', 'd', 'e', 'f']
        formats = {
            "hex|named": [str],
            "subnamed1": [str, str],
            "subnamed2": [str, str, str],
            "hex|named_opacity1": [str, int],
            "subnamed1_opacity1": [str, str, int],
            "subnamed2_opacity1": [str, str, str, int],
            "hex|named_opacity2": [str, float],
            "subnamed1_opacity2": [str, str, float],
            "subnamed2_opacity2": [str, str, str, float]
        }
        # Cycle through all values
        for key in spec:
            # if key not in output:
            #    continue
            val = spec[key]
            color = ['invalid']
            # Make sure every value is a list
            if not isinstance(val, list):
                val = [val]

            # Figure out what format current spec is in
            types = [type(v) for v in val]
            format = "invalid"
            for f in formats:
                if formats[f] == types:
                    format = f
            # Pop out opacity so that it can be assumed not present
            if "_opacity" in format:
                opacity = round(val.pop(-1))
                format = format.replace("_opacity", "")
            else:
                opacity = 255
            # Tell the difference between hex and single named values
            if "hex|named" in format:
                if val[0] in cLib:
                    # Extract named colour
                    color = cLib[val[0]]
                    format = format.replace("hex|", "")
                elif len(val[0]) == 7:
                    hex = val[0]
                    if hex[0] == "#" and all([h in hexchars for h in hex[1:].lower()]):
                        # Convert hex colour
                        format = format.replace("|named", "")
                        wxcolor = ThemeMixin.hex2rgb(None, hex)
                        color = list(wxcolor[:3])
                    else:
                        format = "invalid"
                else:
                    format = "invalid"

            if "subnamed" in format:
                if len(val) == 2 and all([v in cLib for v in val]):
                    color = cLib[val[0]][val[1]]
                elif len(val) == 3 and all([v in cLib for v in val]):
                    color = cLib[val[0]][val[1]][val[2]]
                else:
                    format = "invalid"

            if format == "invalid" \
                    or "color" not in locals() \
                    or "opacity" not in locals() \
                    or "invalid" in color:
                raise Exception("Invalid app colour spec")
            else:
                self.appColors[key] = wx.Colour(color + [opacity])

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


class PsychopyTabArt(aui.AuiDefaultTabArt, ThemeMixin):
    def __init__(self):
        aui.AuiDefaultTabArt.__init__(self)

        self.SetDefaultColours()
        self.SetAGWFlags(aui.AUI_NB_NO_TAB_FOCUS)

    def SetDefaultColours(self):
        """
        Sets the default colours, which are calculated from the given base colour.

        :param `base_colour`: an instance of :class:`wx.Colour`. If defaulted to ``None``, a colour
         is generated accordingly to the platform and theme.
        """
        cs = ThemeMixin.appColors
        self.SetBaseColour( wx.Colour(cs['tab_bg']) )
        self._background_top_colour = wx.Colour(cs['panel_bg'])
        self._background_bottom_colour = wx.Colour(cs['panel_bg'])

        self._tab_text_colour = lambda page: cs['text']
        self._tab_top_colour = wx.Colour(cs['tab_bg'])
        self._tab_bottom_colour = wx.Colour(cs['tab_bg'])
        self._tab_gradient_highlight_colour = wx.Colour(cs['tab_bg'])
        self._border_colour = wx.Colour(cs['tab_bg'])
        self._border_pen = wx.Pen(self._border_colour)

        self._tab_disabled_text_colour = cs['text']
        self._tab_inactive_top_colour = wx.Colour(cs['panel_bg'])
        self._tab_inactive_bottom_colour = wx.Colour(cs['panel_bg'])

    def DrawTab(self, dc, wnd, page, in_rect, close_button_state, paint_control=False):
        """
        Extends AuiDefaultTabArt.DrawTab to add a transparent border to inactive tabs
        """
        if page.active:
            self._border_pen = wx.Pen(self._border_colour)
        else:
            self._border_pen = wx.TRANSPARENT_PEN

        out_tab_rect, out_button_rect, x_extent = aui.AuiDefaultTabArt.DrawTab(self, dc, wnd, page, in_rect, close_button_state, paint_control)

        return out_tab_rect, out_button_rect, x_extent

class PsychopyDockArt(aui.AuiDefaultDockArt):
    def __init__(self):
        aui.AuiDefaultDockArt.__init__(self)
        cs = ThemeMixin.appColors
        # Gradient
        self._gradient_type = aui.AUI_GRADIENT_NONE
        # Background
        self._background_colour = wx.Colour(cs['frame_bg'])
        self._background_gradient_colour = wx.Colour(cs['frame_bg'])
        self._background_brush = wx.Brush(self._background_colour)
        # Border
        self._border_size = 0
        self._border_pen = wx.Pen(cs['frame_bg'])
        # Sash
        self._draw_sash = True
        self._sash_size = 5
        self._sash_brush = wx.Brush(cs['frame_bg'])
        # Gripper
        self._gripper_brush = wx.Brush(cs['frame_bg'])
        self._gripper_pen1 = wx.Pen(cs['frame_bg'])
        self._gripper_pen2 = wx.Pen(cs['frame_bg'])
        self._gripper_pen3 = wx.Pen(cs['frame_bg'])
        self._gripper_size = 0
        # Hint
        self._hint_background_colour = wx.Colour(cs['frame_bg'])
        # Caption bar
        self._inactive_caption_colour = wx.Colour(cs['docker_bg'])
        self._inactive_caption_gradient_colour = wx.Colour(cs['docker_bg'])
        self._inactive_caption_text_colour = wx.Colour(cs['docker_fg'])
        self._active_caption_colour = wx.Colour(cs['docker_bg'])
        self._active_caption_gradient_colour = wx.Colour(cs['docker_bg'])
        self._active_caption_text_colour = wx.Colour(cs['docker_fg'])
        # self._caption_font
        self._caption_size = 25
        self._button_size = 20
