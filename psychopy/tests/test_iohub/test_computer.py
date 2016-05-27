""" Test starting and stopping iohub server
"""
from psychopy.tests.utils import skip_under_travis
from psychopy.tests.test_iohub.testutil import startHubProcess, stopHubProcess, skip_not_completed
from psychopy.iohub.devices import Computer
from psychopy.core import getTime

@skip_under_travis
class TestComputer(object):
    """
    Computer Device tests.
    """

    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.io = startHubProcess()
        cls.computer = Computer

    @classmethod
    def teardown_class(cls):
        """ teardown any state that was previously setup with a call to
        setup_class.
        """
        stopHubProcess()
        cls.io = None


    def test_getTime(self):
        ta = Computer.getTime()
        tp = getTime()

        assert ta <= tp
        assert tp - ta < 0.001

        ta = getTime()
        tb = self.io.getTime()
        tc = self.io.getTime()
        tp = getTime()

        assert ta <= tb <= tc <= tp
        assert tp - ta < 0.01

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
        local_priority = Computer.getPriority()
        iohub_priority_rpc = self.io.getPriority()
        assert local_priority == 'normal'
        assert iohub_priority_rpc == 'normal'

        priority_level = Computer.setPriority('high', True)
        get_priority_level = Computer.getPriority()
        assert priority_level == 'high' == get_priority_level
        priority_level = self.io.setPriority('high', True)
        get_priority_level = self.io.getPriority()
        assert priority_level == 'high' == get_priority_level
        priority_level = Computer.setPriority('normal')
        get_priority_level = Computer.getPriority()
        assert priority_level == 'normal' == get_priority_level
        priority_level = self.io.setPriority('normal')
        get_priority_level = self.io.getPriority()
        assert priority_level == 'normal' == get_priority_level

        priority_level = Computer.setPriority('realtime')
        get_priority_level = Computer.getPriority()
        assert priority_level == 'realtime' == get_priority_level
        priority_level = self.io.setPriority('realtime')
        get_priority_level = self.io.getPriority()
        assert priority_level == 'realtime' == get_priority_level
        priority_level = Computer.setPriority('normal')
        get_priority_level = Computer.getPriority()
        assert priority_level == 'normal' == get_priority_level
        priority_level = self.io.setPriority('normal')
        get_priority_level = self.io.getPriority()
        assert priority_level == 'normal' == get_priority_level

    @skip_not_completed
    def test_procAffinity(self):
        pass

