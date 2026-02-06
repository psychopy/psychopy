.. include:: ../global.rst

.. _usingShelf:

Advanced Features for Online Experiments
========================================

 .. note::
   If your experiment is simple and does not require automatic counterbalancing, multi-session designs, or multiplayer interactions, you can skip this page and continue directly to :doc:`create-pavlovia-project`. 

This page covers advanced tools for online experiments, including:

- Eye tracking integration (Webgazer.js)
- Face tracking and emotion recognition (FaceAPI.js)

As well advanced workflows for online experiments that require information about participants to be stored and shared across sessions or participants. These include:

- Counterbalancing conditions automatically 
- Face and emotion recognition (FaceAPI.js)
- Sharing information across sessions
- Multi-player or multi-session designs
- Leaderboards and other custom online interactions

Advanced online tools
-----------------------------------------------

Online Eye-Tracking
^^^^^^^^^^^^^^^^^^

Online eye-tracking is possible using the external library `WebGazer.js <https://webgazer.cs.brown.edu/>`_. Currently, interaction with WebGazer requires **custom code components** within your PsychoPy experiment.

- **Live demo:** You can try an example experiment here:  
  `Face Preference Eye-Tracking Demo <https://run.pavlovia.org/demos/eye_tracking_face_preference/>`_

- **Source code:** The experiment code is available for download and inspection:  
  `GitLab repository <https://gitlab.pavlovia.org/demos/eye_tracking_face_preference/>`_

Using WebGazer.js, you can record gaze position data from participants’ webcams in real-time. Implementing this requires understanding of PsychoJS code components, as well as careful consideration of privacy and participant consent when using webcam-based tracking.


Online Face Detection
^^^^^^^^^^^^^^^^^^^^^

Face detection can be implemented in online experiments using the `Face API <https://justadudewhohacks.github.io/face-api.js/docs/index.html>`_ library. This library allows real-time tracking of facial features using participants’ webcams.

- **Background:** This approach was originally used by `Levordashka et al. (2025) <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11703984/>`_ to study audience engagement in real-time.


- **Live demo:** Try the Face API demo experiment here:  
  `Face API Demo <https://run.pavlovia.org/demos/face_api/>`_

- **Source code:** Download the experiment code for integration into your own studies:  
  `GitLab repository <https://gitlab.pavlovia.org/demos/face_api/>`_

**Notes:**  

- Face detection requires participants’ consent to access the webcam. Make sure to clearly inform participants and obtain agreement before starting the experiment.  

Advanced online worksflows: The Shelf
-----------------------------------------------

The primary tool for enabling these workflow features is the `Shelf <https://psychopy.github.io/psychojs/module-data.Shelf.html>`__, a flexible and multi-use mechanism that allows experiments to store and retrieve data between participants, sessions, or studies.

Currently, the Shelf can be accessed through :ref:`Code Components <code>`. In the future, we hope to make these features more accessible via a dedicated :ref:`Builder <builder>` component.

Use cases we will cover include:

* :ref:`Multi-session testing <multi-session-testing>`
* :ref:`Counterbalancing <counterbalance-shelf>`
* :ref:`Multi-player games <multiplayer-shelf>`
* :ref:`Leaderboards <leaderboard-shelf>`

In the sections below, we will walk through each use case and how to implement it.

You can access the Shelf in your `Pavlovia.org <https://pavlovia.org/>`__ account by selecting Dashboard > Shelf.

.. figure:: /images/shelf_access.png
    :name: shelfAccess
    :align: center
    :figclass: align-center
    
    How to access the Shelf from your pavlovia.org account. 

To begin with your Shelf will be empty. The value of each Record is a Json format, so be careful when formatting (that means use double quotations rather than single quotations!).

You can then add one or several "Records" to your Shelf. Each Record can be one of several variable types; Integer, Boolean, Text, List or Dictionary. The type of Record you create is up to you and will depend on the type of experiment you are trying to create. Each Record can be made available either to a single *Experiment* or to the *Designer*, meaning this Record is available to all of your experiments (for instance if you would like several experiments to interact with one another). Each Record can also be unlocked, meaning it can be interacted with and edited by your experiments, or locked, meaning it is frozen and not open to further edits. The way in which you choose to use Shelf is flexible and up to you! but we walk through some guidance to get started below.

