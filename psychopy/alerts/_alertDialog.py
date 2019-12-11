import wx
import webbrowser
from psychopy.alerts._alerts import AlertEntry
from psychopy.alerts._alerts import alertLog


class AlertPanel(wx.Panel):
    """
    Alerts panel for presenting alerts stored in _alerts.alertLog
    """
    def __init__(self, parent=None, id=wx.ID_ANY, size=[400,150]):
        wx.Panel.__init__(self, parent, id, size=size)

        self.alertTextCtrl = AlertRichText(parent=self, style=wx.TE_MULTILINE, size=size)

        header = AlertEntry(9998, {})
        self.write(header)

        for alert in alertLog:
            if isinstance(alert, AlertEntry):
                self.write(alert)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.alertTextCtrl, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(mainSizer)
        self.SetMinSize(size)

    def onURL(self, evt):
        """
        Open link in default browser.
        """
        wx.BeginBusyCursor()
        try:
            if evt.String.startswith("http"):
                webbrowser.open(evt.String)
        except Exception:
            print("Could not open URL: {}".format(evt.String))
        wx.EndBusyCursor()

    def write(self, text):
        self.alertTextCtrl.write(text)


class AlertRichText(wx.richtext.RichTextCtrl):
    """
    A rich text ctrl for formatting and presenting alerts.
    """
    def __init__(self, parent, style, size=None, font=None, fontSize=None):
        kwargs = {'parent': parent, 'style': style}
        if size is not None:
            kwargs['size'] = size
        wx.richtext.RichTextCtrl.__init__(self, **kwargs)

        currFont = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.NORMAL)
        if fontSize:
            currFont.SetPointSize(fontSize)
        self.BeginFont(currFont)

        self.parent = parent
        self.Bind(wx.EVT_TEXT_URL, parent.onURL)

    def write(self, alert):
        # Write Code
        self.BeginTextColour([255, 105, 0])
        self.WriteText("{:<8}".format(alert.code))
        self.EndTextColour()

        # Write category
        self.BeginTextColour([255, 0, 0])
        self.WriteText("{:<13}".format(alert.cat))
        self.EndTextColour()

        # Write URL
        self.BeginBold()
        self.BeginTextColour(wx.BLUE)
        self.BeginURL(alert.url)
        urlLabel = [alert.url, "Learn more"][type(alert.code) == int]  # Set header as "URL"
        self.WriteText("{:<15}".format(urlLabel))
        self.EndURL()
        self.EndBold()
        self.EndTextColour()

        # Write Message
        self.BeginTextColour([0, 150, 0])
        self.WriteText(alert.msg)
        self.EndTextColour()

        self.Newline()
        self.ShowPosition(self.GetLastPosition())
