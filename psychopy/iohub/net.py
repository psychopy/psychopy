# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import struct
from weakref import proxy

from gevent import sleep, Greenlet
import msgpack
try:
    import msgpack_numpy
    msgpack_numpy.patch()
except ImportError:
    from .errors import print2err
    print2err("Warning: msgpack_numpy could not be imported. ",
              "This may cause issues for iohub.")

from .devices import Computer
from .errors import print2err, printExceptionDetailsToStdErr
from .util import NumPyRingBuffer as RingBuffer

if Computer.platform == 'win32':
    MAX_PACKET_SIZE = 64 * 1024
else:
    MAX_PACKET_SIZE = 16 * 1024

class SocketConnection(): # pylint: disable=too-many-instance-attributes
    def __init__(
            self,
            local_host=None,
            local_port=None,
            remote_host=None,
            remote_port=None,
            rcvBufferLength=1492,
            broadcast=False,
            blocking=0,
            timeout=0):
        self._local_port = local_port
        self._local_host = local_host
        self._remote_host = remote_host
        self._remote_port = remote_port
        self._rcvBufferLength = rcvBufferLength
        self.lastAddress = None
        self.sock = None
        self.initSocket(broadcast, blocking, timeout)

        self.coder = msgpack
        self.packer = msgpack.Packer()
        self.unpacker = msgpack.Unpacker(use_list=True)
        self.pack = self.packer.pack
        self.feed = self.unpacker.feed
        self.unpack = self.unpacker.unpack

    def initSocket(self, broadcast=False, blocking=0, timeout=0):
        if Computer.is_iohub_process is True:
            from gevent import socket
        else:
            import socket

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if broadcast is True:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL,
                                 struct.pack('@i', 1))

        if blocking:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sock.settimeout(timeout)
        self.sock.setblocking(blocking)

    def sendTo(self, data, address=None):
        if address is None:
            address = self._remote_host, self._remote_port
        max_pkt_sz = 8192
        packed_data = self.pack(data)
        payload_size = len(packed_data)
        if payload_size > max_pkt_sz:
            # Send multi packet request to server
            pkt_cnt = int(payload_size // max_pkt_sz) + 1
            mpr_payload = ('IOHUB_MULTIPACKET_REQUEST', pkt_cnt)
            self.sock.sendto(self.pack(mpr_payload), address)
            for p in range(pkt_cnt):
                si = p * max_pkt_sz
                self.sock.sendto(packed_data[si:si + max_pkt_sz], address)
        else:
            self.sock.sendto(packed_data, address)
        return len(packed_data)

    def receive(self):
        try:
            data, address = self.sock.recvfrom(self._rcvBufferLength)
            self.lastAddress = address
            self.feed(data)
            result = self.unpack()
            if result[0] == 'IOHUB_MULTIPACKET_RESPONSE':
                num_packets = result[1]
                while num_packets > 0:
                    data, address = self.sock.recvfrom(self._rcvBufferLength)
                    self.feed(data)
                    num_packets = num_packets - 1
                result = self.unpack()
            return result, address
        except:
            pass

    def close(self):
        self.sock.close()


class UDPClientConnection(SocketConnection):
    def __init__(self, remote_host='127.0.0.1', remote_port=9000,
                 rcvBufferLength=MAX_PACKET_SIZE, broadcast=False,
                 blocking=1, timeout=None):
        SocketConnection.__init__(self, remote_host=remote_host,
                                  remote_port=remote_port,
                                  rcvBufferLength=rcvBufferLength,
                                  broadcast=broadcast,
                                  blocking=blocking,
                                  timeout=timeout)
        self.sock.settimeout(timeout)

    def initSocket(self, broadcast=False, blocking=1, timeout=None):
        if Computer.is_iohub_process is True:
            from gevent import socket
        else:
            import socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,
                             MAX_PACKET_SIZE)
        self.sock.settimeout(timeout)
        self.sock.setblocking(blocking)

##### TIME SYNC CLASS ######


class ioHubTimeSyncConnection(UDPClientConnection):
    """A special purpose version of the UDPClientConnection class which has the
    only job of sending and receiving time sync rmessage requests and responses
    with a remote ioHub Server instance."""

    def __init__(self, remote_address):
        self.remote_iohub_address = tuple(remote_address)

        UDPClientConnection.__init__(
            self,
            remote_host=self.remote_iohub_address[0],
            remote_port=self.remote_iohub_address[1],
            rcvBufferLength=MAX_PACKET_SIZE,
            broadcast=False,
            blocking=1,
            timeout=1)

        self.sync_batch_size = 5

    def sync(self):
        sync_count = self.sync_batch_size
        sync_data = ['SYNC_REQ', ]

        feed = self.feed
        unpack = self.unpack
        pack = self.pack

        recvfrom = self.sock.recvfrom
        rcvBufferLength = self._rcvBufferLength

        remote_address = self.remote_iohub_address
        sendto = self.sock.sendto

        min_delay = 1000.0
        min_local_time = 0.0
        min_remote_time = 0.0

        while sync_count > 0:
            # send sync request
            sync_start = Computer.getTime()
            sendto(pack(sync_data), remote_address)
            sync_start2 = Computer.getTime()

            # get reply
            feed(recvfrom(rcvBufferLength)[0])
            _, remote_time = unpack()
            sync_end = Computer.getTime()
            rtt = sync_end - (sync_start + sync_start2) / 2.0

            old_delay = min_delay
            min_delay = min(min_delay, rtt)

            if old_delay != min_delay:
                min_local_time = (sync_end + sync_start) / 2.0
                min_remote_time = remote_time
            sync_count = sync_count - 1

        return min_delay, min_local_time, min_remote_time


