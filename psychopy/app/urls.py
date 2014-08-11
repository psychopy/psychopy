"""A central location to store information about urls
"""

import wxIDs

urls={}

#links based on string names
urls['builder']="http://www.psychopy.org/builder/builder.html"
urls['builder.loops']="http://www.psychopy.org/builder/flow.html#loops"
#NB. builder components get their urls defined by the component code (so a custom component can have a url)

urls['downloads']="https://sourceforge.net/projects/psychpy/files"
urls['changelog']="http://www.psychopy.org/changelog.html"
urls['prefs']="http://www.psychopy.org/general/prefs.html"
urls['prefs.general']="http://www.psychopy.org/general/prefs.html#general-settings"
urls['prefs.app']="http://www.psychopy.org/general/prefs.html#application-settings"
urls['prefs.coder']="http://www.psychopy.org/general/prefs.html#coder-settings"
urls['prefs.builder']="http://www.psychopy.org/general/prefs.html#builder-settings"
urls['prefs.connections']="http://www.psychopy.org/general/prefs.html#connection-settings"

#links keyed by wxIDs (e.g. menu item IDs)
urls[wxIDs.psychopyHome]="http://www.psychopy.org/"
urls[wxIDs.psychopyReference]="http://www.psychopy.org/api/api.html"
urls[wxIDs.coderTutorial]="http://www.psychopy.org/coder/tutorial1.html"
urls[wxIDs.builderHelp]=urls['builder']
urls[wxIDs.builderDemos]="http://code.google.com/p/psychopy/downloads/list?can=2&q=demos"
