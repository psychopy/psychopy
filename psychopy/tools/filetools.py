#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to file and directory handling
"""
from __future__ import absolute_import, print_function

# from future import standard_library
# standard_library.install_aliases()
import os
import shutil
import sys
import codecs
import numpy as np
import json_tricks

try:
    import cPickle as pickle
except ImportError:
    import pickle

from psychopy import logging
from psychopy.tools.fileerrortools import handleFileCollision


def toFile(filename, data):
    """Save data (of any sort) as a pickle file.

    simple wrapper of the cPickle module in core python
    """
    f = open(filename, 'wb')
    pickle.dump(data, f)
    f.close()


def fromFile(filename):
    """Load data from a pickle or JSON file.
    """
    if filename.endswith('.psydat'):
        with open(filename, 'rb') as f:
            contents = pickle.load(f)
            # if loading an experiment file make sure we don't save further
            # copies using __del__
            if hasattr(contents, 'abort'):
                contents.abort()
    elif filename.endswith('.json'):
        with open(filename, 'r') as f:
            contents = json_tricks.load(f)

            # Restore RNG if we load a TrialHandler2 object.
            # We also need to remove the 'temporary' ._rng_state attribute that
            # was saved with it.
            from psychopy.data import TrialHandler2
            if isinstance(contents, TrialHandler2):
                contents._rng = np.random.RandomState(seed=contents.seed)
                contents._rng.set_state(contents._rng_state)
                del contents._rng_state
    else:
        msg = "Don't know how to handle this file type, aborting."
        raise ValueError(msg)

    return contents


def mergeFolder(src, dst, pattern=None):
    """Merge a folder into another.

    Existing files in `dst` folder with the same name will be
    overwritten. Non-existent files/folders will be created.
    """
    # dstdir must exist first
    srcnames = os.listdir(src)
    for name in srcnames:
        srcfname = os.path.join(src, name)
        dstfname = os.path.join(dst, name)
        if os.path.isdir(srcfname):
            if not os.path.isdir(dstfname):
                os.makedirs(dstfname)
            mergeFolder(srcfname, dstfname)
        else:
            try:
                # copy without metadata:
                shutil.copyfile(srcfname, dstfname)
            except IOError as why:
                print(why)


def openOutputFile(fileName=None, append=False, fileCollisionMethod='rename',
                   encoding='utf-8'):
    """Open an output file (or standard output) for writing.

    :Parameters:

    fileName : None, 'stdout', or str
        The desired output file name. If `None` or `stdout`, return
        `sys.stdout`. Any other string will be considered a filename.
    append : bool, optional
        If ``True``, append data to an existing file; otherwise, overwrite
        it with new data.
        Defaults to ``True``, i.e. appending.
    fileCollisionMethod : string, optional
        How to handle filename collisions. Valid values are `'rename'`,
        `'overwrite'`, and `'fail'`.
        This parameter is ignored if ``append``  is set to ``True``.
        Defaults to `rename`.
    encoding : string, optional
        The encoding to use when writing the file. This parameter will be
        ignored if `append` is `False` and `fileName` ends with `.psydat`
        or `.npy` (i.e. if a binary file is to be written).
        Defaults to ``'utf-8'``.

    :Returns:

    f : file
        A writable file handle.

    """
    if (fileName is None) or (fileName == 'stdout'):
        return sys.stdout

    if append:
        mode = 'a'
    else:
        if fileName.endswith(('.psydat', '.npy')):
            mode = 'wb'
        else:
            mode = 'w'

        # Rename the output file if a file of that name already exists
        # and it should not be appended.
        if os.path.exists(fileName) and not append:
            fileName = handleFileCollision(
                fileName,
                fileCollisionMethod=fileCollisionMethod)

    # Do not use encoding when writing a binary file.
    if 'b' in mode:
        encoding = None

    if os.path.exists(fileName) and mode in ['w', 'wb']:
        logging.warning('Data file %s will be overwritten!' % fileName)

    # The file wil always be opened in binary writing mode,
    # see https://docs.python.org/2/library/codecs.html#codecs.open
    f = codecs.open(fileName, mode=mode, encoding=encoding)
    return f


def genDelimiter(fileName):
    """Return a delimiter based on a filename.

    :Parameters:

    fileName : string
        The output file name.

    :Returns:

    delim : string
        A delimiter picked based on the supplied filename. This will be
        ``,`` if the filename extension is ``.csv``, and a tabulator
        character otherwise.

    """
    if fileName.endswith(('.csv', '.CSV')):
        delim = ','
    else:
        delim = '\t'

    return delim


def genFilenameFromDelimiter(filename, delim):
    # If no known filename extension was specified, derive a one from the
    # delimiter.
    if not filename.endswith(('.dlm', '.DLM', '.tsv', '.TSV', '.txt',
                              '.TXT', '.csv', '.CSV', '.psydat', '.npy',
                              '.json')):
        if delim == ',':
            filename += '.csv'
        elif delim == '\t':
            filename += '.tsv'
        else:
            filename += '.txt'

    return filename
