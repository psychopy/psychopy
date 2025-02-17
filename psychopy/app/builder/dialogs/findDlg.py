import wx
from psychopy import experiment
from psychopy.experiment.components.routineSettings import RoutineSettingsComponent
from psychopy.app import utils
from psychopy.app.themes import icons
from psychopy.localization import _translate
from psychopy.tools import stringtools


class BuilderFindDlg(wx.Dialog):
    def __init__(self, frame, exp):
        self.frame = frame
        self.exp = exp

        self.results = []

        wx.Dialog.__init__(
            self,
            parent=frame,
            title=_translate("Find in experiment..."),
            size=(512, 512),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        # setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, border=12, proportion=1, flag=wx.EXPAND | wx.ALL)

        # create search box and controls
        self.searchPnl = wx.Panel(self)
        self.searchPnl.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.searchPnl.SetSizer(self.searchPnl.sizer)
        self.sizer.Add(self.searchPnl, flag=wx.EXPAND | wx.ALL, border=6)

        # create search box
        self.termCtrl = wx.SearchCtrl(self.searchPnl)
        self.termCtrl.Bind(wx.EVT_TEXT, self.onSearchTyping)
        self.searchPnl.sizer.Add(self.termCtrl, proportion=1, flag=wx.EXPAND, border=6)

        # add toggle for case sensitivity
        self.caseSensitiveToggle = wx.ToggleButton(self.searchPnl, style=wx.BU_EXACTFIT)
        self.caseSensitiveToggle.SetBitmap(
            icons.ButtonIcon("case", size=16, theme="light").bitmap
        )
        self.caseSensitiveToggle.SetToolTip(_translate("Match case?"))
        self.caseSensitiveToggle.Bind(wx.EVT_TOGGLEBUTTON, self.onSearchTyping)
        self.searchPnl.sizer.Add(self.caseSensitiveToggle, flag=wx.EXPAND | wx.LEFT, border=6)

        # add toggle for regex
        self.regexToggle = wx.ToggleButton(self.searchPnl, style=wx.BU_EXACTFIT)
        self.regexToggle.SetBitmap(
            icons.ButtonIcon("regex", size=16, theme="light").bitmap
        )
        self.regexToggle.SetToolTip(_translate("Match regex?"))
        self.regexToggle.Bind(wx.EVT_TOGGLEBUTTON, self.onSearchTyping)
        self.searchPnl.sizer.Add(self.regexToggle, flag=wx.EXPAND | wx.LEFT, border=6)

        # create results box
        self.resultsCtrl = utils.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.resetListCtrl()
        self.resultsCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectResult)
        self.resultsCtrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onSelectResult)
        self.resultsCtrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onViewResult)
        self.sizer.Add(self.resultsCtrl, border=6, proportion=1, flag=wx.EXPAND | wx.ALL)

        # setup component icons
        self.imageList = wx.ImageList(16, 16)
        self.imageMap = {}
        # icon for each Component/Routine
        for cls in experiment.getAllElements().values():
            i = self.imageList.Add(
                icons.ComponentIcon(cls, theme="light", size=16).bitmap
            )
            self.imageMap[cls] = i
        # icon for loop
        i = self.imageList.Add(
                icons.ButtonIcon("loop", theme="light", size=16).bitmap
            )
        self.imageMap[experiment.loops.LoopInitiator] = i
        # set icons
        self.resultsCtrl.SetImageList(self.imageList, wx.IMAGE_LIST_SMALL)

        # add buttons
        btnSzr = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        self.border.Add(btnSzr, border=12, flag=wx.EXPAND | wx.ALL)
        # relabel OK to Go
        for child in btnSzr.GetChildren():
            if child.Window and child.Window.GetId() == wx.ID_OK:
                self.okBtn = child.Window
        self.okBtn.SetLabel(_translate("Go"))
        self.okBtn.Disable()
        # rebind OK to view method
        self.okBtn.Bind(wx.EVT_BUTTON, self.onViewResult)

        self.Layout()
        self.termCtrl.SetFocus()

    def resetListCtrl(self):
        self.resultsCtrl.ClearAll()
        self.resultsCtrl.AppendColumn(_translate("Location"), width=120)
        self.resultsCtrl.AppendColumn(_translate("Parameter"), width=120)
        self.resultsCtrl.AppendColumn(_translate("Value"), width=-1)
        self.resultsCtrl.resizeLastColumn(minWidth=120)
        self.selectedResult = None

    def onSearchTyping(self, evt):
        term = self.termCtrl.GetValue()
        caseSensitive = self.caseSensitiveToggle.GetValue()
        regex = self.regexToggle.GetValue()
        
        if term:
            # get locations of term in experiment
            self.results = getParamLocations(self.exp, term=term, caseSensitive=caseSensitive, regex=regex)
        else:
            # return nothing for blank string
            self.results = []

        # clear old output
        self.resetListCtrl()

        # show new output
        for result in self.results:
            # unpack result
            parent, comp, paramName, param = result
            # sanitize val for display
            val = str(param.val)
            if "\n" in val:
                # if multiline, show first line with match
                for line in val.split("\n"):
                    if compareStrings(line, term, caseSensitive, regex):
                        val = line
                        break
            # construct location string
            if parent is None:
                location = comp.name
            else:
                location = f"{comp.name} ({parent.name})"
            # construct entry
            entry = [location, param.label, val]
            # add entry
            self.resultsCtrl.Append(entry)
            # set image for comp
            fallbackImg = icons.ButtonIcon("experiment", theme="light", size=16).bitmap
            self.resultsCtrl.SetItemImage(
                item=self.resultsCtrl.GetItemCount()-1,
                image=self.imageMap.get(type(comp), fallbackImg)
            )
        
        # size
        self.resultsCtrl.Layout()
        # disable Go button until item selected
        self.okBtn.Disable()

        evt.Skip()

    def onSelectResult(self, evt):
        if evt.GetEventType() == wx.EVT_LIST_ITEM_SELECTED.typeId:
            # if item is selected, store its info
            self.selectedResult = self.results[evt.GetIndex()]
            # enable Go button
            self.okBtn.Enable()
        else:
            # if no item selected, clear its info
            self.selectedResult = None
            # disable Go button
            self.okBtn.Disable()

        evt.Skip()

    def onViewResult(self, evt):
        # there should be a selected result if this button was enabled, but just in case...
        if self.selectedResult is None:
            return
        # do usual OK button stuff
        # self.Close()
        # unpack
        rt, comp, paramName, param = self.selectedResult
        # navigate to routine
        self.frame.routinePanel.setCurrentRoutine(rt)
        # navigate to component & category
        page = self.frame.routinePanel.getCurrentPage()
        if isinstance(comp, experiment.components.BaseComponent):
            # if we have a component, open its dialog and navigate to categ page
            if hasattr(comp, 'type') and comp.type.lower() == 'code':
                # For code components, we need to find the index of the page
                openToPage = list(comp.params.keys()).index(paramName)
            else:
                openToPage = param.categ
            page.editComponentProperties(component=comp, openToPage=openToPage)
        elif isinstance(comp, experiment.routines.BaseStandaloneRoutine):
            # if we're in a standalone routine, just navigate to categ page
            i = page.ctrls.getCategoryIndex(param.categ)
            page.ctrls.ChangeSelection(i)
        elif isinstance(comp, experiment.loops.LoopInitiator):
            # if we're in a loop, open the loop dialog
            self.frame.flowPanel.canvas.editLoopProperties(loop=comp.loop)


