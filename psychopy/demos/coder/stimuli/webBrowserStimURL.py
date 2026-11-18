#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of WebBrowserStim showing a page from the internet

The page can be used with the mouse and keyboard: scroll it, follow links, or
click in a text box and type. The bar at the top shows the page's title and how
far it has loaded. Press escape to quit.

Needs Qt WebEngine (pip install psychopy[web]) and an internet connection.

"""
from psychopy import visual, core
from psychopy.hardware import keyboard

URL = 'https://www.psychopy.org'

win = visual.Window((1280, 800), units='height', fullscr=False)
kb = keyboard.Keyboard()

status = visual.TextStim(
    win, text='', pos=(0, 0.46), height=0.025, wrapWidth=1.5)

# the page fills most of the window, laid out at the size it is drawn
page = visual.WebBrowserStim(
    win, url=URL, pos=(0, -0.03), size=(1.5, 0.88))

while not kb.getKeys(['escape']):
    if page.loadError:
        text = page.loadError
    elif page.isLoading:
        text = 'Loading {} ({}%)'.format(page.url, page.loadProgress)
    else:
        text = '{}  ({})'.format(page.title or page.url, page.url)
    if text != status.text:
        status.text = text

    status.draw()
    page.draw()
    win.flip()

page.close()
win.close()
core.quit()
