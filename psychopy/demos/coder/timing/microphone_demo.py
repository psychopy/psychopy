import psychopy.core as core
import psychopy.sound as sound

## generate white noise
wn = sound.AudioClip.whiteNoise(1.0)
wn.save(r'C:\Users\matth\OneDrive\Desktop\white_noise.wav')

## getting connected microphones

microphones = sound.Microphone.getDevices()
## create a new microphone stream

recordingMicrophone = microphones[0]  # get the first device
print(recordingMicrophone.deviceName)  # print the device name

## initialize a microphone

# using the selected device, set recording quality to voice (16Khz)

mic = sound.Microphone(recordingMicrophone, sampleRateHz=sound.SAMPLE_RATE_48kHz,
                       bufferSecs=10.0)

## do a recording

mic.start()
core.wait(10.0)  # record for 10 seconds
myRecording, _, _, _ = mic.getAudioClip()  # get the audio clip as an AudioClip
mic.stop()  # end the recording

## get the RMS of the recording
print(myRecording.rms())

## save the result

myRecording.save(r'C:\Users\matth\OneDrive\Desktop\test_mic.wav')

## manipulate the audio we just recorded and saved

# load the clip
myRecording = sound.AudioClip.load(r'C:\Users\matth\OneDrive\Desktop\test_tone.wav')

# add silence and a cue tone to the end of the clip (like a voicemail message)
newSound = myRecording + \
           sound.AudioClip.silence(
               0.5, sampleRateHz=myRecording.sampleRateHz) + \
           sound.AudioClip.sine(
               5., 440, sampleRateHz=myRecording.sampleRateHz)

#  save the result as a flac file
myRecording.save(r'C:\Users\matth\OneDrive\Desktop\test_mic_with_cue.flac', codec='flac')

