# Ecowitt custom driver

Receives the uploads of an Ecowitt console or gateway set to a customized server
and feeds them to WeeWX. It does not read the console itself and needs no Ecowitt
account.

This is the driver of Werner Krenn's
[ecowittcustom](https://github.com/WernerKr/Ecowitt-or-DAVIS-stations-and-Season-skin)
without its skins, based on Matthew Wall's `weewx-interceptor`. See
[ORIGIN.md](ORIGIN.md).

## Requirements

- An Ecowitt or Fine Offset console or gateway with **Customized** server upload.
- A network path from the console to the WeeWX machine.

## Installation

Install `ecowittcustom` from the [WeeWX packages catalog](https://github.com/weewx-packages/catalog/blob/main/packages/ecowittcustom.md).
The catalog page lists the current release, its WeeWX and Python
requirements, and the install, update and removal commands.

Then select the driver and restart WeeWX:

```sh
weectl station reconfigure --driver=user.ecowittcustom
sudo systemctl restart weewx
```

In WS View Plus, under **Weather Services**, **Customized**, set the protocol to
Ecowitt, the server to the address of the WeeWX machine, the path to `/`, the port
to `8080` and the interval to 60 seconds.

## Configuration

```ini
[Ecowittcustom]
    driver = user.ecowittcustom
    device_type = ecowitt-client
    port = 8080
```

| Option | Default | Meaning |
| --- | --- | --- |
| `device_type` | `ecowitt-client` | `ecowitt-client` for the Ecowitt protocol, `wu-client` for the Weather Underground protocol. |
| `port` | `80` in the driver, `8080` after installation | Port to listen on. |
| `address` | all interfaces | Address to listen on. |

`[[sensor_map_extensions]]` assigns uploaded fields to WeeWX fields. A field needs
a database column to keep its history.

## Limitations

- Tested with simulated uploads, not with a real console.
- The listener has no authentication. Keep the port on a network you trust.

## Development

```sh
python -m pytest -q tests
```

## License

Copyright 2016-2020 Matthew Wall, 2025-2026 Werner Krenn, 2026 Manuel Hilgert.
Distributed under the GNU General Public License, version 3.
