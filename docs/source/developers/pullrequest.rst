Creating a pull request on GitHub
===============================================================

Submitting a pull request means that you're asking for on your own :ref:`fork <createClone>` of |PsychoPy| to be "pulled in" to the main code - essentially, taking all of the changes on that fork and applying them. To open a pull request...

#. Go to the `|PsychoPy| repository on GitHub <https://github.com/psychopy/psychopy>`_
#. Open the "Pull Requests" tab
#. Click "New pull request"
#. Click the link near the top which says "compare across forks"
#. On the left, choose the branch of `psychopy/psychopy` which you'd like to pull into; :ref:`click here for more information on what the branches mean <gitWorkflow>`
#. On the right, choose the branch of your fork which you'd like to merge into the main code
   .. warning::
       Make sure your branch was based off of the branch you're pulling into - so that you don't accidentally pull the entirety of one branch into another!
#. Check that the commits and changes shown below are the ones you're intending to make, then click "Create pull request"
#. Give your pull request a name - this will appear in the `release notes <https://github.com/psychopy/psychopy/releases>`_, so try to make it informative and concise, but still understandable to a novice user
   .. note::
       Adding a prefix to your pull request title in line with our :ref:`commit conventions <_commitMessages>` makes it easier for to sort pull requests when writing the release notes
#. Write any additional details you want to give in the pull request description and click "Create pull request"

...and you're done! The developers will review your pull request and either accept, or give you some feedback on what you need to do for your changes to be pulled in. It's very normal for pull requests to need a few tweaks before being pulled in, so please don't be disheartened if it isn't accepted right away!
