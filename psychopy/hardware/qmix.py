#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
Simple interface to the Cetoni neMESYS syringe pump system, based on the
`pyqmix <https://github.com/psyfood/pyqmix/>`_ library. The syringe pump
system is described in the following publication:

    CA Andersen, L Alfine, K Ohla, & R Höchenberger (2018):
    "A new gustometer: Template for the construction of a portable and
     modular stimulator for taste and lingual touch."
    Behavior Research Methods. doi: 10.3758/s13428-018-1145-1

"""


from psychopy import prefs
from pyqmix import config, QmixBus, QmixPump
import pyqmix.pump

syringeTypes = list(pyqmix.pump.syringes.keys())
volumeUnits = ['mL']
flowRateUnits = ['mL/s', 'mL/min']
configName = prefs.hardware['qmixConfiguration']
bus = None
pumps = []  # To keep track of all instantiated pumps.


def _init_bus():
    global bus

    config.set_qmix_config(configName)
    bus = QmixBus()


def _init_all_pumps():
    # Initialize the very first pump to make its `n_pumps` property visible.
    # After that, instantiate all remaining pumps.
    p = Pump(index=0)
    n_pumps = p._pyqmix_pump.n_pumps
    [Pump(index=index) for index in range(1, n_pumps)]


class Pump(object):
    """
    An interface to Cetoni neMESYS syringe pumps, based on the
    `pyqmix <https://github.com/psyfood/pyqmix/>`_ library.
    """
    def __init__(self, index, volumeUnit='mL',
                 flowRateUnit='mL/s',
                 syringeType='50 mL glass'):
        """

        Parameters
        ----------
        index : int
            The index of the pump. The first pump in the system has `index=0`,
            the second `index=1`, etc.

        volumeUnit: 'mL'
            The unit in which the volumes are provided. Currently, only `'ml'`
            is supported.

        flowRateUnit : 'mL/s' or 'mL/min
            The unit in which flow rates are provided.

        syringeType : '25 mL glass' or '50 mL glass'
            Type of the installed syringe, `as understood by pyqmix
            <https://pyqmix.readthedocs.io/en/latest/interface.html#pyqmix.pump.QmixPump.set_syringe_params_by_type>`_.

        """
        # Only initialize the bus when instantiating the very first pump.
        if bus is None:
            _init_bus()

        self._pyqmix_pump = QmixPump(index=index)
        self.volumeUnit = volumeUnit
        self.flowRateUnit = flowRateUnit
        self.syringeType = syringeType
        self.index = index
        pumps.append(self)

    @property
    def fillLevel(self):
        """Current fill level of the syringe.
        """
        return self._pyqmix_pump.fill_level

    @property
    def maxFlowRate(self):
        """Maximum flow rate the pump can provide with the installed syringe.
        """
        return self._pyqmix_pump.max_flow_rate

    @property
    def isInFaultState(self):
        """Whether the pump is currently in a non-operational "fault state".

        To enable the pump again, call :meth:`~Pump.clearFaultState`.
        """
        return self._pyqmix_pump.is_in_fault_state

    @property
    def syringeType(self):
        """Type of the installed syringe.
        """
        return self._syringeType

    @syringeType.setter
    def syringeType(self, syringeType):
        self._pyqmix_pump.set_syringe_params_by_type(syringeType)
        self._syringeType = syringeType

    @property
    def volumeUnit(self):
        """The unit in which the volumes are provided.
        """
        return self._volumeUnit

    @volumeUnit.setter
    def volumeUnit(self, volumeUnit):
        if volumeUnit not in volumeUnits:
            raise ValueError('Volume unit must be one of %s' % volumeUnits)

        self._pyqmix_pump.set_volume_unit(prefix='milli', unit='litres')
        self._volumeUnit = 'mL'

    @property
    def flowRateUnit(self):
        """The unit in which flow rates are provided.
        """
        return self._flowRateUnit

    @flowRateUnit.setter
    def flowRateUnit(self, flowRateUnit):
        if flowRateUnit == 'mL/s':
            flow_time_unit = 'per_second'
        elif flowRateUnit == 'mL/min':
            flow_time_unit = 'per_minute'
        else:
            msg = 'Invalid flow rate unit: must be one of' %flowRateUnits
            raise ValueError(msg)

        self._pyqmix_pump.set_flow_unit(prefix='milli',
                                        volume_unit='litres',
                                        time_unit=flow_time_unit)
        self._flowRateUnit = flowRateUnit

    def clearFaultState(self):
        """Switch the pump back to an operational state after an error had
        occurred.
        """
        self._pyqmix_pump.clear_fault_state()

    def calibrate(self, waitUntilDone=False):
        """Calibrate the syringe pump.

        You must not use this function if a syringe is installed in the
        pump as the syringe may be damaged!

        Parameters
        ----------
        waitUntilDone : bool
            Whether to block program execution until calibration is completed.

        """
        self._pyqmix_pump.calibrate(wait_until_done=waitUntilDone)

    def dispense(self, volume, flowRate, waitUntilDone=False,
                 switchValveWhenDone=False):
        """Dispense the specified volume.

        Parameters
        ----------
        volume : float
            The volume to dispense.
        flowRate : float
            The desired flow rate.
        waitUntilDone : bool
            Whether to block program execution until calibration is completed.
        switchValveWhenDone : bool
            If `True`, switch the valve to aspiation position after the
            dispense is finished. Implies `wait_until_done=True`.

        """
        if flowRate <= 0 or flowRate > self._pyqmix_pump.max_flow_rate:
            msg = ('Flow rate must be positive and <= .3%f %s'
                   % (self.maxFlowRate,
                      self.flowRateUnit))
            raise ValueError(msg)

        self._pyqmix_pump.dispense(volume=volume,
                                   flow_rate=flowRate,
                                   wait_until_done=waitUntilDone,
                                   switch_valve_when_done=switchValveWhenDone)

    def aspirate(self, volume, flowRate, waitUntilDone=False,
                 switchValveWhenDone=False):
        """Aspirate the specified volume.

        Parameters
        ----------
        volume : float
            The volume to aspirate.
        flowRate : float
            The desired flow rate.
        waitUntilDone : bool
            Whether to block program execution until calibration is completed.
        switchValveWhenDone : bool
            If `True`, switch the valve to dispense position after the
            aspiration is finished. Implies `wait_until_done=True`.

        """
        if flowRate <= 0 or flowRate > self._pyqmix_pump.max_flow_rate:
            msg = ('Flow rate must be positive and <= .3%f %s'
                   % (self.maxFlowRate,
                      self.flowRateUnit))
            raise ValueError(msg)

        self._pyqmix_pump.aspirate(volume=volume,
                                   flow_rate=flowRate,
                                   wait_until_done=waitUntilDone,
                                   switch_valve_when_done=switchValveWhenDone)

    def fill(self, flowRate, waitUntilDone=False,
             switchValveWhenDone=False):
        """Fill the syringe entirely.

        Parameters
        ----------
        flowRate : float
            The desired flow rate.
        waitUntilDone : bool
            Whether to block program execution until calibration is completed.
        switchValveWhenDone : bool
            If `True`, switch the valve to dispense position after the
            aspiration is finished. Implies `wait_until_done=True`.

        """
        if flowRate <= 0 or flowRate > self._pyqmix_pump.max_flow_rate:
            msg = ('Flow rate must be positive and <= .3%f %s'
                   % (self.maxFlowRate,
                      self.flowRateUnit))
            raise ValueError(msg)

        self._pyqmix_pump.fill(flow_rate=flowRate,
                               wait_until_done=waitUntilDone,
                               switch_valve_when_done=switchValveWhenDone)

    def empty(self, flowRate, waitUntilDone=False,
              switchValveWhenDone=False):
        """Empty the syringe entirely.

        Parameters
        ----------
        flowRate : float
            The desired flow rate.
        waitUntilDone : bool
            Whether to block program execution until calibration is completed.
        switchValveWhenDone : bool
            If `True`, switch the valve to aspirate position after the
            dispensing is finished. Implies `wait_until_done=True`.

        """
        if flowRate <= 0 or flowRate > self._pyqmix_pump.max_flow_rate:
            msg = ('Flow rate must be positive and <= .3%f %s'
                   % (self.maxFlowRate,
                      self.flowRateUnit))
            raise ValueError(msg)

        self._pyqmix_pump.empty(flow_rate=flowRate,
                                wait_until_done=waitUntilDone,
                                switch_valve_when_done=switchValveWhenDone)

    def switchValvePosition(self):
        """Switch the valve to the opposite position.
        """
        self._pyqmix_pump.valve.switch_position()

    def stop(self):
        """Stop any pump operation immediately.
        """
        self._pyqmix_pump.stop()


class _PumpWrapperForBuilderComponent(object):
    """
    Merely for use in the corresponding Builder component, to allow
    re-using the same Pump (in different components) within the same
    routine. To make this possible, we expose a `status` attribute,
    allowing e.g. one Pump Component to finish, while another Pump Component
    in the same routine will be left entirely unaffected, even if it is
    referring to the exact same Pump (i.e., same pump index).

    The methods implemented here simply pass on their arguments to the
    respective methods in the `Pump` instance (stored in `.pump`); this just
    happens for convenience: One can now e.g. invoke
    `_PumpWrapperForBuilderComponent.empty()` instead of
    `_PumpWrapperForBuilderComponent.pump.empty()`, which should make the
    code generated by Builder easier to read and work with.

    """
    def __init__(self, pump):
        """
        Parameters
        ----------
        pump : Pump

        """
        self.pump = pump
        self.status = None

    def fill(self, *args, **kwargs):
        self.pump.fill(*args, **kwargs)

    def empty(self, *args, **kwargs):
        self.pump.empty(*args, **kwargs)

    def stop(self):
        self.pump.stop()

    def switchValvePosition(self):
        self.pump.switchValvePosition()

    @property
    def syringeType(self):
        return self.pump.syringeType

    @syringeType.setter
    def syringeType(self, syringeType):
        self.pump.syringeType = syringeType

    @property
    def flowRateUnit(self):
        return self.pump.flowRateUnit

    @flowRateUnit.setter
    def flowRateUnit(self, flowRateUnit):
        self.pump.flowRateUnit = flowRateUnit
