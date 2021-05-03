import os

_travisTesting = bool("{}".format(os.environ.get('TRAVIS')).lower() == 'true')
_anacondaTesting = bool("{}".format(os.environ.get('CONDA')).lower() == 'true')
_githubActions = str(os.environ.get('GITHUB_WORKFLOW')) != 'None'
_vmTesting = _travisTesting or _githubActions

if _vmTesting:  # then let's also create some skip functions
    import pytest  # only import if we are testing
    # some pytest decorators for those conditions
    skip_under_travis = pytest.mark.skipif(_travisTesting, reason="Cannot run that test under Travis")
    skip_under_ghActions = pytest.mark.skipif(_githubActions, reason="Cannot run that test on GitHub Actions")
    skip_under_vm = pytest.mark.skipif(_vmTesting, reason="Cannot run that test on a virtual machine")
