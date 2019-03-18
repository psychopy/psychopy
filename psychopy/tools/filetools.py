#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to file and directory handling
"""
from __future__ import absolute_import, print_function

# from future import standard_library
# standard_library.install_aliases()
import os
import shutil
import sys
import atexit
import codecs
import numpy as np
import json
import json_tricks

try:
    import cPickle as pickle
except ImportError:
    import pickle

from psychopy import logging, constants
from psychopy.tools.fileerrortools import handleFileCollision


def toFile(filename, data):
    """Save data (of any sort) as a pickle file.

    simple wrapper of the cPickle module in core python
    """
    f = open(filename, 'wb')
    pickle.dump(data, f)
    f.close()


def fromFile(filename, encoding='utf-8'):
    """Load data from a pickle or JSON file.

    Parameters
    ----------
    encoding : str
        The encoding to use when reading a JSON file. This parameter will be
        ignored for any other file type.

    """
    filename = pathToString(filename)
    if filename.endswith('.psydat'):
        with open(filename, 'rb') as f:
            contents = pickle.load(f)
            # if loading an experiment file make sure we don't save further
            # copies using __del__
            if hasattr(contents, 'abort'):
                contents.abort()
    elif filename.endswith('.json'):
        with codecs.open(filename, 'r', encoding=encoding) as f:
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
                   encoding='utf-8-sig'):
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
    fileName = pathToString(fileName)
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
    fileName = pathToString(fileName)
    if fileName.endswith(('.csv', '.CSV')):
        delim = ','
    else:
        delim = '\t'

    return delim


def genFilenameFromDelimiter(filename, delim):
    # If no known filename extension was specified, derive a one from the
    # delimiter.
    filename = pathToString(filename)
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


class DictStorage(dict):
    """Helper class based on dictionary with storage to json
    """

    def __init__(self, filename, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.filename = filename
        self.load()
        self._deleted = False
        atexit.register(self.__del__)

    def load(self, filename=None):
        """Load all tokens from a given filename
        (defaults to ~/.PsychoPy3/pavlovia.json)
        """
        if filename is None:
            filename = self.filename
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                try:
                    self.update(json.load(f))
                except ValueError:
                    logging.error("Tried to load %s but it wasn't valid "
                                  "JSON format"
                                  %filename)

    def save(self, filename=None):
        """Save all tokens from a given filename
        (defaults to the filename given to the class but can be overridden)
        """
        if filename is None:
            filename = self.filename
        # make sure the folder exists
        folder = os.path.split(filename)[0]
        if not os.path.isdir(folder):
            os.makedirs(folder)
        # save the file as json
        with open(filename, 'wb') as f:
            json_str = json.dumps(self, indent=2, sort_keys=True)
            if constants.PY3:
                f.write(bytes(json_str, 'UTF-8'))
            else:
                f.write(json_str)

    def __del__(self):
        if not self._deleted:
            self.save()
        self._deleted = True


class KnownProjects(DictStorage):
    def save(self, filename=None):
        """Purge unnecessary projects (without a local root) and save"""
        toPurge = []
        for projname in self:
            proj = self[projname]
            if not proj['localRoot']:
                toPurge.append(projname)
        for projname in toPurge:
            del self[projname]
        DictStorage.save(self, filename)


def pathToString(filepath):
    """
    Coerces pathlib Path objects to a string (only python version 3.6+)
    any other objects passed to this function will be returned as is.
    This WILL NOT work with on Python 3.4, 3.5 since the __fspath__ dunder
    method did not exist in those verisions, however psychopy does not support
    these versions of python anyways.

    :Parameters:

    filepath : str or pathlib.Path
        file system path that needs to be coerced into a string to
        use by Psychopy's internals

    :Returns:

    filepath : str or same as input object
        file system path coerced into a string type
    """
    if hasattr(filepath, "__fspath__"):
        return filepath.__fspath__()
    return filepath
