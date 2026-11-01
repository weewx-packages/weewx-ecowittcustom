# Copyright 2025-2026 Werner Krenn
# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
# Distributed under the terms of the GNU General Public License, version 3.
# Changed 2026-10-30: package the driver without upstream skins and helpers.
# Changed 2026-11-01: install the refactored modules and their JSON definitions.
"""Install the Ecowitt upload driver and its accumulator configuration."""

import json
from pathlib import Path

from weecfg.extension import ExtensionInstaller

VERSION = '0.3.0'


def loader():
    return EcowittcustomInstaller()


class EcowittcustomInstaller(ExtensionInstaller):
    def __init__(self):
        root = Path(__file__).resolve().parent
        package = 'bin/user/ecowittcustomlib'
        definitions = root / package / 'definitions.json'
        if not definitions.exists():
            # WeeWX caches only install.py under USER_ROOT/installer/NAME.
            # During removal the tables still exist in the installed package.
            definitions = root.parents[1] / 'ecowittcustomlib/definitions.json'
        with definitions.open(encoding='utf-8') as source:
            config = json.load(source)['installation']
        super().__init__(
            version=VERSION,
            name='ecowittcustom',
            description='Capture weather data from Ecowitt consoles and gateways over HTTP',
            author='Matthew Wall, Werner Krenn, Manuel Hilgert',
            author_email='',
            files=[
                ('bin/user', ['bin/user/ecowittcustom.py']),
                (package, [package + '/' + name for name in (
                    '__init__.py', 'cli.py', 'definitions.py', 'driver.py',
                    'http.py', 'parser.py', 'sniff.py', 'definitions.json')]),
            ],
            config=config)
