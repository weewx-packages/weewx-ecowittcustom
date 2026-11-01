# Driver internals

These notes describe changes to the driver itself. For station setup, see the
[README](../README.md).

## Modules

`bin/user/ecowittcustom.py` exports the WeeWX loaders and the existing driver,
configuration editor and consumer classes. Importing it registers the additional
units before WeeWX initializes its services.

The `ecowittcustomlib` package separates the other responsibilities:

- `definitions.py` loads the bundled JSON with duplicate-key rejection and
  registers observations and units.
- `parser.py` decodes forms, validates readings, tracks counters and maps internal
  observations to WeeWX field names. Parsing needs no socket or running engine.
- `http.py` accepts GET queries and POST bodies. It limits uploads to 64 KiB,
  times out idle connections after 10 seconds and responds with 503 when the
  receiver's queue is full. Each queue holds at most 128 uploads.
- `sniff.py` provides optional Ethernet/IPv4/TCP capture. It maintains separate
  HTTP buffers for at most 32 connections and removes retransmitted bytes. A
  sequence gap discards that stream. The pcap binding loads only in passive mode.
- `driver.py` owns the receiver, its thread and the WeeWX generator.
- `cli.py` implements the diagnostic command.

## Definition tables

`definitions.json` is installed with the Python package. It contains data only;
the parsers and installer never evaluate Python expressions from its mappings.
The `installation` section includes a WeeWX calibration expression, which WeeWX
handles as station configuration.

| Key | Meaning |
| --- | --- |
| `sensor_map` | WeeWX output field to internal observation name. |
| `observation_groups` | WeeWX observation to unit group. |
| `unit_systems` | Additional unit groups for US, metric and metricwx. |
| `unit_formats`, `unit_labels` | Formats and labels for additional units. |
| `protocols` | Ecowitt and WU field maps, ignored names, map overrides, counter sources and replies. |
| `installation` | Configuration defaults injected by the extension installer. |

Each protocol's `labels` table maps uploaded names to internal observation names.
Keep the internal names stable because existing `sensor_map_extensions` refer to
them. Each protocol's `sensor_map` overrides the shared default map. WU uses that
override for its soil temperature fields.

Add new fields to both the protocol map and the output map, with a unit group for
numeric observations whose units are known. Give status fields and cumulative
totals a `last` accumulator and interval increments a `sum` accumulator. Keep
unknown units unassigned until a protocol source establishes them. The inherited
noise, peak and laser power fields still need that verification.

The cached installer must work after the source archive disappears. Stock WeeWX
caches only `install.py`; during removal this installer reads definitions from
the still-installed package. The installation test exercises that path.

## Counter and timestamp rules

Each parser belongs to one receiver. Its first valid total establishes a baseline
and produces no interval amount. A decrease is a counter reset; the new total is
the interval amount. Missing or invalid totals leave the last valid baseline
intact. A negative total does not establish or update a baseline.

The JSON lists counter sources in preference order. Once a parser selects a valid
source, it keeps that source until restart. A partial upload omitting it does not
switch the parser to a counter with a different baseline. Bucket rain, piezo rain
and lightning maintain separate baselines.

The parser converts `dateutc` as UTC. A missing date or `now` uses receipt time.
An invalid date discards the upload. Older measurements and consecutive identical
uploads at the same timestamp are rejected before counters change. Different
partial uploads at the same timestamp remain valid.

Ecowitt and WU readings use WeeWX US units. Ecowitt lightning distance is converted
from kilometres to miles. Empty values, `--`, `-9999`, invalid numbers and
non-finite numbers become `None`.

## Ecowitt coverage

The comparison recorded in [ORIGIN.md](../ORIGIN.md) covers raw names in Ultimate
Push's Ecowitt HTTP catalog. Every name has an output mapping here. It does not
compare that project's gateway polling API or other manufacturers' protocols.

Existing observation placements remain stable. In particular, `tf_ch1` through
`tf_ch8` still map to `soilTemp1` through `soilTemp8`, and `soil_ec_temp1` through
`soil_ec_temp16` still map to `soilmTemp1` through `soilmTemp16`. Higher `tf_ch`
channels use the previously unused `extraTemp17` through `extraTemp24` fields.

These are parser and mapping checks. They do not establish which measurements a
particular console firmware uploads or validate a physical sensor's readings.
