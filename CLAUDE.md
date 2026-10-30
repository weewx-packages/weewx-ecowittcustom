# weewx-ecowittcustom

WeeWX driver for Ecowitt consoles that upload to a customized server. It is the
driver of WernerKr/Ecowitt-or-DAVIS-stations-and-Season-skin without the skins.

## Checks

- `python -m pytest -q tests`: about 1 second. Needs WeeWX and pytest.

## Conventions

`bin/user/ecowittcustom.py` stays unchanged from upstream, so a new upstream driver
can replace it file for file. Record each import in `ORIGIN.md`. Packaging changes
get a `.post` version. Nothing from the skins, the helpers or Highcharts comes in:
their rights are not shown. See `catalog/ci/wiki-audit.json`, line 201.
