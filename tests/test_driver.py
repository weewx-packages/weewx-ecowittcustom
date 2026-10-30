# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
"""The driver turns an Ecowitt upload into WeeWX observations."""

import ast
import pathlib

import pytest

from user import ecowittcustom

ROOT = pathlib.Path(__file__).resolve().parents[1]
UPLOAD = ('PASSKEY=0123456789ABCDEF0123456789ABCDEF&stationtype=GW1100B_V2.3.1'
          '&dateutc=2026-10-30+19:00:00&tempinf=72.0&humidityin=45&baromrelin=29.92'
          '&baromabsin=29.80&tempf=50.0&humidity=70&winddir=180&windspeedmph=3.0'
          '&windgustmph=5.0&solarradiation=100.0&uv=1&rainratein=0.0&dailyrainin=0.01'
          '&totalrainin=1.00&wh65batt=0&freq=868M&model=GW1100B')


def test_upload_becomes_observations():
    parser = ecowittcustom.EcowittClient.Parser()
    packet = parser.parse(UPLOAD)
    mapped = parser.map_to_fields(packet, ecowittcustom.Consumer.DEFAULT_SENSOR_MAP)
    assert mapped['outTemp'] == pytest.approx(50.0)
    assert mapped['outHumidity'] == pytest.approx(70.0)
    assert mapped['windDir'] == pytest.approx(180.0)
    assert mapped['usUnits'] == 1


def test_installer_stays_inside_the_extension_paths():
    source = (ROOT / 'install.py').read_text(encoding='utf-8')
    assert ast.parse(source)
    for forbidden in ('DataBindings', 'bin/schemas', '[Engine]', 'skins/'):
        assert forbidden not in source
