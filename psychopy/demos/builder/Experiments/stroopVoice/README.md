# Stroop - measuring reaction times to incongruent stimuli

## The experiment: 
    
In this task subjects must speak the letters spelling each word, ignoring the word 
that they spell!

Note that PsychoPy can use various different engines ()"backends") to achieve the transcription. Locally you can use the psychopy-whisper but online you need either Google or Microsoft and, for that, you need an "API key" from those sites.

To use Whisper locally you will need the `psychopy-whisper` plugin which can be installed from
   >Tools>Plugin/packages manager...

## How is (local Whisper) transcription achieved?

Whisper is built on the OpenAI large language model (LLM) using the same technology that brought you ChatGPT. This is NOT sending any information to OpenAI/ChatGPT, however, and does not require any subscription or user account. In fact after the first operation, where the language model is downloaded, you won't even need a network connection to run the transcription.

In the micResp/Transcription settings of the demo, you'll see an option to select the transcription engine (Google is another option which has the advantage that it can be used online but requires a username/API key). When Whisper is seleced as the transcription engine, there is also a setting to choose which language model to use. There are several sized models (large models give more accuracy but are slower and we've found the small mdels to be very good) and the option to use and English-only model (with .en in the name) whereas the standard models are multi-lingual.

## When does transcription occur and how long does it take?

If the Mic is set to perform transcription then it will be performed during the end of the current Routine, and it could take several seconds during which the experiment won't progress, so do bear that in mind when designing your study.

The transcription time depends on the duration of the speech in the response, the size of the model selected, and on the computer that you use. 10 seconds of speaking may take 5-10 seconds to transcribe on the small model on a decent PC.

If you have a powerful nVidia graphics card then you may be able to install the CUDA libraries and, if these are available, then psychopy-whisper will make use of the graphics card and the transcription will run much faster.

See https://github.com/guillaumekln/faster-whisper for more details about the underlying lib that PsychoPy is using (called `faster-whisper`)
