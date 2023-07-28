from pathlib import Path

from . import _TestDisabledMixin, _TestBaseComponentsMixin
from psychopy.experiment import Experiment
from psychopy.experiment.loops import TrialHandler
from psychopy.experiment.routines import Routine
from psychopy.experiment.components.mouse import MouseComponent
from psychopy.experiment.components.polygon import PolygonComponent
from psychopy.tests.utils import TESTS_DATA_PATH
from psychopy.hardware.mouse import Mouse


class TestMouseComponent(_TestBaseComponentsMixin, _TestDisabledMixin):
    """
    Test that Mouse coponents have the correct params and write as expected.
    """
    libraryClass = Mouse

    def setup_method(self):
        # Make blank experiment
        self.exp = Experiment()
        # Make blank routine
        self.routine = Routine(name="testRoutine", exp=self.exp)
        self.exp.addRoutine("testRoutine", self.routine)
        self.exp.flow.addRoutine(self.routine, 0)
        # Add loop around routine
        self.loop = TrialHandler(exp=self.exp, name="testLoop")
        self.exp.flow.addLoop(self.loop, 0, -1)
        # Make Mouse component
        self.comp = MouseComponent(exp=self.exp, parentName="testRoutine", name="testMouse")
        self.routine.addComponent(self.comp)
        # Make a rect for when we need something to click on
        self.target = PolygonComponent(exp=self.exp, parentName="testRoutine", name="testPolygon")
        self.routine.addComponent(self.target)

    def test_click_save_end_clickable_cases(self):
        """
        Test all combinations of options for what to save, what can be clicked on & what kind of clicks to end the
        routine on.
        """
        saveMouseStateCases = [
            {'val': "final",
             'want': ["thisExp.addData('testMouse.x', x)"],  # should contain code for adding final value of x
             'avoid': ["testMouse.x.append(x)"]},  # should not contain code to update testMouse.x in frame loop
            {'val': "on click",
             'want': ["thisExp.addData('testMouse.x', testMouse.x)",  # should add testMouse.x at the end
                      "testMouse.x.append(x)"],  # should contain code to update testMouse.x in frame loop
             'avoid': ["thisExp.addData('testMouse.x', x)"]},  # should not add final value of x
            {'val': "on valid click",
             'want': ["thisExp.addData('testMouse.x', testMouse.x)",  # should add testMouse.x at the end
                      "testMouse.x.append(x)",  # should contain code to update testMouse.x in frame loop
                      "if gotValidClick:"],  # should check for valid clicks
             'avoid': ["thisExp.addData('testMouse.x', x)"]},  # should not add final value of x
            {'val': "every frame",
             'want': ["thisExp.addData('testMouse.x', testMouse.x)",  # should add testMouse.x at the end
                      "testMouse.x.append(x)"],  # should contain code to update testMouse.x in frame loop
             'avoid': ["thisExp.addData('testMouse.x', x)"]},  # should not add final value of x
            {'val': "never",
             'want': [],
             'avoid': ["thisExp.addData('testMouse.x', testMouse.x)",  # should not add testMouse.x at the end
                       "testMouse.x.append(x)",  # should not contain code to update testMouse.x in frame loop
                       "thisExp.addData('testMouse.x', x)"]},  # should not add final value of x]},
        ]
        forceEndRoutineOnPressCases = [
            {'val':  "never",
             'want': [],
             'avoid': ["# end routine on response",  # should not include code to end routine
                       "# end routine on response"]},
            {'val': "any click",
             'want': ["# end routine on response"],  # should include code to end routine on response
             'avoid': []},
            {'val': "valid click",
             'want': ["# end routine on response",  # should include code to end routine on response
                      "if gotValidClick:"],  # should check for valid clicks
             'avoid': []},
        ]
        clickableCases = [
            {'val': "[]",
             'want': [],
             'avoid': ["clickableList = [testPolygon]"]},  # should not define a populated clickables list
            {'val': "[testPolygon]",
             'want': [],
             'avoid': ["clickableList = []"]},  # should not define a blank clickables list
        ]
        # Iterate through saveMouseState cases
        for SMScase in saveMouseStateCases:
            # Set saveMouseState
            self.comp.params['saveMouseState'].val = SMScase['val']
            for FEROPcase in forceEndRoutineOnPressCases:
                # Set forceEndRoutineOnPress
                self.comp.params['forceEndRoutineOnPress'].val = FEROPcase['val']
                for Ccase in clickableCases:
                    # Set clickable
                    self.comp.params['clickable'].val = Ccase['val']

                    # Compile script
                    script = self.exp.writeScript(target="PsychoPy")
                    try:
                        # Look for wanted phrases
                        for phrase in SMScase['want']:
                            assert phrase in script, (
                                f"{phrase} not found in script when saveMouseState={self.comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={self.comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={self.comp.params['clickable']}"
                            )
                        for phrase in FEROPcase['want']:
                            assert phrase in script, (
                                f"{phrase} not found in script when saveMouseState={self.comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={self.comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={self.comp.params['clickable']}"
                            )
                        for phrase in Ccase['want']:
                            assert phrase in script, (
                                f"{phrase} not found in script when saveMouseState={self.comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={self.comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={self.comp.params['clickable']}"
                            )
                        # Check there's no avoid phrases
                        for phrase in SMScase['avoid']:
                            assert phrase not in script, (
                                f"{phrase} found in script when saveMouseState={self.comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={self.comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={self.comp.params['clickable']}"
                            )
                        for phrase in FEROPcase['avoid']:
                            assert phrase not in script, (
                                f"{phrase} found in script when saveMouseState={self.comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={self.comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={self.comp.params['clickable']}"
                            )
                        for phrase in Ccase['avoid']:
                            assert phrase not in script, (
                                f"{phrase} found in script when saveMouseState={self.comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={self.comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={self.comp.params['clickable']}"
                            )
                    except AssertionError as err:
                        # If any assertion fails, save script to view
                        filename = Path(TESTS_DATA_PATH) / f"{__class__.__name__}_clicks_cases_local.py"
                        with open(filename, "w") as f:
                            f.write(script)
                        # Append ref to saved script in error message
                        print(
                            f"\n"
                            f"Case: {SMScase} {FEROPcase} {Ccase}\n"
                            f"Script saved at: {filename}\n"
                        )
                        # Raise original error
                        raise err