Counterbalancing
^^^^^^^^^^^^^^^^^
**PsychoPy Version 2024.1 or later required**

`Demo link <https://run.pavlovia.org/Consultancy/numgroup_test>`__

`Demo experiment files <https://gitlab.pavlovia.org/Consultancy/numgroup_test>`__

We now have a Counterbalance Routine where you can set up your counterbalance groups in Builder Mode and interact with the Shelf with the record type, Counterbalance.

.. figure:: /images/counterbalanceBuilder.png
    :name: counterbalanceBuilder
    :align: center
    :figclass: align-center
    :scale: 50

    Settings in the Counterbalance Routine in Builder Mode

To set up your Counterbalance Shelf, you would need to first upload your task to Pavlovia and set it to Pilot/Running Mode.

In your Shelf view of your Dashboard, click on Add Record. In Key, add the name of your Counterbalance Routine as in your Builder task. For Scope, choose Experiment and select the name of your Builder task. For Type, select Counterbalance (*you might need to scroll down*).

Once you click on Ok, you will see an empty table in Value. Here, set up the same group parameters as in your Builder task.

.. figure:: /images/counterbalanceRecordTypeParameters.png
    :name: counterbalanceRecordTypeParameters
    :align: center
    :figclass: align-center
    :scale: 50

    Settings in the Counterbalance Shelf Record on Pavlovia.org

Your resulting Shelf record should look like this:

.. figure:: /images/counterbalanceRecordType.png
    :name: counterbalanceRecordType
    :align: center
    :figclass: align-center
    :width: 75%

    Completed settings in the Counterbalance Shelf Record on Pavlovia.org

.. seealso::
	
	:ref:`counterbalanceroutine`

Choosing slots and repetitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The way you configure **parameter slots** and **number of repetitions** depends on how you want participants to be distributed across groups during data collection.

For example, suppose you want:

- **2 groups**
- **20 participants per group**

One option would be to set:

- Slots = 20
- Repetitions = 1

However, this means that (depending on participant arrival order and randomness) it is possible for the first 20 participants to be assigned to the same group.

If you want participants to be assigned more evenly *as data are collected*, you may prefer to divide the total number of participants into smaller batches. For example:

- Slots = 2
- Repetitions = 10

This approach helps ensure that participants are approximately evenly distributed between groups throughout data collection, rather than only once all data have been collected.

.. note::
   When a participant starts the experiment and is assigned to a counterbalance group, a slot is reserved immediately. If that participant does not complete the study, this can lead to some unevenness in group assignment.


Interacting with Integer Records
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Demo link <https://run.pavlovia.org/lpxrh6/shelf_basic_integer/>`__

`Demo experiment files <https://gitlab.pavlovia.org/lpxrh6/shelf_basic_Integer/>`__

Imagine a simple use case where you want to **count how many participants have completed your task**. 

To do this, you would create an **Integer Record** in the Shelf, which starts at `0`, and assign its **scope** to the experiment of interest.

Within your experiment, you can interact with Integer Records using several methods (among others; see full list `here <https://psychopy.github.io/psychojs/Shelf.html>`__):

* :code:`psychoJS.shelf.getIntegerValue()`
* :code:`psychoJS.shelf.setIntegerValue()`
* :code:`psychoJS.shelf.addIntegerValue()`

For example, to increment a participant counter, you can add a **JavaScript code component** to your experiment and use:

.. code-block:: javascript

    psychoJS.shelf.addIntegerValue({
        key: ['participant_counter'],
        delta: 1
    });

* :code:['participant_counter'] corresponds to the key name of your Integer Record.
* delta: 1 is the amount to increment the value by.

You can place this snippet in the **Begin Experiment** tab if you want to increment the counter at the start of the experiment, or in the **End Experiment** tab if you prefer to increment it at the end of the session.

To fetch the current value of the counter, use:

