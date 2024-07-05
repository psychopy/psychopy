#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Writes the current version, build platform etc.
"""


def createGitShaFile(dist=None, version=None, sha=None):
    """Create psychopy/GIT_SHA

    :param:`dist` can be:
        None:
            writes __version__
        'sdist':
            for python setup.py sdist - writes git id (__git_sha__)
        'bdist':
            for python setup.py bdist - writes git id (__git_sha__)
            and __build_platform__
    """

    import os
    from pathlib import Path
    import setuptools_git_versioning as git_vers

    root = Path(__file__).parent.parent
    shaPath = root/"psychopy/GIT_SHA"
    if sha is None:
        from subprocess import check_output, PIPE
        # see if we're in a git repo and fetch from there
        try:
            output = check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                cwd=root, stderr=PIPE)
        except Exception:
            output = False
        if output:
            __git_sha__ = output.strip()  # remove final linefeed
            
        sha = git_vers.get_sha() or 'n/a'
    with open(shaPath, 'w') as f:
        f.write(sha)
    print(f"Created file: {shaPath.absolute()}")

if __name__ == "__main__":
    createGitShaFile()
