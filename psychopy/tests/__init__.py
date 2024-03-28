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


def requires_plugin(plugin):
    """
    Decorator to skip test if a particular plugin is not installed.

    Parameters
    ----------
    plugin : str
        Name of plugin which must be installed in other for decorated test to run

    Returns
    -------
        pytest.mark with condition on which to run the test

    Examples
    --------
        ```
        @requires_plugin("psychopy-visionscience")
        def test_EnvelopeGrating():
            win = visual.Window()
            stim = visual.EnvelopeGrating(win)
            stim.draw()
            win.flip()
        ```
    """
    from psychopy import plugins

    return pytest.mark.skipif(plugin not in plugins.listPlugins(), reason="Cannot run that test on a virtual machine")
