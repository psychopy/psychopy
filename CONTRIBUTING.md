# Have you ever contributed to an Open Source project?
If you haven't, your first contribution can be a bit intimidating. Feel free to take a chance; we would happily guide you through the process. 

The first step is discussing what you've got in mind in the [development section of the forum](https://discourse.psychopy.org/c/dev). Depending out the outcome, here is the next step:
* **I won't program it myself.** Please file a [GitHub issue](https://github.com/psychopy/psychopy/issues).
* **I'd like to take a shot.** Read on!

# How to contribute
Contributing to PsychoPy consists of four steps:
1. Getting your own copy
2. Making your changes
3. Committing your changes
4. Submitting a Pull Request

## 1. Getting your own copy of the PsychoPy codebase
To be sure your changes can easily be integrated later on, follow these steps:
1. **Make a [fork](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo) of the [PsychoPy repo](https://github.com/psychopy/psychopy).** This provides you with your own copy of the PsychoPy source code.
2. **Inside your fork, make a new [branch](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-branches) for the feature you've got in mind.** If you'd like to fix a bug, base your new branch on the *release* branch. If you'd like to add a new feature, base it on the *dev* branch.
3. **Clone your fork to your hard drive.** Next, switch to the new branch, and you're ready to program!

Look [here](https://www.psychopy.org/developers/repository.html) for more information about how the PsychoPy repo is setup.

## 2. Making your changes
We've got guides for modifying different parts of PsychoPy in the [developer documentation](https://www.psychopy.org/developers/index.html). To test your modified PsychoPy, do a [developers install](https://www.psychopy.org/download.html#developers-install).

## 3. Committing your changes
Please use the tags below in your commit, and be sure to add an informative commit message.
  - **BF:** bug fix. For fixing bugs in the *release* branch.
  - **FF:** ‘feature’ fix. For fixing bugs in the *dev* branch.
  - **RF:** refactoring
  - **NF:** new feature
  - **ENH:** enhancement (to existing code, but don't worry too much about the difference between this and NF)
  - **DOC:** for all kinds of documentation related commits
  - **TEST:** for adding or changing tests

## 4. File a Pull Request
Once you're done, it's time to add it to the central PsychoPy codebase. File a [Pull Request](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request) from your fork and your new branch to the PsychoPy repo. Be sure to target the right branch in PsychoPy (*release* or *dev*). Thanks for contributing!