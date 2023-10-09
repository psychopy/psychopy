==============================
Translations
==============================

|PsychoPy| is used worldwide. Starting with v1.81, many parts of |PsychoPy| itself (the app) can be translated into any language that has a unicode character set.

A translation changes the language that the **experimenter** sees in the |PsychoPy| app while creating and running experiments

As a translator, you will likely introduce many new people to |PsychoPy|, and your translations will greatly influence their experience. 

.. note:: 
  Translations here do **not** refer to what the participant in a study sees, nor what is seen in documentation (help files, etc.). 

|

What you need to *know* already
---------------------------------

In order to translate the |PsychoPy| app to another language, you need a thorough understanding of at least three things:

* |psychopyWebpage| itself, as an experiment designer yourself
* the English language
* the language you want to translate into (e.g., Korean)

You will also need an understanding of two more things. But in contrast to the above, these can be learned in less than a day.

* how to contribute to the |PsychoPy| project using |gitWebpage| via |githubWebpage|
* how to use the free app |poeditWebpage| 
 
To help you along with |gitWebpage| and |githubWebpage|, you should read through :ref:`the instructions on how to do so<usingRepos>`. However, we explain how to use |poeditWebpage| in the tutorial directly below.

.. note::
  For a more step-by-step tutorial for translators, please see the materials from our 3-hour translator workshop. You can go to the |translatorWorkshopSlides|, or the |translatorWorkshopWebpage|. The information is identical in both.

.. |psychopyWebpage| raw:: html

  <a href="https://www.psychopy.org/" target="_blank">PsychoPy</a>

.. |gitWebpage| raw:: html

  <a href="https://git-scm.com/" target="_blank">Git</a>

.. |githubWebpage| raw:: html

  <a href="https://github.com/" target="_blank">GitHub</a>

.. |poeditWebpage| raw:: html

  <a href="https://poedit.net/" target="_blank">Poedit</a>

.. |translatorWorkshopSlides| raw:: html

  <a href="https://workshops.psychopy.org/slides/translators/#1" target="_blank">workshop slides</a>

.. |translatorWorkshopWebpage| raw:: html

  <a href="https://workshops.psychopy.org/translators/index.html" target="_blank">workshop webpage</a>

|

What you need to *have already done* before you begin
----------------------------------------------------------

Importantly, everything in the rest of this tutorial assumes you have already done the following: 

* forked the |psychopyOnGithub| to your own *GitHub* account
* cloned the repository to your own computer

Again, see :ref:`the instructions on how to contribute to PsychoPy<usingRepos>` if you are unclear on how to do any or all of this.

.. warning::
  If you are **also** working on things other than translations, consider creating a new branch based on the *release* branch, but rename it according to what you are going to do (e.g., ``translate-spanish``). This will help you keep things organised in your own workspace. But if you are only doing translations, then just stay on the *release* branch.

.. |psychopyOnGithub| raw:: html

  <a href="https://github.com/psychopy/psychopy" target="_blank">PsychoPy repository on GitHub</a>

|

Finding the file you need for your translation
--------------------------------------------------

|PsychoPy| uses |gettextWebpage| and |wxPythonWebpage| to allow for translations into other languages. But the only thing you as translator need to understand here is that in order to add any particular translation to |PsychoPy|, you need to work on a particular ``messages.po`` file.

The ``messages.po`` file for any given language is stored within a unique subdirectory within the following directory in the repository:

``THE/PATH/ON/YOUR/COMPUTER/TO/psychopy/app/locale/``

The list of subdirectory names you see at that location are |localeNames| from the ``ll_CC`` system in |gettextWebpage|. The naming convention works as follows:

* For any given language, the first pair of letters, ``ll``, is replaced by an |iso639pairs| of lowercase letters that identify that language
* For any given country, the second pair of letters, ``CC``, is replaced by an |iso3166pairs| of uppercase letters that identify a country.
  
For example, for German, ``ll_CC`` becomes ``de_DE``, and refers to the German language (``de``, for *deutsch*) as it is used in the country of Germany (``DE``, *Deutschland*). Together, they index the dialect known as *High German* (the standard dialect used in Germany).

Once you understand the naming conventions for language folders, your first order of business one of the following:

* finding the directory that corresponds to your language (in cases where it is already there), or 
* creating a new one (in cases where it is not). 

If your language is **not** listed and you need to add it (or even if you are unsure whether you should be using the one already listed), scroll down to the section on :ref:`Creating a new language subdirectory<newLangSubdirect>` to learn more about what to do. Then return here when you are done.

If the appropriate language subdirectory is already listed, then proceed to the next section.

