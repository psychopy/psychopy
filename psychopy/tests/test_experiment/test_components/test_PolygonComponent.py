from psychopy.tests.test_experiment.test_components.test_base_components import BaseComponentTests, _TestLibraryClassMixin
from psychopy.experiment.components.polygon import PolygonComponent
from psychopy.visual.polygon import Polygon


class TestPolygonComponent(BaseComponentTests, _TestLibraryClassMixin):
    """
    Test that Polygon coponents have the correct params and write as expected.
    """
    comp = PolygonComponent
    libraryClass = Polygon

    def test_vertices_usage(self):
        """
        Test that vertices values are used only under the correct conditions
        """
        # make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
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
        comp.params['nVertices'].val = "___nVertices___"
        comp.params['vertices'].val = "___vertices___"
        # Test each case
        for case in cases:
            # Set shape
            comp.params['shape'].val = case['val']
            # Write experiment
            pyScript = exp.writeScript(target="PsychoPy")
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
