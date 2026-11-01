# Copyright 2016-2020 Matthew Wall, 2025-2026 Werner Krenn
# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
# Distributed under the terms of the GNU General Public License, version 3.
# Changed 2026-11-01: separate WeeWX lifecycle from upload parsing and transport.
"""Connect the upload receiver and parsers to the WeeWX driver interface."""

import logging
import math
import queue
import threading
from typing import cast

import weewx.drivers
import weeutil.weeutil

from . import VERSION
from .definitions import DEFAULT_SENSOR_MAP, DEFINITIONS
from .http import UploadServer
from .parser import EcowittParser, Parser, WUParser
from .sniff import SniffServer

log = logging.getLogger(__name__)
DRIVER_NAME = 'Ecowittcustom'
DEFAULT_ADDR = ''
DEFAULT_PORT = 80
DEFAULT_DEVICE_TYPE = 'ecowitt-client'


class Consumer:
    """Own one station parser, receiver and bounded upload queue."""

    DEFAULT_SENSOR_MAP = DEFAULT_SENSOR_MAP
    Parser = Parser

    def __init__(self, parser, mode='listen', address=DEFAULT_ADDR,
                 port=DEFAULT_PORT, iface='eth0', pcap_filter='dst port 80',
                 promiscuous=False):
        self.parser = parser
        self.queue = queue.Queue(maxsize=128)
        if mode == 'listen':
            response = DEFINITIONS['protocols'][parser.PROTOCOL]['response']
            self._server = cast('UploadServer|SniffServer',
                                UploadServer(address, port, self.queue, response))
        elif mode == 'sniff':
            self._server = SniffServer(iface, pcap_filter,
                                       weeutil.weeutil.to_bool(promiscuous),
                                       self.queue)
        else:
            raise ValueError("Unsupported mode '%s'" % mode)

    def default_sensor_map(self):
        """Return an independent sensor map for this upload protocol."""
        return dict(self.DEFAULT_SENSOR_MAP,
                    **DEFINITIONS['protocols'][self.parser.PROTOCOL]['sensor_map'])

    def run_server(self):
        self._server.run()

    def stop_server(self):
        self._server.stop()

    def get_queue(self):
        return self.queue


class EcowittClient(Consumer):
    Parser = EcowittParser

    def __init__(self, **settings):
        super().__init__(self.Parser(), **settings)


class WUClient(Consumer):
    Parser = WUParser

    def __init__(self, **settings):
        super().__init__(self.Parser(), **settings)


class EcowittcustomDriver(weewx.drivers.AbstractDevice):
    DEVICE_TYPES = {'ecowitt-client': EcowittClient, 'wu-client': WUClient}

    def __init__(self, **settings):
        log.info('Driver version %s', VERSION)
        settings.pop('driver', None)
        self._device_type = settings.pop('device_type', DEFAULT_DEVICE_TYPE)
        if self._device_type not in self.DEVICE_TYPES:
            raise ValueError("Unsupported device type '%s'" % self._device_type)
        self._queue_timeout = float(settings.pop('queue_timeout', 10))
        if not math.isfinite(self._queue_timeout) or self._queue_timeout <= 0:
            raise ValueError('queue_timeout must be positive and finite')
        sensor_map = settings.pop('sensor_map', None)
        extensions = settings.pop('sensor_map_extensions', {})
        self._device = self.DEVICE_TYPES[self._device_type](**settings)
        self._obs_map = (self._device.default_sensor_map() if sensor_map is None
                         else dict(sensor_map))
        self._obs_map.update(extensions)
        self._closed = threading.Event()
        self._server_thread = threading.Thread(
            target=self._device.run_server, name='EcowittcustomReceiver', daemon=True)
        self._server_thread.start()

    @property
    def hardware_name(self):
        return '%s %s' % (DRIVER_NAME, self._device_type)

    def closePort(self):
        """Stop the receiver and release its port; repeated calls are harmless."""
        if self._closed.is_set():
            return
        self._closed.set()
        try:
            self._device.get_queue().put_nowait(None)
        except queue.Full:
            pass
        self._device.stop_server()
        self._server_thread.join(timeout=20)
        if self._server_thread.is_alive():
            log.error('Receiver did not stop within 20 seconds')

    def genLoopPackets(self):
        """Yield mapped observations until the driver closes."""
        while not self._closed.is_set():
            try:
                payload = self._device.get_queue().get(timeout=self._queue_timeout)
            except queue.Empty:
                continue
            if self._closed.is_set():
                return
            packet = self._device.parser.parse(payload)
            if packet:
                yield self._device.parser.map_to_fields(packet, self._obs_map)


class EcowittcustomConfigurationEditor(weewx.drivers.AbstractConfEditor):
    @property
    def default_stanza(self):
        return """
[Ecowittcustom]
    driver = user.ecowittcustom
    # Upload protocol: ecowitt-client or wu-client.
    device_type = ecowitt-client
    # Match the port configured on the console's customized server.
    port = 8080
"""

    def prompt_for_settings(self):
        return {'device_type': self._prompt('device_type', DEFAULT_DEVICE_TYPE,
                                            list(EcowittcustomDriver.DEVICE_TYPES))}
