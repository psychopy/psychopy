#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Helper functions in PsychoPy for interacting with projects (e.g. from pyosf)
"""
import glob
import os
from psychopy import logging

try:
    import pyosf
    from pyosf import constants
    constants.PROJECT_NAME = "PsychoPy"
    havePyosf = True
    if pyosf.__version__ < "1.0.3":
        logging.warn("pyosf is version {} whereas PsychoPy expects 1.0.3+"
                     .format(pyosf.__version__))
except ImportError:
    havePyosf = False

from psychopy import prefs

projectsFolder = os.path.join(prefs.paths['userPrefsDir'], 'projects')


class ProjectCatalog(dict):
    """Handles info about known project files (either in project history or in
    the ~/.psychopy/projects folder).
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.refresh()

    def projFromId(self, id):
        for key, item in list(self.items()):
            if item.project_id == id:
                return key, item
        return (None, None)  # got here without finding anything

    def refresh(self):
        """Search the locations and update the catalog
        """
        self.clear()
        # prev used files
        projFileList = set(prefs.appData['projects']['fileHistory'])
        projFileList.update(glob.glob(
            os.path.join(projectsFolder, "*.psyproj")))
        # check for files that have gone (from prev files list)
        for filePath in projFileList:
            try:
                key = self.addFile(filePath)
            except:
                key = None
            if key is None and \
                    (filePath in prefs.appData['projects']['fileHistory']):
                prefs.appData['projects']['fileHistory'].remove(filePath)

    def addFile(self, filePath):
        """Try to add the file and return a dict key (or None if non-existent)
        """
        if not os.path.isfile(filePath):
            return None
        try:
            thisProj = pyosf.Project(project_file=filePath)  # load proj file
        except pyosf.OSFDeleted:
            return None
        if hasattr(thisProj, 'name'):
            key = "%s: %s" % (thisProj.project_id, thisProj.name)
        else:
            key = "%s: n/a" % (thisProj.project_id)
        if key not in self:
            self.__setitem__(key, thisProj)
        return key


projectCatalog = ProjectCatalog()
