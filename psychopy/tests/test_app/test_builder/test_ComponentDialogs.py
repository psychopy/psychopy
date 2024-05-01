
import pytest

from psychopy import experiment
from psychopy.app.builder.dialogs import DlgCodeComponentProperties
from psychopy.experiment.components.code import CodeComponent


class TestComponentDialogs:

    def setup_method(self):
        # Create experiment
        self.exp = experiment.Experiment()
        self.exp.addRoutine(
            "testRoutine",
            experiment.routines.Routine("testRoutine", self.exp)
        )

    @pytest.mark.usefixtures("get_app")
    def test_code_component_changed_marking(self, get_app):
        """
        Tests that, when opening a Code component dialog, the correct tabs are marked based on the contents
        """
        _nl = "\n"
        # Create frame
        frame = get_app.newBuilderFrame()
        # Define cases by which fields are populated, which tab should be open first and which tabs should be starred
        cases = [
            # JS populated then py
            {'params': ["Begin JS Routine", "Each Frame"],
             'first': "Begin Routine",
             'starred': ["Begin Routine", "Each Frame"]},
            # JS populated then both then py
            {'params': ["Begin JS Routine", "Each Frame", "Each JS Frame", "End Routine"],
             'first': "Begin Routine",
             'starred': ["Begin Routine", "Each Frame", "End Routine"]},
            # Py populated then both then js
            {'params': ["Begin Routine", "Each Frame", "Each JS Frame", "End JS Routine"],
             'first': "Begin Routine",
             'starred': ["Begin Routine", "Each Frame", "End Routine"]},
            # Py populated then js
            {'params': ["Begin Routine", "Each JS Frame"],
             'first': "Begin Routine",
             'starred': ["Begin Routine", "Each Frame"]},
            # All populated
            {'params': ["Before Experiment", "Before JS Experiment", "Begin Experiment", "Begin JS Experiment",
                        "Begin Routine", "Begin JS Routine", "Each Frame", "Each JS Frame", "End Routine",
                        "End JS Routine", "End Experiment", "End JS Experiment"],
             'first': "Before Experiment",
             'starred': ["Before Experiment", "Begin Experiment", "Begin Routine", "Each Frame", "End Routine",
                         "End Experiment"]},
            # None populated
            {'params': [],
             'first': "Begin Experiment",
             'starred': []},
        ]
        # For each case...
        for case in cases:
            # Create Code component
            comp = CodeComponent(
                exp=self.exp, parentName="testRoutine", codeType="Both"
            )
            # Assign values from case
            for param in case['params']:
                comp.params[param].val = "x = 1"  # Dummy code just so there's some valid content
            # Make dialog
            dlg = DlgCodeComponentProperties(
                frame=frame,
                element=comp,
                experiment=self.exp,
                timeout=200
            )
            # Check that correct tab is shown first
            pg = dlg.codeNotebook.GetCurrentPage()
            i = dlg.codeNotebook.FindPage(pg)
            tabLabel = dlg.codeNotebook.GetPageText(i)
            assert case['first'].lower() in tabLabel.lower(), (
                f"Tab {case['first']} should be opened first when the following fields are populated:\n"
                f"{_nl.join(case['params'])}\n"
                f"Instead, first tab open was {tabLabel}"
            )
            # Check that correct tabs are starred
            for i in range(dlg.codeNotebook.GetPageCount()):
                tabLabel = dlg.codeNotebook.GetPageText(i)
                populated = any(name.lower() in tabLabel.lower() for name in case['starred'])

                if populated:
                    assert "*" in tabLabel, (
                        f"Tab '{tabLabel}' should include a * when the following fields are populated:\n"
                        f"{_nl.join(case['params'])}"
                    )
                else:
                    assert "*" not in tabLabel, (
                        f"Tab '{tabLabel}' should not include a * when the following fields are populated:\n"
                        f"{_nl.join(case['params'])}"
                    )
        # Close frame
        frame.closeFrame()
