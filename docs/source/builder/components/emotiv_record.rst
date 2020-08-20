.. _emotiv_record:

Emotiv Record Component
-------------------------------

The emotiv_record component causes Psychopy to connect to the headset so that markers
can be sent to the datastream.

The emotiv_record component should be added ONCE before any stimuli have been presented at the top of 
first trial of the experiment. 

We recommend that you use the EmotivApp and or EmotivPro software to
establish that the headset is connected and the quality of the signals are good before running
the experiment with Psychopy.

If you do want PschoPy to record the data into a gzipped csv file you need to set an environment
variable CORTEX_DATA=1. Otherwise we recommend viewing the eeg data in EmotivPro from which it can be 
exported as a csv or edf file.

Getting Started
===============

Before you can connect Psychopy to Emotiv hardware, you need to register your AppId on the Emotiv
website (https://emotiv.com) Goto My Account > Cortex Apps.  There you will get a client_id and
a client_secret that you need to copy into a file called .emotiv_creds in your home directory.
One line should have "client_id" (without the quotes) then a space and then the client_id,
another line should have "client_secret" (without the quotes and then as space and then the
client secret.  A line beginning with a hash will be ignored. eg

| ---begin file ---
| # client_id and client_secret for Emotiv application
| client_id abcd1234...
| client_secret wxyz78910....
| ---end file---

Parameters
~~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only
    letters, numbers and underscores (no punctuation marks or spaces).

Start :
    Has no effect

Stop :
    Has no effect
