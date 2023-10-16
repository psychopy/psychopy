from psychopy.tools import systemtools

# for skip_under we need pytest but we don't want that to be a requirement for normal use
try:
    import pytest
    # some pytest decorators for those conditions
    skip_under_travis = pytest.mark.skipif(systemtools.isVM_CI() == 'travis',
                                           reason="Cannot run that test under Travis")
    skip_under_ghActions = pytest.mark.skipif(systemtools.isVM_CI() == 'github',
                                              reason="Cannot run that test on GitHub Actions")
    skip_under_vm = pytest.mark.skipif(bool(systemtools.isVM_CI()),
                                       reason="Cannot run that test on a virtual machine")
except ImportError:
    def no_op(fn, reason=None):
        return fn
    skip_under_travis = no_op
    skip_under_ghActions = no_op
    skip_under_vm = no_op
