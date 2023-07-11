import wx
from psychopy import experiment
from psychopy.app import utils
from psychopy.app.themes import icons
from psychopy.localization import _translate


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

        # create search box
        self.termCtrl = wx.SearchCtrl(self)
        self.termCtrl.Bind(wx.EVT_SEARCH, self.onSearch)
        self.sizer.Add(self.termCtrl, border=6, flag=wx.EXPAND | wx.ALL)

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
        for cls in experiment.getAllElements().values():
            i = self.imageList.Add(
                icons.ComponentIcon(cls, theme="light", size=16).bitmap
            )
            self.imageMap[cls] = i
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
        self.resultsCtrl.AppendColumn(_translate("Component"), width=120)
        self.resultsCtrl.AppendColumn(_translate("Parameter"), width=120)
        self.resultsCtrl.AppendColumn(_translate("Value"), width=-1)
        self.resultsCtrl.resizeLastColumn(minWidth=120)
        self.selectedResult = None

    def onSearch(self, evt):
        # get term to search
        term = evt.GetString()
        if term:
            # get locations of term in experiment
            self.results = getParamLocations(self.exp, term=term)
        else:
            # return nothing for blank string
            self.results = []
        # clear old output
        self.resetListCtrl()
        # show new output
        for result in self.results:
            # unpack result
            rt, comp, paramName, param = result
            # sanitize val for display
            val = str(param.val)
            if "\n" in val:
                # if multiline, show first line with match
                for line in val.split("\n"):
                    if self.termCtrl.GetValue() in line:
                        val = line
                        break
            # construct entry
            entry = [comp.name, param.label, val]
            # add entry
            self.resultsCtrl.Append(entry)
            # set image for comp
            self.resultsCtrl.SetItemImage(
                item=self.resultsCtrl.GetItemCount()-1,
                image=self.imageMap[type(comp)]
            )
        # size
        self.resultsCtrl.Layout()
        # disable Go button until item selected
        self.okBtn.Disable()

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
        self.Close()
        # unpack
        rt, comp, paramName, param = self.selectedResult
        # navigate to routine
        self.frame.routinePanel.setCurrentRoutine(rt)
        # navigate to component & category
        page = self.frame.routinePanel.getCurrentPage()
        if isinstance(comp, experiment.components.BaseComponent):
            # if we have a component, open its dialog and navigate to categ page
            if hasattr(comp, 'type') and comp.type.lower() == 'code':
                openToPage = paramName
            else:
                openToPage = param.categ
            page.editComponentProperties(component=comp, openToPage=openToPage)
        else:
            # if we're in a standalone routine, just navigate to categ page
            i = page.ctrls.getCategoryIndex(param.categ)
            page.ctrls.ChangeSelection(i)


def getParamLocations(exp, term):
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
                if term in str(param.val):
                    # append path (routine -> param)
                    found.append(
                        (rt, rt, paramName, param)
                    )
        if isinstance(rt, experiment.routines.Routine):
            # find in regular routine
            for comp in rt:
                for paramName, param in comp.params.items():
                    if term in str(param.val):
                        # append path (routine -> component -> param)
                        found.append(
                            (rt, comp, paramName, param)
                        )

    return found

