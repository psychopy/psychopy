# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/client.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

from gevent import socket
import msgpack
import struct

MAX_PACKET_SIZE=64*1024

class SocketConnection(object):
    def __init__(self,local_host=None,local_port=None,remote_host=None,remote_port=None,rcvBufferLength=1492, broadcast=False, blocking=0, timeout=0):
        self._local_port= local_port
        self._local_host = local_host
        self._remote_host= remote_host
        self._remote_port = remote_port
        self._rcvBufferLength=rcvBufferLength
        self.lastAddress=None
        self.sock=None
        self.initSocket()

        self.coder=msgpack
        self.packer=msgpack.Packer()
        self.unpacker=msgpack.Unpacker(use_list=True)
        self.pack=self.packer.pack
        self.feed=self.unpacker.feed
        self.unpack=self.unpacker.unpack

    def initSocket(self,broadcast=False,blocking=0, timeout=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if broadcast is True:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('@i', 1))

        if blocking is not 0:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sock.settimeout(timeout)
        self.sock.setblocking(blocking)

    def sendTo(self,data,address=None):
        if address is None:
            address=self._remote_host, self._remote_port
        d=self.pack(data)
        byte_count=len(d)+2
        self.sock.sendto(d+'\r\n',address)
        return byte_count

    def receive(self):
        try:
            data, address = self.sock.recvfrom(self._rcvBufferLength)
            self.lastAddress=address
            self.feed(data[:-2])
            result=self.unpack()
            if result[0] == 'IOHUB_MULTIPACKET_RESPONSE':
                num_packets=result[1]

                for p in xrange(num_packets-1):
                    data, address = self.sock.recvfrom(self._rcvBufferLength)
                    self.feed(data)

                data, address = self.sock.recvfrom(self._rcvBufferLength)
                self.feed(data[:-2])
                result=self.unpack()
            return result,address
        except Exception as e:
            print "Error during SocketConnection.receive: ",e
            raise e

    def close(self):
        self.sock.close()


class UDPClientConnection(SocketConnection):
    def __init__(self,remote_host='127.0.0.1',remote_port=9000,rcvBufferLength = MAX_PACKET_SIZE,broadcast=False,blocking=1, timeout=1):
        SocketConnection.__init__(self,remote_host=remote_host,remote_port=remote_port,rcvBufferLength=rcvBufferLength,broadcast=broadcast,blocking=blocking, timeout=timeout)
    def initSocket(self,**kwargs):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, MAX_PACKET_SIZE)
