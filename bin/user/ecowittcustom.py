#!/usr/bin/env python
# Copyright 2016-2020 Matthew Wall, 2025-2026 Werner Krenn
# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
# Distributed under the terms of the GNU General Public License, version 3.
# Changed 2026-11-01: keep the WeeWX entry points and move implementation into
# ecowittcustomlib. This package is maintained independently of upstream.
"""WeeWX entry points for customized-server uploads from Ecowitt stations."""

from user.ecowittcustomlib import VERSION as DRIVER_VERSION
from user.ecowittcustomlib.definitions import register_units
from user.ecowittcustomlib.driver import (
    DEFAULT_ADDR, DEFAULT_DEVICE_TYPE, DEFAULT_PORT, DRIVER_NAME, Consumer,
    EcowittClient, EcowittcustomConfigurationEditor, EcowittcustomDriver, WUClient,
)

register_units()


def loader(config_dict, engine):
    """Build the driver from the Ecowittcustom configuration section."""
    return EcowittcustomDriver(**config_dict[DRIVER_NAME])


def confeditor_loader():
    return EcowittcustomConfigurationEditor()


if __name__ == '__main__':
    from user.ecowittcustomlib.cli import main
    main()