def compareStrings(text, term, caseSensitive, regex):
    # lowercase everything if doing a non-case-sensitive check
    if not caseSensitive:
        term = term.lower()
        text = text.lower()
    # convert to regex object if using regex
    if regex:
        # if term isn't valid regex, assume no match
        try:
            stringtools.re.compile(term)
        except stringtools.re.error:
            return False
        # convert to a regex searchable
        text = stringtools.RegexSearchable(text)
    
    return term in text


def getParamLocations(exp, term, caseSensitive=False, regex=False):
    """
    Get locations of params containing the given term.

    Parameters
    ----------
    term : str
        Term to search for

    Returns
    -------
    list
        List of tuples, with each tuple functioning as a path to the found
        param
    """

    # array to store results in
    found = []

    # go through all routines
    for rt in exp.routines.values():
        if isinstance(rt, experiment.routines.BaseStandaloneRoutine):
            # find in standalone routine
            for paramName, param in rt.params.items():
                if compareStrings(str(param.val), term, caseSensitive, regex):
                    # append path (routine -> param)
                    found.append(
                        (None, rt, paramName, param)
                    )
        if isinstance(rt, experiment.routines.Routine):
            # find in regular routine
            for comp in rt:
                for paramName, param in comp.params.items():
                    if compareStrings(str(param.val), term, caseSensitive, regex):
                        # treat RoutineSettings as synonymous with the Routine
                        if isinstance(comp, RoutineSettingsComponent):
                            parent = None
                        else:
                            parent = rt
                        # append path (routine -> component -> param)
                        found.append(
                            (parent, comp, paramName, param)
                        )
    for obj in exp.flow:
        # find in loop
        if isinstance(obj, experiment.loops.LoopInitiator):
            loop = obj.loop
            for paramName, param in loop.params.items():
                if compareStrings(str(param.val), term, caseSensitive, regex):
                    # append path (loop -> param)
                    found.append(
                        (None, obj, paramName, param)
                    )

    return found



