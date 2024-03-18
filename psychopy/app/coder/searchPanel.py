#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import wx.dataview
import re


class BaseSearchPanel(wx.Panel):
    """Base class for the search panel in the Coder view.

    This class is a subclass of `wx.Panel` and is used to create the search
    panel in the Coder view. This class is not meant to be used directly, but
    to be subclassed by a class that implements the search panel.

    Parameters
    ----------
    parent : `wx.Window`
        The parent window that owns the search panel.
    id : int, optional
        The window identifier. Default is `wx.ID_ANY`.
    pos : ArrayLike or `wx.Point`, optional
        The initial position of the window. Default is `wx.DefaultPosition`.
    size : ArrayLike or `wx.Size`, optional
        The initial size of the window. Default is `wx.DefaultSize`.
    style : int, optional
        The window style. Default is `wx.TAB_TRAVERSAL`.
    name : str, optional
        The window name. Default is an empty string.

    """
    def __init__(self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
            size = wx.Size(500, 300), 
            style = wx.TAB_TRAVERSAL, 
            name = wx.EmptyString ):
        
        wx.Panel.__init__ (
            self, parent, id=id, pos=pos, size=size, style=style, name=name)

        szrMain = wx.BoxSizer( wx.VERTICAL )

        szrSearchPanel = wx.BoxSizer( wx.HORIZONTAL )

        self.lblSearchBar = wx.StaticText( self, wx.ID_ANY, u"Search:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lblSearchBar.Wrap( -1 )

        szrSearchPanel.Add( self.lblSearchBar, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5 )

        self.txtSearch = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
        szrSearchPanel.Add( self.txtSearch, 1, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5 )

        self.tglMatchCase = wx.BitmapToggleButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.tglMatchCase.SetToolTip( u"Match case of search term." )
        szrSearchPanel.Add( self.tglMatchCase, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        self.tglMatchWord = wx.BitmapToggleButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.tglMatchWord.SetToolTip( u"Match only whole words." )
        szrSearchPanel.Add( self.tglMatchWord, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        self.tglUseRegEx = wx.BitmapToggleButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.tglUseRegEx.SetToolTip( u"Evaluate search text as a regular expression." )
        szrSearchPanel.Add( self.tglUseRegEx, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        szrMain.Add( szrSearchPanel, 0, wx.ALL|wx.EXPAND, 5 )

        self.tvwSearchResults = wx.dataview.TreeListCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.TL_DEFAULT_STYLE )
        szrMain.Add( self.tvwSearchResults, 1, wx.EXPAND, 5 )


        self.SetSizer( szrMain )
        self.Layout()

        # Connect Events
        self.txtSearch.Bind(wx.EVT_TEXT_ENTER, self.OnSearchEnter)
        self.tglMatchCase.Bind(wx.EVT_TOGGLEBUTTON, self.OnMatchCaseToggle)
        self.tglMatchWord.Bind(wx.EVT_TOGGLEBUTTON, self.OnMatchWordToggle)
        self.tglUseRegEx.Bind(wx.EVT_TOGGLEBUTTON, self.OnUseRegEx)
        self.tvwSearchResults.Bind(
            wx.dataview.EVT_TREELIST_ITEM_ACTIVATED, self.OnSearchItemActivated)
        self.tvwSearchResults.Bind(
            wx.dataview.EVT_TREELIST_SELECTION_CHANGED, 
            self.OnSearchItemChanged)

    def __del__( self ):
        pass

    def OnSearchEnter( self, event ):
        event.Skip()

    def OnMatchCaseToggle( self, event ):
        event.Skip()

    def OnMatchWordToggle( self, event ):
        event.Skip()

    def OnUseRegEx( self, event ):
        event.Skip()

    def OnSearchItemActivated( self, event ):
        event.Skip()

    def OnSearchItemChanged( self, event ):
        event.Skip()


class SearchPanel(BaseSearchPanel):
    """Class for the search panel in the Coder view.

    This class is a subclass of `BaseSearchPanel` and is used to create the
    search panel in the Coder view. It is used to search for text within the
    current script and display the search results.

    Search results are displayed in a `wx.dataview.TreeListCtrl` widget that 
    shows the file name and the line number for each match. The user can
    click on an item in the search results to jump to the corresponding line
    in the script.

    Parameters
    ----------
    parent : `wx.Window`
        The parent window that owns the search panel.
    frame : `CoderFrame`
        The `CoderFrame` object that owns the search panel.

    """
    def __init__(self, parent, frame):
        BaseSearchPanel.__init__(self, parent)

        if frame is None:
            raise ValueError("The frame cannot be `None`.")

        self._coder = frame

        # initialize search settings and results
        self._searchString = ""
        self._searchResults = {}
        self._useRegEx = self.tglUseRegEx.GetValue()
        self._matchCase = self.tglMatchCase.GetValue()
        self._matchWord = self.tglMatchWord.GetValue()

        # add coulmns to the search results tree list control
        self.tvwSearchResults.AppendColumn("Results")
        self.tvwSearchResults.AppendColumn("Line")
        self.tvwSearchResults.AppendColumn("Column")

    def _searchText(self, text):
        """Search for text within the opened scripts.

        This method searches for the specified text within the current script
        and returns the search results.

        Parameters
        ----------
        text : str
            The text to search for withing the document.

        Returns
        -------
        list of tuple
            A list of tuples, where each tuple contains the file name and the
            line and column number of each match and the line of text. If there'
            are multiple matches on a line, there will be multiple tuples for
            that line.

        """
        results = []
        lines = text.split("\n")
        for lineNum, line in enumerate(lines):
            if self._useRegEx:
                # search for the text using a regular expression
                if self._matchCase:
                    matches = re.finditer(self._searchString, line)
                else:
                    matches = re.finditer(
                        self._searchString, line, re.IGNORECASE)
            else:
                # search for the text using a simple string search
                if self._matchCase:
                    matches = re.finditer(re.escape(self._searchString), line)
                else:
                    matches = re.finditer(
                        re.escape(self._searchString), line, re.IGNORECASE)

            for match in matches:
                results.append((lineNum, match.start(), line))

        return results

    def _displaySearchResults(self):
        """Display the search results in the search panel.

        This method displays the search results in the search panel. It adds
        the search results to the `wx.dataview.TreeListCtrl` widget, where the
        file name and line number of each match is shown.

        """
        # clear the previous results
        self.tvwSearchResults.DeleteAllItems()

        # add the search results to the search panel
        for docName, results in self._searchResults.items():
            # add the document to the search results
            resultRoot = self.tvwSearchResults.GetRootItem()
            docItem = self.tvwSearchResults.AppendItem(resultRoot, docName)

            # add the search results to the document
            for lineNum, lineCol, lineText in results:
                lineItem = self.tvwSearchResults.AppendItem(
                    docItem, str(lineText))
                self.tvwSearchResults.SetItemText(lineItem, 1, str(lineNum + 1))
                self.tvwSearchResults.SetItemText(lineItem, 2, str(lineCol + 1))

            self.tvwSearchResults.Expand(docItem)

    def doSearch(self, searchText=None):
        """Search for text within the current script.

        This method searches for the specified text within the current script
        and displays the search results in the search panel.

        The value of `_searchResults` is updated with the search results, and
        they are displayed in the `wx.dataview.TreeListCtrl`.

        Parameters
        ----------
        searchText : str, optional
            The text to search for within the current script. If `None`, the
            text entered in the search box is used instead. If any text is 
            specified in the search box, it will be overwritten by the specified 
            text. Default is `None`.

        """
        if searchText is None:
            self._searchString = self.txtSearch.GetValue()
        else:
            searchText = str(searchText)
            # set the search string to the specified text
            self.txtSearch.SetValue(searchText)
            self._searchString = searchText

        if not self._searchString:
            return

        # get a list of open coder document handles
        openDocs = self._coder.getOpenDocs()

        if not openDocs:
            return

        # clear the search results
        self._searchResults = {}

        # search for the text in each open coder document
        for doc in openDocs:
            # get the text of the document
            text = doc.GetText()

            # search for the text in the document
            results = self._searchText(text)

            # add the search results to the search results list
            if results:
                self._searchResults[doc.filename] = results

        # display the search results in the search panel
        self._displaySearchResults()

    def getSearchResults(self):
        """Get the results of the last search.

        This method returns the results of the last search as a dictionary,
        where the keys are the file names and the values are lists of tuples
        containing the line numbers and the lines of text that matched the
        search.

        Returns
        -------
        dict
            A dictionary where the keys are the file names and the values are
            lists of tuples containing the line numbers and the lines of text
            that matched the search.

        """
        return self._searchResults

    def OnSearchEnter(self, event):
        """Handle the user pressing the Enter key in the search text box.

        This method is called when the user presses the Enter key in the search
        text box. It triggers a search for the text entered in the search box.

        Parameters
        ----------
        event : `wx.CommandEvent`
            The event object that contains information about the event.

        """
        self.doSearch()  # search for the text entered in the search box

    def OnMatchCaseToggle(self, event):
        """Handle the user toggling the Match Case button.

        This method is called when the user toggles the Match Case button. It
        triggers a search for the text entered in the search box, using the
        current match case setting.

        Parameters
        ----------
        event : `wx.CommandEvent`
            The event object that contains information about the event.

        """
        self._matchCase = self.tglMatchCase.GetValue()

    def OnMatchWordToggle(self, event):
        """Handle the user toggling the Match Word button.

        This method is called when the user toggles the Match Word button. It
        triggers a search for the text entered in the search box, using the
        current match word setting.

        Parameters
        ----------
        event : `wx.CommandEvent`
            The event object that contains information about the event.

        """
        self._matchWord = self.tglMatchWord.GetValue()

    def OnUseRegEx(self, event):
        """Handle the user toggling the Use Regular Expression button.

        This method is called when the user toggles the Use Regular Expression
        button. It triggers a search for the text entered in the search box, 
        using the current regular expression setting.

        Parameters
        ----------
        event : `wx.CommandEvent`
            The event object that contains information about the event.

        """
        self._useRegEx = self.tglUseRegEx.GetValue()

    def OnSearchItemActivated(self, event):
        """Handle the user activating an item in the search results.

        This method is called when the user activates an item in the search
        results. It jumps to the corresponding line in the script.

        Parameters
        ----------
        event : `wx.dataview.TreeListEvent`
            The event object that contains information about the event.

        """
        item = event.GetItem()
        lineNumber = self.tvwSearchResults.GetItemText(item, 1)

        if lineNumber:
            # get the document that corresponds to the selected item
            fileName = self.tvwSearchResults.GetItemText(
                self.tvwSearchResults.GetItemParent(item))
            self._coder.gotoLine(fileName, int(lineNumber))
        else:
            # user clicked on the document name, just go to the document
            fileName = self.tvwSearchResults.GetItemText(item)
            self._coder.setCurrentDoc(fileName)

    def _applyAppTheme(self):
        """Apply the application theme to the search panel.

        This method applies the application theme to the search panel. It
        sets the background color of the search panel to the background color
        of the application theme.

        """
        pass


if __name__ == "__main__":
    pass


