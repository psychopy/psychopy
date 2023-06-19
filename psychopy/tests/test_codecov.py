import requests
from . import utils
from pathlib import Path


def test_valid_yaml():
    """
    Send the codecov YAML file to CodeCov to check that it's valid, meaning we find out in the
    test suite if it's invalid rather than finding out when it tries to run.
    """
    # ensure data type
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    # navigate to codecov file
    file = Path(utils.TESTS_PATH).parent.parent / "codecov.yml"
    # create bytes object for yaml file
    data = open(str(file), "rb")

    try:
        resp = requests.post("https://codecov.io/validate", headers=headers, data=data, timeout=5)
    except TimeoutError:
        resp = {}
        resp.status_code = 400
        resp.text = "Could not connect to Codecov, timed out after 5s"

    assert resp.status_code == 200, (
        f"`codecov.yaml` is invalid or could not be validated. Message received from Codecov:\n"
        f"{resp.text}"
    )

