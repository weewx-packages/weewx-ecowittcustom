# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
"""Exercise incomplete uploads and state shared across successive measurements."""

import pytest

from user import ecowittcustom


def upload(parser, timestamp, values):
    return parser.parse('dateutc=2026-11-01+00:00:%02d&%s' % (timestamp, values))


def test_invalid_timestamp_drops_the_upload():
    assert ecowittcustom.EcowittClient.Parser().parse('dateutc=broken&tempf=50') == {}


def test_partial_lightning_upload_keeps_other_observations():
    packet = ecowittcustom.EcowittClient.Parser().parse('lightning_time=123&tempf=50')
    assert packet['temperature_out'] == 50
    assert 'lightning_strike_count' not in packet


@pytest.mark.parametrize('value', ['', '--', '-9999', 'nan', 'inf', 'broken'])
def test_missing_or_invalid_number_is_not_zero(value):
    packet = ecowittcustom.EcowittClient.Parser().parse('tempf=%s&humidity=45' % value)
    assert packet['temperature_out'] is None
    assert packet['humidity_out'] == 45


def test_form_values_are_decoded():
    packet = ecowittcustom.EcowittClient.Parser().parse('model=A%26B%3DC&tempf=50')
    assert packet['model'] == 'A&B=C'


def test_missing_counter_does_not_erase_last_valid_total():
    parser = ecowittcustom.EcowittClient.Parser()
    upload(parser, 1, 'totalrainin=1')
    upload(parser, 2, 'totalrainin=--')
    assert upload(parser, 3, 'totalrainin=1.1')['rain'] == pytest.approx(0.1)


def test_parsers_do_not_change_each_others_rain_mapping():
    yearly = ecowittcustom.EcowittClient.Parser()
    total = ecowittcustom.EcowittClient.Parser()
    upload(yearly, 1, 'yearlyrainin=10')
    upload(total, 1, 'totalrainin=1')
    assert upload(total, 2, 'totalrainin=1.1')['rain'] == pytest.approx(0.1)


def test_old_upload_does_not_change_the_rain_baseline():
    parser = ecowittcustom.EcowittClient.Parser()
    upload(parser, 2, 'totalrainin=1')
    assert upload(parser, 1, 'totalrainin=0.8') == {}
    assert upload(parser, 3, 'totalrainin=1.1')['rain'] == pytest.approx(0.1)


def test_wu_yearly_total_does_not_require_a_daily_total():
    parser = ecowittcustom.WUClient.Parser()
    upload(parser, 1, 'yearlyrainin=10')
    assert upload(parser, 2, 'yearlyrainin=10.1')['rain'] == pytest.approx(0.1)


def test_rain_reset_and_missing_source_do_not_mix_counters():
    parser = ecowittcustom.EcowittClient.Parser()
    assert upload(parser, 1, 'totalrainin=10')['rain'] is None
    assert 'rain' not in upload(parser, 2, 'yearlyrainin=2')
    assert upload(parser, 3, 'totalrainin=0.1')['rain'] == pytest.approx(0.1)


def test_piezo_counters_and_aliases_are_preserved():
    parser = ecowittcustom.EcowittClient.Parser()
    assert upload(parser, 1, 'train_piezo=2')['rain_piezo'] is None
    packet = upload(parser, 2, 'train_piezo=2.1&gain10_piezo=1.2&rain2_gain=1.3')
    mapped = parser.map_to_fields(packet, ecowittcustom.Consumer.DEFAULT_SENSOR_MAP)
    assert mapped['train_piezo'] == pytest.approx(2.1)
    assert mapped['p_rain'] == pytest.approx(0.1)
    assert mapped['gain0'] == pytest.approx(1.2)
    assert mapped['gain1'] == pytest.approx(1.3)


def test_duplicate_upload_does_not_consume_an_increment():
    parser = ecowittcustom.EcowittClient.Parser()
    upload(parser, 1, 'totalrainin=1')
    assert upload(parser, 1, 'totalrainin=1') == {}
    assert upload(parser, 2, 'totalrainin=1.1')['rain'] == pytest.approx(0.1)


def test_partial_upload_at_the_same_time_is_still_accepted():
    parser = ecowittcustom.EcowittClient.Parser()
    upload(parser, 1, 'tempf=32')
    assert upload(parser, 1, 'humidity=0')['humidity_out'] == 0


def test_lightning_counter_does_not_depend_on_a_changed_detection_time():
    parser = ecowittcustom.EcowittClient.Parser()
    upload(parser, 1, 'lightning_num=10&lightning_time=123')
    packet = upload(parser, 2, 'lightning_num=12&lightning_time=123&lightning=1.609344')
    assert packet['lightning_strike_count'] == 2
    assert packet['lightning'] == pytest.approx(1)
    assert upload(parser, 3, 'lightning_num=0&lightning_time=123')['lightning_strike_count'] == 0


def test_high_temperature_channels_reach_distinct_fields():
    parser = ecowittcustom.EcowittClient.Parser()
    packet = parser.parse('tf_ch1=32&soil_ec_temp1=41&tf_ch9=50&tf_ch16=59')
    mapped = parser.map_to_fields(packet, ecowittcustom.Consumer.DEFAULT_SENSOR_MAP)
    assert mapped['soilTemp1'] == 32
    assert mapped['soilmTemp1'] == 41
    assert mapped['extraTemp17'] == 50
    assert mapped['extraTemp24'] == 59


def test_yearly_rain_is_emitted_alongside_lifetime_rain():
    parser = ecowittcustom.EcowittClient.Parser()
    packet = parser.parse('yearlyrainin=1&totalrainin=10')
    mapped = parser.map_to_fields(packet, ecowittcustom.Consumer.DEFAULT_SENSOR_MAP)
    assert mapped['totalRain'] == 10
    assert mapped['yearRain'] == 1


@pytest.mark.parametrize('timestamp', ['2026-11-01+00:00:01',
                                      '2026-11-01%2000%3A00%3A01'])
def test_timestamp_is_utc_independently_of_local_timezone(timestamp):
    packet = ecowittcustom.EcowittClient.Parser().parse('dateutc=%s&tempf=32' % timestamp)
    assert packet['dateTime'] == 1793491201


def test_malformed_form_drops_upload_without_logging_values(caplog):
    parser = ecowittcustom.EcowittClient.Parser()
    assert parser.parse('PASSKEY=secret&bad-segment&tempf=32') == {}
    assert parser.parse('model=%ff&tempf=32') == {}
    assert 'secret' not in caplog.text


def test_legacy_sensor_patterns_match_plain_and_qualified_names():
    parser = ecowittcustom.EcowittClient.Parser()
    assert parser.map_to_fields({'temperature_out': 32},
                                {'outTemp': 'temperature_out.*.*'}) == {'outTemp': 32}
    packet = {'temperature.1.2': 32, 'temperature.2.2': 50}
    assert parser.map_to_fields(packet, {'outTemp': 'temperature.?.2'}) == {'outTemp': 50}
