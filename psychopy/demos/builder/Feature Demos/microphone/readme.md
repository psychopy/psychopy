# Microphone

This demo shows off the recording and transcription capabilities of the microphone component. It will present some phrases to read out, then will display what the Microphone component heard.

This demo uses the OpenAI's Whisper transcriber. You can find out more from https://github.com/openai/whisper

The ```load_dictionary``` routine allows the microphones to initialise.

The ```fixation``` routine allows some buffer time before the microphone is initialise to when it needs to start recording each trial.