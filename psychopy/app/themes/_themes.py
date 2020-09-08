import os
import subprocess
import sys

import wx
import wx.lib.agw.aui as aui
import wx.stc as stc
from psychopy.localization import _translate
from wx import py
import keyword
import builtins
from pathlib import Path
from psychopy import prefs
from psychopy import logging
import psychopy
from ...experiment import components
import json

if sys.platform=='win32':
    from matplotlib import font_manager
    fm = font_manager.FontManager()

thisFolder = Path(__file__).parent
iconsPath = Path(prefs.paths['resources'])

try:
    FileNotFoundError
except NameError:
    # Py2 has no FileNotFoundError
    FileNotFoundError = IOError

allCompons = components.getAllComponents()  # ensures that the icons get checked

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


class ThemeMixin:
    lexers = {
        stc.STC_LEX_PYTHON: "python",
        stc.STC_LEX_CPP: "c++",
        stc.STC_LEX_R: "R"
    }
    # these are populated and modified by PsychoPyApp.theme.setter
    spec = None
    codetheme = 'PsychopyLight'
    mode = 'light'
    icons = 'light'
    codeColors = {}
    appColors = {}
    appIcons = {'components': {},
                'resources': {}}

    def loadThemeSpec(self, themeName):
        """Load a spec file from disk"""
        # a theme spec contains the spec for the *code* theme as well as a mode
        # that determines which colorscheme to load for the app (separate)
        themesPath = Path(prefs.paths['themes'])

        # first load the *theme* which contains the mode name for the app
        try:
            with open(str(themesPath / (themeName+".json")), "rb") as fp:
                ThemeMixin.spec = themeSpec = json.load(fp)
        except FileNotFoundError:
            with open(str(themesPath / "PsychopyLight.json"), "rb") as fp:
                ThemeMixin.spec = themeSpec = json.load(fp)
        appColorMode = themeSpec['app']
        # Get app spec
        try:
            with open(str(themesPath / "app/{}.json".format(appColorMode)), "rb") as fp:
                ThemeMixin.spec = appColors = json.load(fp)
        except FileNotFoundError:
            with open(str(themesPath / "app/light.json"), "rb") as fp:
                ThemeMixin.spec = appColors = json.load(fp)

        # Set app theme
        ThemeMixin.mode = appColorMode
        self._setAppColors(appColors)
        # Set app icons
        if 'icons' in themeSpec:
            ThemeMixin.icons = themeSpec['icons']
        else:
            ThemeMixin.icons = themeSpec['app']
        # Set coder theme
        codertheme = themeSpec
        ThemeMixin.codetheme = themeName
        self._setCodeColors(codertheme)

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
            # Clear tools
            target.ClearTools()
            # Redraw tools
            target.makeTools()

        def applyToStatusBar(target):
            target.SetBackgroundColour(cLib['white'])

        def applyToFrame(target):
            target.SetBackgroundColour(ThemeMixin.appColors['frame_bg'])
            target.SetForegroundColour(ThemeMixin.appColors['text'])
            if hasattr(target, 'GetAuiManager'):
                target.GetAuiManager().SetArtProvider(PsychopyDockArt())
                target.GetAuiManager().Update()
            for menu in target.GetMenuBar().GetMenus():
                for submenu in menu[0].MenuItems:
                    if isinstance(submenu.SubMenu, ThemeSwitcher):
                        submenu.SubMenu._applyAppTheme()


        def applyToPanel(target):
            target.SetBackgroundColour(ThemeMixin.appColors['panel_bg'])
            target.SetForegroundColour(ThemeMixin.appColors['text'])

        def applyToNotebook(target):
            # Dict of icons to apply to specific tabs
            tabIcons = {
                "Structure": "coderclass16.png",
                "FileBrowser": "folder-open16.png",
                "PythonShell": "coderpython16.png"
            }
            target.SetArtProvider(PsychopyTabArt())
            target.GetAuiManager().SetArtProvider(PsychopyDockArt())
            for index in range(target.GetPageCount()):
                page = target.GetPage(index)
                page.SetBackgroundColour(ThemeMixin.appColors['panel_bg'])
                if page.GetName() in tabIcons:
                    bmp = IconCache.getBitmap(IconCache(), tabIcons[page.GetName()])
                    target.SetPageBitmap(index, bmp)
                page._applyAppTheme()

        def applyToCodeEditor(target):
            spec = ThemeMixin.codeColors.copy()
            base = spec['base']
            # Set margin size according to text size
            if not isinstance(target, wx.py.shell.Shell):
                target.SetMarginWidth(0, 4 * prefs.coder['codeFontSize'])
            # Override base font with user spec if present
            prefkey = 'outputFont' if isinstance(target, wx.py.shell.Shell) else 'codeFont'
            if prefs.coder[prefkey].lower() != "From Theme...".lower():
                for key in spec:
                    if 'font' in spec[key]:
                        spec[key]['font'] = prefs.coder[prefkey] if spec[key]['font'] == base['font'] \
                            else base['font']
                base['font'] = prefs.coder[prefkey]

            # Check that key is in tag list
            invalid = []
            for key in spec:
                if key not in self.tags:
                    invalid += [key]
            for key in invalid:
                del spec[key]

            # Check for language specific spec
            if target.GetLexer() in target.lexers:
                lexer = target.lexers[target.GetLexer()]
            else:
                lexer = 'invlex'
            if lexer in spec:
                # If there is lang specific spec, delete subkey...
                lang = spec['lexer'] # ...and append spec to root, overriding any generic spec
                spec.update({key: lang[key] for key in lang})
            else:
                lang = {}

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
            bold = wx.FONTWEIGHT_BOLD if "bold" in base['font'] else wx.FONTWEIGHT_NORMAL
            italic = wx.FONTSTYLE_ITALIC if "italic" in base['font'] else wx.FONTSTYLE_NORMAL
            # Override base font with user spec if present
            if prefs.coder['outputFont'].lower() == "From Theme...".lower():
                fontName = base['font'].replace("bold", "").replace("italic", "").replace(",", "")
            else:
                fontName = prefs.coder['outputFont']

            _font = wx.Font(
                int(prefs.coder['outputFontSize']),
                wx.FONTFAMILY_TELETYPE, italic,
                bold, False,
                faceName=fontName
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

        def applyToTextCtrl(target):
            base = ThemeMixin.codeColors['base']
            target.SetForegroundColour(base['fg'])
            target.SetBackgroundColour(base['bg'])

        # Define dict linking object types to subfunctions
        handlers = {
            wx.Frame: applyToFrame,
            wx.Panel: applyToPanel,
            aui.AuiNotebook: applyToNotebook,
            psychopy.app.coder.coder.BaseCodeEditor: applyToCodeEditor,
            wx.richtext.RichTextCtrl: applyToRichText,
            wx.py.shell.Shell: applyToCodeEditor,
            wx.ToolBar: applyToToolbar,
            wx.StatusBar: applyToStatusBar,
            wx.TextCtrl: applyToTextCtrl
        }

        # If no target supplied, default to using self
        if target is None:
            target = self

        if not hasattr(self, '_recursionDepth'):
            self._recursionDepth = 0
        else:
            self._recursionDepth += 1

        appCS = ThemeMixin.appColors
        base = ThemeMixin.codeColors['base']
        # Abort if target is immune
        if hasattr(target, 'immune'):
            return

        # Style target
        isHandled = False
        for thisType in handlers:
            if isinstance(target, thisType):
                handlers[thisType](target)
                isHandled = True

        if not isHandled:
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
            if hasattr(target, 'Children'):
                children.extend(target.Children)
            elif hasattr(target, 'immune'):
                pass
            elif hasattr(target, 'paneManager'):
                for pane in target.paneManager.AllPanes:
                    children.append(pane.window)
            elif hasattr(target, 'Sizer') and target.Sizer:
                children.append(target.Sizer)

        if hasattr(self, 'btnHandles'):
            for thisBtn in self.btnHandles:
                pass
        # then apply to all children as well
        for c in children:
            if hasattr(c, '_applyAppTheme'):
            # if the object understands themes then request that
                c._applyAppTheme()
            elif self._recursionDepth>10:
                return
            else:
                # if not then use our own recursive method to search
                if hasattr(c, 'Window') and c.Window is not None:
                    ThemeMixin._applyAppTheme(c.Window)
                elif hasattr(c, 'Sizer') and c.Sizer is not None:
                    ThemeMixin._applyAppTheme(c.Sizer)
                # and then apply
                # try:
                #     ThemeMixin._applyAppTheme(c)
                # except AttributeError:
                #     pass

        if hasattr(target, 'Refresh'):
            target.Refresh()
        if hasattr(target, '_mgr'):
            target._mgr.Update()

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
        elif self.GetLexer() == stc.STC_LEX_CPP:
            # C/C++
            keywords = baseC
            if hasattr(self, 'filename'):
                if self.filename.endswith('.js'):
                    # JavaScript
                    keywords = {
                        0: ['var', 'const', 'let', 'import', 'function', 'if', 'else', 'return', 'struct', 'for', 'while', 'do',
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

    def hex2rgb(self, hex, base=(0, 0, 0, 255)):
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
        return wx.Colour(r, g, b, 255)

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

    def extractFont(self, fontList, base=[]):
        """Extract specified font from theme spec"""
        # Convert to list if not already
        if isinstance(base, str):
            base = base.split(",")
            base = base if isinstance(base, list) else [base]
        if isinstance(fontList, str):
            fontList = fontList.split(",")
            fontList = fontList if isinstance(fontList, list) else [fontList]
        # Extract styles
        bold, italic = [], []
        if "bold" in fontList:
            bold = [fontList.pop(fontList.index("bold"))]
        if "italic" in fontList:
            italic = [fontList.pop(fontList.index("italic"))]
        # Extract styles from base, if needed
        if "bold" in base:
            bold = [base.pop(base.index("bold"))]
        if "italic" in base:
            italic = [base.pop(base.index("italic"))]
        # Append base and default fonts
        fontList.extend(base+["Consolas", "Monaco", "Lucida Console"])
        # Set starting font in case none are found
        if sys.platform == 'win32':
            finalFont = [wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetFaceName()]
        else:
            finalFont = [wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT).GetFaceName()]
        # Cycle through font names, stop at first valid font
        if sys.platform == 'win32':
            for font in fontList:
                if fm.findfont(font) not in fm.defaultFont.values():
                    finalFont = [font] + bold + italic
                    break

        return ','.join(finalFont)

    def _setCodeColors(self, spec):
        """To be called from _psychopyApp only"""
        #if not self.GetTopWindow() == self:
        #    psychopy.logging.warning("This function should only be called from _psychopyApp")

        base = spec['base']
        base['font'] = self.extractFont(base['font'])

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
                spec[key]['font'] = self.extractFont(spec[key]['font'], base['font'])
                spec[key]['size'] = int(prefs.coder['codeFontSize'])
            elif key in ['app', 'icons']:
                pass
            else:
                invalid += [key]
        for key in invalid:
            del spec[key]

        # we have a valid theme so continue
        for key in spec:
            ThemeMixin.codeColors[key] = spec[key]  # class attribute for all mixin subclasses

    def _setAppColors(self, spec):

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
                ThemeMixin.appColors[key] = wx.Colour(color + [opacity])


def getBitmap(name, theme, size=None,
                emblem=None, emblemPos='bottom_right'):
    """Retrieves the wx.Bitmap based on name, theme, size and emblem"""
    global _allIcons
    return _allIcons.getBitmap(name, theme, size, emblem, emblemPos)


class IconCache:
    """A class to load icons and store them just once as a dict of wx.Bitmap
    objects according to theme"""
    _theme = ThemeMixin
    _bitmaps = {}
    _buttons = []  # a list of all created buttons
    _lastBGColor = None
    _lastIcons = None

    # def _loadComponentIcons(self, folderList=(), theme=None, forceReload=False):
    #     """load the icons for all the components
    #     """
    #     if theme is None:
    #         theme = _IconCache.iconTheme
    #     if forceReload or len(self)==0:
    #         compons = experiment.getAllComponents(folderList)
    #         _allIcons = {}
    #         for thisName, thisCompon in compons.items():
    #             if thisName in components.iconFiles:
    #                 # darkmode paths
    #                 if "base.png" not in components.iconFiles[thisName]:
    #                     iconFolder = theme
    #                     components.iconFiles[thisName] = join(
    #                             dirname(components.iconFiles[thisName]),
    #                             iconFolder,
    #                             basename(components.iconFiles[thisName])
    #                     )
    #                 _allIcons[thisName] = self._loadIcons(
    #                         components.iconFiles[thisName])
    #             else:
    #                 _allIcons[thisName] = self._loadIcons(None)
    #         return _allIcons
    #     else:
    #         return _allIcons

    def _findImageFile(self, name, theme, emblem=None, size=None):
        """Tries to find a valid icon in a range of places with and without a
        size suffix"""
        orig = Path(name)
        if not orig.suffix:  # check we have an image suffix
            orig = Path(name+'.png')
        if emblem:  # add the emblem into the name
            orig = orig.with_name(
                    "{}_{}{}".format(orig.stem, emblem, orig.suffix))
        nameAndSize = orig.with_name(orig.stem+str(size)+orig.suffix)
        nameAndDouble = orig.with_name(orig.stem+str(size)+"@2x"+orig.suffix)
        for filename in [nameAndSize, orig, nameAndDouble]:
            # components with no themes folders (themes were added in 2020.2)
            if filename.exists():
                return str(filename)
            # components with theme folders
            # try using the theme name (or 'light' as a default name)
            for themeName in [theme, 'light']:
                thisPath = filename.parent / themeName / filename.name
                if thisPath.exists():
                    return str(thisPath)
            # try in the app icons folder (e.g. for "run.png")
            thisPath = iconsPath / theme / filename
            if thisPath.exists():
                return str(thisPath)
            # and in the root of the app icons
            thisPath = iconsPath / filename
            if thisPath.exists():
                return str(thisPath)
        # still haven't returned nay path. Out of ideas!
        logging.warning("Failed to find icon name={}, theme={}, "
                        "size={}, emblem={}"
                        .format(name, theme, size, emblem))

    def _loadBitmap(self, name, theme, size=None, emblem=None):
        """Creates wxBitmaps based on the image.
        png files work best, but anything that wx.Image can load should be fine

        Doesn't return the icons, just stores them in the dict
        """
        filename = self._findImageFile(name, theme, emblem, size)
        if not filename:
            filename = self._findImageFile('unknown.png', theme, emblem, size)

        # load image with wx.LogNull() to stop libpng complaining about sRGB
        nologging = wx.LogNull()
        try:
            im = wx.Image(filename)
        except TypeError:
            raise FileNotFoundError("Failed to find icon name={}, theme={}, "
                        "size={}, emblem={}"
                        .format(name, theme, size, emblem))
        del nologging  # turns logging back on

        pix = im.GetSize()[0]
        if pix > size:
            im = im.Scale(pix, pix)
        nameMain = _getIdentifier(name, theme, emblem, size)
        self._bitmaps[nameMain] = wx.Bitmap(im)
        if pix > 24:  # for bigger images lets create a 1/2 size one too
            nameSmall = _getIdentifier(name, theme, emblem, pix//2)
            self._bitmaps[nameSmall] = wx.Bitmap(im.Scale(pix//2, pix//2))

    def getBitmap(self, name, theme=None, size=None, emblem=None):
        """Retrieves an icon based on its name, theme, size and emblem
        either from the cache or loading from file as needed"""
        if theme is None:
            theme = ThemeMixin.icons
        if size is None:
            size = 48
        identifier = _getIdentifier(name, theme=theme, emblem=emblem, size=size)
        # find/load the bitmaps first
        if identifier not in IconCache._bitmaps:
            # load all size icons for this name
            self._loadBitmap(name, theme, emblem=emblem, size=size)
        return IconCache._bitmaps[identifier]

    def makeBitmapButton(self, parent, filename,
                         name="",  # name of Component e.g. TextComponent
                         label="", # label on the button, often short name
                         emblem=None,
                         toolbar=None, tip=None, size=None,
                         tbKind=wx.ITEM_NORMAL, theme=None):
        if theme is None:
            theme = ThemeMixin.icons
        bmp = self.getBitmap(filename, theme, size, emblem)
        if toolbar:
            if 'phoenix' in wx.PlatformInfo:
                button = toolbar.AddTool(wx.ID_ANY, label=label,
                                         bitmap=bmp, shortHelp=tip,
                                         kind=tbKind)
            else:
                button = toolbar.AddSimpleTool(wx.ID_ANY, label=label,
                                               bitmap=bmp, shortHelp=tip,
                                               kind=tbKind)
        else:
            button = wx.Button(parent, wx.ID_ANY,
                               label=label, name=name, style=wx.NO_BORDER)
            button.SetBitmap(bmp)
            button.SetBitmapPosition(wx.TOP)
            button.SetBackgroundColour(ThemeMixin.appColors['frame_bg'])
            # just for regular buttons (not toolbar objects) we can re-use
            buttonInfo = {'btn': button,
                          'filename': filename,
                          'size': size,
                          'emblem': emblem,
                          'theme': theme}
            self._buttons.append(buttonInfo)

            if tip:
                button.SetToolTip(wx.ToolTip(tip))

        return button

    def getComponentButton(self, parent, name, label,
                           theme=None, size=None, emblem=None,
                           tip=""):
        """Checks in the experiment.components.iconFiles for filename and
        loads it into a wx.Bitmap"""
        if name in components.iconFiles:
            filename = components.iconFiles[name]
            btn = self.makeBitmapButton(
                    parent=parent,
                    filename=filename, name=name, label=label,
                    tip=tip, size=size)
            return btn

    def getComponentBitmap(self, name, size=None):
        """Checks in the experiment.components.iconFiles for filename and
        loads it into a wx.Bitmap"""
        if type(name) != str:  # got a class instead of a name?
            name = name.getType()
        if name in components.iconFiles:
            filename = components.iconFiles[name]
            bmp = self.getBitmap(name=filename, size=size)
            return bmp
        else:
            print(components.iconFiles)
            raise ValueError("Failed to find '{}' in components.iconFiles"
                             .format(name))

    def setTheme(self, theme):
        if theme.icons != IconCache._lastIcons:
            for thisBtn in IconCache._buttons:
                if thisBtn['btn']:  # Check that button hasn't been deleted
                    newBmp = self.getBitmap(name=thisBtn['filename'],
                                            size=thisBtn['size'],
                                            theme=theme.icons,
                                            emblem=thisBtn['emblem'])
                    thisBtn['btn'].SetBitmap(newBmp)
                    thisBtn['btn'].SetBitmapCurrent(newBmp)
                    thisBtn['btn'].SetBitmapPressed(newBmp)
                    thisBtn['btn'].SetBitmapFocus(newBmp)
                    thisBtn['btn'].SetBitmapDisabled(newBmp)
                    thisBtn['btn'].SetBitmapPosition(wx.TOP)
        IconCache._lastIcons = theme.icons
        if theme.appColors['frame_bg'] != IconCache._lastBGColor:
            for thisBtn in IconCache._buttons:
                try:
                    thisBtn['btn'].SetBackgroundColour(
                            theme.appColors['frame_bg'])
                except RuntimeError:
                    pass
        IconCache._lastBGColor = theme


def _getIdentifier(name, theme, emblem, size=None):
    if size is None:
        return "{}_{}_{}".format(name, theme, emblem)
    else:
        return "{}_{}_{}_{}".format(name, theme, emblem, size)


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


class ThemeSwitcher(wx.Menu):
    """Class to make a submenu for switching theme, meaning that the menu will
    always be the same across frames."""
    def __init__(self, frame):
        # Get list of themes
        themePath = Path(prefs.paths['themes'])
        themeList = {}
        for themeFile in themePath.glob("*.json"):
            try:
                with open(themeFile, "rb") as fp:
                    theme = json.load(fp)
                    # Add themes to list only if min spec is defined
                    base = theme['base']
                    if all(key in base for key in ['bg', 'fg', 'font']):
                            themeList[themeFile.stem] = theme['info'] if "info" in theme else ""

            except (FileNotFoundError, IsADirectoryError):
                pass
        # Make menu
        wx.Menu.__init__(self)
        # Make priority theme buttons
        priority = ["PsychopyDark", "PsychopyLight", "ClassicDark", "Classic"]
        for theme in priority:
            tooltip = themeList.pop(theme)
            item = self.AppendRadioItem(wx.ID_ANY, _translate(theme), tooltip)
            # Bind to theme change method
            frame.Bind(wx.EVT_MENU, frame.app.onThemeChange, item)
        # Make other theme buttons
        for theme in themeList:
            item = self.AppendRadioItem(wx.ID_ANY, _translate(theme), help=themeList[theme])
            frame.Bind(wx.EVT_MENU, frame.app.onThemeChange, item)
        self.AppendSeparator()
        # Add Theme Folder button
        item = self.Append(wx.ID_ANY, _translate("Open theme folder"))
        frame.Bind(wx.EVT_MENU, self.openThemeFolder, item)

    def openThemeFolder(self, event):
        subprocess.call("explorer %(themes)s" % prefs.paths, shell=True)

    def _applyAppTheme(self):
        for item in self.GetMenuItems():
            if item.IsRadio():  # This means it will not attempt to check the separator
                item.Check(item.ItemLabel.lower() == ThemeMixin.codetheme.lower())
