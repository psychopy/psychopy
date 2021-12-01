# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import logging

import msgpack
import zmq.green as zmq
from psychopy.iohub.devices import Computer

logger = logging.getLogger(__name__)


class PupilRemote:
    """
    'R'  # start recording with auto generated session name
    'R rec_name'  # start recording named "rec_name"
    'r'  # stop recording
    'C'  # start currently selected calibration
    'c'  # stop currently selected calibration
    'T 1234.56'  # resets current Pupil time to given timestamp
    't'  # get current Pupil time; returns a float as string.
    'v'  # get the Pupil Core software version string
    """

    def __init__(
        self,
        subscription_topics,
        ip_address: str = "127.0.0.1",
        port: int = 50020,
        timeout_ms: int = 1000,
    ):

        # Creates a zmq-REQ socket and connect it to Pupil Capture
        # See https://docs.pupil-labs.com/developer/core/network-api/ for details.
        self._zmq_ctx = zmq.Context.instance()
        self._zmq_req_socket = self._zmq_ctx.socket(zmq.REQ)
        self._zmq_req_socket.connect(f"tcp://{ip_address}:{port}")

        # Create a zmq-SUB socket to get IPC Backbone notifications
        self._zmq_req_socket.send_string("SUB_PORT")
        if self._zmq_req_socket.poll(timeout=timeout_ms, flags=zmq.POLLIN) == 0:
            raise TimeoutError("Could not connect to Pupil Capture")
        sub_port = self._zmq_req_socket.recv_string()
        self._zmq_sub_socket = self._zmq_ctx.socket(zmq.SUB)
        self._zmq_sub_socket.connect(f"tcp://{ip_address}:{sub_port}")

        # Subscribe to IPC Backbone notification topics
        for topic in subscription_topics:
            self._zmq_sub_socket.subscribe(topic)

        # State values
        self._is_recording = False

        self._psychopy_pupil_clock_offset = 0.0
        self.update_psychopy_pupil_clock_offset()

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def psychopy_pupil_clock_offset(self) -> float:
        return self._psychopy_pupil_clock_offset

    def update_psychopy_pupil_clock_offset(self):
        time_before = Computer.getTime()
        time_pupil_at_pupil_clock_reading = self.get_pupil_time()
        time_after = Computer.getTime()
        time_psychopy_at_pupil_clock_reading = (time_before + time_after) / 2.0
        self._psychopy_pupil_clock_offset = (
            time_pupil_at_pupil_clock_reading - time_psychopy_at_pupil_clock_reading
        )

    def start_recording(self, rec_name: str = None):
        if self._is_recording:
            return
        if rec_name:
            self._zmq_req_socket.send_string(f"R {rec_name}")
        else:
            self._zmq_req_socket.send_string("R")
        logger.debug(self._zmq_req_socket.recv_string())
        self._is_recording = True

    def stop_recording(self):
        if not self._is_recording:
            return
        self._zmq_req_socket.send_string("r")
        logger.debug(self._zmq_req_socket.recv_string())
        self._is_recording = False

    def start_calibration(self):
        self._zmq_req_socket.send_string("C")
        logger.debug(self._zmq_req_socket.recv_string())

    def stop_calibration(self):
        self._zmq_req_socket.send_string("c")
        logger.debug(self._zmq_req_socket.recv_string())

    def set_pupil_time(self, pupil_time: float):
        self._zmq_req_socket.send_string(f"T {pupil_time}")
        logger.debug(self._zmq_req_socket.recv_string())

    def get_pupil_time(self):
        """Uses an existing Pupil Core software connection to request the remote time.
        Returns the current "pupil time" at the timepoint of reception.
        See https://docs.pupil-labs.com/core/terminology/#pupil-time for more information
        about "pupil time".
        """
        self._zmq_req_socket.send_string("t")
        pupil_time = self._zmq_req_socket.recv()
        return float(pupil_time)

    def get_software_version(self) -> str:
        self._zmq_req_socket.send_string("v")
        return self._zmq_req_socket.recv_string()

    def fetch(self, endless=False):
        while True:
            if not endless and not self.has_new_data:
                break

            topic = self._zmq_sub_socket.recv_string()
            payload = self._zmq_sub_socket.recv()
            payload = msgpack.loads(payload, raw=False)

            yield topic, payload

    def cleanup(self):
        self._zmq_req_socket.close()
        self._zmq_sub_socket.close()

    @property
    def has_new_data(self):
        return self._zmq_sub_socket.get(zmq.EVENTS) & zmq.POLLIN
