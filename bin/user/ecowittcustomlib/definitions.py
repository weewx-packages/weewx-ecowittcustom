# Copyright 2016-2020 Matthew Wall, 2025-2026 Werner Krenn
# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
# Distributed under the terms of the GNU General Public License, version 3.
# Changed 2026-11-01: load the inherited field and unit tables from JSON.
"""Load the bundled observation definitions and register their WeeWX units."""

import json
from pathlib import Path

import weewx.units


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate definition: %s' % key)
        result[key] = value
    return result


def load_definitions():
    """Return the bundled tables, rejecting duplicate JSON keys.

    Returns:
        dict: Sensor maps, unit definitions, protocols and installer settings.
    """
    path = Path(__file__).with_name('definitions.json')
    with path.open(encoding='utf-8') as source:
        return json.load(source, object_pairs_hook=_unique_object)


DEFINITIONS = load_definitions()
DEFAULT_SENSOR_MAP = DEFINITIONS['sensor_map']


def register_units():
    """Register the additional observations before WeeWX builds accumulators."""
    weewx.units.obs_group_dict.update(DEFINITIONS['observation_groups'])
    for name, groups in DEFINITIONS['unit_systems'].items():
        getattr(weewx.units, name).update(groups)
    weewx.units.default_unit_format_dict.update(DEFINITIONS['unit_formats'])
    weewx.units.default_unit_label_dict.update(DEFINITIONS['unit_labels'])
