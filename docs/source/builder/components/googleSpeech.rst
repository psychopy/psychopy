.. _googleSpeech:

Creating a Google Cloud Speech API key
=========================================

There are a few steps but they’re relatively easy. Pricing is free for the first 60 minutes per month and 1-2cents per minute after that
Information here:
https://cloud.google.com/speech-to-text

Note that You might be asked to enter card details but you are not charged an auto update unless you manually enter the card details when prompted

Steps
------

- Create an account on `Google Cloud Platform <https://cloud.google.com/>`_ (this is not the same as simply gmail or Google Worksuite)
- Create a project from here: https://console.cloud.google.com/home/dashboard by selecting manage resources > create project The projects could just be for the entire lab, say, or for each experiment, depending on the granularity you need for billing (We believe)
- Enable the Speech API for that project: select the project in the manage resources page, go to https://console.cloud.google.com/apis/library/speech.googleapis.com click "enable".
- Then click on Credentials and create Service Account credentials. 

.. figure:: /images/google_speech_service_acc.png
	
	Add credentials to your Google cloud project and select "Service Account".

- Grant the service account access to Google Speech Client.

.. figure:: /images/service_acc_setup.png
	
	Search for "Google Speech Client" and give this account access to that API.


- Once you have your service account set up you can add a key and make a downloadable JSON file. Store it somewhere (private) on your computer. You don't need to go through these steps for every new project - once you have a key you can use it for all of your projects.

.. warning::
	Be careful not to store the json file in the same location as any experiment folder that might later be shared on |Pavlovia| - this is a private file - so keep it somewhere safe.


.. figure:: /images/make_json.png
	
	Generate a downloadable JSON for this project.

- Finally, in |PsychoPy| go fo File > Preferences and add the path to the JSON file in General > appKeyGoogleCloud.

.. figure:: /images/appkey_preferences.png
	
	Setup your |PsychoPy| preferences to use your downloaded JSON - this will apply to all experiments using the mic - not just this |PsychoPy| experiment.

.. warning:: 
	Remember to check that your accounts billing information stays up to date. Even if you haven't done enough recordings to warrant a large payment, if a card on your billing account expires this will invalidate the JSON key and raise a "billing" error in |PsychoPy|.
