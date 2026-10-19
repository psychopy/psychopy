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
Once you're happy with your changes, commit them to your GitHub repo. Please use the tags below in your commit and add an informative message:

- `fix` : Bug fix
- `refactor` : Restructuring code
- `feat` : Add a new feature or improvement
- `docs`: Any changes to documentation (including comments, demos and function docstrings)
- `test`: Any changes to the test suite
- `chore`: Changes to processes, actions, etc. (devops stuff, basically)

You can add the following after the tag (before the `:`) to give more specific detail:

- `(reg)` : Regression scope - indicates that you are fixing/improving something unreleased, e.g. `fix(reg): Forgot to delete print statement from debugging a new feature`
- `!` : Breaking change - indicates that this change may break users' existing experiments, e.g. `refactor!: Completely rearrange everything`

You can also indicate a breaking change by adding BREAKING CHANGE: to the commit footer. For more information on the structure of commit messages, check out the [Conventional Commits](https://conventionalcommits.org/) specification.

## 4. File a Pull Request
Once you're done, it's time to add it to the central PsychoPy source code. File a [Pull Request](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request) from your own fork and branch to the PsychoPy repo. Be sure to target the right branch in PsychoPy (*release* or *dev*). Thanks for contributing!