.. code-block:: javascript

    participantN = await psychoJS.shelf.getIntegerValue({
        key: ['participant_counter'],
        defaultValue: 0
    });

**Important:** you must use `await` because these Shelf functions return **JavaScript Promises**. Using `await` ensures that the Promise is fulfilled and you have the actual value before trying to use or display it.

Interacting with Boolean Records
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Demo link <https://run.pavlovia.org/lpxrh6/shelf_boolean_demo/>`__

`Demo experiment files <https://gitlab.pavlovia.org/lpxrh6/shelf_Boolean_demo/>`__


Boolean Records are the simplest type of Shelf Record, because they can only have two values: :code:`true` or :code:`false`. This limits the ways you need to interact with them, making them ideal for toggling states or flags.

The most commonly used methods for Boolean Records are:

.. code-block:: javascript

    psychoJS.shelf.getBooleanValue()
    psychoJS.shelf.setBooleanValue()
    psychoJS.shelf.flipBooleanValue()

---

Example: Controlling an "Open/Closed" Session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Imagine you have an experiment that can be **opened** or **closed** by a host. You could:

1. Add a Boolean Record called :code:`session_open`.
2. In the experiment, allow a participant to sign in either as a **host** (who can open/close the session) or as a **viewer** (who observes the session state).

Host interaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To allow the host to open or close the session:

- Use a code component (type: JS) in the **End Routine** tab.
- Toggle the Boolean Record using:

.. code-block:: javascript

    psychoJS.shelf.flipBooleanValue({
        key: ['session_open']
    });

- You can connect this to a response component (e.g., mouse click) so the host controls the session.

Participant view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To let participants observe the session state:

- Use a code component that repeatedly checks the Boolean Record:

.. code-block:: javascript

    const isOpen = await psychoJS.shelf.getBooleanValue({
        key: ['session_open'],
        defaultValue: false
    });

- Use this value to control elements in your experiment. For example, show a **door image** that opens or closes depending on :code:`isOpen`.


Interacting with Text Records
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Demo link <https://run.pavlovia.org/lpxrh6/shelf_text_demo/>`__

`Demo experiment files <https://gitlab.pavlovia.org/lpxrh6/shelf_text_demo/>`__

Reading and writing Text Records from the Shelf requires two main functions:

* :code:`psychoJS.shelf.getTextValue()`
* :code:`psychoJS.shelf.setTextValue()`

Quite simply - we use these to check the text currently on the shelf and set it respectively!

Interacting with List Records
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Demo link <https://run.pavlovia.org/lpxrh6/shelf_list_demo/>`__

`Demo experiment files <https://gitlab.pavlovia.org/lpxrh6/shelf_list_demo/>`__


List Records are useful when you want to store and share collections of values between participants. A common example is a **multi-player experiment** where participants need to see information about other players, such as their screen names.

For example, you might want:
- A shared list of all players who are currently signed in
- Each participant to be able to view the screen names of other players

To support this, you would create a Shelf Record with the type set to **List**.

When interacting with a List Record from your experiment, the most commonly used methods are:

* :code:`psychoJS.shelf.getListValue()`
* :code:`psychoJS.shelf.setListValue()`
* :code:`psychoJS.shelf.appendListValue()`
* :code:`psychoJS.shelf.popListValue()`

Example: Managing a shared player list
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Suppose your experiment maintains a shared list of player screen names called :code:`player_list`.

Clearing the list
~~~~~~~~~~~~~~~~~~~~~~~~

In some cases (for example, via a drop-down menu in a host interface), you may want to clear any existing players from the list. You can do this by setting the list to an empty array:

.. code-block:: javascript

    psychoJS.shelf.setListValue({
        key: ['player_list'],
        value: []
    });

Adding a player
~~~~~~~~~~~~~~~~~~~~~~~~

To add the current player’s screen name to the existing list, use:

.. code-block:: javascript

    psychoJS.shelf.appendListValue({
        key: ['player_list'],
        elements: expInfo['screen name']
    });

Fetching the list
~~~~~~~~~~~~~~~~~~~~~~~~

