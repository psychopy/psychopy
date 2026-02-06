.. include:: ../global.rst

.. _create-pavlovia-project:

Create a Pavlovia project
=========================

.. important::

   *As of December 27th 2025 you will need to have PsychoPy 2025.1.1 installed in order to sync to Pavlovia from PsychoPy.*
   If you have an older version please see this guide on :doc:`how to sync with Pavlovia independently of PsychoPy app <syncingToPavlovia>`.


**Goal:** Create a new project on Pavlovia to host your online experiment.

Before you start
----------------

You should already have:

- An experiment prepared for online use
- A Pavlovia account (https://pavlovia.org/)

What this step covers
---------------------

In this step, you will:

- Create a new project on Pavlovia
- Sync your local experiment to the online repository
- Understand version control basics for your experiment
- Learn how to share your experiment with collaborators or make it public
- Best practice for sharable and reusable projects

Create a new Pavlovia project
-----------------------------

1. Ensure that you have a clean folder structure for your experiment, with all necessary files included. We recommend placing your .psyexp file and all associated resources (images, sounds, data files) in a dedicated folder in a location that is not already under version control.
2. Open your experiment in **PsychoPy Builder**.
3. Go to the **"Pavlovia.org" menu → "User" → "Log into Pavlovia"** and sign into your account.
4. Click the **"Pavlovia.org" menu → "Sync"** or the green **"Sync"** icon.
5. Give your project a **name** - do not use spaces of special characters. This will be the name of your project on Pavlovia.
6. You should now be able to find your experiment when you log into Pavlovia.org, under **Dashboard → Experiments**.

.. figure:: /images/newProjectUpload.png
    :name: newProjectUpload
    :align: center
    :figclass: align-center
    :scale: 50

    Dialog box for uploading a new Pavlovia project from PsychoPy Builder.

Interacting with |Pavlovia| from the Builder App
------------------------------------------------

When running your study online, the relevant controls are in the Browser and Pavlovia sections of the ribbon:

.. figure:: /images/pavlovia_icons_2025.png
    :name: pavlovia_icons_2025
    :align: center
    :figclass: align-center

From left to right:

- The "Compile JS" button will write your experiment as a JavaScript (JS) file, which can run in a web browser.
- The "Run JS" (green) or "Pilot JS" (orange) buttons will run your experiment in a web browser; via Pavlovia in running mode, or via a local debugging server in piloting mode. Note that, in order to run in Pavlovia, the project needs to be set to "running" on Pavlovia (not "piloting" or "inactive").
- The "Sync" button will synchronise the local files for your experiment with its online counterpart on Pavlovia.
- The "User" panel is for managing your Pavlovia user - once you're logged in, your name will appear in the panel (ToddOST in the image above). Click it to view your profile online, or click the drop down arrow to log in/out of Pavlovia in the PsychoPy app.
-  The "Project" panel is for managing the Pavlovia project associated with the current experiment, click it to view the experiment on Pavlovia or click the drop down menu to edit its details and search for other projects.


Updating your experiment
--------------------------

To make changes to your experiment you can make changes in PsychoPy Builder as normal. When you are ready to upload your changes to Pavlovia:

- PsychoPy will prompt you to **commit your experiment** to the online repository.
- Review the changes (number of files added/deleted), add a description of the change and click **"Sync"** to upload your files.

Version control basics
---------------------

Every time you make a change locally, click **Sync** to update the online version, Pavlovia keeps track of versions automatically. This means that you can revert to previous versions if needed.

To view the version history of your experiment, log into Pavlovia.org, go to your experiment page and click on the **"View Code"** button. Here you can select **"Repository" → "Commits"** to see a list of all changes made to your experiment, and download previous versions if you wish. To reinstate a previous version, you will need to download the files, replace those in your existing local folder (keeping the same names) and re-upload them to your local experiment folder.

.. figure:: /images/navigateVersionHistory.png
    :name: navigateVersionHistory
    :align: center
    :figclass: align-center
    :scale: 50

    Once you have selected "View Code", navigate to the "Commits" tab to see the version history of your experiment.


Sharing and project visibility
------------------------------

Once your project exists on Pavlovia, you can control **who can see or edit it**. By default, new projects are **private**, meaning only you can access them.

On Pavlovia.org:

1. Open your project page.
2. Click the **View Code** button to access the GitLab repository page.
3. Go to **Settings → General** in the left sidebar.
4. Scroll down to the **Visibility, project features, permissions** section. Here you can set the visibility level of your project:

   - **Private**: Only project members can access the repository.
   - **Public**: Anyone can view and clone the project.

Sharing with specific users:

1. Navigate to **Project information → Members** in the left sidebar.
2. Invite collaborators by username or email address.
3. Assign permission levels (GitLab roles):

   - **Guest**: Can view issues, wiki, and project information; cannot push code.
   - **Reporter**: Can view code, download the repository, and see issues; cannot push code.
   - **Developer**: Can push code, create branches, and merge into non-protected branches; cannot manage project settings or members.
   - **Maintainer**: Can push to protected branches, manage project settings, and invite or remove members.
   - **Owner**: Only available for projects in a personal namespace; full control including deleting the project.

.. note::
   On Pavlovia’s GitLab instance, the **Owner role** is typically reserved for your personal projects. Team projects may use **Maintainer** as the highest role for collaborators.

Creating a reusable and shareable project
----------------------------------------

If you plan to make your project public, share it with collaborators, or reuse it as a template, there are a few practices that make it easier for others to understand and use your experiment.

1. **Add a README file**:

   - Create a `README.md` file in your project folder.  
   - Include a short description of the experiment, required resources, instructions for running it, and any dependencies.  
   - Markdown formatting allows headings, lists, and links to make the file readable online.

2. **Add a project description**:  

   - On Pavlovia, open your project page → click **Settings → General → Project description**.  
   - Provide a concise summary that will appear under the project title in the public repository view.

3. **Add a project avatar** :

   - A small image (e.g., 200×200 px) can be added under **Settings → General → Avatar**.  
   - This helps your project stand out visually in the public repository and when browsing multiple experiments.

4. **Organize your experiment folder**:

   - Consider subfolders for resources (e.g., `images/`, `sounds/`) to keep things tidy.
   - Consider a "spreadsheets" subfolder for condition files if applicable.
   - Only have one .psyexp file in the root folder to avoid confusion.

5. **Include example data (optional)** :

   - If sharing templates, include anonymized example output files or CSVs so users can see what the experiment generates.
   - You might even want to include an example on how you extract or analyse data.

Using GitLab groups for collaboration and sharing
-------------------------------------------------

GitLab groups allow multiple users to manage and collaborate on projects under a shared namespace. This is useful for labs or teams where several members may need to access, edit, or adapt the same experiments.

Why use groups?
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Centralized organization: All lab projects can live in the same group.
- Easy collaboration: Team members can fork, edit, or contribute without affecting the original repository.
- Template management: You can maintain canonical experiments in a “lab group” and allow others to fork them for adaptation.

Example workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Create a group**  

   - On GitLab (accessible either via gitlab.pavlovia.org or though the "View Code" of a project), go to **Menu → Groups → Create group**.  
   - Give your group a descriptive name (e.g., *The Best Lab*) and set the visibility (private or public).  

2. **Fork a project into the group**  

   - Navigate to an existing project (either your own or a template).  
   - Click **Fork** and select your group as the target namespace.  
   - The project now exists under the group and can be managed collaboratively.

3. **Invite members to the group**

   - Go to the group page → **Group information → Members**.  
   - Invite lab members by username or email and assign appropriate roles (e.g., Developer, Maintainer).

3. **Collaborators fork to their own account** 

   - Individual lab members can fork the group project into their personal account.  
   - They can make edits, test changes, and optionally submit merge requests back to the group project.


Next step
---------

Once your project is created and synced, continue to:

:doc:`test-online`

