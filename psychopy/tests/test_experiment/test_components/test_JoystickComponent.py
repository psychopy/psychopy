from . import BaseComponentTests
from psychopy.experiment.components.joystick import JoystickComponent


class TestJoystickComponent(BaseComponentTests):
    """
    Test that Joystick components have the correct params and write as expected.
    """
    comp = JoystickComponent

    def test_start_stop_written_for_all_save_end_cases(self):
        """
        Test that start/stop code is always written, regardless of what is saved or whether a
        press ends the Routine - otherwise status never reaches FINISHED and the Routine never
        ends (see #7865).
        """
        # make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
        comp.params['stopType'].val = "duration (s)"
        comp.params['stopVal'].val = 1

        for saveCase in ['final', 'on click', 'every frame', 'never']:
            comp.params['saveJoystickState'].val = saveCase
            for endCase in ['never', 'any click', 'valid click']:
                comp.params['forceEndRoutineOnPress'].val = endCase
                # compile script
                script = exp.writeScript(target="PsychoPy")
                case = f"saveJoystickState={saveCase}, forceEndRoutineOnPress={endCase}"
                # should always write start and stop code
                assert f"{comp.name}.status = STARTED" in script, (
                    f"No start code written when {case}"
                )
                assert f"{comp.name}.status = FINISHED" in script, (
                    f"No stop code written when {case}"
                )
                # should only poll in the frame loop if storing as we go or ending on press
                polls = f"{comp.name}.poll()  # refresh the joystick state" in script
                wantPoll = saveCase in ['on click', 'every frame'] or endCase != 'never'
                assert polls == wantPoll, (
                    f"Joystick {'polled' if polls else 'not polled'} in frame loop when {case}"
                )
