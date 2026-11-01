# Ecowitt custom driver

Receives the uploads of an Ecowitt console or gateway set to a customized server
and feeds them to WeeWX. It does not read the console itself and needs no Ecowitt
account.

This is an independent continuation of the driver from Werner Krenn's
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
| `mode` | `listen` | HTTP listener, or `sniff` for passive capture. |
| `queue_timeout` | `10` | Seconds to wait for an upload before checking again. Must be positive. |
| `sensor_map` | built-in map | Replaces the WeeWX-field-to-internal-name mapping. |
| `sensor_map_extensions` | empty | Adds or overrides individual mappings. |
| `iface` | `eth0` | Network interface for passive capture. |
| `pcap_filter` | `dst port 80` | Capture filter in passive mode. |
| `promiscuous` | `False` | Enables promiscuous capture. |

Use `[[sensor_map_extensions]]` to assign an internal observation to another WeeWX
field. For example, `extraTemp1 = temperature_1` maps the first extra temperature
channel. A field needs a database column to keep its history. The driver does not
extend the station's database schema.

## Limitations

- Tested with simulated uploads, not with a real console.
- The listener has no authentication. Keep the port on a network you trust.
- Use one receiver per console or gateway. Its uploads share one set of counters.
- Passive capture requires a Python `pcap` binding and capture privileges. It
  supports unencrypted HTTP over Ethernet and VLAN-tagged IPv4. Streams with
  missing or out-of-order TCP segments are discarded.

## Development

```sh
PYTHONPATH=bin uv run --isolated --no-project --with weewx --with pytest python -m pytest -q tests
```

Decode a saved upload without opening a listener:

```sh
PYTHONPATH=bin python bin/user/ecowittcustom.py --data 'tempf=32&humidity=45'
```

See [development notes](docs/development.md) for module responsibilities,
definition tables and counter behavior. See the [changelog](CHANGELOG.md) for
changes that affect stored observations.

## License

Copyright 2016-2020 Matthew Wall, 2025-2026 Werner Krenn, 2026 Manuel Hilgert.
Distributed under the GNU General Public License, version 3.
