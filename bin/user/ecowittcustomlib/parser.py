# Copyright 2016-2020 Matthew Wall, 2025-2026 Werner Krenn
# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
# Distributed under the terms of the GNU General Public License, version 3.
# Changed 2026-11-01: separate protocol parsing and isolate counter state.
"""Decode form uploads into observations in the WeeWX US unit system."""

import calendar
import fnmatch
import logging
import math
import time
from urllib.parse import parse_qsl

import weewx

from .definitions import DEFINITIONS

log = logging.getLogger(__name__)


def decode_form(payload):
    """Decode a UTF-8 form, preserving empty values and taking the last duplicate.

    Args:
        payload (str): URL-encoded query or request body.

    Returns:
        dict: Decoded field names and string values.

    Raises:
        ValueError: The form is malformed or has more than 4096 fields.
    """
    return dict(parse_qsl(payload, keep_blank_values=True, strict_parsing=True,
                          errors='strict', max_num_fields=4096))


class Parser:
    """Parse successive uploads from one station with independent counters."""

    PROTOCOL = 'ecowitt-client'
    LABEL_MAP = {}
    IGNORED_LABELS = []

    def __init__(self):
        self.definition = DEFINITIONS['protocols'][self.PROTOCOL]
        self._counter_sources = {}
        self._last_counters = {}
        self._last_timestamp = None
        self._last_data = None

    def parse(self, payload):
        """Decode one upload, rejecting malformed forms and older measurements.

        Args:
            payload (str): URL-encoded station upload.

        Returns:
            dict: Internal observations with dateTime and usUnits. Invalid or
            repeated uploads return an empty dictionary. Invalid numeric fields
            become None without discarding other observations.
        """
        try:
            data = decode_form(payload)
            timestamp = self.decode_datetime(data.get('dateutc', 'now'))
        except (ValueError, UnicodeError, OverflowError):
            log.warning('Discarding upload with an invalid form or UTC timestamp')
            return {}
        if self._last_timestamp is not None:
            if timestamp < self._last_timestamp:
                log.debug('Discarding older upload at %s', timestamp)
                return {}
            if timestamp == self._last_timestamp and data == self._last_data:
                return {}

        packet = {}
        for name, value in data.items():
            target = self.LABEL_MAP.get(name)
            if target is None:
                if name not in self.IGNORED_LABELS:
                    log.debug('Unrecognized upload field: %s', name)
                continue
            if target in ('model', 'stationtype'):
                packet[target] = value
            else:
                packet[target] = self.decode_float(value)

        counter_names = self.definition['rain_counters'] + self.definition['piezo_counters']
        if not packet and not any(name in data for name in counter_names):
            return {}
        packet.update(dateTime=timestamp, usUnits=weewx.US)
        if self.PROTOCOL == 'ecowitt-client':
            # Ecowitt sends lightning distance in kilometres even though its
            # temperatures, wind and rain use US units. WeeWX expects miles.
            if packet.get('lightning') is not None:
                packet['lightning'] /= 1.609344

        self._rain_counter(data, packet, self.definition['rain_counters'],
                           'rain_total', 'rain')
        self._rain_counter(data, packet, self.definition['piezo_counters'],
                           'rain_total_piezo', 'rain_piezo')
        count = packet.get('lightning_num')
        if count is not None and count >= 0:
            packet['lightning_strike_count'] = self._counter_delta(
                count, self._last_counters.get('lightning'))
            self._last_counters['lightning'] = count

        self._last_timestamp = timestamp
        self._last_data = data
        return packet

    def _rain_counter(self, data, packet, sources, total_field, delta_field):
        source = self._counter_sources.get(delta_field)
        if source is None:
            for name in sources:
                value = self.decode_float(data.get(name))
                if value is not None and value >= 0:
                    source = name
                    self._counter_sources[delta_field] = source
                    break
        if source is None or source not in data:
            return
        value = self.decode_float(data[source])
        if value is not None and value < 0:
            value = None
        packet[total_field] = value
        packet[delta_field] = self._counter_delta(
            value, self._last_counters.get(delta_field))
        # Partial uploads must not switch between daily, yearly and lifetime
        # totals. Their different baselines would create fictitious rain.
        if value is not None:
            self._last_counters[delta_field] = value

    @staticmethod
    def _counter_delta(value, previous):
        """Return a counter increment, or None before the first valid baseline."""
        if value is None or previous is None:
            return None
        return value if value < previous else value - previous

    @staticmethod
    def decode_float(value):
        """Return a finite reading or None for missing and invalid station values.

        Args:
            value (str|int|float|None): Uploaded numeric value.

        Returns:
            float|None: Reading, with -9999 treated as the missing-value sentinel.
        """
        if value in (None, '', '--'):
            return None
        try:
            number = float(value)
        except (ValueError, TypeError):
            return None
        return number if math.isfinite(number) and number != -9999 else None

    @staticmethod
    def decode_datetime(value):
        """Return Unix seconds for a decoded UTC date, 'now', or an integer."""
        if isinstance(value, int):
            return value
        if value == 'now':
            return int(time.time() + 0.5)
        return calendar.timegm(time.strptime(value.replace('+', ' '),
                                            '%Y-%m-%d %H:%M:%S'))

    @staticmethod
    def map_to_fields(packet, sensor_map):
        """Apply a WeeWX-field-to-internal-name mapping without changing inputs.

        Args:
            packet (dict): Parsed observations.
            sensor_map (dict|None): Internal names or legacy three-part patterns.
                None returns a copy of all observations.

        Returns:
            dict: Mapped fields, retaining dateTime and usUnits.
        """
        if sensor_map is None:
            return dict(packet)
        result = {name: packet[name] for name in ('dateTime', 'usUnits')
                  if name in packet}
        for field, pattern in sensor_map.items():
            match = Parser._find_match(pattern, packet)
            if match is not None:
                result[field] = packet[match]
        return result

    @staticmethod
    def _find_match(pattern, keys):
        if pattern in keys:
            return pattern
        parts = pattern.split('.')
        if len(parts) == 3:
            matches = [key for key in keys
                       if (key == parts[0] or
                           (len(key.split('.')) == 3 and all(
                               fnmatch.fnmatchcase(value, part)
                               for part, value in zip(parts, key.split('.')))))]
            if matches:
                return matches[-1]
        return None


class EcowittParser(Parser):
    PROTOCOL = 'ecowitt-client'
    LABEL_MAP = DEFINITIONS['protocols'][PROTOCOL]['labels']
    IGNORED_LABELS = DEFINITIONS['protocols'][PROTOCOL]['ignored']


class WUParser(Parser):
    PROTOCOL = 'wu-client'
    LABEL_MAP = DEFINITIONS['protocols'][PROTOCOL]['labels']
    IGNORED_LABELS = DEFINITIONS['protocols'][PROTOCOL]['ignored']
