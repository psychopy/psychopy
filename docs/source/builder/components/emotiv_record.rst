.. _emotiv_record:

Emotiv Record Component
-------------------------------

The emotiv_record component causes Psychopy to connect to the headset so that markers
can be sent to the datastream.

The emotiv_record component should be added ONCE before any stimuli have been presented at the top of 
first trial of the experiment. 

We recommend that you use the EmotivLauncher and or EmotivPro software to
establish that the headset is connected and the quality of the signals are good before running
the experiment with Psychopy.

We recommend viewing the eeg data in EmotivPro from which it can be
exported as a csv or edf file.  However, if you do want PschoPy to record the
data into a gzipped csv file you need to set an environment
variable CORTEX_DATA=1. Additionally you will need to apply for a RAW EEG API license.
See: https://emotiv.gitbook.io/cortex-api/#prerequisites for more details.

If you are exporting the experiment to HTML the emotiv components will have no effect in Pavlovia.
To import the experiment into Emotiv OMNI, export the experiment to HTML and follow the instructions
in the OMNI platform.

Getting Started
===============

Before you can connect Psychopy to Emotiv hardware, you need to register your AppId on the Emotiv
website (https://emotiv.com).

**Note**: Normally you should **NOT** click the checkbox:
"My App requires EEG access".  Otherwise you will need to apply for a RAW EEG API license.

Login to your account at emotiv.com, Goto My Account > Cortex Apps.
There you will get a client_id and
a client_secret that you need to copy into a file called .emotiv_creds in your home directory.
One line should have "client_id" (without the quotes) then a space and then the client_id,
another line should have "client_secret" (without the quotes and then as space and then the
client secret.  A line beginning with a hash will be ignored. eg

| ---begin file ---
| # client_id and client_secret for Emotiv application
| client_id abcd1234...
| client_secret wxyz78910....
| ---end file---

Troubleshooting
===============

* Check that the .emotiv_creds file does not have ".txt" file extension.
* Ensure the file format is exactly correct (do **not** include the begin and end file lines)
* Ensure that your AppId does not require EEG data **or** apply for RAW EEG API access through EMOTIV support.
* Ensure you connect your headset using EmotivPro or EmotivLauncher before you run the experiment.

Parameters
~~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only
    letters, numbers and underscores (no punctuation marks or spaces).

Start :
    Set this to 0

Stop :
    Set this to 1 seconds

Setting these values just allows the routine to finish
