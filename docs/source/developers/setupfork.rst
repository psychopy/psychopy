.. _forkPsychoPy

Create a fork of |PsychoPy|
==================================================

Fork your own copy of the PsychoPy repository:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make any changes to the documentation that exists on psychopy.org, you will firstly need your own copy of the PsychoPy repository. To do this, please follow these steps:

1. Create an account or sign in to GitHub.
2. Navigate to the PsychoPy repository.
3. You'll need your own fork of the PsychoPy repository; to do this, click on the drop-down next to the Fork option and select ‘+ Create a new fork':

.. figure:: /images/fork_psychopy.png

4. There will be a box checked by default that says ‘only fork the dev branch' of the repository (or word to that effect). You'll need to un-check this because it's the release branch that you'll need to push your changes to in order to update the current documentation.
5. Create your fork!

Create a branch to make your changes in:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's good practice to create a new branch of the repository for each piece of work you're doing. For example, if you know you'll be working on improving the clarity of the hardware documentation, you would create a branch to do this in. 

1. To create a new branch, click on the Branches icon from your copy of the PsychoPy repository:

.. figure:: /images/branches.png

2. Then, click Create New Branch. The pop-up that appears will allow you to select which branch of PsychoPy you want to use as the source for your new branch. When we're editing documentation, we always use the release branch because this will update the pages that are written to psychopy.org. The dev branch is used for developing the next release of PsychoPy.


.. figure:: /images/create_branch.png
      :scale: 60%

Now that you have your own fork of the PsychoPy repository, and a branch to make your changes in, you can make changes to the code! 
You'll then make a pull request so that your changes can be merged into the PsychoPy repository itself. 
There are several ways to do this, depending on the extent of the changes you wish to make. 
In this walkthrough we're imagining that you just want to make a change to a single page on the documentation, but if you want to see how to make bigger changes take a look at the other links on the :ref:`developers` page!