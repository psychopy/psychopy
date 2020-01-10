import sys
from psychopy.alerts import _alerts


class TestAlertsModule():
    """A class for testing the alerts module"""

    def teardown(self):
        sys.stderr = sys.__stderr__
        del _alerts.alertLog[:]

    def test_alert_catalog(self):
        """Test the alerts catalog has been created and loaded correctly"""
        assert (isinstance(_alerts.catalog, _alerts.AlertCatalog))
        assert (9999 in _alerts.catalog.alert.keys())

    def test_alertlog(self):
        """Tests the creation of the AlertLog object"""
        assert (isinstance(_alerts.alertLog, list))
        assert (len(_alerts.alertLog) == 0)

    def test_alertlog_extend(self):
        """Tests append and retrieve of the alertlog"""
        _alerts.alertLog.extend([1])
        assert (_alerts.alertLog == [1])

    def test_alertentry(self):
        """Test creation of AlertEntry object"""
        newAlert = _alerts.AlertEntry(9999, self)
        assert (isinstance(newAlert, _alerts.AlertEntry))
        assert (newAlert.msg == "TEST_MSG {testString}")

    def test_alertentry_stringformatting(self):
        """Test AlertEntry string formatting"""
        testString = {"testString": "TEST ALERT"}
        newAlert = _alerts.AlertEntry(9999, self, strFields=testString)
        assert (newAlert.msg == "TEST_MSG TEST ALERT")

    def test_alert_written_to_console(self, capsys):
        """Test alerts are written to console when no errorhandler exists"""
        _alerts.alert(9999, self, strFields={"testString": "TEST ALERT"})
        out, err = capsys.readouterr()  # Capture stdout stream and test
        assert ("TEST_MSG TEST ALERT" in err)

    def test_alertlog_clear(self):
        _alerts.alertLog.extend([1])
        del _alerts.alertLog[:]
        assert (_alerts.alertLog == [])
