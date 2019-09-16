import shutil
from psychopy.alerts import Alerts
from tempfile import mkdtemp


class TestAlertsLogger():
    """A class for testing the alerts package"""

    def setup(self):
        """Test creation of the AlertLogger"""
        self.temp_dir = mkdtemp()
        self.alert = Alerts.AlertLogger("TestCase", self.temp_dir)

    def teardown(self):
        shutil.rmtree(self.temp_dir)

    def test_alert_catalogue(self):
        """Test the alerts catalogue has been created and loaded correctly"""
        assert isinstance(Alerts.catalogue, Alerts.AlertCatalogue)
        assert 9999 in Alerts.catalogue.alert.keys()

    def test_fresh_root(self):
        """Test the AlertLog is instantiated"""
        assert isinstance(Alerts.root, Alerts.AlertLog)
        assert len(Alerts.root.alertLog) == 0

    def test_fresh_master_log(self):
        """Test the MasterLog is instantiated"""
        assert isinstance(Alerts.master, Alerts.MasterLog)

    def test_alert_logger_instance(self):
        """Test the AlertLogger is instantiated"""
        assert isinstance(self.alert, Alerts.AlertLogger)

    def test_alert_logger_name(self):
        """Test the name of the AlertLogger"""
        assert self.alert.name == "TestCase"

    def test_alert_logger_write(self):
        """Test the AlertLogger write method fills the AlertLog Object"""
        self.alert.write(9999, self)
        assert len(Alerts.root.alertLog) == 1

    def test_alert_entry_instance(self):
        """Test the entries in AlertLog are AlertEntry objects"""
        assert isinstance(Alerts.root.alertLog[0], Alerts.AlertEntry)

    def test_alert_entry_attributes(self):
        """Test the AlertEntry object has the correct values assigned to its attributes"""
        assert Alerts.root.alertLog[0].logName == "TestCase"
        assert Alerts.root.alertLog[0].type == None
        assert Alerts.root.alertLog[0].name == None
        assert Alerts.root.alertLog[0].code == 9999
        assert Alerts.root.alertLog[0].cat == "TEST_ISSUE"
        assert Alerts.root.alertLog[0].msg == "TEST_MSG"
        assert Alerts.root.alertLog[0].url == "https://psychopy.org"
        assert isinstance(Alerts.root.alertLog[0].obj, type(self))

    def test_alert_logger_flush(self):
        self.alert.flush()
        assert len(Alerts.root.alertLog) == 0