class ioHubTimeGreenSyncManager(Greenlet):
    """The time synchronization manager class used within an ioHub Server when a
    ioHubRemoteEventSubscriber device is running.

    The time synchronization manager monitors and calculates the ongoing
    offset and drift between the local ioHub instance and a remote ioHub
    instance running on another computer that is publishing events that
    are being received by the local ioHubRemoteEventSubscriber.

    """

    def __init__(self, remote_address, sync_state_target):
        try:
            Greenlet.__init__(self)
            self._sync_socket = None
            self.initial_sync_interval = 0.2
            self._remote_address = remote_address
            while self._sync_socket is None:
                self._sync_socket = ioHubTimeSyncConnection(remote_address)
                sleep(1)
            self.sync_state_target = proxy(sync_state_target)
            self._running = False
        except Exception: # pylint: disable=broad-except
            print2err(
                '** Exception during ioHubTimeGreenSyncManager.__init__: ',
                self._remote_address)
            printExceptionDetailsToStdErr()

    def _run(self): # pylint: disable=method-hidden
        self._running = True
        while self._sync(False) is False:
            sleep(0.5)
        self._sync(False)
        while self._running is True:
            sleep(self.initial_sync_interval)
            r = self._sync()
            if r is False:
                print2err(
                    'SYNC FAILED: ioHubTimeGreenSyncManager {0}.'.format(
                        self._remote_address))
        self._close()

    def _sync(self, calc_drift_and_offset=True):
        try:
            if self._sync_socket:
                r = self._sync_socket.sync()
                min_delay, min_local_time, min_remote_time = r
                sync_state_target = self.sync_state_target
                sync_state_target.RTTs.append(min_delay)
                sync_state_target.L_times.append(min_local_time)
                sync_state_target.R_times.append(min_remote_time)

                if calc_drift_and_offset is True:
                    l1 = sync_state_target.L_times[-2]
                    l2 = sync_state_target.L_times[-1]
                    r1 = sync_state_target.R_times[-2]
                    r2 = sync_state_target.R_times[-1]
                    self.sync_state_target.drifts.append((r2 - r1) / (l2 - l1))

                    l = sync_state_target.L_times[-1]
                    r = sync_state_target.R_times[-1]
                    self.sync_state_target.offsets = (r - l)
        except Exception: # pylint: disable=broad-except
            return False
        return True

    def _close(self):
        if self._sync_socket:
            self._running = False
            self._sync_socket.close()
            self._sync_socket = None

    def __del__(self):
        self._close()


class ioHubTimeSyncManager():

    def __init__(self, remote_address, sync_state_target):
        self.initial_sync_interval = 0.2
        self._remote_address = remote_address
        self._sync_socket = ioHubTimeSyncConnection(remote_address)
        self.sync_state_target = proxy(sync_state_target)

    def sync(self, calc_drift_and_offset=True):
        if self._sync_socket:
            r = self._sync_socket.sync()
            min_delay, min_local_time, min_remote_time = r
            sync_state_target = self.sync_state_target
            sync_state_target.RTTs.append(min_delay)
            sync_state_target.L_times.append(min_local_time)
            sync_state_target.R_times.append(min_remote_time)

            if calc_drift_and_offset is True:
                l1 = sync_state_target.L_times[-2]
                l2 = sync_state_target.L_times[-1]
                r1 = sync_state_target.R_times[-2]
                r2 = sync_state_target.R_times[-1]
                self.sync_state_target.drifts.append((r2 - r1) / (l2 - l1))

                l = sync_state_target.L_times[-1]
                r = sync_state_target.R_times[-1]
                self.sync_state_target.offsets = (r - l)

    def close(self):
        if self._sync_socket:
            self._sync_socket.close()
            self._sync_socket = None

    def __del__(self):
        self.close()


class TimeSyncState():
    """Container class used by an ioHubSyncManager to hold the data necessary
    to calculate the current time base offset and drift between an ioHub Server
    and a ioHubRemoteEventSubscriber client."""
    RTTs = RingBuffer(10)
    L_times = RingBuffer(10)
    R_times = RingBuffer(10)
    drifts = RingBuffer(20)
    offsets = RingBuffer(20)

    def getDrift(self):
        """Current drift between two time bases."""
        return self.drifts.mean()

    def getOffset(self):
        """Current offset between two time bases."""
        return self.offsets.mean()

    def getAccuracy(self):
        """Current accuracy of the time synchronization, as calculated as the.

        average of the last 10 round trip time sync request - response delays
        divided by two.

        """
        return self.RTTs.mean() / 2.0

    def local2RemoteTime(self, local_time=None):
        """Converts a local time (sec.msec format) to the corresponding remote
        computer time, using the current offset and drift measures."""
        if local_time is None:
            local_time = Computer.getTime()
        return self.getDrift() * local_time + self.getOffset()

    def remote2LocalTime(self, remote_time):
        """Converts a remote computer time (sec.msec format) to the
        corresponding local time, using the current offset and drift
        measures."""
        return (remote_time - self.getOffset()) / self.getDrift()
