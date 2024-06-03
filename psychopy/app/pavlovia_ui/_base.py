#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import sys

import wx
import wx.html2
import requests

from psychopy.localization import _translate
from psychopy.projects import pavlovia
from psychopy import logging


class BaseFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.Center()
        # set up menu bar
        self.menuBar = wx.MenuBar()
        self.fileMenu = self.makeFileMenu()
        self.menuBar.Append(self.fileMenu, _translate('&File'))
        self.SetMenuBar(self.menuBar)

    def makeFileMenu(self):
        fileMenu = wx.Menu()
        app = wx.GetApp()
        keyCodes = app.keys
        # add items to file menu
        fileMenu.Append(wx.ID_CLOSE,
                        _translate("&Close View\t%s") % keyCodes['close'],
                        _translate("Close current window"))
        self.Bind(wx.EVT_MENU, self.closeFrame, id=wx.ID_CLOSE)
        # -------------quit
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_EXIT,
                        _translate("&Quit\t%s") % keyCodes['quit'],
                        _translate("Terminate the program"))
        self.Bind(wx.EVT_MENU, app.quit, id=wx.ID_EXIT)
        return fileMenu

    def closeFrame(self, event=None, checkSave=True):
        self.Destroy()

    def checkSave(self):
        """If the app asks whether everything is safely saved
        """
        return True  # for OK


class PavloviaMiniBrowser(wx.Dialog):
    """This class is used by to open an internal browser for the user stuff
    """
    style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
    def __init__(self, parent, user=None, loginOnly=False, logoutOnly=False,
                 style=style, *args, **kwargs):
        # create the dialog
        wx.Dialog.__init__(self, parent, style=style, *args, **kwargs)
        # create browser window for authentication
        self.browser = wx.html2.WebView.New(self)
        self.loginOnly = loginOnly
        self.logoutOnly = logoutOnly
        self.tokenInfo = {}

        # do layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.browser, 1, wx.EXPAND, 10)
        self.SetSizer(sizer)
        if loginOnly:
            self.SetSize((600, 600))
        else:
            self.SetSize((700, 600))
        self.CenterOnParent()

        # check there is a user (or log them in)
        if not user:
            self.user = pavlovia.getCurrentSession().user
        if not user:
            self.login()
        if not user:
            return None

    def logout(self):
        self.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.checkForLogoutURL)
        self.browser.LoadURL('https://gitlab.pavlovia.org/users/sign_out')

    def login(self):
        self._loggingIn = True
        authURL, state = pavlovia.getAuthURL()
        self.browser.Bind(wx.html2.EVT_WEBVIEW_ERROR, self.onConnectionErr)
        self.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.getAccessTokenFromURL)
        self.browser.LoadURL(authURL)
        self.Close()

    def setURL(self, url):
        self.browser.LoadURL(url)

    def gotoUserPage(self):
        if self.user:
            url = self.user.attributes['web_url']
            self.browser.LoadURL(url)

    def editUserPage(self):
        url = "https://gitlab.pavlovia.org/profile"
        self.browser.LoadURL(url)
        self.SetSizeWH(1240, 840)

    def gotoProjects(self):
        self.browser.LoadURL("https://pavlovia.org/projects.html")

    def onConnectionErr(self, event):
        if 'INET_E_DOWNLOAD_FAILURE' in event.GetString():
            self.EndModal(wx.ID_EXIT)
            raise Exception("{}: No internet connection available.".format(event.GetString()))
    
    def getAccessTokenFromURL(self, event):
        """
        Parse the redirect url from a login request for the parameter `code`, this is 
        the "Auth code" which is used later to get an access token.

        Parameters
        ----------
        event : wx.html2.EVT_WEBVIEW_LOADED
            Load event from the browser window.
        """
        # get URL
        url = event.GetURL()
        # get auth code from URL
        if "code=" in url:
            # get state from redirect url
            self.tokenInfo['state'] = self.getParamFromURL('state', url)
            # if returned an auth code, use it to get a token
            resp = requests.post(
                "https://gitlab.pavlovia.org/oauth/token",
                params={
                    'client_id': pavlovia.client_id,
                    'code': self.getParamFromURL("code", url),
                    'grant_type': "authorization_code",
                    'redirect_uri': pavlovia.redirect_url,
                    'code_verifier': pavlovia.code_verifier
                }
            ).json()
            # use the json response from that http request to get access remaining token info
            self.tokenInfo['token'] = resp['access_token']
            self.tokenInfo['tokenType'] = resp['token_type']
        elif "access_token=" in url:
            self.tokenInfo['token'] = self.getParamFromURL(
                'access_token', url)
            self.tokenInfo['tokenType'] = self.getParamFromURL(
                'token_type', url)
            self.tokenInfo['state'] = self.getParamFromURL(
                'state', url)
            self._loggingIn = False  # we got a log in
            self.browser.Unbind(wx.html2.EVT_WEBVIEW_LOADED)
            pavlovia.login(self.tokenInfo['token'])
            if self.loginOnly:
                self.EndModal(wx.ID_OK)
        elif url == 'https://gitlab.pavlovia.org/dashboard/projects':
            # this is what happens if the user registered instead of logging in
            # try now to do the log in (in the same session)
            self.login()
        else:
            logging.info("OAuthBrowser.onNewURL: {}".format(url))

    def checkForLogoutURL(self, event):
        url = event.GetURL()
        if url == 'https://gitlab.pavlovia.org/users/sign_in':
            if self.logoutOnly and self.IsModal():
                self.EndModal(wx.ID_OK)

    def getParamFromURL(self, paramName, url=None):
        """Takes a url and returns the named param"""
        if url is None:
            url = self.browser.GetCurrentURL()
        return url.split(paramName + '=')[1].split('&')[0]


