.. _projects:

Projects
====================================

As of version 1.84 PsychoPy connects directly with the Open Science Framework website (http://OSF.io) allowing you to search for existing projects and upload your own experiments and data.

There are several reasons you may want to do this:
  - sharing files with collaborators
  - sharing files with the rest of the scientific community
  - maintaining historical evidence of your work
  - providing yourself with a simple version control across your different machines

Sharing with collaborators
------------------------------

You may find it simple to share files with your collaborators using dropbox but that means your data are stored by a commercial company over which you have no control and with no interest in scientific integrity. Check with your ethics committee how they feel about your data (e.g. personal details of participants?) being stored on dropbox. OSF, by comparison, is designed for scientists to stored their data securely and forever.

Once you've created a project on OSF you can add other contributors to it and when they log in via PsychoPy they will see the projects they share with you (as well as the project they have created themselves). Then they can sync with that project just like any other.

Sharing files/projects with others
--------------------------------------------------

Optionally, you can make your project (or subsets of it) publicly accessible so that others can view the files. This has various advantages, to the scientific field but also to you as a scientist.

Good for open science:
  * Sharing your work allows scientists to work out why one experiment gave a different result to another; there are often subtleties in the exact construction of a study that didn't get described fully in the methods section. By sharing the actual experiment, rather than just a description of it, we can reduce the failings of replications
  * Sharing your work helps others get up and running quickly. That's good for the scientific community. We want science to progress faster and with fewer mistakes.

Some people feel that, having put in all that work to create their study, it would be giving up their advantage to let others simply use their work. Luckily, sharing is good for you as a scientist as well!

Good for the scientist:
  * When you create a study you want others to base their work on yours (we call that academic impact)
  * By giving people the exact materials from your work you increase the chance that they will work on your topic and base their next study on something of yours
  * By making your project publicly available on OSF (or other sharing repository) you raise visibility of your work

You don't need to decide to share immediately. Probably you want your work to be private until the experiment is complete and the paper is under review (or has been accepted even). That's fine. You can create your project and keep it private between you and your collaborators and then share it at a later date with the click of a button.

Maintaining a validated history of your work
--------------------------------------------------

In many areas of science researchers are very careful about maintaining a full documented history of what their work; what they discovered, the data they collected and what they predicted for the next experiment. In the behavioural and social sciences we haven't been very good at that. With OSF:
  * you can "preregister" your plans for the next experiment (so that people can't later accuse you of "p-hacking").
  * all your files are timestamped so you can prove to others that they were collected on/by a certain date, removing any potential doubts about who collected data first
  * your projects (and individual files) have a unique URL on OSF so you can cite/reference resources.
  Additionally, "Registrations" (snapshots of your project at a fixed point in time) can be given a DOI, which guarantees they will exist permanently

.. _projectSync:

Using PsychoPy to sync with OSF
---------------------------------

PsychoPy doesn't currently have the facility to *create* user profiles or projects, so the first step is for you to do that yourself.

Login to OSF
~~~~~~~~~~~~~~~

From the `Projects` menu you can log in to OSF with your username and password (this is never stored; see :ref:`OSFsecurity`). This user will stay logged in while the PsychoPy application remains open, or until you switch to a different user. If you select "Remember me" then your login will be stored and you can log in again without typing your password each time.

Projects that you have previously synchronised will try to use the stored details of the known users if possible and will revert to username and password if not. Project files (defining the details of the project to sync) can be stored wherever you choose; either in a private or shared location. User details are stored in the home space of the user currently logged in to the operating system so are not shared with other users by default.

.. _OSFsecurity:

Security
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you log in with your username and password these details are not stored by PsychoPy in any way. They are sent immediately to OSF using a secure (https) connection. OSF sends back an "authorisation token" identifying you as a valid user with authorised credentials. This is stored locally for future log in attempts. By visiting your user profile at http://OSF.io you can see what applications/computers have retrieved authorisation tokens for your account (and revoke them if you choose).

The auth token is stored in plain text on your computer, but a malicious attacker with access to your computer could only use this to log in to OSF.io. They could not use it to work out your password.

All files are sent by secure connection (https) to the server.

Searching for projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Having logged in to OSF from the projects menu you can search for projects to work with using the `>Projects>Search` menu. This brings up a view that shows you all the current projects for the logged in user (owned or shared) and allows you to search for public projects using tags and/or words in the title.

When you select a project, either in your own projects or in the search box, then the details for that project come up on the right hand side, including a link to visit the project page on the web site.

On the web page for the project you can "fork" the project to your own username and then you can use PsychoPy to download/update/sync files with that project, just as with any other project. The project retains information about its history; the project from which it was forked gets its due credit.

Synchronizing projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Having found your project online you can then synchronize a local folder with that set of files.

To do this the first time:
  - select one of your projects in the project search window so the details appear on the right
  - press the "Sync..." button
  - the Project Sync dialog box will appear
  - set the location/name for a project file, which will store information about the state of files on the last sync
  - set the location of the (root) folder locally that you want to be synchronised with the remote files
  - press sync

The sync process and rules:
  - on the first synchronisation all the files/folders will be merged:
    - the contents of the local folder will be uploaded to the server and vice versa
    - files that have the same name but different contents (irrespective of dates) will be flagged as conflicting (see below) and both copies kept
  - on subsequent sync operations a two-way sync will be performed taking into account the previous state. **If you delete the files locally and then sync then they will be deleted remotely as well**
  - files that are the same (according to an md5 checksum) and have the same location will be left as they are
  - if a file is in conflict (it has been changed in both locations since the last sync) then both versions will be kept and will be tagged as conflicting
  - if a file is deleted in one location but is also changed in the other (since the last sync) then it will be recreated on the side where it was deleted with the state of the side where is was not deleted.

Conflicting files will be labelled with their original filename plus the string "_CONFLICT<datetimestamp>"
Deletion conflicts will be labelled with their original filename plus the string "_DELETED"

Limitations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - PsychoPy does not directly allow you to create a new project yet, nor create a user account. To start with you need to go to http://osf.io to create your username and/or project. You also cannot currently fork public projects to your own user space yet from within PsychoPy. If you find a project that is useful to you then fork it from the website (the link is available in the details panel of the project search window)
  - The synchronisation routines are fairly basic right now and will not cater for all possible eventualities. For example, if you create a file locally but your colleague created a folder with the same name and synced that with the server, it isn't clear what will (or should ideally) happen when you now sync your project. You should be careful with this tool and always back up your data by an independent means in case damage to your files is caused
  - This functionality is new and may well have bugs. **User beware!**
