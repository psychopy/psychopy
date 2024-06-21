#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This script is used to:
    - update the version numbers
    - update the psychopyVersions repo:
        - copy over the code
        - commit, tag and push(?)

    It should be run from the root of the main git repository, which should be
    next to a clone of the psychopy/versions git repository
"""
import os, sys, shutil, subprocess
from os.path import join
from createGitShaFile import createGitShaFile
from pathlib import Path

# MAIN is the root of the psychopy repo
MAIN = Path(__file__).parent.parent.parent.absolute()
# versions repo is next to MAIN
VERSIONS = MAIN.parent / 'versions'
print("Building release version from: ", MAIN)
print("To: ", VERSIONS)

if sys.platform == "darwin":
    gitgui = ["git", "gui"]
elif sys.platform == "linux":
    gitgui = ["cola"]
else:
    gitgui = ["git", "gui"]
    print("This script requires a unix-based terminal to run (for commands "
          "like `du -sck` to work)")
    sys.exit()


def getSHA(cwd='.'):
    if cwd == '.':
        cwd = os.getcwd()
    # get the SHA of the git HEAD
    SHA_string = subprocess.check_output(
        ['git', 'rev-parse', '--short', 'HEAD'],
        cwd=cwd).split()[0].decode('utf-8')

    # convert to hex from a string and return it
    print('SHA:', SHA_string, 'for repo:', cwd)
    return SHA_string


def buildRelease(versionStr, noCommit=False, interactive=True):
    #
    createGitShaFile()
    dest = VERSIONS / "psychopy"
    shutil.rmtree(dest)
    ignores = shutil.ignore_patterns("demos", "docs", "tests", "pylink",
                                     "*.pyo", "*.pyc", "*.orig", "*.bak",
                                     ".DS_Store", ".coverage")
    shutil.copytree("psychopy", dest, symlinks=False, ignore=ignores)
    os.mkdir(dest/'tests')
    shutil.copyfile("psychopy/tests/__init__.py", dest/'tests/__init__.py')
    shutil.copyfile("psychopy/tests/utils.py", dest/'tests/utils.py')

    # todo: would be nice to check here that we didn't accidentally add anything large (check new folder size)
    Mb = float(subprocess.check_output(["du", "-sck", dest]).split()[0])/10**3
    print("size for '%s' will be: %.2f Mb" %(versionStr, Mb))
    if noCommit:
        return False

    if interactive:
        ok = input("OK to continue? [n]y :")
        if ok != "y":
            return False

    lastSHA = getSHA(cwd=VERSIONS)
    print('updating: git add --all')
    output = subprocess.check_output(["git", "add", "--all"], cwd=VERSIONS)
    if interactive:
        ok = subprocess.call(gitgui, cwd=VERSIONS)
        if lastSHA == getSHA():
            # we didn't commit the changes so quit
            print("no git commit was made: exiting")
            return False
    else:
        print("committing: git commit -m 'release version %s'" %versionStr)
        subprocess.call(
            ["git", "commit", "-m", "'release version %s'" %versionStr],
            cwd=VERSIONS)

    print("tagging: git tag -m 'release %s'" %versionStr)
    ok = subprocess.call(
        ["git", "tag", versionStr, "-m", "'release %s'" %versionStr],
        cwd=VERSIONS)

    print("'versions' tags are now:", subprocess.check_output(
        ["git","tag"], cwd=VERSIONS).split())
    print('pushing: git push origin %s' %versionStr)
    output = subprocess.check_output(["git", "push", "origin", "%s" % versionStr],
                         cwd=VERSIONS)
    print(output)

    # revert the __init__ file to non-ditribution state
    print('reverting the main master branch: git checkout HEAD psychopy/__init__.py ')
    print(subprocess.check_output(
         ["git", "checkout", "HEAD", "psychopy/__init__.py"],
         cwd=MAIN))
    return True  # success


if __name__ == "__main__":
    if "--noCommit" in sys.argv:
        noCommit = True
    else:
        noCommit = False
    if "--noInteractive" not in sys.argv:
        interactive = True
    else:
        interactive = False
    # todo: update versions first
    versionStr = input("version:")
    buildRelease(versionStr, noCommit=noCommit, interactive=interactive)
