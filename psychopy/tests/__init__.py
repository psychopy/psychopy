import os

_travisTesting = bool("{}".format(os.environ.get('TRAVIS')).lower() == 'true')
_anacondaTesting = bool("{}".format(os.environ.get('CONDA')).lower() == 'true')
_githubActions = str(os.environ.get('GITHUB_WORKFLOW')) != 'None'
_vmTesting = _travisTesting or _githubActions

# for skip_under we need pytest but we don't want that to be a requirement for normal use
try:
    import pytest
    # some pytest decorators for those conditions
    skip_under_travis = pytest.mark.skipif(_travisTesting,
                                           reason="Cannot run that test under Travis")
    skip_under_ghActions = pytest.mark.skipif(_githubActions,
                                              reason="Cannot run that test on GitHub Actions")
    skip_under_vm = pytest.mark.skipif(_vmTesting,
                                       reason="Cannot run that test on a virtual machine")
except ImportError:
    def no_op(fn, reason=None):
        return fn
    skip_under_travis = no_op
    skip_under_ghActions = no_op
    skip_under_vm = no_op
