import sys
from psychopy.alerts import _alerts


class TestAlertsModule():
    """A class for testing the alerts module"""

    def teardown(self):
        sys.stderr = sys.__stderr__
        _alerts.alertLog.clear()

    def test_alertlog(self):
        """Tests the creation of the AlertLog object"""
        assert (isinstance(_alerts.alertLog, _alerts.AlertLog))
        assert (_alerts.alertLog._log == [])
        assert (_alerts.alertLog._logIndex == 0)

    def test_alert_iteration(self):
        _alerts.alertLog.store([1,2,3])
        for i, j in enumerate(_alerts.alertLog):
            assert (i + 1 == j)

    def test_alert_catalogue(self):
        """Test the alerts catalogue has been created and loaded correctly"""
        assert (isinstance(_alerts.catalogue, _alerts.AlertCatalogue))
        assert (9999 in _alerts.catalogue.alert.keys())

    def test_alertlog_store(self):
        """Tests append and retrieve of the alertlog"""
        _alerts.alertLog.store([1])
        assert (_alerts.alertLog._log == [1])

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

    def test_alertlog_clear(self):
        _alerts.alertLog.store([1])
        _alerts.alertLog.clear()
        assert (_alerts.alertLog._log == [])
