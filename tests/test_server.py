# -*- coding: utf-8 -*-
import json
import os
import socket
import sys
import unittest

try:
    from Queue import Queue
    from urllib2 import HTTPError, Request, urlopen
except ImportError:
    from queue import Queue
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mod', 'scripts', 'client', 'gui'))

from session_stats.server import ApiServer  # noqa: E402


def free_port():
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class ServerTest(unittest.TestCase):

    def setUp(self):
        self.commands = Queue()
        self.server = ApiServer(lambda: json.dumps({'ok': True}).encode('utf-8'), self.commands,
                                {'index.html': b'<html></html>', 'assets/app.js': b'1;'})
        self.server.start(free_port())

    def tearDown(self):
        self.server.stop()

    def get(self, path):
        return urlopen(self.server.url + path, timeout=5)

    def test_state(self):
        response = self.get('api/session')
        self.assertEqual(json.loads(response.read().decode('utf-8')), {'ok': True})
        self.assertIn('application/json', response.headers['Content-Type'])

    def test_static(self):
        self.assertEqual(self.get('').read(), b'<html></html>')
        response = self.get('assets/app.js?v=1')
        self.assertIn('javascript', response.headers['Content-Type'])

    def test_not_found(self):
        with self.assertRaises(HTTPError) as ctx:
            self.get('nope.js')
        self.assertEqual(ctx.exception.code, 404)

    def test_command_goes_to_queue(self):
        urlopen(Request(self.server.url + 'api/reset', data=b''), timeout=5)
        self.assertEqual(self.commands.get_nowait(), 'reset')

    def test_unknown_command(self):
        with self.assertRaises(HTTPError):
            urlopen(Request(self.server.url + 'api/format_c', data=b''), timeout=5)
        self.assertTrue(self.commands.empty())

    def test_busy_port_moves_to_next(self):
        other = ApiServer(lambda: b'{}', Queue())
        port = other.start(self.server.port)
        try:
            self.assertNotEqual(port, self.server.port)
        finally:
            other.stop()


if __name__ == '__main__':
    unittest.main()