class PavloviaCommitDialog(wx.Dialog):
    """This class will be used to brings up a commit dialog
    (if there is anything to commit)"""

    def __init__(self, *args, **kwargs):

        # pop kwargs for Py2 compatibility
        changeInfo = kwargs.pop('changeInfo', '')
        initMsg = kwargs.pop('initMsg', '')

        super(PavloviaCommitDialog, self).__init__(*args, **kwargs)

        # Set Text widgets
        wx.Dialog(None, id=wx.ID_ANY, title=_translate("Committing changes"))
        self.updatesInfo = wx.StaticText(self, label=changeInfo)
        self.commitTitleLbl = wx.StaticText(self, label=_translate('Summary of changes'))
        self.commitTitleCtrl = wx.TextCtrl(self, size=(500, -1), value=initMsg)
        self.commitDescrLbl = wx.StaticText(self, label=_translate('Details of changes\n (optional)'))
        self.commitDescrCtrl = wx.TextCtrl(self, size=(500, 200), style=wx.TE_MULTILINE | wx.TE_AUTO_URL)

        # Set buttons
        self.btnOK = wx.Button(self, wx.ID_OK)
        self.btnCancel = wx.Button(self, wx.ID_CANCEL)

        # Format elements
        self.setToolTips()
        self.setDlgSizers()

    def setToolTips(self):
        """Set the tooltips for the dialog widgets"""
        self.commitTitleCtrl.SetToolTip(
            wx.ToolTip(
                _translate("Title summarizing the changes you're making in these files")))
        self.commitDescrCtrl.SetToolTip(
            wx.ToolTip(
                _translate("Optional details about the changes you're making in these files")))

    def setDlgSizers(self):
        """
        Set the commit dialog sizers and layout.
        """
        commitSizer = wx.FlexGridSizer(cols=2, rows=2, vgap=5, hgap=5)
        commitSizer.AddMany([(self.commitTitleLbl, 0, wx.ALIGN_RIGHT),
                             self.commitTitleCtrl,
                             (self.commitDescrLbl, 0, wx.ALIGN_RIGHT),
                             self.commitDescrCtrl])
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        if sys.platform == "win32":
            btns = [self.btnOK, self.btnCancel]
        else:
            btns = [self.btnCancel, self.btnOK]
        buttonSizer.AddMany(btns)

        # main sizer and layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.updatesInfo, 0, wx.ALL | wx.EXPAND, border=5)
        mainSizer.Add(commitSizer, 1, wx.ALL | wx.EXPAND, border=5)
        mainSizer.Add(buttonSizer, 0, wx.ALL | wx.ALIGN_RIGHT, border=5)
        self.SetSizerAndFit(mainSizer)
        self.Layout()

    def ShowCommitDlg(self):
        """Show the commit application-modal dialog

        Returns
        -------
        wx event
        """
        return self.ShowModal()

    def getCommitMsg(self):
        """
        Gets the commit message for the git commit.

        Returns
        -------
        string:
            The commit message and description.
            If somehow the commit message is blank, a default is given.
        """
        if self.commitTitleCtrl.IsEmpty():
            commitMsg = "_"
        else:
            commitMsg = self.commitTitleCtrl.GetValue()
            if not self.commitDescrCtrl.IsEmpty():
                commitMsg += "\n\n" + self.commitDescrCtrl.GetValue()
        return commitMsg
