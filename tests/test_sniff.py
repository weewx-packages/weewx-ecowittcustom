# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
"""Exercise passive HTTP framing with synthetic Ethernet/IPv4/TCP frames."""

import queue

from user.ecowittcustomlib.sniff import HTTPStreams


def frame(payload, sequence=100, port=1234, vlan=False):
    ethernet = b'\x00' * 12 + (b'\x81\x00\x00\x01\x08\x00' if vlan else b'\x08\x00')
    ip = bytearray(20)
    ip[0] = 0x45
    ip[2:4] = (40 + len(payload)).to_bytes(2, 'big')
    ip[9] = 6
    ip[12:20] = b'\x7f\x00\x00\x01' * 2
    tcp = bytearray(20)
    tcp[:2] = port.to_bytes(2, 'big')
    tcp[2:4] = (80).to_bytes(2, 'big')
    tcp[4:8] = sequence.to_bytes(4, 'big')
    tcp[12] = 0x50
    return ethernet + ip + tcp + payload


def test_interleaved_connections_and_retransmitted_segments():
    incoming = queue.Queue()
    streams = HTTPStreams(incoming)
    first = b'POST / HTTP/1.0\r\nContent-Length: 8\r\n\r\ntempf='
    streams.feed(frame(first))
    streams.feed(frame(first))
    streams.feed(frame(b'GET /?humidity=45 HTTP/1.0\r\n\r\n', port=5678, vlan=True))
    streams.feed(frame(b'32', sequence=100 + len(first)))
    assert incoming.get_nowait() == 'humidity=45'
    assert incoming.get_nowait() == 'tempf=32'
    assert incoming.empty()


def test_missing_tcp_segment_does_not_produce_a_corrupt_upload():
    incoming = queue.Queue()
    streams = HTTPStreams(incoming)
    streams.feed(frame(b'POST / HTTP/1.0\r\nContent-Length: 8\r\n\r\ntempf='))
    streams.feed(frame(b'32', sequence=999))
    assert incoming.empty()


def test_short_or_unrelated_frames_are_ignored():
    incoming = queue.Queue()
    streams = HTTPStreams(incoming)
    for size in range(54):
        streams.feed(b'\x00' * size)
    streams.feed(frame(b'HTTP/1.0 200 OK\r\n\r\n'))
    assert incoming.empty()
