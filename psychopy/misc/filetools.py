#!/usr/bin/env python

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Functions and classes related to file and directory handling'''

from psychopy import logging

import os
import shutil
import glob
import cPickle


def toFile(filename, data):
    """save data (of any sort) as a pickle file

    simple wrapper of the cPickle module in core python
    """
    f = open(filename, 'w')
    cPickle.dump(data,f)
    f.close()


def fromFile(filename):
    """load data (of any sort) from a pickle file

    simple wrapper of the cPickle module in core python
    """
    f = open(filename)
    contents = cPickle.load(f)
    f.close()
    #if loading an experiment file make sure we don't save further copies using __del__
    if hasattr(contents, 'abort'):
        contents.abort()
    return contents


def mergeFolder(src, dst, pattern=None):
    """Merge a folder into another.

    Existing files in dst with the same name will be overwritten. Non-existent
    files/folders will be created.

    """
    # dstdir must exist first
    srcnames = os.listdir(src)
    for name in srcnames:
        srcfname = os.path.join(src, name)
        dstfname = os.path.join(dst, name)
        if os.path.isdir(srcfname):
            if not os.path.isdir(dstfname): os.makedirs(dstfname)
            mergeFolder(srcfname, dstfname)
        else:
            try:
                shutil.copyfile(srcfname, dstfname)#copy without metadata
            except IOError, why:
                print why


def _handleFileCollision(fileName, fileCollisionMethod):
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
