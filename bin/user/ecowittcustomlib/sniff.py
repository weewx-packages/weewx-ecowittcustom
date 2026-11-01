# Copyright 2016-2020 Matthew Wall, 2025-2026 Werner Krenn
# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
# Distributed under the terms of the GNU General Public License, version 3.
# Changed 2026-11-01: decode Ethernet/IPv4/TCP bytes and frame HTTP uploads.
"""Optional passive receiver for unencrypted HTTP on Ethernet IPv4 networks."""

import logging
import queue
import threading
from urllib.parse import urlsplit

from .http import MAX_UPLOAD_BYTES

log = logging.getLogger(__name__)


class HTTPStreams:
    """Reassemble contiguous TCP payloads separately for each connection."""

    def __init__(self, upload_queue):
        self.queue = upload_queue
        self._streams = {}

    def feed(self, frame):
        """Read one Ethernet frame, discarding fragments and incomplete streams."""
        if len(frame) < 14:
            return
        offset = 14
        kind = frame[12:14]
        if kind == b'\x81\x00' and len(frame) >= 18:
            offset = 18
            kind = frame[16:18]
        if kind != b'\x08\x00' or len(frame) < offset + 20:
            return
        ip = frame[offset:]
        ip_length = (ip[0] & 15) * 4
        total_length = int.from_bytes(ip[2:4], 'big')
        if (ip[0] >> 4 != 4 or ip_length < 20 or ip[9] != 6 or
                int.from_bytes(ip[6:8], 'big') & 0x3fff or
                len(ip) < total_length or total_length < ip_length + 20):
            return
        tcp = ip[ip_length:total_length]
        tcp_length = (tcp[12] >> 4) * 4
        if tcp_length < 20 or len(tcp) < tcp_length:
            return
        key = (ip[12:20], tcp[:4])
        if tcp[13] & 0x07:
            self._streams.pop(key, None)
        payload = tcp[tcp_length:]
        if not payload:
            return
        sequence = int.from_bytes(tcp[4:8], 'big')
        expected, buffered = self._streams.pop(key, (sequence, b''))
        # Captures can contain retransmissions. Never append their bytes twice,
        # and discard a stream with a gap rather than joining unrelated bytes.
        overlap = (expected - sequence) & 0xffffffff
        if overlap > len(payload):
            return
        payload = payload[overlap:]
        buffered += payload
        if len(buffered) > MAX_UPLOAD_BYTES + 8192:
            return
        buffered = self._extract(buffered)
        if buffered:
            if len(self._streams) >= 32:
                self._streams.pop(next(iter(self._streams)))
            self._streams[key] = ((sequence + overlap + len(payload)) & 0xffffffff,
                                  buffered)

    def _extract(self, buffered):
        while buffered:
            if not (b'GET '.startswith(buffered[:4]) or
                    b'POST '.startswith(buffered[:5])):
                return b''
            end = buffered.find(b'\r\n\r\n')
            if end < 0:
                return buffered if len(buffered) <= 8192 else b''
            try:
                lines = buffered[:end].decode('ascii').split('\r\n')
                method, path, version = lines[0].split()
                headers = {}
                for line in lines[1:]:
                    name, value = line.split(':', 1)
                    name = name.lower()
                    if name in headers:
                        return b''
                    headers[name] = value.strip()
                if 'transfer-encoding' in headers:
                    return b''
                length = int(headers['content-length']) if method == 'POST' else 0
                if not 0 <= length <= MAX_UPLOAD_BYTES:
                    return b''
                start = end + 4
                if len(buffered) < start + length:
                    return buffered
                payload = (buffered[start:start + length].decode('utf-8')
                           if method == 'POST' else urlsplit(path).query)
            except (ValueError, UnicodeError, KeyError):
                return b''
            if payload:
                try:
                    self.queue.put_nowait(payload)
                except queue.Full:
                    log.warning('Passive upload queue full')
            buffered = buffered[start + length:]
        return b''


class SniffServer:
    def __init__(self, iface, pcap_filter, promiscuous, upload_queue):
        try:
            import pcap
        except ImportError as error:
            raise ImportError('mode=sniff requires a Python pcap binding') from error
        self._stopped = threading.Event()
        self._streams = HTTPStreams(upload_queue)
        self._legacy = hasattr(pcap, 'pcapObject')
        if self._legacy:
            self._capture = pcap.pcapObject()
            self._capture.open_live(iface, 65535, int(promiscuous), 100)
            self._capture.setfilter(pcap_filter, 0, 0)
        else:
            self._capture = pcap.pcap(name=iface, snaplen=65535,
                                      promisc=promiscuous, timeout_ms=100)
            self._capture.setfilter(pcap_filter)
        try:
            if self._capture.datalink() != 1:
                raise ValueError('mode=sniff requires Ethernet capture frames')
            self._capture.setnonblock(True)
        except Exception:
            self._capture.close()
            raise

    def run(self):
        try:
            while not self._stopped.is_set():
                if self._legacy:
                    self._capture.dispatch(16, self._legacy_packet)
                else:
                    self._capture.dispatch(16, self._packet)
                self._stopped.wait(0.05)
        finally:
            self._capture.close()

    def _packet(self, timestamp, frame):
        self._streams.feed(frame)

    def _legacy_packet(self, length, frame, timestamp):
        self._streams.feed(frame)

    def stop(self):
        self._stopped.set()
