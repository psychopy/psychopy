.. _developers:

For Developers
=====================================

There is a separate mailing list to discuss development ideas and issues.

For developers the best way to use PsychoPy is to install a version to your own copy of python (preferably 2.6 but 2.5 is OK). Make sure you have all the :ref:`dependencies`, including the extra :ref:`recommendedPackages` for developers.

Don't *install* PsychoPy. Instead fetch a copy of the git repository and add this to the python path using a .pth file. Other users of the computer might have their own standalone versions installed without your repository version touching them.

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
        - when the unit tests pass merge changes back into the `master` branch
        - submit a pull request to the central repository
        - 
.. createClone:

Create your own fork of the central repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Go to `github <http://www.github.com>`_, create an account and make a fork of the `psychopy repository <https://github.com/psychopy/psychopy>`_
You can change this fork in any way you choose without it affecting the central project. You can also share your fork with others.

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
    $ git pull upstream

Fixing bugs and making minor improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can make minor changes directly in the `master` branch of your fork. After making a change you need to `commit` a set of changes to your files with a message. This enables you to group together changes and you will subsequently be able to go back to any previous `commit`, so your changes are reversible.

I (Jon) usually do this by opening the graphical user interface that comes with git::

    $ git gui
    
From the GUI you can select (or `stage` in git terminology) the files that you want to include in this particular `commit` and give it a message. Give a clear summary of the changes for the first line. You can add more details about the changes on lower lines if needed.

If you have internet access then you could also push your changes back up to your fork (which is called your `origin` by default), either by pressing the `push` button in the GUI or by closing that and typing::

    $ git push

.. _pullRequest:

Share your improvement with others
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Only a couple of people have direct write-access to the psychopy repository, but you can get your changes included in `upstream` by pushing your changes back to your github fork and then `submitting a pull request <http://nipy.sourceforge.net/nitime/devel/development_workflow.html#asking-for-your-changes-to-be-merged-with-the-main-repo>`_. 

Creating a new feature branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For more substantial work, you should create a new branch in your repository. Often whle working on a new feature other aspects of the code will get broken and the `master` branch should always be in a working state. To create a new branch::

    $ git branch feature-somethingNew

You can now switch to your new feature branch with::

    $ git checkout feature-somethingNew
    
And get back to your `master` branch with::

    $ git checkout master
    
You can push your new branch back to your fork (`origin`) with::

    $ git push origin feature-somethingNew

Completing work on a feature
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When you're done run the unit tests for your feature branch. If they pass you hopefully haven't damaged other parts of PsychoPy (!?). If possible add a unit test for your new feature too, so that if other people make changes they don't break your work!

You can merge your changes back into your master branch with::

    $ git checkout master
    $ git merge feature-somethingNew

Once you've folded your new code back into your master and pushed it back to your github fork then it's time to :ref:`pullRequest`.

Happy Coding Folks!!

