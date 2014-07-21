#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Functions and classes related to file and directory handling'''

import os
import shutil
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

    Existing files in `dst` folder with the same name will be overwritten. Non-existent
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
