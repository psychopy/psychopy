#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Writes the current version, build platform etc.
"""

from semanticVersion import getSemanticVersion, getLastCommit
from pathlib import Path

root = Path(__file__).parent.parent  # root of the repo

def updateVersionFile():
    """Take psychopy/VERSION, append the branch and distance to commit
    and update the VERSION file accordingly"""
    raw = (root/'psychopy/VERSION').read_text().strip()
    version = getSemanticVersion()
    if version != raw:
        (root/'psychopy/VERSION').write_text(version)
        print(f"Updated version file to {version}")

def updateGitShaFile(sha=None):
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
    shaPath = root/"psychopy/GIT_SHA"
    if sha is None:
        sha = getLastCommit() or 'n/a'
    with open(shaPath, 'w') as f:
        f.write(sha)
        print(f"Created file: {shaPath.absolute()}")

if __name__ == "__main__":
    updateGitShaFile()
    updateVersionFile()
