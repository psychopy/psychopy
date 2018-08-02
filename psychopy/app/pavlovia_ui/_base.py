#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import wx.html2

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
        self.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.checkForLoginURL)
        self.browser.LoadURL(authURL)

    def setURL(self, url):
        self.browser.LoadURL(url)

    def gotoUserPage(self):
        if self.user:
            url = self.user.attributes['web_url']
            self.browser.LoadURL(url)

    def gotoProjects(self):
        self.browser.LoadURL("https://pavlovia.org/projects.html")

    def onConnectionErr(self, event):
        if 'INET_E_DOWNLOAD_FAILURE' in event.GetString():
            self.EndModal(wx.ID_EXIT)
            raise Exception("{}: No internet connection available.".format(event.GetString()))

    def checkForLoginURL(self, event):
        url = event.GetURL()
        if 'access_token=' in url:
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
            if self.logoutOnly:
                self.EndModal(wx.ID_OK)

    def getParamFromURL(self, paramName, url=None):
        """Takes a url and returns the named param"""
        if url is None:
            url = self.browser.GetCurrentURL()
        return url.split(paramName + '=')[1].split('&')[0]