# -*- coding: utf-8 -*-
import wx

from pyglet.gl import gl_info, GLint, glGetIntegerv, GL_MAX_ELEMENTS_VERTICES
from psychopy import visual, preferences
import sys
import os
import platform


class SystemInfoDialog(wx.Dialog):
    """Dialog for retrieving system information within the PsychoPy app suite.

    Shows the same information as the 'sysinfo.py' script and provide options
    to save details to a file or copy them to the clipboard.

    """
    def __init__(self, parent):
        wx.Dialog.__init__(
            self, parent, id=wx.ID_ANY, title=u"System Information",
            pos=wx.DefaultPosition, size=wx.Size(575, 575),
            style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT)

        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)

        bszMain = wx.BoxSizer(wx.VERTICAL)

        self.txtSystemInfo = wx.TextCtrl(
            self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
            wx.TE_MULTILINE | wx.TE_READONLY)
        bszMain.Add(self.txtSystemInfo, 1, wx.ALL | wx.EXPAND, 5)

        gszControls = wx.GridSizer(0, 3, 0, 0)

        self.cmdCopy = wx.Button(
            self, wx.ID_ANY, u"C&opy", wx.DefaultPosition, wx.DefaultSize, 0)
        self.cmdSave = wx.Button(
            self, wx.ID_ANY, u"&Save", wx.DefaultPosition, wx.DefaultSize, 0)
        self.cmdClose = wx.Button(
            self, wx.ID_ANY, u"&Close", wx.DefaultPosition, wx.DefaultSize, 0)
        self.cmdClose.SetDefault()

        if sys.platform == "win32":
            btns = [self.cmdCopy, self.cmdSave, self.cmdClose]
        else:
            btns = [self.cmdClose, self.cmdCopy, self.cmdSave]
        gszControls.Add(btns[0], 0, wx.ALL, 5)
        gszControls.Add(btns[1], 0, wx.ALL, 5)
        gszControls.Add(btns[2], 0, wx.ALL, 5)

        bszMain.Add(gszControls, 0, wx.ALIGN_RIGHT, 5)

        self.SetSizer(bszMain)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.cmdCopy.Bind(wx.EVT_BUTTON, self.OnCopy)
        self.cmdSave.Bind(wx.EVT_BUTTON, self.OnSave)
        self.cmdClose.Bind(wx.EVT_BUTTON, self.OnClose)

        self.txtSystemInfo.SetValue(self.getInfoText())

    def getLine(self, *args):
        """Get a line of text to append to the output."""
        return ' '.join([str(i) for i in args]) + '\n'

    def getInfoText(self):
        """Get system information text."""
        outputText = ""  # text to return

        # show the PsychoPy version
        from psychopy import __version__
        outputText += self.getLine("PsychoPy", __version__)

        # get system paths
        outputText += self.getLine("\nPaths to files on the system:")
        for key in ['userPrefsFile', 'appDataFile', 'demos', 'appFile']:
            outputText += self.getLine(
                "    %s: %s" % (key, preferences.prefs.paths[key]))

        # system information such as OS, CPU and memory
        outputText += self.getLine("\nSystem Info:")
        outputText += self.getLine(
            ' '*4, 'Operating System: {}'.format(platform.platform()))
        outputText += self.getLine(
            ' ' * 4, 'Processor: {}'.format(platform.processor()))

        # requires psutil
        try:
            import psutil
            outputText += self.getLine(
                ' ' * 4, 'CPU freq (MHz): {}'.format(psutil.cpu_freq().max))
            outputText += self.getLine(
                ' ' * 4, 'CPU cores: {} (physical), {} (logical)'.format(
                    psutil.cpu_count(False), psutil.cpu_count()))
            outputText += self.getLine(
                ' ' * 4, 'Installed memory: {} (Total), {} (Available)'.format(
                    *psutil.virtual_memory()))
        except ImportError:
            outputText += self.getLine(' ' * 4, 'CPU freq (MHz): N/A')
            outputText += self.getLine(
                ' ' * 4, 'CPU cores: {} (logical)'.format(os.cpu_count()))
            outputText += self.getLine(' ' * 4, 'Installed memory: N/A')

        # if on MacOS
        if sys.platform == 'darwin':
            OSXver, junk, architecture = platform.mac_ver()
            outputText += self.getLine(
                ' ' * 4, "macOS %s running on %s" % (OSXver, architecture))

        # Python information
        outputText += self.getLine("\nPython info:")
        outputText += self.getLine(' '*4, 'Executable path:', sys.executable)
        outputText += self.getLine(' '*4, 'Version:', sys.version)
        outputText += self.getLine(' ' * 4, '(Selected) Installed Packages:')
        import numpy
        outputText += self.getLine(' '*8, "numpy ({})".format(
            numpy.__version__))
        import scipy
        outputText += self.getLine(' '*8, "scipy ({})".format(
            scipy.__version__))
        import matplotlib
        outputText += self.getLine(' '*8, "matplotlib ({})".format(
            matplotlib.__version__))
        import pyglet
        outputText += self.getLine(' '*8, "pyglet ({})".format(pyglet.version))
        try:
            import glfw
            outputText += self.getLine(' '*8, "PyGLFW ({})".format(
                glfw.__version__))
        except Exception:
            outputText += self.getLine(' '*8, 'PyGLFW [not installed]')

        # sound related
        try:
            import pyo
            outputText += self.getLine(
                ' '*8, "pyo", ('%i.%i.%i' % pyo.getVersion()))
        except Exception:
            outputText += self.getLine(' '*8, 'pyo [not installed]')
        try:
            import psychtoolbox
            outputText += self.getLine(' '*8, "psychtoolbox ({})".format(
                psychtoolbox._version.__version__))
        except Exception:
            outputText += self.getLine(' '*8, 'psychtoolbox [not installed]')

        # wxpython version
        try:
            import wx
            outputText += self.getLine(' '*8, "wxPython ({})".format(
                wx.__version__))
        except Exception:
            outputText += self.getLine(' '*8, 'wxPython [not installed]')

        # get OpenGL details
        win = visual.Window([100, 100])  # some drivers want a window open first

        outputText += self.getLine("\nOpenGL Info:")
        # # get info about the graphics card and drivers
        outputText += self.getLine(
            ' '*4, "Vendor:", gl_info.get_vendor())
        outputText += self.getLine(
            ' '*4, "Rendering engine:", gl_info.get_renderer())
        outputText += self.getLine(
            ' '*4, "OpenGL version:", gl_info.get_version())
        outputText += self.getLine(
            ' '*4, "Shaders supported: ", win._haveShaders)

        # get opengl extensions
        outputText += self.getLine(' '*4, "(Selected) Extensions:")
        extensionsOfInterest = [
            'GL_ARB_multitexture',
            'GL_EXT_framebuffer_object',
            'GL_ARB_fragment_program',
            'GL_ARB_shader_objects',
            'GL_ARB_vertex_shader',
            'GL_ARB_texture_non_power_of_two',
            'GL_ARB_texture_float',
            'GL_STEREO']

        for ext in extensionsOfInterest:
            outputText += self.getLine(
                ' '*8, ext + ':', bool(gl_info.have_extension(ext)))

        # also determine nVertices that can be used in vertex arrays
        maxVerts = GLint()
        glGetIntegerv(GL_MAX_ELEMENTS_VERTICES, maxVerts)
        outputText += self.getLine(
            ' '*4, 'max vertices in vertex array:', maxVerts.value)

        win.close()

        return outputText

    def OnCopy(self, event):
        """Copy system information to clipboard."""

        # check if we have a selection
        start, end = self.txtSystemInfo.GetSelection()
        if start != end:
            txt = self.txtSystemInfo.GetStringSelection()
        else:
            txt = self.txtSystemInfo.GetValue()

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(txt))
            wx.TheClipboard.Close()

        event.Skip()

    def OnSave(self, event):
        """Save system information report to a file."""
        with wx.FileDialog(
                self, "Save system information report",
                wildcard="Text files (*.txt)|*.txt",
                defaultFile='psychopy_sysinfo.txt',
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'w') as file:
                    file.write(self.txtSystemInfo.GetValue())
            except IOError:
                errdlg = wx.MessageDialog(
                    self,
                    "Cannot save to file '%s'." % pathname,
                    "File save error",
                    wx.OK_DEFAULT | wx.ICON_ERROR | wx.CENTRE)
                errdlg.ShowModal()
                errdlg.Destroy()

        event.Skip()

    def OnClose(self, event):
        self.Destroy()
        event.Skip()
