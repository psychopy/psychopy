from copy import deepcopy

from . import colors, icons, theme
from ...preferences.preferences import prefs

# --- Functions to handle specific subclasses of wx.Window ---
import wx
import wx.lib.agw.aui as aui
import wx.stc as stc
import wx.richtext


def styleFrame(target):
    # Set background color
    target.SetBackgroundColour(colors.app['frame_bg'])
    # Set foreground color
    target.SetForegroundColour(colors.app['text'])
    # Set aui art provider
    if hasattr(target, 'getAuiManager'):
        target.getAuiManager().SetArtProvider(PsychopyDockArt())
        target.getAuiManager().Update()


def stylePanel(target):
    # Set background color
    target.SetBackgroundColour(colors.app['panel_bg'])
    # Set text color
    target.SetForegroundColour(colors.app['text'])


def styleToolbar(target):
    # Set background color
    target.SetBackgroundColour(colors.app['frame_bg'])
    # Recreate tools
    target.makeTools()
    target.Realize()


def styleNotebook(target):
    # Set art provider to style tabs
    target.SetArtProvider(PsychopyTabArt())
    # Set dock art provider to get rid of outline
    target.GetAuiManager().SetArtProvider(PsychopyDockArt())
    # Iterate through each page
    for index in range(target.GetPageCount()):
        page = target.GetPage(index)
        # Set page background
        page.SetBackgroundColour(colors.app['panel_bg'])
        # If page points to an icon for the tab, set it
        if hasattr(page, "tabIcon"):
            btn = icons.ButtonIcon(page.tabIcon, size=(16, 16))
            target.SetPageBitmap(index, btn.bitmap)


def styleCodeEditor(target):
    from . import fonts
    fonts.coderTheme.load(theme.code)

    target.SetBackgroundColour(colors.app['tab_bg'])
    # Set margin
    margin = fonts.coderTheme.margin
    target.SetFoldMarginColour(True, margin.backColor)
    target.SetFoldMarginHiColour(True, margin.backColor)
    # Set caret colour
    caret = fonts.coderTheme.caret
    target.SetCaretForeground(caret.foreColor)
    target.SetCaretLineBackground(caret.backColor)
    target.SetCaretWidth(1 + (caret.bold))
    # Set selection colour
    select = fonts.coderTheme.select
    target.SetSelForeground(True, select.foreColor)
    target.SetSelBackground(True, select.backColor)
    # Set wrap point
    target.edgeGuideColumn = prefs.coder['edgeGuideColumn']
    target.edgeGuideVisible = target.edgeGuideColumn > 0
    # Set line spacing
    spacing = min(int(prefs.coder['lineSpacing'] / 2), 64)  # Max out at 64
    target.SetExtraAscent(spacing)
    target.SetExtraDescent(spacing)

    # Set styles
    for tag, font in fonts.coderTheme.items():
        if tag is None:
            # Skip tags for e.g. margin, caret
            continue
        if isinstance(font, dict) and tag == target.GetLexer():
            # If tag is the current lexer, then get styles from sub-dict
            for subtag, subfont in font.items():
                target.StyleSetSize(subtag, subfont.pointSize)
                target.StyleSetFaceName(subtag, subfont.obj.GetFaceName())
                target.StyleSetBold(subtag, subfont.bold)
                target.StyleSetItalic(subtag, subfont.italic)
                target.StyleSetForeground(subtag, subfont.foreColor)
                target.StyleSetBackground(subtag, subfont.backColor)
        elif isinstance(font, dict):
            # If tag is another lexer, skip
            continue
        else:
            # If tag is a direct style tag, apply
            target.StyleSetSize(tag, font.pointSize)
            target.StyleSetFaceName(tag, font.obj.GetFaceName())
            target.StyleSetBold(tag, font.bold)
            target.StyleSetItalic(tag, font.italic)
            target.StyleSetForeground(tag, font.foreColor)
            target.StyleSetBackground(tag, font.backColor)
    # Update lexer keywords
    lexer = target.GetLexer()
    filename = ""
    if hasattr(target, "filename"):
        filename = target.filename
    keywords = fonts.getLexerKeywords(lexer, filename)
    for level, val in keywords.items():
        target.SetKeyWords(level, " ".join(val))


def styleTextCtrl(target):
    from . import fonts
    fonts.coderTheme.load(theme.code)
    font = fonts.coderTheme.base

    # Set background
    target.SetBackgroundColour(font.backColor)
    target.SetForegroundColour(font.foreColor)
    # Construct style
    style = wx.TextAttr(
        colText=font.foreColor,
        colBack=font.backColor,
        font=font.obj,
    )
    if isinstance(target, wx.richtext.RichTextCtrl):
        style = wx.richtext.RichTextAttr(style)
    # Set base style
    target.SetDefaultStyle(style)
    # Style existing content
    i = 0
    for ln in range(target.GetNumberOfLines()):
        # Line length +1 (to include the \n)
        i += target.GetLineLength(ln) + 1
    target.SetStyle(start=0, end=i, style=style)
    # Update
    target.Refresh()
    target.Update()


def styleListCtrl(target):
    target.SetBackgroundColour(colors.app['tab_bg'])
    target.SetTextColour(colors.app['text'])
    target.Refresh()