.. |wxPythonWebpage| raw:: html

  <a href="https://docs.wxpython.org/wx.Locale.html" target="_blank">wxPython</a>

.. |localeNames| raw:: html

  <a href="https://www.gnu.org/software/gettext/manual/gettext.html#Locale-Names" target="_blank">locale names</a>

.. |gettextWebpage| raw:: html

  <a href="https://www.gnu.org/software/gettext/" target="_blank">gettext</a>

.. |iso639pairs| raw:: html

  <a href="https://www.gnu.org/software/gettext/manual/gettext.html#Language-Codes" target="_blank">ISO 639 pair</a>

.. |iso3166pairs| raw:: html

  <a href="https://www.gnu.org/software/gettext/manual/gettext.html#Country-Codes" target="_blank">ISO 3166 pair</a>

.. _translateProcess:

|

The translation process in *Poedit*
--------------------------------------

Open the relevant ``ll_CC`` directory. You will see a subdirectory titled ``LC_MESSAGE``. Inside that subdirectory are two files. The one you work on as a translator is the ``.po`` file: ``messages.po``. The other file is ``messages.mo``, an un-editable binary file that actually turns out to be the file that |PsychoPy| will use during operation. This file is compiled during major and minor releases of |PsychoPy|, however. So you should not do it yourself within *Poedit*.

There are a number of tools you can use to edit the ``messages.po`` file, but the rest of this tutorial assumes that you are using the free app |poeditWebpage|. It is cross-platform, and very user-friendly. If you haven't done so already, |poeditDownloadPage| and install it in order to continue.

.. note:: 
  How to translate the *start-up tips* in |PsychoPy| is covered below under the section titled *Step 3b: Translating Start-up Tips*. It involves a somewhat different process. First however, please read through the section directly below.

.. |poeditDownloadPage| raw:: html

  <a href="https://poedit.net/download" target="_blank">download Poedit</a>

|

Step 1: Initial setup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Start *Poedit*

* Open the ``.po`` file for the language you're working on. 
* Go to ``File`` > ``Preferences`` (on a PC), or ``Poedit`` > ``Settings`` on a Mac.

  * Add your name and e-mail address, where indicated   

* Go to ``Translation`` > ``Properties``.
  
  * Under the tab labled ``Translation properties``
    
    * ``Project name and version``: Type in *PsychoPy* followed by the |PsychoPy| version you are working on (usually the most recently released version of |PsychoPy|)
    * ``Language``: Scroll to and select the appropriate language or language variety (language + country; see above)
    * ``Charset``: Set this to *UTF-8*.
  * Under the tab labeled ``Sources Paths``
    
    * ``Base path``: Set this to the path on your computer that leads to the ``psychopy`` directory *within* the cloned repository on your computer. Assuming you forked and cloned the *psychopy* repository in the usual way, this path would appear as follows on your computer: ``..THE/PATH/ON/YOUR/COMPUTER/TO/psychopy/psychopy``   
  * Under the tab labeled ``Sources Keywords``

    * ``Additional keywords``: Make sure that the keyword ``_translate`` is listed in that box. If not, type it in.   
* Save your work (``File`` > ``Save``)   

Start your preferred text editor (e.g., *TextEdit*, *Visual Studio Code*, *PyCharm*)

* Go to ``psychopy/app/localization/mappings.txt`` in the repository

  * Find or type in the appropriate ``ll_CC`` code at the appropriate line (entries are listed alphabetically)
  * Add the 3-letter Microsoft code that refers to the language. These can be found in the rightmost column (`Language code`) on |msListOfLangIDsAndLocales|.
  * At the far right, be sure that there is a label for the language (and possibly country) that should be familiar to people who read that language, followed by the same in English, but in parentheses. The purpose is to highlight the name of the language as written in the non-English language itself. For example:
  
    *  " ``español, España (Spanish, Spain)``" (not just "``Spanish``")   
    *  " ``עִברִית (Hebrew)``" (not just "``Hebrew``")   
* Save the altered ``mappings.txt`` file in your editor

.. note:: 
  In some language varieties, like the example of Spanish above, you might find it appropriate to include the country of the locale as well. This is important for Spanish since there are varieties that differ significantly (e.g., Argentinean Spanish, Mexican Spanish). But notice that writing *Hebrew, Israel* would probably not be necessary since there is practially only one variety of the language that anyone would ever expect to see in a software program.

.. |msListOfLangIDsAndLocales| raw:: html

  <a href="https://learn.microsoft.com/en-us/previous-versions/windows/embedded/ms903928(v=msdn.10)?redirectedfrom=MSDN" target="_blank">Microsoft's list of Language Idenfiers and and Locales</a>

