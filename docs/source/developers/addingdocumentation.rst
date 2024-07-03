.. _editingDocs:

Making edits to PsychoPy's documentation
=========================================

Fork your own copy of the PsychoPy repository:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make any changes to the documentation that exists on psychopy.org, you will firstly need your own copy of the PsychoPy repository. To do this, please follow these steps:

1. Create an account or sign in to GitHub.
2. Navigate to the PsychoPy repository.
3. You’ll need your own fork of the PsychoPy repository; to do this, click on the drop-down next to the Fork option and select ‘+ Create a new fork’:

.. figure:: /images/fork_psychopy.png

4. There will be a box checked by default that says ‘only fork the dev branch’ of the repository (or word to that effect). You’ll need to un-check this because it’s the release branch that you’ll need to push your changes to in order to update the current documentation.
5. Create your fork!

Create a branch to make your changes in:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It’s good practice to create a new branch of the repository for each piece of work you’re doing. For example, if you know you’ll be working on improving the clarity of the hardware documentation, you would create a branch to do this in. 

1. To create a new branch, click on the Branches icon from your copy of the PsychoPy repository:

.. figure:: /images/branches.png

2. Then, click Create New Branch. The pop-up that appears will allow you to select which branch of PsychoPy you want to use as the source for your new branch. When we’re editing documentation, we always use the release branch because this will update the pages that are written to psychopy.org. The dev branch is used for developing the next release of PsychoPy.


.. figure:: /images/create_branch.png
      :scale: 60%



Now that you have your own fork of the PsychoPy repository, and a branch to make your changes in, you can make changes to the code! 
You’ll then make a pull request so that your changes can be merged into the PsychoPy repository itself. 
There are several ways to do this, depending on the extent of the changes you wish to make. 
In this walkthrough we're imagining that you just want to make a change to a single page on the documentation, but if you want to see how to make bigger changes take a look at the other links on the :ref:`developers` page!


If you only want to change a single file:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For example, you’ve spotted a typo in one of the documentation pages, want to fix a broken link, or add in a few extra paragraphs to improve the clarity of the page. Essentially anything that involves you changing just one file. 
The easiest way to do this is directly within `GitHub <https://www.github.com>`_ itself. 

If you’re not already aware, it’s worth noting how the URLs in the documentation are linked to the folder structure of the PsychoPy repository: 
All of the documentation files are located in the folder docs > source. 
Each html page is created from a reStructured text (rst) file, and these files are stored in several folders. 
For instance, the page: https://psychopy.org/builder/routines.html is created from the routines.rst file located in: docs/source/builder. 

**Let’s imagine that you want to change that routines.rst file:**

1. In your fork of the PsychoPy repository, click through to the routines.rst file located in: docs/source/builder and click on the ‘edit’ pencil icon:

.. figure:: /images/edit_rst.png

2. Make the changes you need to.
3. Click on the ‘Commit changes…’ button that becomes active when you’ve made changes:

.. figure:: /images/commit_changes_rst.png

4. Add a commit message: For documentation changes we use ‘DOC:’ followed by a brief description of what we’ve changed (see :ref:`usingRepos` for more on commit messages):

.. figure:: /images/rename_commit.png
      :scale: 60%

5. Commit your changes: This commits the changes you’ve made to your PsychoPy repository. You now need to make a pull request so that those changes can be merged into the main PsychoPy repository. 

Make a pull request:
~~~~~~~~~~~~~~~~~~~~~

1. Click back into your main PsychoPy repository:

.. figure:: /images/back_to_psychopy.png

2. Click on the message that says ‘Compare and pull request’:

.. figure:: /images/comp_pr.png

3. As you want to contribute to the documentation on the website, you’ll need to select ‘release’ as your base branch:

.. figure:: /images/choose_base.png

4. Make sure the title of your pull request matches the one that you put as your commit message. You can add a description of your changes if you like, too. Then click ‘Create pull request’:

.. figure:: /images/create_pr.png

5. You’ve made a pull request! Your code will be reviewed, and you’ll receive an email when your changes have been pulled in!