To retrieve the current list of players (for example, to update a display periodically), use:

.. code-block:: javascript

    players = await psychoJS.shelf.getListValue({
        key: ['player_list'],
        defaultValue: []
    });

Remember that :code:`getListValue()` returns a **JavaScript Promise**, so it is important to use :code:`await` to ensure the list has been retrieved before attempting to use it.

.. _multi-session-testing:

Interacting with Dictionary Records
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Demo link <https://run.pavlovia.org/lpxrh6/shelf_dict_demo/>`__

`Demo experiment files <https://gitlab.pavlovia.org/lpxrh6/shelf_dict_demo/>`__

Dictionary Records are useful when you want to store **key–value pairs**, where each key has an associated value. This is particularly helpful when tracking participant-specific information across sessions.

The most commonly used methods for Dictionary Records are:

* :code:`psychoJS.shelf.setDictionaryFieldValue()`  
  Create a new field or update an existing field within a Dictionary Record.
* :code:`psychoJS.shelf.getDictionaryFieldValue()`  
  Retrieve the value associated with a specific Dictionary field.

When you first create a Dictionary Record, it is empty.

Example: Tracking sessions per participant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, we use a Dictionary Record called :code:`session_tracker` to track how many times each participant has completed the experiment.

Each entry in the dictionary will use:
- The **participant ID** as the field name
- The **number of completed sessions** as the field value

Checking for existing participants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a participant joins, we first retrieve the existing field names from the dictionary:

.. code-block:: javascript

    existing_participants = await psychoJS.shelf.getDictionaryFieldNames({
        key: ['session_tracker']
    });

We then check whether the current participant ID (retrieved from the startup dialog) already exists in the dictionary.

Updating the session count
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the participant is new, we create a new dictionary field and set the session count to `1`.  
If the participant already exists, we retrieve their current session count, increment it, and store the updated value:

.. code-block:: javascript

    if (!existing_participants.includes(expInfo['participant'])) {
        psychoJS.shelf.setDictionaryFieldValue({
            key: ['session_tracker'],
            fieldName: expInfo['participant'],
            fieldValue: 1
        });
    } else {
        session_number = await psychoJS.shelf.getDictionaryFieldValue({
            key: ['session_tracker'],
            fieldName: expInfo['participant'],
            defaultValue: 0
        });
        session_number = session_number + 1;
        psychoJS.shelf.setDictionaryFieldValue({
            key: ['session_tracker'],
            fieldName: expInfo['participant'],
            fieldValue: session_number
        });
    }

This approach allows you to track how many times each participant has completed the experiment using a single Dictionary Record.

.. note::
   Be careful with capitalisation when interacting with the Shelf API. For example, use :code:`fieldName`, not :code:`fieldname`.

.. _counterbalance-shelf:


.. _multiplayer-shelf:

Multiplayer experiments
^^^^^^^^^^^^^^^^^^^^^^^^

`Demo link <https://run.pavlovia.org/jfkominsky/multiplayer_demo>`__ (Note: Requires multiple browser windows or multiple people accessing the link at once!)

`Demo experiment files <https://gitlab.pavlovia.org/jfkominsky/multiplayer_demo>`__

Using the shelf, you can create synchronous multi-participant experiments, i.e., multiplayer activities. First, two important notes:

* The shelf is **slow**. It can take up to 60 seconds for an update from one participant to be received by another participant via updating and checking the shelf.
* If you are planning to copy the demo, you will need to set up your own lists and dictionaries (described below) in your own account's shelf.

Multiplayer activities first require a matchmaking routine to pair a participant with another participant (or, in principle, multiple other participants), and once the other player has been found, whatever communication is required by the task itself. This demo uses a very simple coordination game in which each player must select a red or green card, and both players win if they choose the same color.

The demo requires three entries on the shelf (which you will need to re-create on your own shelf if you want to create your own copy of the demo):

.. figure:: /images/multiplayer_images/multiplayerShelf.png
    :align: center
    :figclass: align-center
    :scale: 50

    

