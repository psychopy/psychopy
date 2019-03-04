#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import requests
from psychopy import logging, prefs
import wx

newsURL = "http://news.psychopy.org/"

CRITICAL = 50
ANNOUNCE = 40
TIP = 30
JOKE = 20


def getNewsItems(app=None):
    url = newsURL + "news_items.json"
    try:
        resp = requests.get(url, timeout=0.5)
    except requests.ConnectionError:
        return None
    if resp.status_code == 200:
        try:
            items = resp.json()
        except Exception as e:
            logging.warning("Found, but failed to parse '{}'".format(url))
            print(str(e))
    else:
        logging.debug("failed to connect to '{}'".format(url))
    if app:
        app.news = items["news"]
    return items["news"]


def showNews(app=None, checkPrev=True):
    """Brings up an internal html viewer and show the latest psychopy news

    :Returns:
        itemShown : bool

    """
    if checkPrev and app.news:
        toShow = None
        if 'lastNewsDate' in prefs.appData['lastNewsDate']:
            lastNewsDate = prefs.appData['lastNewsDate']
        else:
            lastNewsDate = ""
        for item in app.news:
            if item['importance'] >= ANNOUNCE and item['date'] > lastNewsDate:
                toShow = item
                break
        if not toShow:
            return 0
    else:
        return 0

    dlg = wx.Dialog(None, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                    size=(800, 400))
    browser = wx.html2.WebView.New(dlg)

    # do layout
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(browser, 1, wx.EXPAND, 10)
    dlg.SetSizer(sizer)

    browser.LoadURL(newsURL)
    dlg.Show()
    return 1


#
# class NewsFrame(wx.Dialog):
#     """This class is used by to open an internal browser for the user stuff
#     """
#     style =
#
#     def __init__(self, parent, style=style, *args, **kwargs):
#         # create the dialog
#         wx.Dialog.__init__(self, parent, style=style, *args, **kwargs)
#         # create browser window for authentication
#         self.browser = wx.html2.WebView.New(self)
#
#         # do layout
#         sizer = wx.BoxSizer(wx.VERTICAL)
#         sizer.Add(self.browser, 1, wx.EXPAND, 10)
#         self.SetSizer(sizer)
#
#         self.browser.LoadURL(newsURL)
#         self.Show()
