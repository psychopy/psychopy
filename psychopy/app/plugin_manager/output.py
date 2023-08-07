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
        """Write out bytes coming from the current subprocess.

        Parameters
        ----------
        content : str or bytes
            Text to write.
        color : bool
            Color to show the text as
        style : str
            Whether to show the text as bold and/or italic.
            * ""  = Regular
            * "b" = Bold
            * "i" = Italic
            * "bi" / "ib" = Bold Italic
        """
        # Decode content if needed
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        # Set font
        from psychopy.app.themes import fonts
        self.output.BeginFont(fonts.CodeFont().obj)
        # Set style
        self.output.BeginTextColour(color)
        if "b" in style:
            self.output.BeginBold()
        if "i" in style:
            self.output.BeginItalic()
        # Write content
        self.output.WriteText(f"\n{content}")
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
        """
        Write input (black, bold, italic, prefaced by >>) text to the output panel.

        Parameters
        ----------
        cmd : bytes or str
            Command which was supplied to the subprocess
        """
        self.write(f">> {cmd}", style="bi")

    def writeStdOut(self, lines=""):
        """
        Write output (black) text to the output panel.

        Parameters
        ----------
        lines : bytes or str
            String to print, can also be bytes (as is the case when retrieved directly from the subprocess).
        """
        self.write(lines)

    def writeStdErr(self, lines=""):
        """
        Write error (red) text to the output panel.

        Parameters
        ----------
        lines : bytes or str
            String to print, can also be bytes (as is the case when retrieved directly from the subprocess).
        """
        self.write(lines, color=colors.scheme["red"])

    def writeTerminus(self, msg="Process completed"):
        """
        Write output when the subprocess exits.

        Parameters
        ----------
        msg : str
            Message to be printed flanked by `#` characters.
        """
        # Construct a close message, shows the exit code
        closeMsg = f" {msg} ".center(80, '#')
        # Write close message
        self.write(closeMsg, color=colors.scheme["green"])

    def onLink(self, evt=None):
        webbrowser.open(evt.String)