1. :code:`player_pairs`: A **dictionary** consisting of key:value pairs where one player ID is the key and the partnered player is the value. This contains one key per player, so each pair has two entries in this dictionary. This keeps track of the matches once they have been made.
2. :code:`unpaired_players`: A **list** of Pavlovia IDs for players who have not yet been matched up.
3. :code:`player_clicked`: A **dictionary** consisting of key:value pairs where one player ID is the key and the color that player clicked (red or green) is the value.

The experiment starts with a matchmaking routine. This routine displays a message to the participant to let them know that matchmaking is happening, a timer to show them that the experiment is not frozen, and a code component that conducts matchmaking in three repeating steps:

1. Check if the current player's Pavlovia ID is already present as a key in the :code:`player_pairs` dictionary. If so, record the value of that entry as the partner ID.

.. figure:: /images/multiplayer_images/matchmakingStep1.png
    :name: matchmakingStep1
    :align: center
    :figclass: align-center
    :scale: 50

2. If the current player's Pavlovia ID is not a key in the :code:`player_pairs` dictionary, check the :code:`unpaired_players` list. If there is already an unpaired player listed, record them as the partner ID, remove them from the :code:`unpaired_players` list, and add two matched entries to :code:`player_pairs`, one for the current player and one for the partner.

.. figure:: /images/multiplayer_images/matchmakingStep2.png
    :name: matchmakingStep2
    :align: center
    :figclass: align-center
    :scale: 50

3. If the :code:`unpaired_players` list is empty, add the current player's ID to the :code:`unpaired_players` list, and repeat from step 1.

.. figure:: /images/multiplayer_images/matchmakingStep3.png
    :name: matchmakingStep3
    :align: center
    :figclass: align-center
    :scale: 50

To prevent the code from freezing every time it checks the shelf, this code uses :code:`.then(function(result){})` asynchronous code. The difference between this and the :code:`await` keyword used with other shelf demos is that :code:`await` freezes the rest of the experiment until the communication with the shelf is complete, whereas :code:`.then(function(result){})` executes when the communication is complete while letting the frame loop continue uninterrupted in the meantime. Note that in step 3, it uses neither of these, which means that the code **does not know when the shelf has finished updating with the current player's ID added to the unpaired player list**. In this case that's fine because nothing in this code depends on that completing, and there is a boolean that makes sure that the player's ID is only added to the list once regardless of whether or not the update has finished from one frame to the next.

As a safety measure to ensure that the unpaired player list is cleared, the code component also includes an "end routine" step that makes sure the current player ID is removed from the list. Because it does not use :code:`await`, this can happen while the experiment proceeds to the next routine.

.. figure:: /images/multiplayer_images/matchmakingEnd.png
    :name: matchmakingEnd
    :align: center
    :figclass: align-center
    :scale: 50

After a partner has been found, the participant moves on to the coordination game, where they can click either the red or green card. Two black cards on the other side of the screen represent the partner's cards. The code component in this routine does three things:

1. When the current player clicks a card, add an entry to the :code:`player_clicked`: dictionary with the current player's ID as a key and the value equal to the color that the current player clicked.

.. figure:: /images/multiplayer_images/coordinationUpdate.png
    :name: coordinationUpdate
    :align: center
    :figclass: align-center
    :scale: 50

2. Check whether the partner ID has appeared as a key in the :code:`player_clicked` dictionary, and if so, animate one of the partner's cards (always the left one) as moving toward the center (and record what color they actually chose in a separate variable).

.. figure:: /images/multiplayer_images/coordinationCheck.png
    :name: coordinationCheck
    :align: center
    :figclass: align-center
    :scale: 50

3. When both (1) and (2) have occurred, end routine and go to the routine that presents the outcome.

The logic here once again uses :code:`.then(function(result){})` to make sure each player can make their own choice without the code freezing waiting for the other player's choice.

.. _leaderboard-shelf:

Leaderboard
^^^^^^^^^^^^

`Demo link <https://run.pavlovia.org/SueLynnNotts/leaderboard>`__

`Demo experiment files <https://gitlab.pavlovia.org/SueLynnNotts/leaderboard>`__

