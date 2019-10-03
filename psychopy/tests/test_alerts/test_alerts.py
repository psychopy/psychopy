import shutil
from psychopy.alerts import _alerts
from tempfile import mkdtemp


class TestAlertsLogger():
    """A class for testing the alerts package"""

    def setup(self):
        """Test creation of the AlertLogger"""
        self.temp_dir = mkdtemp()

    def teardown(self):
        shutil.rmtree(self.temp_dir)

    def test_alert_catalogue(self):
        """Test the alerts catalogue has been created and loaded correctly"""
        assert isinstance(_alerts.catalogue, _alerts.AlertCatalogue)
        assert 9999 in _alerts.catalogue.alert.keys()
