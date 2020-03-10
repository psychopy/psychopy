"""Functions and classes for applying UI themes."""

import wx
import wx.lib.agw.aui as aui
# from wx.lib.agw.aui.aui_utilities import GetBaseColour, LightColour


defaultArt = aui.AuiDefaultDockArt()  # defines default theme

# UI themes
UI_THEMES = {
    # This theme is mostly the same as the default except the caption header
    # gradient is inverted (looks nicer).
    'PsychoPy Light': {
        'dockart': {
            'colors': {
                aui.AUI_DOCKART_INACTIVE_CAPTION_GRADIENT_COLOUR:
                    defaultArt.GetColor(
                        aui.AUI_DOCKART_INACTIVE_CAPTION_COLOUR),
                aui.AUI_DOCKART_INACTIVE_CAPTION_COLOUR:
                    defaultArt.GetColor(
                        aui.AUI_DOCKART_INACTIVE_CAPTION_GRADIENT_COLOUR),
            },
            'metrics': {}
        }
    }
}


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

