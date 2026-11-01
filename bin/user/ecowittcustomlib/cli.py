# Copyright 2016-2020 Matthew Wall, 2025-2026 Werner Krenn
# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
# Distributed under the terms of the GNU General Public License, version 3.
# Changed 2026-11-01: parse --data without opening a listener and close on exit.
"""Run an upload receiver or decode a saved form without network access."""

import argparse
import logging

from . import VERSION
from .driver import DEFAULT_ADDR, DEFAULT_PORT, EcowittcustomDriver
from .parser import EcowittParser, WUParser


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--device', dest='device_type', default='ecowitt-client',
                        choices=list(EcowittcustomDriver.DEVICE_TYPES))
    parser.add_argument('--data', help='decode a URL-encoded upload and exit')
    parser.add_argument('--mode', choices=['listen', 'sniff'], default='listen')
    parser.add_argument('--address', default=DEFAULT_ADDR)
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--iface', default='eth0')
    parser.add_argument('--filter', dest='pcap_filter', default='dst port 80')
    options = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if options.debug else logging.INFO)
    settings = vars(options).copy()
    settings.pop('debug')
    payload = settings.pop('data')
    if payload is not None:
        protocol_parser = (EcowittParser() if options.device_type == 'ecowitt-client'
                           else WUParser())
        sensor_map = EcowittcustomDriver.DEVICE_TYPES[options.device_type].DEFAULT_SENSOR_MAP.copy()
        sensor_map.update(protocol_parser.definition['sensor_map'])
        print(protocol_parser.map_to_fields(protocol_parser.parse(payload), sensor_map))
        return
    driver = EcowittcustomDriver(**settings)
    try:
        for packet in driver.genLoopPackets():
            print(packet)
    except KeyboardInterrupt:
        pass
    finally:
        driver.closePort()
