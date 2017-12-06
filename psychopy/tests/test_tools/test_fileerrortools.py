#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import os
import shutil
from tempfile import mkstemp, mkdtemp, NamedTemporaryFile

from psychopy.tools.fileerrortools import handleFileCollision


def test_handleFileCollision_overwrite():
    _, path = mkstemp()
    handled_path = handleFileCollision(fileName=path,
                                       fileCollisionMethod='overwrite')

    assert path == handled_path


def test_handleFileCollision_fail():
    _, path = mkstemp()

    with pytest.raises(IOError):
        handleFileCollision(fileName=path,
                            fileCollisionMethod='fail')


def test_handleFileCollision_rename_file_does_not_exist():
    temp_dir = mkdtemp()

    # Create temporary file and close it (to destroy it). We simply use this
    # procedure to grab a unique file name.
    with NamedTemporaryFile(dir=temp_dir) as f:
        path = f.name

    handled_path = handleFileCollision(fileName=path,
                                       fileCollisionMethod='rename')
    assert path == handled_path


def test_handleFileCollision_rename_file_exists():
    temp_dir = mkdtemp()

    # Create temporary file and close it (to destroy it). We simply use this
    # procedure to grab a unique file name.
    with NamedTemporaryFile(dir=temp_dir, suffix='.xyz') as f:
        path = f.name

        handled_path = handleFileCollision(fileName=path,
                                           fileCollisionMethod='rename')
    filename, suffix = os.path.splitext(path)
    expected_path = '%s_1%s' % (filename, suffix)

    assert handled_path == expected_path
    os.rmdir(temp_dir)


def test_handleFileCollision_rename_multiple_files_exists():
    temp_dir = mkdtemp()
    path = os.path.join(temp_dir, 'test.txt')

    filename, suffix = os.path.splitext(path)

    # Create a file to start with.
    with open(path, 'w') as f:
        f.write('foo')

    # Now handle collisions of files with the same name.
    for i, _ in enumerate(range(10), start=1):
        handled_path = handleFileCollision(fileName=path,
                                           fileCollisionMethod='rename')

        expected_path = '%s_%i%s' % (filename, i, suffix)
        assert handled_path == expected_path

        # We need to write something to the file to create it.
        with open(handled_path, 'w') as f:
            f.write('foo')

    shutil.rmtree(temp_dir)


def test_handleFileCollision_invalid_method():
    _, path = mkstemp()

    with pytest.raises(ValueError):
        handleFileCollision(fileName=path,
                            fileCollisionMethod='invalid_value')


if __name__ == '__main__':
    test_handleFileCollision_overwrite()
    test_handleFileCollision_fail()
    test_handleFileCollision_rename_file_does_not_exist()
    test_handleFileCollision_rename_file_exists()
    test_handleFileCollision_rename_multiple_files_exists()
    test_handleFileCollision_invalid_method()
