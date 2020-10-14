.. _usingRepos:

Using the repository
------------------------------

.. note::

    Much of the following is explained with more detail in the `nitime documentation
    <http://nipy.sourceforge.net/nitime/devel/git_development.html>`_, 
    and then in further detail in numerous online tutorials.

Workflow
~~~~~~~~~~

The use of git and the following workflow allows people to contribute changes that can easily be incorporated back into the project, while (hopefully) maintaining order and consistency in the code. All changes should be tracked and reversible.

- Create a fork of the central psychopy/psychopy repository
- Create a local clone of that fork
- For small changes
    - make the changes directly in the master branch
    - push back to your fork
    - submit a pull request to the central repository
- For substantial changes (new features)
    - create a branch
    - when finished run unit tests
    - when the unit tests pass, submit a pull request to the central repository

.. createClone:

Create your own fork of the central repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Go to `github <http://www.github.com>`_, create an account and make a fork of the `psychopy repository <https://github.com/psychopy/psychopy>`_
You can change your fork in any way you choose without it affecting the central project. You can also share your fork with others, including the central project.

Fetch a local copy
~~~~~~~~~~~~~~~~~~~~
`Install git on your computer <http://book.git-scm.com/2_installing_git.html>`_. 
Create and upload an ssh key to your github account - this is necessary for you to push changes back to your fork of the project at github.

Then, in a folder of your choosing fetch your fork::

    $ git clone git@github.com:USER/psychopy.git
    $ cd psychopy
    $ git remote add upstream git://github.com/psychopy/psychopy.git

The last line connects your copy (with read access) to the central server so you can easily fetch any updates to the central repository.

Fetching the latest version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Periodically it's worth fetching any changes to the central psychopy repository (into your `master` branch, more on that below)::

    $ git checkout master
    $ git pull upstream master  # here 'master' is the desired branch of psychopy to fetch

Run PsychoPy using your local copy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Now that you've fetched the latest version of psychopy using git, you should run this version in order to try out yours/others latest improvements. See `this guide <http://www.ehow.com/how_8510325_set-python-path.html>`_ on how to permanently run your git version of psychopy instead of the version you previously installed.

*Run git version for just one session (Linux and Mac only)*:
If you want to switch between the latest-and-greatest development version from git and the stable version installed on your system, you can choose to only temporarily run the git version. Open a terminal and set a temporary python path to your psychopy git folder::

	$ export PYTHONPATH=/path/to/local/git/folder/

To check that worked you should open python in the terminal and try to import psychopy::

	$ python
	Python 2.7.6 (default, Mar 22 2014, 22:59:56) 
	[GCC 4.8.2] on linux2
	Type "help", "copyright", "credits" or "license" for more information.
	>>> import psychopy

PsychoPy depends on a lot of other packages and you may get a variety of failures to import them until you have them all installed in your custom environment!

Fixing bugs and making minor improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can make minor changes directly in the `master` branch of your fork. After making a change you need to `commit` a set of changes to your files with a message. This enables you to group together changes and you will subsequently be able to go back to any previous `commit`, so your changes are reversible.

I (Jon) usually do this by opening the graphical user interface that comes with git::

    $ git gui
    
From the GUI you can select (or `stage` in git terminology) the files that you want to include in this particular `commit` and give it a message. Give a clear summary of the changes for the first line. You can add more details about the changes on lower lines if needed.

If you have internet access then you could also push your changes back up to your fork (which is called your `origin` by default), either by pressing the `push` button in the GUI or by closing that and typing::

    $ git push
    
Commit messages
~~~~~~~~~~~~~~~~~~~~~
Informative commit messages are really useful when we have to go back through the repository finding the time that a particular change to the code occurred. Precede your message with one or more of the following to help us spot easily if this is a bug fix (which might need pulling into other development branches) or new feature (which we might want to avoid pulling in if it might disrupt existing code).

* *BF* : bug fix
* *FF* : 'feature' fix. This is for fixes to code that hasn't been released
* *RF* : refactoring
* *NF* : new feature
* *ENH* : enhancement (improvement to existing code)
* *DOC*: for all kinds of documentation related commits
* *TEST*: for adding or changing tests