|

Step 2: Generate a list of strings to translate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
 
* In *Poedit*, go to the ``Translation`` menu and select ``Update from Source Code``. As long as you added ``_translate`` to the keywords (see above), you should subsequently see a list of strings that need translating in your language. An example is shown below (from Swedish, which does not yet have any translations).

.. image:: /images/poeditUntranslatedStringsSwedish.png
  :width: 80%
  :align: center
  :alt: Screenshot of untranslated strings that appear after the user selects "translation" from the menu in Poedit, followed by selecting "update from source code." The example is from Swedish. The highlighted source text is "Your stimulus size exceeds the {dimension} of your window." The window on the right is blank since, as of the writing of this, no strings for Swedish had been translated.
  
|

Step 3a: Translate the strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
* From the list, select a string that you want to translate.
* Once selected, you should see it appear as English in the ``Source text`` box below the list.
* Type in your translation to the box under ``Translation``. A screenshot of the relatively complete file for Japanese is shown below.
  
.. image:: /images/poeditTranslatedStringsJapanese.png
  :width: 99%
  :align: center
  :alt: Screenshot of translated strings that appear after the translator adds translations. The example is from Japanese. The highlighted source text is the PsychoPy string "Cannot calculate parameter," with the Japanese translation to the right of it.

|

* If you think your translation might have room for improvement, toggle the ``Needs Work`` button to the right of the ``Translation`` header
* You can also add notes by clicking the ``Add Comment`` button to the lower-right of the app window if you have the sidebar visible.
* Save your work (``File > Save``).

|

Some important notes
^^^^^^^^^^^^^^^^^^^^^^^

* Technical terms should not be translated: ``Builder``, ``Coder``, |PsychoPy|, ``Flow``, ``Routine``, and so on. (See the Japanese translation for guidance.)
* If there are formatting arguments in the original string (``%s``, ``%(first)i``), the same number of arguments must also appear in the translation, though their position in the translation would be dictated by the word-order rules of the language being translated into). If they are named (e.g., ``%(first)i``), that part should not be translated -- here ``first`` is a python name.
* Sometimes, you will not understand what a particular function does in |PsychoPy|, and you may be unable to translate it. There are a few possible things you can do in this situation. 
  
  * Ask
  
    * Go to the |psychopyForum|. There are friendly, useful experts there. 
    
      * Click ``+ New Topic``
      * Choose *Development* as the ``category``
      * Type in ``translation`` as an ``optional tag``
      * Type in your question in English, of course
      * The reasons for the category and the tag is to alert the people more involved with the underlying code of |PsychoPy|
  * Determine it yourself
  
    * Place your mouse over the relevant string in the ``Source text`` box and right-click it (control-click on a Mac). You can see where the string is defined under ``Code Occurrences`` with the file(s), followed by a colon, ``:``, then the respective line number. You can then go into that file (or those files) to determine the function. Naturally, you need to understand *Python* quite well to take this approach.   
  * Do nothing
    
    * If still in doubt, just leave out the translation until you do understand. There is nothing wrong with this approach. It is, by far, preferable to mis-translating a string. Use the ``Needs Work`` or ``Add Comment`` in *Poedit*, if you feel it is appropriate.   

.. |psychopyForum| raw:: html

  <a href="https://discourse.psychopy.org/" target="_blank">PsychoPy Forum on discourse.org</a>

|

Step 3b: Translating the *Start-up Tips*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Instead of being translated as a set of strings in a ``.po`` file, all of the *start-up tips* in US-English are stored in a separate, single ``.txt`` file called ``tips.txt``. This file is then generated as a  string under ``Source text - English`` in the ``.po`` file. If there are translations of these tips for another language, they are stored in separate ``.txt`` file in the same directory, but with a different name (e.g., ``tips_es_ES.txt``). This new file is then listed as the translation for ``tips.txt`` in *Poedit*. This is explained next.

The default *Start-up Tips* file (in US-English) is named ``tips.txt`` and is located in the following directory ``psychopy/app/Resources/``.

 To create the same file for another language, do the following:

* Go to ``psychopy/app/Resources/``
* Copy ``tips.txt`` to a new file
* Rename it according to the ``ll_CC`` convention (or possibly just ``ll``) consistent with the language you're working on, whichever is appropriate (e.g., ``tips_zh_CN.txt`` for simplified Chinese, or ``tips_ar_001.txt`` for Modern Standard Arabic)
* Open the new, renamed file using your preferred text editor
* Translate the English-language tips by replacing them entirely with those of the language you are working on

