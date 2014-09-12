""" Test starting and stopping iohub server
"""
from psychopy.tests.utils import skip_under_travis
from psychopy.tests.test_iohub.testutil import startHubProcess, stopHubProcess, skip_not_completed
from psychopy.iohub import Computer
from psychopy.core import getTime

@skip_under_travis
class TestComputer:
    """
    Keyboard Device tests. Starts iohub server, runs test set, then
    stops iohub server.

    Since there is no way to currently automate keyboard event generation in
    a way that would actually test the iohub keyboard event processing logic,
    each test simply calls one of the device methods / properties and checks
    that the return type is as expected.

    Each method is called with no args; that should be improved.

    Following methods are not yet tested:
            addFilter
            enableFilters
            getConfiguration
            getCurrentDeviceState
            getModifierState
            removeFilter
            resetFilter
            resetState
    """

    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.io = startHubProcess()

    @classmethod
    def teardown_class(cls):
        """ teardown any state that was previously setup with a call to
        setup_class.
        """
        stopHubProcess()
        cls.io = None


    def test_getTime(self):
        ta = Computer.currentSec()
        tb = Computer.currentTime()
        tc = Computer.getTime()
        tp = getTime()

        assert ta < tb < tc < tp
        assert tp - ta < 0.002

    def test_getProcesses(self):
        assert Computer.is_iohub_process is False
        assert Computer.psychopy_process == Computer.getCurrentProcess()
        assert Computer.current_process == Computer.psychopy_process
        assert Computer.iohub_process == Computer.getIoHubProcess()
        assert Computer.iohub_process.pid == Computer.iohub_process_id

        assert Computer.getCurrentProcess().is_running()
        assert Computer.getIoHubProcess().is_running()
        assert Computer.getIoHubProcess().parent() == Computer.getCurrentProcess()

    def test_processorCounts(self):
        get_puc = Computer.getProcessingUnitCount()
        cc = Computer.core_count
        puc = Computer.processing_unit_count

        assert puc == get_puc
        assert type(cc) is int
        assert type(puc) is int
        assert puc > 0
        assert cc > 0
        assert cc <= puc

    def test_procPriority(self):
        psycho_proc = Computer.psychopy_process
        iohub_proc = Computer.getIoHubProcess()

        psycho_priority = Computer.getProcessPriority(psycho_proc)
        iohub_priority = Computer.getProcessPriority(iohub_proc)
        assert psycho_priority == 'normal'
        assert iohub_priority == 'normal'

        Computer.enableHighPriority()
        new_psycho_priority = Computer.getProcessPriority(psycho_proc)
        assert new_psycho_priority == 'high'

        self.io.enableHighPriority()
        new_io_priority = Computer.getProcessPriority(iohub_proc)
        assert new_io_priority == 'high'

        Computer.disableHighPriority()
        new_psycho_priority = Computer.getProcessPriority(psycho_proc)
        assert new_psycho_priority == 'normal'

        self.io.disableHighPriority()
        new_io_priority = Computer.getProcessPriority(iohub_proc)
        assert new_io_priority == 'normal'

    @skip_not_completed
    def test_procAffinity(self):
        pass

