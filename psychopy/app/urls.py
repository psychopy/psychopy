#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A central location to store information about urls
"""
urls = dict()

# links based on string names
urls['builder'] = "https://www.psychopy.org/builder"
urls['builder.loops'] = "https://www.psychopy.org/builder/flow.html#loops"
# NB. builder components get their urls defined by the component code
# (so a custom component can have a url)

urls['downloads'] = "https://github.com/psychopy/psychopy/releases"
urls['changelog'] = "https://www.psychopy.org/changelog.html"

general = "https://www.psychopy.org/general/"
urls['prefs'] = general + "prefs.html"
urls['prefs.general'] = general + "prefs.html#general-settings"
urls['prefs.app'] = general + "prefs.html#application-settings"
urls['prefs.coder'] = general + "prefs.html#coder-settings"
urls['prefs.builder'] = general + "prefs.html#builder-settings"
urls['prefs.connections'] = general + "prefs.html#connection-settings"

# links keyed by wxIDs (e.g. menu item IDs)
urls['psychopyHome'] = "https://www.psychopy.org/"
urls['psychopyReference'] = "https://www.psychopy.org/api"
urls['coderTutorial'] = "https://www.psychopy.org/coder/tutorial1.html"
urls['builderHelp'] = urls['builder']
urls['builderDemos'] = "http://code.google.com/p/psychopy/downloads/list?can=2&q=demos"
urls['projsAbout'] = "https://www.psychopy.org/general/projects.html"
