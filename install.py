# installer for the weewx-ecowittcustom driver
# Copyright 2025/2026 Werner Krenn
# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
# Distributed under the terms of the GNU Public License (GPLv3)
#
# Changed 2026-10-30 by Manuel Hilgert: reduced to the driver. The original
# installer also adds a skin, helper services and a database schema, and it
# selects a new database. This one installs the driver and its accumulators and
# leaves the rest of the station alone. See ORIGIN.md.

from io import StringIO

import configobj
from weecfg.extension import ExtensionInstaller

VERSION = "0.2.0.post1"

ecowittcustom_config = """
[Ecowittcustom]
    driver = user.ecowittcustom
    device_type = ecowitt-client
    port = 8080

[StdCalibrate]
    [[Corrections]]
        radiation = luminosity / 126.7 if luminosity is not None else None

# Options for extension 'Ecowittcustom'
[Accumulator]

   [[model]]
        accumulator = firstlast
        extractor = last
   [[stationtype]]
        accumulator = firstlast
        extractor = last

    [[gain0]]
        extractor = last
    [[gain1]]
        extractor = last
    [[gain2]]
        extractor = last
    [[gain3]]
        extractor = last
    [[gain4]]
        extractor = last
    [[gain5]]
        extractor = last

    [[lightning_distance]]
        extractor = last
    [[lightning_strike_count]]
        extractor = sum
    [[lightning_last_det_time]]
        extractor = last
    [[lightningcount]]
        extractor = last
    [[lightning_noise_count]]
        extractor = sum

    [[daymaxwind]]
        extractor = last
    [[windspdmph_avg10m]]
        extractor = last
    [[winddir_avg10m]]
        extractor = last

    [[rainRate]]
        extractor = max
    [[stormRain]]
        extractor = last
    [[hourRain]]
        extractor = last
    [[dayRain]]
        extractor = last
    [[weekRain]]
        extractor = last
    [[monthRain]]
        extractor = last
    [[yearRain]]
        extractor = last
    [[totalRain]]
        extractor = last

    [[rrain_piezo]]
        extractor = max
    [[erain_piezo]]
        extractor = last
    [[hrain_piezo]]
        extractor = last
    [[drain_piezo]]
        extractor = last
    [[wrain_piezo]]
        extractor = last
    [[mrain_piezo]]
        extractor = last
    [[yrain_piezo]]
        extractor = last

    [[p_rainrate]]
        extractor = max
    [[p_eventrain]]
        extractor = last
    [[p_hourrain]]
        extractor = last
    [[p_dayrain]]
        extractor = last
    [[p_weekrain]]
        extractor = last
    [[p_monthrain]]
        extractor = last
    [[p_yearrain]]
        extractor = last

    [[dayHail]]
        extractor = last
    [[hail]]
        extractor = sum

    [[vpd]]
        extractor = last
    [[depth_ch1]]
        extractor = last
    [[depth_ch2]]
        extractor = last

    [[pm2_51_24hav]]
        extractor = last
    [[pm2_52_24hav]]
        extractor = last
    [[pm2_53_24hav]]
        extractor = last
    [[pm2_54_24hav]]
        extractor = last
    [[24havpm255]]
        extractor = last

    [[pm2_51_24h_avg]]
        extractor = last
    [[pm2_52_24h_avg]]
        extractor = last
    [[pm2_53_24h_avg]]
        extractor = last
    [[pm2_54_24h_avg]]
        extractor = last
    [[pm2_55_24h_avg]]
        extractor = last
    [[pm10_24h_avg]]
        extractor = last
    [[co2_24h_avg]]
        extractor = last

    [[wh25_batt]]
        extractor = last
    [[wh26_batt]]
        extractor = last
    [[wh31_ch1_batt]]
        extractor = last
    [[wh31_ch2_batt]]
        extractor = last
    [[wh31_ch3_batt]]
        extractor = last
    [[wh31_ch4_batt]]
        extractor = last
    [[wh31_ch5_batt]]
        extractor = last
    [[wh31_ch6_batt]]
        extractor = last
    [[wh31_ch7_batt]]
        extractor = last
    [[wh31_ch8_batt]]
        extractor = last
    [[wn35_ch1_batt]]
        extractor = last
    [[wn35_ch2_batt]]
        extractor = last
    [[wn35_ch3_batt]]
        extractor = last
    [[wn35_ch4_batt]]
        extractor = last
    [[wn35_ch5_batt]]
        extractor = last
    [[wn35_ch6_batt]]
        extractor = last
    [[wn35_ch7_batt]]
        extractor = last
    [[wn35_ch8_batt]]
        extractor = last
    [[wh40_batt]]
        extractor = last
    [[wh41_ch1_batt]]
        extractor = last
    [[wh41_ch2_batt]]
        extractor = last
    [[wh41_ch3_batt]]
        extractor = last
    [[wh41_ch4_batt]]
        extractor = last
    [[wh45_batt]]
        extractor = last
    [[wh51_ch1_batt]]
        extractor = last
    [[wh51_ch2_batt]]
        extractor = last
    [[wh51_ch3_batt]]
        extractor = last
    [[wh51_ch4_batt]]
        extractor = last
    [[wh51_ch5_batt]]
        extractor = last
    [[wh51_ch6_batt]]
        extractor = last
    [[wh51_ch7_batt]]
        extractor = last
    [[wh51_ch8_batt]]
        extractor = last
    [[wh51_ch9_batt]]
        extractor = last
    [[wh51_ch10_batt]]
        extractor = last
    [[wh51_ch11_batt]]
        extractor = last
    [[wh51_ch12_batt]]
        extractor = last
    [[wh51_ch13_batt]]
        extractor = last
    [[wh51_ch14_batt]]
        extractor = last
    [[wh51_ch15_batt]]
        extractor = last
    [[wh51_ch16_batt]]
        extractor = last
    [[wh55_ch1_batt]]
        extractor = last
    [[wh55_ch2_batt]]
        extractor = last
    [[wh55_ch3_batt]]
        extractor = last
    [[wh55_ch4_batt]]
        extractor = last
    [[wh57_batt]]
        extractor = last
    [[wh65_batt]]
        extractor = last
    [[wh68_batt]]
        extractor = last
    [[ws80_batt]]
        extractor = last
    [[ws85_batt]]
        extractor = last
    [[ws90_batt]]
        extractor = last
    [[ws85cap_volt]]
        extractor = last
    [[ws90cap_volt]]
        extractor = last
    [[ws1900batt]]
        extractor = last
    [[console_batt]]
        extractor = last

    # End GW1000 and Ecowittcustom driver extractors
"""

ecowittcustom_dict = configobj.ConfigObj(StringIO(ecowittcustom_config))


def loader():
    return EcowittcustomInstaller()


class EcowittcustomInstaller(ExtensionInstaller):
    def __init__(self):
        super(EcowittcustomInstaller, self).__init__(
            version=VERSION,
            name='ecowittcustom',
            description='Capture weather data from Ecowitt consoles and gateways over HTTP',
            author="Matthew Wall, Werner Krenn",
            author_email="",
            files=[('bin/user', ['bin/user/ecowittcustom.py'])],
            config=ecowittcustom_dict)
