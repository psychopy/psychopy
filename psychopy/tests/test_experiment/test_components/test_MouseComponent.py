from pathlib import Path

from . import BaseComponentTests
from psychopy.experiment.loops import TrialHandler
from psychopy.experiment.components.mouse import MouseComponent
from psychopy.experiment.components.polygon import PolygonComponent
from psychopy.tests.utils import TESTS_DATA_PATH
from psychopy.hardware.mouse import Mouse


class TestMouseComponent(BaseComponentTests):
    """
    Test that Mouse coponents have the correct params and write as expected.
    """
    comp = MouseComponent
    libraryClass = Mouse

    def test_click_save_end_clickable_cases(self):
        """
        Test all combinations of options for what to save, what can be clicked on & what kind of clicks to end the
        routine on.
        """
        # make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
        # make a rect for when we need something to click on
        target = PolygonComponent(exp=exp, parentName=rt.name, name="testPolygon")
        
        saveMouseStateCases = [
            {'val': "final",
             'want': [f"thisExp.addData('{comp.name}.x', x)"],  # should contain code for adding final value of x
             'avoid': [f"{comp.name}.x.append(x)"]},  # should not contain code to update testMouse.x in frame loop
            {'val': "on click",
             'want': [f"thisExp.addData('{comp.name}.x', {comp.name}.x)",  # should add testMouse.x at the end
                      f"{comp.name}.x.append(x)"],  # should contain code to update testMouse.x in frame loop
             'avoid': [f"thisExp.addData('{comp.name}.x', x)"]},  # should not add final value of x
            {'val': "on valid click",
             'want': [f"thisExp.addData('{comp.name}.x', {comp.name}.x)",  # should add testMouse.x at the end
                      f"{comp.name}.x.append(x)",  # should contain code to update testMouse.x in frame loop
                      "if gotValidClick:"],  # should check for valid clicks
             'avoid': [f"thisExp.addData('{comp.name}.x', x)"]},  # should not add final value of x
            {'val': "every frame",
             'want': [f"thisExp.addData('{comp.name}.x', {comp.name}.x)",  # should add testMouse.x at the end
                      f"{comp.name}.x.append(x)"],  # should contain code to update testMouse.x in frame loop
             'avoid': [f"thisExp.addData('{comp.name}.x', x)"]},  # should not add final value of x
            {'val': "never",
             'want': [],
             'avoid': [f"thisExp.addData('{comp.name}.x', {comp.name}.x)",  # should not add testMouse.x at the end
                       f"{comp.name}.x.append(x)",  # should not contain code to update testMouse.x in frame loop
                       f"thisExp.addData('{comp.name}.x', x)"]},  # should not add final value of x]},
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
            comp.params['saveMouseState'].val = SMScase['val']
            for FEROPcase in forceEndRoutineOnPressCases:
                # Set forceEndRoutineOnPress
                comp.params['forceEndRoutineOnPress'].val = FEROPcase['val']
                for Ccase in clickableCases:
                    # Set clickable
                    comp.params['clickable'].val = Ccase['val']

                    # Compile script
                    script = exp.writeScript(target="PsychoPy")
                    try:
                        # Look for wanted phrases
                        for phrase in SMScase['want']:
                            assert phrase in script, (
                                f"{phrase} not found in script when saveMouseState={comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={comp.params['clickable']}"
                            )
                        for phrase in FEROPcase['want']:
                            assert phrase in script, (
                                f"{phrase} not found in script when saveMouseState={comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={comp.params['clickable']}"
                            )
                        for phrase in Ccase['want']:
                            assert phrase in script, (
                                f"{phrase} not found in script when saveMouseState={comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={comp.params['clickable']}"
                            )
                        # Check there's no avoid phrases
                        for phrase in SMScase['avoid']:
                            assert phrase not in script, (
                                f"{phrase} found in script when saveMouseState={comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={comp.params['clickable']}"
                            )
                        for phrase in FEROPcase['avoid']:
                            assert phrase not in script, (
                                f"{phrase} found in script when saveMouseState={comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={comp.params['clickable']}"
                            )
                        for phrase in Ccase['avoid']:
                            assert phrase not in script, (
                                f"{phrase} found in script when saveMouseState={comp.params['saveMouseState']}, "
                                f"forceEndRoutineOnPress={comp.params['forceEndRoutineOnPress']} and "
                                f"clickable={comp.params['clickable']}"
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
