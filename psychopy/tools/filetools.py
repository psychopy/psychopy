#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Functions and classes related to file and directory handling'''

import os
import shutil
import cPickle
import sys
import codecs
from psychopy import logging
from psychopy.tools.fileerrortools import handleFileCollision


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


def openOutputFile(fileName, append=False, delim=None,
                   fileCollisionMethod='rename', encoding='utf-8'):
    """
    Open an output file (or standard output) for writing.

    :Parameters:
    fileName : string
        The desired output file name.
    append : bool, optional
        If ``True``, append data to an existing file; otherwise, overwrite
        it with new data.
        Defaults to ``True``, i.e. appending.
    delim : string, optional
        The delimiting character(s) between values. For a CSV file, this
        would be a comma. For a TSV file, it would be ``\t``.
        Defaults to ``None``.
    fileCollisionMethod : string, optional
        How to handle filename collisions. This is ignored if ``append``
        is set to ``True``.
        Defaults to `rename`.
    encoding : string, optional
        The encoding to use when writing the file.
        Defaults to ``'utf-8'``.

    :Returns:
    f : file
        A writable file handle.

    :Notes:
    If no known filename extension is given, and the delimiter is a comma,
    the extension ``.csv`` will be chosen automatically. If the extension
    is unknown and the delimiter is a tab, the extension will be
    ``.tsv``. ``.txt`` will be chosen otherwise.

    """

    if fileName == 'stdout':
        f = sys.stdout
        return f

    if delim is None:
        genDelimiter(fileName)

    if not fileName.endswith(('.dlm', '.DLM', '.tsv', '.TSV', '.txt',
                              '.TXT', '.csv', '.CSV', '.psydat', '.npy')):
        if delim == ',':
            fileName += '.csv'
        elif delim == '\t':
            fileName += '.tsv'
        else:
            fileName += '.txt'

    if append:
        writeFormat = 'a'
    else:
        if fileName.endswith(('.psydat', '.npy')):
            writeFormat = 'wb'
        else:
            writeFormat = 'w'

        # Rename the output file if a file of that name already exists
        #  and it should not be appended.
        if os.path.exists(fileName) and not append:
            fileName = handleFileCollision(
                fileName,
                fileCollisionMethod=fileCollisionMethod
            )

    if os.path.exists(fileName) and writeFormat in ['w', 'wb']:
        logging.warning('Data file, %s will be overwritten!' % fileName)

    f = codecs.open(fileName, writeFormat, encoding=encoding)
    return f


def genDelimiter(fileName):
    """
    Return a delimiter based on a filename.

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
