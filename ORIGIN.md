# Origin

This package is maintained independently of upstream. Its original driver
`bin/user/ecowittcustom.py` came unchanged from
`weewx-ecowittcustom.zip` in
[WernerKr/Ecowitt-or-DAVIS-stations-and-Season-skin](https://github.com/WernerKr/Ecowitt-or-DAVIS-stations-and-Season-skin),
revision `07a752442a48484dd6208641febdc46db1b6dc3d`, archive SHA-256 `43905ea3d5f50611c2c9bc8bed98808bc47a05d2ee28059c1677258913d1d200`. It descends from Matthew Wall's
`weewx-interceptor`. Both authors publish it under the GPL version 3, as its
header says and the `license` file in the archive states.

This package takes only the driver. The upstream repository bundles skins and
Highcharts components whose rights this project cannot show, so they are left
out, along with the helpers `historygenerator3.py` and `sunrainduration.py` and
the database schemas. Upstream development continues there.

On 2026-11-01 the driver was refactored into `bin/user/ecowittcustomlib`, and
the field and unit definitions were extracted into `definitions.json`. The
WeeWX entry point remains `user.ecowittcustom`. Upstream files no longer replace
this implementation. The original copyrights and GPL version 3 still apply.

The Ecowitt HTTP field coverage was also compared with
[`weewx-ultimate-push` at `3732d498150bfe6c9217e2169bbf27cb47395b87`](https://github.com/weewx-packages/weewx-ultimate-push/blob/3732d498150bfe6c9217e2169bbf27cb47395b87/bin/user/ultimatepush/catalogs/ecowitt.py).
That catalog descends from the same driver. All its raw field names already
existed here. The refactor adds missing output mappings while preserving this
package's existing temperature placements.

`install.py` is a reduced version of the original installer. Its header says what
changed.
