from psychopy import web
from psychopy.constants import PSYCHOPY_USERAGENT
import pytest
import hashlib
import shutil, os
from tempfile import mkdtemp

# py.test -k web --cov-report term-missing --cov web.py

SELECTOR_FOR_TEST_UPLOAD = 'http://upload.psychopy.org/test/up.php'
BASIC_AUTH_CREDENTIALS = 'psychopy:open-sourc-ami'


@pytest.mark.web
class TestWeb(object):
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
        web.proxyFromPacFiles(web.getPacFiles())
        web.setupProxy()

    def test_upload(self):
        selector = SELECTOR_FOR_TEST_UPLOAD
        selectorS = SELECTOR_FOR_TEST_UPLOAD.replace('http', 'https')
        selectorBad = selector = 'http://upload.psychopy.org/../../up.php'
        filename = __file__
        basicAuth = BASIC_AUTH_CREDENTIALS

        web.upload(selector, filename, basicAuth)
        web.upload(selectorS, filename, basicAuth, https=True)
        with pytest.raises(ValueError):
            web.upload(selectorS, filename, basicAuth)
        with pytest.raises(ValueError):
            web.upload(selector, filename, basicAuth, https=True)
        with pytest.raises(ValueError):
            web.upload('', filename, basicAuth)
        web.upload(selector + 'JUNK', filename, basicAuth)
        with pytest.raises(ValueError):
            web.upload(selector, filename + 'JUNK', basicAuth)
        web.upload(selector, filename, basicAuth + 'JUNK')

    def test_upload_integrity(self):
        def _upload(stuff):
            """assumes that SELECTOR_FOR_TEST_UPLOAD is a configured http server
            """
            selector = SELECTOR_FOR_TEST_UPLOAD
            basicAuth = BASIC_AUTH_CREDENTIALS

            # make a tmp dir just for testing:
            tmp = mkdtemp()
            filename = 'test.txt'
            tmp_filename = os.path.join(tmp, filename)
            f = open(tmp_filename, 'w+')
            f.write(stuff)
            f.close()

            # get local sha256 before cleanup:
            digest = hashlib.sha256()
            digest.update(open(tmp_filename).read())
            dgst = digest.hexdigest()

            # upload:
            status = web.upload(selector, tmp_filename, basicAuth)
            shutil.rmtree(tmp) # cleanup; do before asserts

            # test
            good_upload = True
            disgest_match = False
            if not status.startswith('success'):
                good_upload = False
            elif status.find(dgst) > -1:
                digest_match = True

            return int(status.split()[3]), good_upload, digest_match

        # test upload: normal text, binary:
        msg = PSYCHOPY_USERAGENT # can be anything
        bytecount, good_upload, digest_match = _upload(msg) #normal text
        assert (bytecount == len(msg)) # FAILED to report len() bytes
        assert good_upload # remote server FAILED to report success
        assert digest_match # sha256 mismatch local vs remote file

        digest = hashlib.sha256()  # to get binary, 256 bits
        digest.update(msg)
        bytecount, good_upload, digest_match = _upload(digest.digest())
        assert (bytecount == 32) # FAILED to report 32 bytes for a 256-bit binary file (= odd if digests match)
        assert good_upload # remote server FAILED to report success
        assert digest_match # sha256 mismatch local vs remote file
