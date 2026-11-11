"""Stands in for the web browser server in tests, without Qt.

Speaks the same protocol (see `psychopy.visual.web._protocol`). Pages are a
solid color, given as ``html='color:R,G,B'``, and input and messages sent to a
page are sent back as page messages, so tests can check what reached it.
JavaScript `'crash'` makes the server exit, `'ignore'` is never answered, and
anything else is answered with its length.

Use it by setting the `PSYCHOPY_WEB_SERVER_CMD` environment variable to
``<python> <this file>``.
"""
import argparse
import os
import sys
import threading

# import the protocol modules as the real server does, without PsychoPy
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir,
    os.pardir, 'visual', 'web'))
import _protocol  # noqa: E402
import _shm  # noqa: E402
import _watchdog  # noqa: E402

NUM_SLOTS = 3


class FakeView:
    def __init__(self, conn, viewId, cfg):
        self.conn = conn
        self.id = viewId
        self.gen = 0
        self.seq = 0
        self.ring = None
        self.free = set()
        html = cfg.get('html') or ''
        if html.startswith('color:'):
            self.color = tuple(int(v) for v in html[6:].split(',')) + (255,)
        else:
            self.color = (255, 255, 255, 255)
        self.send('loadStarted')
        self.resize(cfg['w'], cfg['h'])
        self.send('loadFinished', ok=True, url=cfg.get('url') or 'about:blank')

    def send(self, op, **msg):
        self.conn.send_bytes(_protocol.pack(dict(op=op, view=self.id, **msg)))

    def resize(self, width, height):
        if self.ring is not None:
            self.ring.close()
        self.gen += 1
        name = _protocol.shmName(os.getpid(), self.id, self.gen)
        self.ring = _shm.FrameRing.create(
            name, width, height, width * 4, 'rgba_pm', NUM_SLOTS, self.gen)
        self.free = set(range(NUM_SLOTS))
        self.send('surface', shm=name, w=width, h=height, stride=width * 4,
                  fmt='rgba_pm', slots=NUM_SLOTS, gen=self.gen, dpr=1.0)
        self.frame()

    def frame(self):
        if not self.free:
            return
        slot = min(self.free)
        self.free.discard(slot)
        self.ring.write(slot, bytes(self.color) * (self.ring.width *
                                                   self.ring.height))
        self.seq += 1
        self.send('frame', slot=slot, seq=self.seq, gen=self.gen, t=0.)

    def close(self):
        if self.ring is not None:
            self.ring.close()
            self.ring = None
        try:
            self.send('closed')
        except OSError:  # shutting down after the connection closed
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--address', required=True)
    parser.add_argument('--parent-pid', type=int, required=True)
    parser.add_argument('--platform', default='auto')
    args = parser.parse_args()

    from multiprocessing.connection import Client
    authkey = bytes.fromhex(os.environ.pop(_protocol.ENV_AUTHKEY, ''))
    conn = Client(args.address, authkey=authkey)
    _watchdog.startParentWatchdog(args.parent_pid, _shm.closeOwnedRings,
                                  grace=0.5)
    lock = threading.Lock()

    class LockedConn:
        def send_bytes(self, data):
            with lock:
                conn.send_bytes(data)

    out = LockedConn()
    out.send_bytes(_protocol.pack(dict(
        op='hello', protocol=_protocol.PROTOCOL_VERSION, pid=os.getpid(),
        versions={'fake': True}, platform='fake', qpa='fake')))
    views = {}
    try:
        while True:
            msg = _protocol.unpack(conn.recv_bytes())
            op = msg['op']
            view = views.get(msg.get('view'))
            if op == 'create':
                views[msg['view']] = FakeView(out, msg['view'], msg)
            elif op == 'shutdown':
                break
            elif op == 'ping':
                out.send_bytes(_protocol.pack(dict(op='pong', id=msg['id'])))
            elif view is None:
                continue
            elif op == 'release':
                if msg['gen'] == view.gen:
                    view.free.add(msg['slot'])
            elif op == 'resize':
                view.resize(msg['w'], msg['h'])
            elif op in ('input', 'message', 'navigate', 'history', 'setHtml'):
                view.send('pageMessage', data=msg, origin='fake')
            elif op == 'js':
                if msg['code'] == 'crash':
                    _shm.closeOwnedRings()
                    os._exit(1)
                if msg['code'] != 'ignore':
                    view.send('jsResult', id=msg['id'], ok=True,
                              value=len(msg['code']))
            elif op == 'close':
                views.pop(msg['view']).close()
    except (EOFError, OSError):
        pass
    for view in views.values():
        view.close()
    _shm.closeOwnedRings()


if __name__ == '__main__':
    main()
