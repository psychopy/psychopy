import pytest
from psychopy import core, constants, sound, validation
from psychopy.hardware import microphone, voicekey, DeviceManager


@pytest.mark.needs_sound
class TestVoiceKeyValidator:
    def setup_class(cls):
        cls.vk = cls.speaker = None
        # find best vk/speaker pair to use
        for profile in DeviceManager.getAvailableDevices(
            "psychopy.hardware.voicekey.MicrophoneVoiceKeyEmulator"
        ):
            # setup voicekey
            try:
                # make sure the mic exists
                if not DeviceManager.getDevice(profile['device']):
                    for micProfile in DeviceManager.getAvailableDevices(
                        "psychopy.hardware.microphone.MicrophoneDevice"
                    ):
                        if micProfile['index'] == profile['device']:
                            DeviceManager.addDevice(**micProfile)
                # create voicekey emulator
                vk = DeviceManager.addDevice(**profile)
            except Exception as err:
                continue
            # find matching speakers
            foundSpeakers = vk.findSpeakers(channel=0)
            # check that speakers can be initialised
            for speaker in foundSpeakers:
                try:
                    sound.Sound("A", speaker=speaker)
                except:
                    continue
                else:
                    # if successful, we have a matching pair!
                    cls.speaker = speaker
                    cls.vk = vk
        # skip if no devices were found
        if cls.vk is None or cls.speaker is None:
            pytest.skip()
        # create validator
        cls.validator = validation.VoiceKeyValidator(cls.vk)
    
    def test_soundHeard(self):
        """
        Check that the voicekey validator detects a sound played from an audible speaker.
        """
        # setup timing
        clock = core.Clock()
        self.validator.resetTimer(clock)
        t = 0
        # setup sound
        snd = sound.Sound("A", speaker=self.speaker)
        snd.tStart = snd.tStop = None
        # set starting statuses
        snd.status = self.validator.status = constants.NOT_STARTED
        # begin a frame loop
        while t < 3:
            t = clock.getTime()
            # validate start
            if self.validator.status == constants.STARTED and snd.status == constants.STARTED:
                self.validator.tStart, self.validator.valid = self.validator.validate(
                    state=True, 
                    t=snd.tStart,
                    adjustment=0.12
                )
                if self.validator.tStart:
                    self.validator.status = constants.FINISHED
                    assert self.validator.valid            
            # validate stop
            if self.validator.status == constants.STARTED and snd.status == constants.FINISHED:
                self.validator.tStop, self.validator.valid = self.validator.validate(
                    state=False, 
                    t=snd.tStop,
                    adjustment=0
                )
                if self.validator.tStop:
                    self.validator.status = constants.FINISHED
                    assert self.validator.valid
            # start sound
            if snd.status == constants.NOT_STARTED and t > 1:
                snd.play()
                snd.tStart = t
                snd.status = constants.STARTED
                self.validator.status = constants.STARTED
            # stop sound
            if snd.status == constants.STARTED and t > 2:
                snd.stop()
                snd.tStop = t
                snd.status = constants.FINISHED
                self.validator.status = constants.STARTED
        # make sure the validator got some times
        assert self.validator.tStart is not None
        assert self.validator.tStop is not None
