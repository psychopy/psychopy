#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Functions and classes related to file and directory error handling'''

import os
import glob

from psychopy import logging


def handleFileCollision(fileName, fileCollisionMethod):
    """ Handle filename collisions by overwriting, renaming, or failing hard.

    :Parameters:

        fileCollisionMethod: 'overwrite', 'rename', 'fail'
            If a file with the requested name already exists, specify how to deal with it. 'overwrite' will overwite existing files in place, 'rename' will append an integer to create a new file ('trials1.psydat', 'trials2.pysdat' etc) and 'error' will raise an IOError.
    """
    if fileCollisionMethod == 'overwrite':
        logging.warning('Data file, %s, will be overwritten' % fileName)
    elif fileCollisionMethod == 'fail':
        raise IOError("Data file %s already exists. Set argument fileCollisionMethod to overwrite." % fileName)
    elif fileCollisionMethod == 'rename':
        rootName, extension = os.path.splitext(fileName)
        matchingFiles = glob.glob("%s*%s" % (rootName, extension))
        count = len(matchingFiles)

        fileName = "%s_%d%s" % (rootName, count, extension) # Build the renamed string.

        if os.path.exists(fileName): # Check to make sure the new fileName hasn't been taken too.
            raise IOError("New fileName %s has already been taken. Something is wrong with the append counter." % fileName)

    else:
        raise ValueError("Argument fileCollisionMethod was invalid: %s" % str(fileCollisionMethod))

    return fileName
