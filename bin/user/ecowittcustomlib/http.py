# Copyright 2016-2020 Matthew Wall, 2025-2026 Werner Krenn
# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
# Distributed under the terms of the GNU General Public License, version 3.
# Changed 2026-11-01: isolate HTTP reception and validate request framing.
"""Receive station uploads on an HTTP listener with a queue per instance."""

import logging
import queue
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import cast
from urllib.parse import urlsplit

log = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 65536


class UploadHandler(BaseHTTPRequestHandler):
    """Accept form uploads without logging request URLs or credentials."""

    def setup(self):
        self.request.settimeout(10)
        super().setup()

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            log.debug('Upload connection closed before completion')

    def do_GET(self):
        try:
            payload = urlsplit(self.path).query
        except ValueError:
            self.send_error(400, 'Invalid request URL')
            return
        if len(payload.encode('utf-8')) > MAX_UPLOAD_BYTES:
            self.send_error(413, 'Upload too large')
            return
        self._enqueue(payload)

    def do_POST(self):
        if self.headers.get('Transfer-Encoding'):
            self.send_error(501, 'Transfer encoding is unsupported')
            return
        lengths = self.headers.get_all('Content-Length', [])
        if not lengths:
            self.send_error(411, 'Content-Length required')
            return
        try:
            if len(lengths) != 1:
                raise ValueError('Multiple content lengths')
            length = int(lengths[0])
            if length < 0:
                raise ValueError('Negative content length')
        except ValueError:
            self.send_error(400, 'Invalid Content-Length')
            return
        if length > MAX_UPLOAD_BYTES:
            self.send_error(413, 'Upload too large')
            return
        try:
            body = self.rfile.read(length)
            if len(body) != length:
                self.send_error(400, 'Incomplete upload')
                return
            payload = body.decode('utf-8')
        except UnicodeError:
            self.send_error(400, 'Upload must be UTF-8')
            return
        except TimeoutError:
            self.send_error(408, 'Upload timed out')
            return
        self._enqueue(payload)

    def _enqueue(self, payload):
        server = cast(UploadServer, self.server)
        if payload:
            try:
                server.upload_queue.put_nowait(payload)
            except queue.Full:
                self.send_error(503, 'Upload queue full')
                return
        response = server.upload_response.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', server.response_type)
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format_string, *args):
        # BaseHTTPRequestHandler includes the request URL in its default log.
        # WU uploads place their password in that URL.
        pass


class UploadServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, port, upload_queue, response):
        self.upload_queue = upload_queue
        self.upload_response = response
        self.response_type = ('application/json' if response.startswith('{')
                              else 'text/plain; charset=utf-8')
        super().__init__((address, int(port)), UploadHandler)

    def run(self):
        self.serve_forever(poll_interval=0.1)

    def stop(self):
        self.shutdown()
        self.server_close()
