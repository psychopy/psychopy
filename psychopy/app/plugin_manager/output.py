import webbrowser
import wx
import wx.richtext
from psychopy.app.themes import handlers, colors


class InstallStdoutPanel(wx.Panel, handlers.ThemeMixin):
    def __init__(self, parent):
        wx.Panel.__init__(
            self, parent
        )
        # Setup sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        # Output
        self.output = wx.richtext.RichTextCtrl(self, style=wx.BORDER_NONE)
        self.output.Bind(wx.EVT_TEXT_URL, self.onLink)
        self.sizer.Add(self.output, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Start off hidden
        self.Hide()
        self.Layout()

    def open(self):
        notebook = self.GetParent()
        # Skip if parent isn't a notebook
        if not isinstance(notebook, wx.Notebook):
            return
        # Navigate to own page
        i = notebook.FindPage(self)
        notebook.ChangeSelection(i)

    def write(self, content, color="black", style=""):
        from psychopy.app.themes import fonts
        self.output.BeginFont(fonts.CodeFont().obj)
        # Set style
        self.output.BeginTextColour(color)
        if "b" in style:
            self.output.BeginBold()
        if "i" in style:
            self.output.BeginItalic()
        # Write content
        self.output.WriteText(content)
        # End style
        self.output.EndTextColour()
        self.output.EndBold()
        self.output.EndItalic()
        # Scroll to end
        self.output.ShowPosition(self.output.GetLastPosition())
        # Make sure we're shown
        self.open()
        # Update
        self.Update()
        self.Refresh()

    def writeLink(self, content, link=""):
        # Begin style
        self.output.BeginURL(link)
        # Write content
        self.write(content, color=colors.scheme["blue"], style="i")
        # End style
        self.output.EndURL()

    def writeCmd(self, cmd=""):
        self.write(f">> {cmd}\n", style="bi")

    def writeStdOut(self, lines=""):
        self.write(f"{lines}\n")

    def writeStdErr(self, lines=""):
        self.write(f"{lines}\n", color=colors.scheme["red"])

    def writeTerminus(self):
        self.write("\n---\n\n\n", color=colors.scheme["green"])

    def onLink(self, evt=None):
        webbrowser.open(evt.String)
