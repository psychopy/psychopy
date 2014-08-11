Adding documentation
=====================================

There are several ways to add documentation, all of them useful: doc strings, comments in the code, and demos to show an example of actual usage. To further explain something to end-users, you can create or edit a .rst file that will automatically become formatted for the web, and eventually appear on www.psychopy.org.

You make a new file under psychopy/docs/source/, either as a new file or folder or within an existing one.

To test that your doc source code (.rst file) does what you expect in terms of formatting for display on the web, you can simply do something like (this is my actual path, unlikely to be yours)::

  $ cd /Users/jgray/code/psychopy/docs/
  $ make html

Do this within your docs directory (requires sphinx to be installed, try "easy_install sphinx" if it's not working). That will add a build/html sub-directory.

Then you can view your new doc in a browser, e.g., for me:

  file:///Users/jgray/code/psychopy/docs/build/html/
  
Push your changes to your github repository (using a "DOC:" commit message) and let Jon know, e.g. with a pull request.