# Define dict linking object types to style functions
methods = {
    wx.Frame: styleFrame,
    wx.Panel: stylePanel,
    aui.AuiNotebook: styleNotebook,
    stc.StyledTextCtrl: styleCodeEditor,
    wx.TextCtrl: styleTextCtrl,
    wx.richtext.RichTextCtrl: styleTextCtrl,
    wx.ToolBar: styleToolbar,
    wx.ListCtrl: styleListCtrl,
}


class ThemeMixin:
    """
    Mixin class for wx.Window objects, which adds a getter/setter `theme` which will identify children and style them
    according to theme.
    """

    @property
    def theme(self):
        if hasattr(self, "_theme"):
            return self._theme

    @theme.setter
    def theme(self, value):
        # Skip method if theme value is unchanged
        if value == self.theme:
            return
        # Store value
        self._theme = deepcopy(value)

        # Do own styling
        self._applyAppTheme()

        # Get children
        children = []
        if hasattr(self, 'GetChildren'):
            for child in self.GetChildren():
                if child not in children:
                    children.append(child)
        if isinstance(self, aui.AuiNotebook):
            for index in range(self.GetPageCount()):
                page = self.GetPage(index)
                if page not in children:
                    children.append(page.window)
        if hasattr(self, 'GetSizer') and self.GetSizer():
            for child in self.GetSizer().GetChildren():
                if child not in children:
                    children.append(child.Window)
        if hasattr(self, 'MenuItems'):
            for child in self.MenuItems:
                if child not in children:
                    children.append(child)
        if hasattr(self, "GetToolBar"):
            tb = self.GetToolBar()
            if tb not in children:
                children.append(tb)

        # For each child, do styling
        for child in children:
            if isinstance(child, ThemeMixin):
                # If child is a ThemeMixin subclass, we can just set theme
                child.theme = self.theme
            else:
                # Otherwise, look for appropriate method in methods array
                for cls, fcn in methods.items():
                    if isinstance(child, cls):
                        # If child extends this class, call the appropriate method on it
                        fcn(child)

    def _applyAppTheme(self):
        """
        Method for applying app theme to self. By default is the same method as for applying to panels, buttons, etc.
        but can be overloaded when subclassing from ThemeMixin to control behaviour on specific objects.
        """
        for cls, fcn in methods.items():
            if isinstance(self, cls):
                # If child extends this class, call the appropriate method on it
                fcn(self)


class PsychopyDockArt(aui.AuiDefaultDockArt):
    def __init__(self):
        aui.AuiDefaultDockArt.__init__(self)
        # Gradient
        self._gradient_type = aui.AUI_GRADIENT_NONE
        # Background
        self._background_colour = colors.app['frame_bg']
        self._background_gradient_colour = colors.app['frame_bg']
        self._background_brush = wx.Brush(self._background_colour)
        # Border
        self._border_size = 0
        self._border_pen = wx.Pen(colors.app['frame_bg'])
        # Sash
        self._draw_sash = True
        self._sash_size = 5
        self._sash_brush = wx.Brush(colors.app['frame_bg'])
        # Gripper
        self._gripper_brush = wx.Brush(colors.app['frame_bg'])
        self._gripper_pen1 = wx.Pen(colors.app['frame_bg'])
        self._gripper_pen2 = wx.Pen(colors.app['frame_bg'])
        self._gripper_pen3 = wx.Pen(colors.app['frame_bg'])
        self._gripper_size = 0
        # Hint
        self._hint_background_colour = colors.app['frame_bg']
        # Caption bar
        self._inactive_caption_colour = colors.app['docker_bg']
        self._inactive_caption_gradient_colour = colors.app['docker_bg']
        self._inactive_caption_text_colour = colors.app['docker_fg']
        self._active_caption_colour = colors.app['docker_bg']
        self._active_caption_gradient_colour = colors.app['docker_bg']
        self._active_caption_text_colour = colors.app['docker_fg']
        # self._caption_font
        self._caption_size = 25
        self._button_size = 20


class PsychopyTabArt(aui.AuiDefaultTabArt):
    def __init__(self):
        aui.AuiDefaultTabArt.__init__(self)

        self.SetDefaultColours()
        self.SetAGWFlags(aui.AUI_NB_NO_TAB_FOCUS)

        self.SetBaseColour(colors.app['tab_bg'])
        self._background_top_colour = colors.app['panel_bg']
        self._background_bottom_colour = colors.app['panel_bg']

        self._tab_text_colour = lambda page: colors.app['text']
        self._tab_top_colour = colors.app['tab_bg']
        self._tab_bottom_colour = colors.app['tab_bg']
        self._tab_gradient_highlight_colour = colors.app['tab_bg']
        self._border_colour = colors.app['tab_bg']
        self._border_pen = wx.Pen(self._border_colour)

        self._tab_disabled_text_colour = colors.app['text']
        self._tab_inactive_top_colour = colors.app['panel_bg']
        self._tab_inactive_bottom_colour = colors.app['panel_bg']

    def DrawTab(self, dc, wnd, page, in_rect, close_button_state, paint_control=False):
        """
        Overloads AuiDefaultTabArt.DrawTab to add a transparent border to inactive tabs
        """
        if page.active:
            self._border_pen = wx.Pen(self._border_colour)
        else:
            self._border_pen = wx.TRANSPARENT_PEN

        return aui.AuiDefaultTabArt.DrawTab(self, dc, wnd, page, in_rect, close_button_state, paint_control)
