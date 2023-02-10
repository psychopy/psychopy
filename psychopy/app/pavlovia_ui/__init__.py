#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# DONE: add+commit before push
# DONE:  add .gitignore file. Added when opening a repo without one
# DONE: fork+sync doesn't yet fork the project first
# DONE: rather than clone into a folder with files we should init/add/push
#
# TODO: after clone, remember this folder for next file-open call
# TODO: user dlg could/should be local not a browser
# TODO: syncProject() doesn't handle case of a local git pushing to new gitlab
# TODO: if more than one remote then offer options

from psychopy.projects import pavlovia
from .functions import *
from .project import ProjectEditor, syncProject
from ._base import PavloviaMiniBrowser
from . import menu, project, search