When making commits that fall into several commit categories (e.g., BF and TEST), **please make separate commits for each category** and **avoid concatenating commit message prefixes**. E.g., please do not use `BF/TEST`, because this will affect how commit messages are sorted when we pull in fixes for each release.

NB: The difference between BF and FF is that BF indicates a fix that is appropriate for back-porting to earlier versions, whereas FF indicates a fix to code that has not been released, and so cannot be back-ported.

.. _pullRequest:

Share your improvement with others
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Only a couple of people have direct write-access to the psychopy repository, but you can get your changes included in `upstream` by pushing your changes back to your github fork and then `submitting a pull request <http://nipy.sourceforge.net/nitime/devel/development_workflow.html#asking-for-your-changes-to-be-merged-with-the-main-repo>`_. Communication is good, and hopefully you have already been in touch (via the user or dev lists) about your changes.

When adding an improvement or new feature, consider how it might impact others. Is it likely to be generally useful, or is it something that only you or your lab would need? (It's fun to contribute, but consider: does it actually need to be part of PsychoPy?) Including more features has a downside in terms of complexity and bloat, so try to be sure that there is a "business case" for including it. If there is, try at all times to be backwards compatible, e.g., by adding a new keyword argument to a method or function (not always possible). If it's not possible, it's crucial to get wider input about the possible impacts. Flag situations that would break existing user scripts in your commit messages.

Part of sharing your code means making things sensible to others, which includes good coding style and writing some documentation. You are the expert on your feature, and so are in the best position to elaborate nuances or gotchas. Use meaningful variable names, and include comments in the code to explain non-trivial things, especially the intention behind specific choices. Include or edit the appropriate doc-string, because these are automatically turned into API documentation (via sphinx). Include doc-tests if that would be meaningful. The existing code base has a comment / code ratio of about 28%, which earns it high marks. 

For larger changes and especially new features, you might need to create some usage examples, such as a new Coder demo, or even a Builder demo. These can be invaluable for being a starting point from which people can adapt things to the needs of their own situation. This is a good place to elaborate usage-related gotchas.

In terms of style, try to make your code blend in with and look like the existing code (e.g., using about the same level of comments, use camelCase for var names, despite the conflict with the usual PEP -- we'll eventually move to the underscore style, but for now keep everything consistent within the code base). In your own code, write however you like of course. This is just about when contributing to the project.

.. _addFeatureBranch:

Add a new feature branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For more substantial work, you should create a new branch in your repository. Often while working on a new feature other aspects of the code will get broken and the `master` branch should always be in a working state. To create a new branch::

    $ git branch feature-somethingNew

You can now switch to your new feature branch with::

    $ git checkout feature-somethingNew
    
And get back to your `master` branch with::

    $ git checkout master
    
You can push your new branch back to your fork (`origin`) with::

    $ git push origin feature-somethingNew

Completing work on a feature
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When you're done run the unit tests for your feature branch. Set the `debug` preference setting (in the app section) to True, and restart psychopy. This will enable access to the test-suite. In debug mode, from the Coder (not Builder) you can now do Ctrl-T / Cmd-T (see Tools menu, Unit Testing) to bring up the unit test window. You can select a subset of tests to run, or run them all.

It's also possible to run just selected tests, such as doctests within a single file. From a terminal window::

    cd psychopy/tests/  #eg /Users/jgray/code/psychopy/psychopy/tests
    ./run.py path/to/file_with_doctests.py

If the tests pass you hopefully haven't damaged other parts of PsychoPy (!?). If possible add a unit test for your new feature too, so that if other people make changes they don't break your work!

You can merge your changes back into your master branch with::

    $ git checkout master
    $ git merge feature-somethingNew

Merge conflicts happen, and need to be resolved.  If you configure your git preferences (~/.gitconfig) to include::

    [merge]
        summary = true
        log = true
        tool = opendiff

then you'll be able to use a handy GUI interface (opendiff) for reviewing differences and conflicts, just by typing::

    git mergetool

from the command line after hitting a merge conflict (such as during a `git pull upstream master`).

Once you've folded your new code back into your master and pushed it back to your github fork then it's time to :ref:`pullRequest`.
