from pathlib import Path

from . import _TestDisabledMixin, _TestBaseComponentsMixin
from psychopy.experiment import Experiment
from psychopy.experiment.loops import TrialHandler
from psychopy.experiment.routines import Routine
from psychopy.experiment.components.polygon import PolygonComponent
from psychopy.visual.polygon import Polygon


class TestPolygonComponent(_TestBaseComponentsMixin, _TestDisabledMixin):
    """
    Test that Polygon coponents have the correct params and write as expected.
    """
    libraryClass = Polygon

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
        # Make a rect for when we need something to click on
        self.comp = PolygonComponent(exp=self.exp, parentName="testRoutine", name="testPolygon")
        self.routine.addComponent(self.comp)

    def test_vertices_usage(self):
        """
        Test that vertices values are used only under the correct conditions
        """
        # Define values to look for and avoid in code according to value of shape
        cases = [
            # Shape is a line
            {'val': "line",
             'seek': ["visual.Line("],
             'avoid': ["___nVertices___", "___vertices___"]},
            {'val': "triangle",
             'seek': ["visual.ShapeStim("],
             'avoid': ["___nVertices___", "___vertices___"]},
            {'val': "rectangle",
             'seek': ["visual.Rect("],
             'avoid': ["___nVertices___", "___vertices___"]},
            {'val': "circle",
             'seek': ["visual.ShapeStim(", "vertices='circle'"],
             'avoid': ["___nVertices___", "___vertices___"]},
            {'val': "cross",
             'seek': ["visual.ShapeStim(", "vertices='cross'"],
             'avoid': ["___nVertices___", "___vertices___"]},
            {'val': "star",
             'seek': ["visual.ShapeStim(", "vertices='star7'"],
             'avoid': ["___nVertices___", "___vertices___"]},
            {'val': "regular polygon...",
             'seek': ["___nVertices___", "visual.Polygon("],
             'avoid': ["___vertices___"]},
            {'val': "custom polygon...",
             'seek': ["___vertices___", "visual.ShapeStim("],
             'avoid': ["___nVertices___"]},
        ]
        # Setup component with markers for nVertices and vertices
        self.comp.params['nVertices'].val = "___nVertices___"
        self.comp.params['vertices'].val = "___vertices___"
        # Test each case
        for case in cases:
            # Set shape
            self.comp.params['shape'].val = case['val']
            # Write experiment
            pyScript = self.exp.writeScript(target="PsychoPy")
            # Look for sought values in experiment script
            for seekVal in case['seek']:
                assert seekVal in pyScript, (
                    f"Could not find wanted value `{seekVal}` in experiment when polygon shape was {case['val']}."
                )
            # Look for avoid values in experiment script
            for avoidVal in case['avoid']:
                assert avoidVal not in pyScript, (
                    f"Found unwanted value `{avoidVal}` in experiment when polygon shape was {case['val']}."
                )
