from psychopy import web
import pytest

# py.test -k web --cov-report term-missing --cov web.py


@pytest.mark.web
class TestWeb():
    @classmethod
    def setup_class(self):
        try:
            web.requireInternetAccess()
        except web.NoInternetAccessError:
            pytest.skip()
    def teardown(self):
        pass

    def test_setupProxy(self):
        web.getPacFiles()
        web.getWpadFiles()
        web.proxyFromPacFiles(web.getPacFiles(), log=False)
        web.setupProxy()