Leaderboards are a fun way of adding an element of gamification to your tasks! You can do this by using a Dictionary type shelf record. Just like in the counterbalancing example, the Key Component (on your Pavlovia shelf) and the :code:`key` within the code component of your PsychoPy task needs to match and have a meaningful name. Since the demo task records both the reaction times and accuracy data, the name used is "leaderboard_scores".

You would not need to add any fields within the shelf record on Pavlovia as they will automatically be populated when the task is completed. As more people complete the task, the shelf record would look like so:

.. figure:: /images/leaderboard_images/exampleLeaderboardShelf.png
    :name: leaderboardShelf
    :align: center
    :figclass: align-center
    :scale: 50

If you would like to just record each participants' scores, you would only need the following code component:

.. figure:: /images/leaderboard_images/setupLeaderboardCode.png
    :name: leaderboardCodeComponent
    :align: center
    :figclass: align-center
    :width: 85%

This is how you would fetch all the records that's stored within the leaderboard.

.. figure:: /images/leaderboard_images/fetchLeaderboardCode1.png
    :name: fetchLeaderboardCodeComponent1
    :align: center
    :figclass: align-center
    :width: 75%

.. figure:: /images/leaderboard_images/fetchLeaderboardCode2.png
    :name: fetchLeaderboardCodeComponent2
    :align: center
    :figclass: align-center
    :width: 75%

**Average Reaction Times**

This is an example JavaScript snippet to fetch all the reaction times recorded and calculate the average reaction times:

.. figure:: /images/leaderboard_images/leaderboardRTCode.png
    :name: leaderboardRTCodeComponent1
    :align: center
    :figclass: align-center
    :width: 75%

**Ranked Accuracy**

This is an example JavaScript snippet to fetch all the accuracy stored and sort them in descending order:

.. figure:: /images/leaderboard_images/leaderboardAccuracyCode1.png
    :name: leaderboardSortAccuracyCodeComponent1
    :align: center
    :figclass: align-center
    :width: 75%

.. figure:: /images/leaderboard_images/leaderboardAccuracyCode2.png
    :name: leaderboardSortAccuracyCodeComponent2
    :align: center
    :figclass: align-center
    :width: 75%

The above code component only sorts the accuracies of each participant but doesn't return the participants' IDs. To get the sorted IDs, you would need the following code component:

.. figure:: /images/leaderboard_images/leaderboardSortID1.png
    :name: leaderboardSortIDCodeComponent1
    :align: center
    :figclass: align-center
    :width: 75%

.. figure:: /images/leaderboard_images/leaderboardSortID2.png
    :name: leaderboardSortIDCodeComponent2
    :align: center
    :figclass: align-center
    :width: 75%

The IDs and accuracy scores are stored in the separate lists (in descending order) and therefore can be indexed. In this example, we index the first 5 IDs and accuracy scores.

.. figure:: /images/leaderboard_images/leaderboardExample.png
    :name: leaderboardExample
    :align: center
    :figclass: align-center
    :width: 60%

.. _checkIdsShelf:

Checking existing participant IDs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Demo link <https://run.pavlovia.org/SueLynnNotts/check_id_demo>`__

`Demo experiment files <https://gitlab.pavlovia.org/SueLynnNotts/check_id_demo>`__

When running multi-session experiments online, it is sometimes difficult to tell if the person accessing the link is a participant from a previous session. This participant ID checker using the List type Shelf uses a prepopulated list of IDs to first check if the participant ID entered at the startup dialog box exists in the prepopulated list (see list below for accepted IDs) before either showing a message saying "Welcome back!" or "Sorry, your id couldn't be found."

.. figure:: /images/shelf_list_ids.png
    :name: acceptedIDs
    :align: center
    :figclass: align-center

In the experiment files, there's a spreadsheet which automatically formats the IDs to be copied into the Shelf record (see below for an example).

.. figure:: /images/shelf_id_record.png
    :name: shelf_id_record
    :align: center
    :figclass: align-center

Next step
---------

Once you understand the required advanced:

:doc:`create-pavlovia-project` to create your Pavlovia project and upload your experiment.