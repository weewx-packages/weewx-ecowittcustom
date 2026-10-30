# Origin

The driver `bin/user/ecowittcustom.py` comes unchanged from
`weewx-ecowittcustom.zip` in
[WernerKr/Ecowitt-or-DAVIS-stations-and-Season-skin](https://github.com/WernerKr/Ecowitt-or-DAVIS-stations-and-Season-skin),
revision `07a752442a48484dd6208641febdc46db1b6dc3d`, archive SHA-256 `43905ea3d5f50611c2c9bc8bed98808bc47a05d2ee28059c1677258913d1d200`. It descends from Matthew Wall's
`weewx-interceptor`. Both authors publish it under the GPL version 3, as its
header says and the `license` file in the archive states.

This package takes only the driver. The upstream repository bundles skins and
Highcharts components whose rights this project cannot show, so they are left
out, along with the helpers `historygenerator3.py` and `sunrainduration.py` and
the database schemas. Upstream development continues there; this repository
follows its driver releases.

`install.py` is a reduced version of the original installer. Its header says what
changed.
