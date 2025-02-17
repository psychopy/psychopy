#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to file and directory error handling
"""
import os
import glob
from pathlib import Path

from psychopy import logging


def handleFileCollision(fileName, fileCollisionMethod):
    """Handle filename collisions by overwriting, renaming, or failing hard.

    :Parameters:

        fileCollisionMethod: 'overwrite', 'rename', 'fail'
            If a file with the requested name already exists, specify
            how to deal with it. 'overwrite' will overwrite existing
            files in place, 'rename' will append an integer to create
            a new file ('trials1.psydat', 'trials2.pysdat' etc) and
            'error' will raise an IOError.
    """
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
