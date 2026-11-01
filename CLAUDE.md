# weewx-ecowittcustom

WeeWX driver for Ecowitt consoles that upload to a customized server. It is the
driver of WernerKr/Ecowitt-or-DAVIS-stations-and-Season-skin without the skins.

## Checks

- `PYTHONPATH=bin uv run --isolated --no-project --with weewx --with pytest python -m pytest -q tests`:
  parser, loopback HTTP, passive framing and archive installation/removal tests.
- Run the `python-docstring-types` skill after changing typed docstrings.

## Conventions

This is an independent continuation. Do not replace files with upstream copies.
Keep the authorship and source archive recorded in `ORIGIN.md`.

`bin/user/ecowittcustom.py` supplies the stable WeeWX entry points. Implementation
lives in `bin/user/ecowittcustomlib`; field maps, units and installation settings
live in `definitions.json`. See `docs/development.md` for the data format and
counter rules. Preserve the existing observation names when changing mappings.

Python follows WeeWX conventions, with types in Google docstrings rather than
runtime annotations. Use the standard library and WeeWX dependencies.

Skins, upstream helper services, database schemas and Highcharts remain excluded.
Their rights are not shown. See `ORIGIN.md` and the catalog license audit.
