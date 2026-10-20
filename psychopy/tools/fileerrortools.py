#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to file and directory error handling
"""
import os
import glob
from pathlib import Path

from psychopy import logging


def _stripTrailingSpaces(fileName):
    """Remove trailing spaces from each component of a file path.

    Windows silently strips trailing spaces from folder names when they are
    created, so a requested path like ``'data/sub002 /file.psydat'`` would
    end up in a folder called ``'sub002'`` on disk and later writes to the
    original path would fail (see issue #7755).
    """
    if not fileName:
        return fileName
    fileObj = Path(fileName)
    # strip every part except the root/drive anchor of an absolute path
    parts = [
        part if i == 0 and fileObj.is_absolute() else part.rstrip(' ')
        for i, part in enumerate(fileObj.parts)
    ]
    return str(Path(*parts))


def handleFileCollision(fileName, fileCollisionMethod):
    """Handle filename collisions by overwriting, renaming, or failing hard.

    Trailing spaces are removed from each path component before the
    collision is handled, as Windows silently strips them when creating
    folders and would otherwise save data under a different path than the
    one requested (fixes issue #7755).

    :Parameters:

        fileCollisionMethod: 'overwrite', 'rename', 'fail'
            If a file with the requested name already exists, specify
            how to deal with it. 'overwrite' will overwrite existing
            files in place, 'rename' will append an integer to create
            a new file ('trials1.psydat', 'trials2.pysdat' etc) and
            'error' will raise an IOError.
    """
    strippedFileName = _stripTrailingSpaces(fileName)
    if strippedFileName != fileName:
        logging.warning("Trailing spaces were removed from the data file "
                        "path '%s', it will be saved as '%s'."
                        % (fileName, strippedFileName))
        fileName = strippedFileName

    if fileCollisionMethod == 'overwrite':
        logging.warning('Data file, %s, will be overwritten' % fileName)
    elif fileCollisionMethod == 'fail':
        msg = ("Data file %s already exists. Set argument "
               "fileCollisionMethod to overwrite.")
        raise IOError(msg % fileName)
    elif fileCollisionMethod == 'rename':
        # convert to a Path object
        fileObj = Path(fileName)
        # use a glob star if we don't have an ext
        if not fileObj.suffix:
            fileObj = fileObj.parent / (fileObj.stem + ".*")
        # get original file name
        rootName = fileObj.stem
        # get total number of sibling files to use as maximum for iteration
        nSiblings = len(list(fileObj.parent.glob("*")))
        # iteratively add numbers to the end until filename isn't taken
        i = 0
        while list(fileObj.parent.glob(fileObj.name)) and i < nSiblings:
            i += 1
            fileObj = fileObj.parent / (f"{rootName}_{i}" + fileObj.suffix)
        # remove glob star from suffix if needed
        if fileObj.suffix == ".*":
            fileObj = fileObj.parent / fileObj.stem
        # convert back to a string
        fileName = str(fileObj)

        # Check to make sure the new fileName hasn't been taken too.
        if os.path.exists(fileName):
            msg = ("New fileName %s has already been taken. Something "
                   "is wrong with the append counter.")
            raise IOError(msg % fileName)

    else:
        msg = "Argument fileCollisionMethod was invalid: %s"
        raise ValueError(msg % str(fileCollisionMethod))

    return fileName
