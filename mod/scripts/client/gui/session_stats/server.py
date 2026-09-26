# -*- coding: utf-8 -*-
"""Маленький HTTP-сервер на 127.0.0.1: отдаёт интерфейс и JSON со статистикой.

Сервер работает в отдельном потоке, поэтому игровые объекты он не трогает:
состояние берёт из готового снимка (строка JSON), а команды складывает в очередь,
которую разбирает основной поток игры.
"""
import logging
import posixpath
import threading

try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
except ImportError:  # python 3, для тестов
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn

logger = logging.getLogger(__name__)

CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.woff2': 'font/woff2',
}
COMMANDS = ('reset',)


class _Server(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = False


class _Handler(BaseHTTPRequestHandler):
    server_version = 'SessionStats'

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/api/session':
            self._send(200, self.server.api.get_state(), CONTENT_TYPES['.json'])
            return
        if path == '/':
            path = '/index.html'
        body = self.server.api.static_files.get(path.lstrip('/'))
        if body is None:
            self._send(404, b'not found', 'text/plain')
            return
        ext = posixpath.splitext(path)[1]
        self._send(200, body, CONTENT_TYPES.get(ext, 'application/octet-stream'))

    def do_POST(self):
        prefix = '/api/'
        command = self.path[len(prefix):] if self.path.startswith(prefix) else None
        if command not in COMMANDS:
            self._send(404, b'unknown command', 'text/plain')
            return
        self.server.api.commands.put(command)
        self._send(202, b'{}', CONTENT_TYPES['.json'])

    def do_OPTIONS(self):
        self._send(204, b'', 'text/plain')

    def _send(self, code, body, content_type):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        # нужно для разработки интерфейса через vite dev server
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # по умолчанию пишет каждый запрос в stderr, а это попадает в python.log игры
        pass


class ApiServer(object):

    def __init__(self, get_state, commands, static_files=None, host='127.0.0.1'):
        self.get_state = get_state
        self.commands = commands
        self.static_files = static_files or {}
        self.host = host
        self.port = None
        self._server = None
        self._thread = None

    @property
    def url(self):
        return 'http://%s:%d/' % (self.host, self.port)

    def start(self, port, attempts=10):
        """Пробует порты port..port+attempts-1, если первый занят."""
        last_error = None
        for candidate in range(port, port + attempts):
            try:
                self._server = _Server((self.host, candidate), _Handler)
            except (OSError, IOError) as error:
                last_error = error
                continue
            self._server.api = self
            self.port = self._server.server_address[1]
            break
        else:
            raise last_error

        self._thread = threading.Thread(target=self._server.serve_forever, name='session_stats_http')
        self._thread.daemon = True
        self._thread.start()
        return self.port

    def stop(self):
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(2)
        self._server = self._thread = None
