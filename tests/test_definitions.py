# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
"""Check the bundled data for ambiguous keys and missing field destinations."""

import json

import pytest
import weewx.units

from user.ecowittcustomlib.definitions import DEFINITIONS, _unique_object


def test_duplicate_json_keys_are_rejected():
    with pytest.raises(ValueError, match='Duplicate definition: rain24'):
        json.loads('{"sensor_map":{"rain24":"one","rain24":"two"}}',
                   object_pairs_hook=_unique_object)


def test_ecowitt_fields_all_have_a_default_output():
    protocol = DEFINITIONS['protocols']['ecowitt-client']
    mapped = set(DEFINITIONS['sensor_map'].values())
    assert not {field: target for field, target in protocol['labels'].items()
                if target not in mapped}
    assert not set(protocol['labels']) & set(protocol['ignored'])


def test_declared_observation_groups_have_units_in_every_system():
    for group in DEFINITIONS['observation_groups'].values():
        for system in (weewx.units.USUnits, weewx.units.MetricUnits,
                       weewx.units.MetricWXUnits):
            assert group in system


def test_installer_accumulators_refer_to_emitted_fields():
    assert set(DEFINITIONS['installation']['Accumulator']) <= set(DEFINITIONS['sensor_map'])
