import sys
from psychopy.alerts import _alerts


class TestAlertsModule():
    """A class for testing the alerts module"""

    def teardown(self):
        sys.stderr = sys.__stderr__

    def test_alert_catalogue(self):
        """Test the alerts catalogue has been created and loaded correctly"""
        assert (isinstance(_alerts.catalogue, _alerts.AlertCatalogue))
        assert (9999 in _alerts.catalogue.alert.keys())

    def test_alertentry(self):
        """Test creation of AlertEntry object"""
        newAlert = _alerts.AlertEntry(9999, self)
        assert (isinstance(newAlert, _alerts.AlertEntry))
        assert (newAlert.msg == "TEST_MSG {testString}")

    def test_alertentry_stringformatting(self):
        """Test AlertEntry string formatting"""
        testString = {"testString": "TEST ALERT"}
        newAlert = _alerts.AlertEntry(9999, self, strFormat=testString)
        assert (newAlert.msg == "TEST_MSG TEST ALERT")

    def test_alert_written_to_console(self, capsys):
        """Test alerts are written to console when no errorhandler exists"""
        _alerts.alert(9999, self, strFormat={"testString": "TEST ALERT"})
        out, err = capsys.readouterr()  # Capture stdout stream and test
        assert ("TEST_MSG TEST ALERT" in err)
