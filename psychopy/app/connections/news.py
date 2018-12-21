#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import requests
from psychopy import logging


newsURL = "http://news.psychopy.org/"


def getNewsItems(app=None):
    url = newsURL + "news_items.json"
    resp = requests.get(url)
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


class NewsFrame():
    def __init__(self, app=None):
        pass
