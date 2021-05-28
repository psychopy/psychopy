# Have you ever contributed to an Open Source project?
Your first contribution can be a bit intimidating, but feel free to give it a try. If you get stuck, don't hesitate to ask for help in our [developer forum](https://discourse.psychopy.org/c/dev). This is also a good place to pitch your idea. Next up:
* **I won't program it myself.** Please file a [GitHub issue](https://github.com/psychopy/psychopy/issues).
* **I'd like to take a shot.** Read on to find out how!

# How to contribute
Contributing to PsychoPy consists of four steps:
1. Getting your own copy
2. Making your changes
3. Committing your changes
4. Submitting a Pull Request

## 1. Getting your own copy of the PsychoPy codebase
To be sure your improvements can easily be integrated, follow these steps:
1. **Make a [fork](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo) of the [PsychoPy repo](https://github.com/psychopy/psychopy).** This provides you with your own copy of the PsychoPy source code.
2. **Inside your fork, make a new [branch](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-branches) for the feature you've got in mind.** If you'd like to fix a bug, base your new branch on the *release* branch. If you'd like to add a new feature, base it on the *dev* branch. We tend to name branches after the feature we're building. For example `olfactory_component`.
3. **Clone your fork to your hard drive.** Next, switch to the new branch and you're all set up!

Look [here](https://www.psychopy.org/developers/repository.html) to see how the PsychoPy repo is organized.

## 2. Making your changes
To help you get started with modifying PsychoPy, we've got some [developer guides](https://www.psychopy.org/developers/index.html). To try out your modified PsychoPy, do a [developer's install](https://www.psychopy.org/download.html#developers-install).

## 3. Committing your changes
Once you're happy with your changes, commit them to your GitHub repo. Please use the tags below in your commit and add an informative message.
  - **BF:** bug fix. For fixing bugs in the *release* branch.
  - **FF:** ‘feature’ fix. For fixing bugs in the *dev* branch.
  - **RF:** refactoring
  - **NF:** new feature
  - **ENH:** enhancement (to existing code, but don't worry too much about the difference between this and NF)
  - **DOC:** for all kinds of documentation related commits
  - **TEST:** for adding or changing tests

## 4. File a Pull Request
Once you're done, it's time to add it to the central PsychoPy source code. File a [Pull Request](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request) from your own fork and branch to the PsychoPy repo. Be sure to target the right branch in PsychoPy (*release* or *dev*). Thanks for contributing!