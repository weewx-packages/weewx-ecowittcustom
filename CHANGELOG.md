# Changelog

## 0.3.0 - 2026-11-01

- Maintain the package independently of upstream. Split the driver into the
  WeeWX entry point, protocol parsers, HTTP receiver and optional passive receiver.
  Move field maps, unit registrations and installer settings into JSON.
- Replace inherited comments and docstrings, retaining copyright and license
  notices. Remove Python 2 and obsolete WeeWX logging compatibility code.
- Decode URL-encoded forms correctly. Invalid numeric fields now become `None`,
  including empty values, instead of zero or a non-finite number. Invalid UTC
  dates and malformed forms no longer crash the driver.
- Isolate queues, sensor maps and counter state per receiver. Reject older and
  repeated uploads before updating counters. Preserve baselines through missing
  values and calculate lightning increments even when the detection time repeats.
  The first valid lightning count now establishes a baseline without an increment.
- Preserve temperature channels 9 through 16 as `extraTemp17` through
  `extraTemp24`. Keep the existing placements for channels 1 through 8 and
  soil conductivity probe temperatures. Restore piezo total and gain mappings,
  the `last24hrainin` alias, yearly rain alongside total rain, WU soil
  temperatures and WU yearly totals without daily totals.
- Prefer `total_piezo`, then `train_piezo`, then `yrain_piezo` as the piezo counter
  source. Keep the first valid source for each receiver's lifetime to avoid
  mixing counter baselines. Configure accumulation for the fields actually emitted.
- Validate HTTP framing, UTF-8 and upload size. Give each receiver a bounded
  queue. Concurrent HTTP handlers prevent one stalled upload blocking another.
  Remove raw uploads from logs and the fixed UTC offset from Ecowitt replies.
- Fix shutdown on current Python and make `--data` work without opening a port.

## 0.2.0.post1 - 2026-10-30

First release of this package: the unchanged driver 0.2.0 with a reduced installer.
