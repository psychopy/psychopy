#!python

"""This script is used to:
    - update the version numbers
    - update the psychopyVersions repo:
        - copy over the code
        - commit, tag and push(?)

    It should be run from the root of the main git repository, which should be
    next to a clone of the psychopy/releases git repository
"""

import os, sys, shutil, subprocess
from os.path import join

def getSHA():
    #get the SHA of the git HEAD
    SHA_string = subprocess.check_output(['git', 'rev-parse', 'HEAD']).split()[0]
    #convert to hex from a string and return it
    return hex(int(SHA_string, 16))

def buildRelease(versionStr, noCommit=False, interactive=True):
    #
    dest = join("..","releases","psychopy")
    shutil.rmtree(dest)
    ignores = shutil.ignore_patterns("demos", "docs", "tests", "pylink",
                                     "*.pyo", "*.pyc", "*.orig", "*.bak",
                                     ".DS_Store", ".coverage")
    shutil.copytree("psychopy", dest, symlinks=False, ignore=ignores)

    #if making a release from previous versions (jon only) then we need to patch in the version chooser
    if not os.path.isfile(join(dest,'tools','versionchooser.py')):
        shutil.copyfile("/home/lpzjwp/code/versionchooser.py", join(dest,'tools','versionchooser.py'))
        initFile = open(join(dest,'__init__.py'), 'a') #append to the end of the file
        initFile.write("\nfrom .tools.versionchooser import useVersion\n\n")
        initFile.close()

    #todo: would be nice to check here that we didn't accidentally add anything large (check new folder size)
    Mb = float(subprocess.check_output(["du", "-bsc", dest]).split()[0])/10**6
    print "size for '%s' will be: %.2f Mb" %(versionStr, Mb)
    if noCommit:
        return False

    if interactive:
        ok = raw_input("OK to continue? [n]y :")
        if ok != "y":
            return False

    os.chdir(dest)
    lastSHA = getSHA()
    print 'updating: git add --all'
    subprocess.call(["git", "add", "--all"])
    if interactive:
        ok = subprocess.call(["cola"])
        if lastSHA==getSHA():
            #we didn't commit the changes so quit
            print("no git commit was made: exiting")
            return False
    else:
        print "committing: git commit -m 'candidate for %s'" %versionStr
        subprocess.call(["git", "commit", "-m", "'candidate for %s'" %versionStr])

    print "tagging: git tag -m 'release %s'" %versionStr
    ok = subprocess.call(["git", "tag", versionStr, "-m", "'release %s'" %versionStr])

    print "tags are now:", subprocess.check_output(["git","tag"]).split()
    return True #success

if __name__=="__main__":
    if "--noCommit" in sys.argv:
        noCommit = True
    else:
        noCommit = False
    #todo: update versions first
    versionStr = raw_input("version:")
    buildRelease(versionStr, noCommit=noCommit, interactive=True)
