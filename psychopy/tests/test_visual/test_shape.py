import pytest
from psychopy import visual
from .test_basevisual import _TestColorMixin, _TestUnitsMixin, _TestSerializationMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin



class TestShape(_TestColorMixin, _TestUnitsMixin, _TestBoilerplateMixin, _TestSerializationMixin):

    @classmethod
    def setup_class(self):

        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        self.obj = visual.Rect(self.win, units="pix", pos=(0, 0), size=(128, 128), lineWidth=10)

        # Pixel which is the border color
        self.borderPoint = (0, 0)
        self.borderUsed = True
        # Pixel which is the fill color
        self.fillPoint = (50, 50)
        self.fillUsed = True
        # Shape has no foreground color
        self.foreUsed = False

    @classmethod
    def teardown_class(self):
        self.win.close()

    def test_lineWidthWarning(self, monkeypatch):
        """A warning is logged when lineWidth goes over the widest the OpenGL
        driver draws lines, once rather than every time it's set."""
        import io
        from psychopy import logging

        # lines up to 4 pix wide, whatever this computer draws
        monkeypatch.setattr(
            self.win, '_maxLineWidth', 4 * self.win.pixScaleFactor)
        stream = io.StringIO()
        logFile = logging.LogFile(stream, level=logging.WARNING)
        try:
            rect = visual.Rect(
                self.win, lineWidth=4, name='wideRect', autoLog=False)
            for lineWidth in (6, 8):  # over, and still over
                rect.lineWidth = lineWidth
            rect.lineWidth = 2  # back under
            rect.lineWidth = 5  # and over again
            logging.flush()
        finally:
            logging.root.removeTarget(logFile)

        warnings = [
            line for line in stream.getvalue().splitlines()
            if 'wideRect: lineWidth' in line]
        assert len(warnings) == 2, warnings
        assert 'lineWidth of 6 pix' in warnings[0]
        assert 'lineWidth of 5 pix' in warnings[1]
        assert 'drawn 4 pix wide' in warnings[0]
