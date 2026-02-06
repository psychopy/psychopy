
from subprocess import run
import pathlib
from packaging import version

root = pathlib.Path(__file__).parent.parent  # root of the repo
VERBOSE = True


def _call(cmd, verbose=False):
    result = run(cmd, capture_output=True, text=True)
    if verbose or result.returncode or result.stderr:
        print(f"Call:\n  {' '.join(cmd)}")
        print(f"Resulted in:\n  {result.stdout + result.stderr}")
        return None
    else:
        return result.stdout.strip()

def _checkValidVersion(v):
    """Check if version string is valid and return True/False"""
    try:
        version.Version(v)
    except version.InvalidVersion:
        print(f"Invalid version: {v}")
        return False
    return True

def getGitDescribe(tag=None):
    if tag:
        return _call(["git", "describe", "--tags", "--long", "--always", tag])
    else:
        # If no tag is provided, use the most recent tag
        return _call(["git", "describe", "--tags", "--long", "--always"])
    
def countSince(ref):
    """Get number of commits since given commit/tag"""

    """Get the number of commits since the specified tag. But can also
    give the number *prior* to the tag if it is behind."""
    # Get the number of commits since the specified tag
    nAhead = int(_call(["git", "rev-list", "--count", f"{ref}..HEAD"]))
    if nAhead > 0:
        return int(nAhead)
    else:
        nBehind = int(_call(["git", "rev-list", "--count", f"HEAD..{ref}"]))
        if nBehind:
            return -int(nBehind)
        else:
            return 0  # it isn't ahead or behind

def getLastCommit(filepath=None):
    """Get SHA of last commit that touched given file or last commit in repo"""
    if filepath:
        cmd = ['git', 'log', '-n', '1', '--pretty=format:%H', filepath]
    else:
        cmd = ['git', 'log', '-n', '1', '--pretty=format:%H']
    return _call(cmd)

def getBranch():
    """Get current branch name"""
    cmd = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
    resp = _call(cmd)
    if resp is None:
        return ''
    return resp

def getTags():
    """Get list of tags"""
    cmd = ['git', 'tag', '--sort=-v:refname']
    resp = _call(cmd)
    if resp is None:
        return []
    return resp.split()

def getTag(tag_name):
    """Return tag if it exists, otherwise None"""
    return _call(["git", "tag", "-l", tag_name])

def getLastTag(commit="HEAD"):
    """Get the most recent tag reachable from the specified commit."""
    return _call(["git", "describe", "--tags", "--abbrev=0", commit])

def isShallowRepo():
    """Check if git repo is shallow (or not a repo)"""
    cmd = ['git', 'rev-parse', '--is-shallow-repository']
    resp = _call(cmd)
    return resp is None or resp=='true'

def getSemanticVersion():
    """Get semantic version number from psychopy/VERSION, tags and branch"""

    raw = (root/'psychopy/VERSION').read_text().strip()
    if isShallowRepo():
        print("Can't calculate good version number in shallow repo. "
              "Did you fetch with `git clone --depth=1`?\n"
              f"Using hardcoded version number ({raw})")
        return ''
    # validate the psychopy/VERSION file with packaging.version.Version
    try:
      origVersion = version.Version(raw)
    except version.InvalidVersion:
        raise version.InvalidVersion("Can't create valid version from invalid starting point:\n"
                                     "  {raw}")
    vernum = origVersion.base_version  # removing things like the dev21 or post3
    
    branch = getBranch()

    tag = getTag(vernum)
    label = ""  # will be "dev", "rc", "", or "post"
    if branch == "release":
        if tag:  # this version label is tagged
            # use that version tag to describe
            describe = getGitDescribe(tag)
            nCommits = countSince(tag)
            if nCommits < 0:
                # This was before the release, so an rc
                label = "rc"
                # get the number of commits since the PREV tag
                tag = getLastTag(tag)
                nCommits = countSince(tag)
                if VERBOSE:
                    print(f"Found tag for '{vernum}' after after current. Currently we are {nCommits} commits ahead of {tag}")
            elif nCommits == 0:
                # This is the release version
                label = ""
                if VERBOSE:
                    print(f"This ref is matching tag '{tag}'")
            else:
                # This is a post-release version and nCommits is already correct
                label = "post"
                if VERBOSE:
                    print(f"Found tag for '{vernum}' and we are currently {nCommits} commits ahead")

        # get n from prev tag an count forwards
        else:
            # If no tag exists, we need to get the number of commits since the last tag
            describe = getGitDescribe()
            parts = describe.split('-')
            nCommits = parts[1]
            label = "rc"  # release candidate because this is release branch and version not yet tagged
            if len(parts) >= 3:
                tag = parts[0]
                nCommits = int(parts[1])
            else:
                tag = describe  # In case no tag exists
                nCommits = 0
            if VERBOSE:
                print(f"No tag for '{vernum}' but we are currently {nCommits} commits ahead of {tag}")

    else:
        # all other branches labelled "dev" with commits since last tag
        # if tag exists then dev branch is ahead of tag. Need version.txt update?
        tag = getTag(vernum)
        if tag:
            label="post"
            # If tag exists, we need to get the number of commits since the last tag
            describe = getGitDescribe(tag)
            nCommits = countSince(tag)
            if VERBOSE:
                print(f"Found tag for '{vernum}' and we are currently {nCommits} commits ahead")
        else:
            # If no tag exists, we need to get the number of commits since the last tag
            label = "dev"
            describe = getGitDescribe()
            parts = describe.split('-')
            nCommits = parts[1]
            if len(parts) >= 3:
                tag = parts[0]
                nCommits = int(parts[1])
            else:
                tag = None
            if VERBOSE:
                print(f"No tag for '{vernum}' but we are currently {nCommits} commits ahead of {tag}")

    # we have the info so build the version string
    if nCommits == 0:
        verStr = vernum
    else:
        verStr = f"{vernum}{label}{nCommits}"
    if not tag:
        tag = "None"  # just to look nicer in the printout
    print(f"Branch: {branch}, Vernum: {vernum}, Closest-tag: {tag}, Describe: {describe}\n Full semantic version: {verStr}")
    return verStr
    
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
    # Get the semantic version
    semver = getSemanticVersion()
    print(semver)
    
    # Check if the version is valid
    if not _checkValidVersion(semver):
        print("Invalid version string")

    # use argparse to handle command line arguments
    import argparse
    # add argument to write the version file
    parser = argparse.ArgumentParser(description="Get semantic version and update files.")
    parser.add_argument('--write-version', action='store_true',
                        help="Write the semantic version to the VERSION file.")
    parser.add_argument('--write-git-sha', action='store_true',
                        help="Write the last commit SHA to the GIT_SHA file.")
    args = parser.parse_args()
    if args.write_version:
        updateVersionFile()
    if args.write_git_sha:
        updateGitShaFile()
    