"""Functions and classes for applying UI themes."""

import wx.lib.agw.aui as aui


defaultDockArt = aui.AuiDefaultDockArt()  # defines default theme
topCol = defaultDockArt.GetColor(aui.AUI_DOCKART_INACTIVE_CAPTION_COLOUR)
bottomCol = defaultDockArt.GetColor(
    aui.AUI_DOCKART_INACTIVE_CAPTION_GRADIENT_COLOUR)

# switch caption gradient colors, looks nicer
defaultDockArt.SetColor(aui.AUI_DOCKART_INACTIVE_CAPTION_COLOUR, bottomCol)
defaultDockArt.SetColor(aui.AUI_DOCKART_INACTIVE_CAPTION_GRADIENT_COLOUR, topCol)


class CustomTabArt(aui.AuiDefaultTabArt):
    """Customizable tab art. This class exposes color properties not normally
    available."""
    def __init__(self):
        super(CustomTabArt, self).__init__()

    def SetTabInactiveBottomColor(self, color):
        self._tab_inactive_bottom_colour = color

    def SetTabInactiveTopColor(self, color):
        self._tab_inactive_top_colour = color

    def SetTabBottomColor(self, color):
        self._tab_bottom_colour = color

    def SetTabTopColor(self, color):
        self._tab_top_colour = color

    def SetTabHighlightColor(self, color):
        self._tab_gradient_highlight_colour = color


def applyDockartTheme(auiMgr, theme='PsychoPy Light'):
    """Apply a theme to AUI dock art.

    Parameters
    ----------
    auiMgr : wx.lib.agw.aui.AuiManager
        AUI manager to theme.
    theme : str
        Name of theme to apply.

    """
    try:
        themeSpec = UI_THEMES[theme]
    except KeyError:
        themeSpec = UI_THEMES['PsychoPy Light']

    # get handle to art provider
    ap = auiMgr.GetArtProvider()

    # setup dock art for AUI manager
    for key, val in themeSpec['dockart']['colors'].items():
        ap.SetColor(key, val)

