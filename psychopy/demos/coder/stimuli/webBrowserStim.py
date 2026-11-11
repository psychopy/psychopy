#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of WebBrowserStim

WebBrowserStim shows a web page in the window, which can be used with the mouse
and keyboard. This page is a short form; when it is submitted, the page sends
the answers to the experiment with `psychopy.send()`, which `getMessages()`
returns. Pages can be loaded from the internet with `url=` too.

Needs Qt WebEngine: pip install psychopy[web]

"""
from psychopy import visual, core
from psychopy.hardware import keyboard

FORM = """<!doctype html>
<html><head><style>
  body { font: 18px sans-serif; margin: 30px; background: #f4f4f4; }
  label { display: block; margin: 16px 0 6px; }
  input, select, button { font: inherit; padding: 4px; }
</style></head>
<body>
  <h2>A few questions</h2>
  <form id="form">
    <label for="name">What is your name?</label>
    <input id="name" autocomplete="off">
    <label for="colour">Favourite colour?</label>
    <select id="colour">
      <option>red</option><option>green</option><option>blue</option>
    </select>
    <label><input type="checkbox" id="agree"> I like web pages</label>
    <p><button type="submit">Submit</button></p>
  </form>
  <script>
    document.getElementById('form').addEventListener('submit', function (e) {
      e.preventDefault();  // stay on this page
      psychopy.send({
        name: document.getElementById('name').value,
        colour: document.getElementById('colour').value,
        agree: document.getElementById('agree').checked
      });
    });
  </script>
</body></html>"""

win = visual.Window((1024, 768), units='height', fullscr=False)
kb = keyboard.Keyboard()

instructions = visual.TextStim(
    win, text="Fill in the form, then submit it (escape quits)",
    pos=(0, 0.45), height=0.03)

# the page is laid out at the size it is drawn on screen
page = visual.WebBrowserStim(
    win, html=FORM, size=(1.0, 0.75), pos=(0, 0), waitForLoad=True)
page.focus()  # so typing goes to it straight away

answers = None
while answers is None:
    instructions.draw()
    page.draw()
    win.flip()

    for message in page.getMessages():
        answers = message
    if kb.getKeys(['escape']):
        break

page.close()

if answers is not None:
    result = visual.TextStim(
        win, height=0.04, text="Thanks {name}!\n\nColour: {colour}\n"
        "Likes web pages: {agree}".format(**answers))
    result.draw()
    win.flip()
    core.wait(10)

win.close()
core.quit()