.. note:: 
  This may be a little bit obvious, but it would be a good idea *not* to delete any English entry in the new ``.txt`` file before you have completely translated it, or decided it is not appropriate. If you are going to translate one of the tips, it would be wise to insert the relevant translation below the English entry, and then delete the English entry only when the translation on the new line is complete.

|

* Save your work
* Open *Poedit*
* Find the string ``tips.txt``  under ``Source text - English`` (the easiest way is ``Edit > Find > Find: tips.txt``)
* Where you would normally provide a translation for it, simply provide the name of the new ``.txt`` file that you just created. See the screenshot below for the case of Japanese.

.. image:: /images/poeditTipsIntoJapanese.png
  :width: 80%
  :align: center
  :alt: Screenshot of how to provide text in the form of "tips_[ll_CC].txt" instead of a translation in Poedit of the string "tips.txt" The example is from Japanese.

|

.. note:: 
   Some of the humor in the *Start-up tips* might not translate well, so feel free to leave out things that would be too odd, or include occasional mild humor that would be more appropriate. Humor must be respectful and suitable for using in a classroom, laboratory, or other professional situation. Don't get too creative here. If you have any doubt, it is better to leave it out. It goes without saying that you should avoid any religious, political, disrespectful, or sexist material.

|

Step 4: The git commit and the pull request
---------------------------------------------
* Commit the files that you have changed
  
  * Usually, this is at least the ``.po`` file 
  * But it could comprise or include other relevant files (e.g., ``tips_[ll_CC].txt``, ``localization/mappings.txt``)
  * Use the prefix ``DOCS:`` in your commit message 
* Push the commit to your repository on *GitHub* (aka *origin*)
* From *origin* on GitHub, make your pull request to the *release* branch of the |PsychoPy| repository as outlined in :ref:`how to contribute to PsychoPy<usingRepos>`

.. _newLangSubdirect:

|

If necessary, create a new language subdirectory
----------------------------------------------------

The default list of languages we have provided is clearly not exhaustive. (|estimatedWorldLanguages| suggest that there are between 6,000 and 8,000 human languages in the world, depending on how you define *language*!) So you may indeed find it necessary to create a new directory containing the ``.po`` file necessary to enable |PsychoPy| to operate in the language you want to translate into.

If this is the case, feel free to add your language or language variety. Below is an explanation of the easiest way to do this, followed by finding the most appropriate label for your new subdirectory.

.. |estimatedWorldLanguages| raw:: html

  <a href="https://www.linguisticsociety.org/content/how-many-languages-are-there-world" target="_blank">Current estimates on the number of languages in the world</a>

|

The easiest way to do this
^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 

The easiest way to get started is to copy and paste one of the other ``ll_CC`` directories, then rename it. Then you can make adjustments to the ``messages.po`` file inside. How to do this is covered up above in the section called *The translation process in Poedit*.

The immediate question, however, is what to rename it **to**. This may require some forethought involving linguistic and cultural appropriateness.

|

What to name the new directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Whichever ``ll_CC`` label you use, please be as inclusive as you possibly can, within reason. Naturally, you are the expert here since you actually know the language, its varieties, and any political implications involved. Make sure, however, that you are highly proficient in whichever one you choose.

If in doubt, please feel free to discuss this with the |PsychoPy| team directly, or on the forum under the *Development* category. The same is true if you cannot find your language at all in the |listOfLanguagesAtGettext|: Please talk with the |PsychoPy| team to find a solution.

* Chinese

  * Chinese is a good example of when locale matters a great deal. Simplified Chinese characters are used in mainland China (``zh_CN``), whereas traditional Chinese characters are used in Taiwan (``zh_TW``).

* German

  * In the case of German however, most German speakers around the world expect to read in High German, which is ``de_DE``. They would not normally expect to see Swiss German (``de_CH``), at least not without *also* seeing High German. 

* Arabic

  * Similarly, most readers of Arabic are going to expect to see Modern Standard Arabic, which has the slightly odd ``ll_CC`` code of ``ar_001`` as it is not the native dialect of any particular country. Spoken regional varieties of Arabic *in the written form* are only ever seen in specialized contexts.

* English

  * Another example is English. The default variety of English for |PsychoPy| is American English (``en_US``). One could include a translation for British English (``en_GB``), but the effort required of such a translation with such minor (mostly spelling) differences hardly seems worth it.

.. |listOfLanguagesAtGettext| raw:: html

  <a href="https://www.gnu.org/software/gettext/manual/gettext.html#Language-Codes" target="_blank">list of languages at Gettext</a>

|

Return to :ref:`The translation process in Poedit<translateProcess>`