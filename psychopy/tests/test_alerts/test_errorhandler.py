import sys
from psychopy.alerts._alerts import alert, AlertEntry
from psychopy.alerts._errorHandler import _BaseErrorHandler


class TestErrorHandler():
    """A class for testing the error handler"""

    def setup(self):
        # Set ErrorHandler
        sys.stderr = self.error = _BaseErrorHandler()

    def teardown(self):
        sys.stderr = sys.__stderr__

    def test_errorhandler(self):
        """Test error handler attributes"""
        assert (hasattr(sys.stderr, "receiveAlert"))
        assert (hasattr(sys.stderr, "alerts"))
        assert (hasattr(sys.stderr, "errors"))
        assert (sys.stderr.alerts == [])

    def test_errorhandler_receiveAlert(self):
        """Test flushing of alert to alertLog and clearing attributes"""
        alert(9999, self, {'testString': 'TEST MESSAGE'})
        assert (isinstance(sys.stderr.alerts[-1], AlertEntry))
