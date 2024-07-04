
def _branchFormatter(name):
    """Receives name of this git branch (from setuptools-git-versioning) and
    returns the relevant release tag"""
    # see https://setuptools-git-versioning.readthedocs.io/en/stable/options/branch_formatter.html
    print("THIS:", name)
    if name == "release":
        return "post"  # so we get 2024.2.1post4+4ea4af for post-release
    else:
        return "dev"  # so we get 2024.2.2dev4+4ea4af for pre-release