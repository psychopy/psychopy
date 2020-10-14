#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A central location to store information about urls
"""

from __future__ import absolute_import, print_function


urls = dict()

# links based on string names
urls['builder'] = "http://www.psychopy.org/builder/builder.html"
urls['builder.loops'] = "http://www.psychopy.org/builder/flow.html#loops"
# NB. builder components get their urls defined by the component code
# (so a custom component can have a url)

urls['downloads'] = "https://github.com/psychopy/psychopy/releases"
urls['changelog'] = "http://www.psychopy.org/changelog.html"

general = "http://www.psychopy.org/general/"
urls['prefs'] = general + "prefs.html"
urls['prefs.general'] = general + "prefs.html#general-settings"
urls['prefs.app'] = general + "prefs.html#application-settings"
urls['prefs.coder'] = general + "prefs.html#coder-settings"
urls['prefs.builder'] = general + "prefs.html#builder-settings"
urls['prefs.connections'] = general + "prefs.html#connection-settings"

# links keyed by wxIDs (e.g. menu item IDs)
urls['psychopyHome'] = "http://www.psychopy.org/"
urls['psychopyReference'] = "http://www.psychopy.org/api/api.html"
urls['coderTutorial'] = "http://www.psychopy.org/coder/tutorial1.html"
urls['builderHelp'] = urls['builder']
urls['builderDemos'] = "http://code.google.com/p/psychopy/downloads/list?can=2&q=demos"
urls['projsAbout'] = "http://www.psychopy.org/general/projects.html"