.. _developers:

For Developers
=====================================

There is a separate mailing list to discuss development ideas and issues.

For developers the best way to use PsychoPy is to install a version to your own copy of python (preferably 2.6 but 2.5 is OK). Make sure you have all the :ref:`dependencies`, including the extra :ref:`recommendedPackages` for developers.

Don't *install* PsychoPy. Instead fetch a copy of the git repository and add this to the python path using a .pth file. This way you can fe

Using the repository
------------------------------

Create your own fork of the central repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Go to `github <www.github.com>`, create an account and make a fork of the `psychopy repository <https://github.com/psychopy/psychopy>`_
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

Fixing bugs and making minor improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can make minor changes directly in the `master` branch of your fork. After making a change you need to:

    - commit your changes to the local repository
    - push the local changes back to your fork at github (so that you can share them)
    