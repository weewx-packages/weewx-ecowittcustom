# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
"""Check HTTP requests and receiver lifetime through real loopback connections."""

import http.client
import logging
import socket
import threading

import pytest

from user.ecowittcustom import EcowittcustomDriver
from user.ecowittcustomlib.http import MAX_UPLOAD_BYTES


@pytest.fixture
def driver_factory():
    drivers = []

    def create(**settings):
        driver = EcowittcustomDriver(address='127.0.0.1', port=0, **settings)
        drivers.append(driver)
        return driver

    yield create
    for driver in drivers:
        driver.closePort()


def request(driver, method, path='/', body=None, headers=None):
    address = driver._device._server.server_address
    connection = http.client.HTTPConnection(*address, timeout=2)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


@pytest.mark.parametrize('protocol, response', [
    ('ecowitt-client', b'{"errcode":"0","errmsg":"ok"}'),
    ('wu-client', b'success'),
])
def test_upload_reaches_the_weewx_generator(driver_factory, protocol, response):
    driver = driver_factory(device_type=protocol)
    assert request(driver, 'POST', body='tempf=32&humidity=0') == (200, response)
    packet = next(driver.genLoopPackets())
    assert packet['outTemp'] == 32
    assert packet['outHumidity'] == 0
    assert packet['usUnits'] == 1


def test_receivers_have_separate_queues_and_sensor_maps(driver_factory):
    first = driver_factory(sensor_map_extensions={'customTemp': 'temperature_out'})
    second = driver_factory()
    request(first, 'GET', '/?tempf=50')
    assert second._device.get_queue().empty()
    assert 'customTemp' not in second._obs_map
    assert next(first.genLoopPackets())['customTemp'] == 50


def test_explicit_sensor_map_is_not_mutated(driver_factory):
    sensor_map = {'temperature': 'temperature_out'}
    driver = driver_factory(sensor_map=sensor_map,
                            sensor_map_extensions={'humidity': 'humidity_out'})
    assert sensor_map == {'temperature': 'temperature_out'}
    request(driver, 'POST', body='tempf=0&humidity=45')
    packet = next(driver.genLoopPackets())
    assert packet['temperature'] == 0
    assert packet['humidity'] == 45
    assert 'outTemp' not in packet


@pytest.mark.parametrize('length, status', [('-1', 400), ('bad', 400),
                                         (str(MAX_UPLOAD_BYTES + 1), 413)])
def test_invalid_content_length_is_rejected(driver_factory, length, status):
    driver = driver_factory()
    assert request(driver, 'POST', headers={'Content-Length': length})[0] == status
    assert driver._device.get_queue().empty()


def test_invalid_utf8_is_rejected(driver_factory):
    driver = driver_factory()
    assert request(driver, 'POST', body=b'tempf=\xff')[0] == 400
    assert driver._device.get_queue().empty()


def test_missing_and_duplicate_content_lengths_are_rejected(driver_factory):
    driver = driver_factory()
    for lengths, expected in [([], 411), (['1', '2'], 400)]:
        connection = http.client.HTTPConnection(*driver._device._server.server_address,
                                                timeout=2)
        try:
            connection.putrequest('POST', '/')
            for length in lengths:
                connection.putheader('Content-Length', length)
            connection.endheaders()
            response = connection.getresponse()
            assert response.status == expected
            response.read()
        finally:
            connection.close()


def test_full_queue_returns_retryable_error(driver_factory):
    driver = driver_factory()
    incoming = driver._device.get_queue()
    for _ in range(incoming.maxsize):
        incoming.put_nowait('tempf=1')
    assert request(driver, 'POST', body='tempf=2')[0] == 503


def test_passwords_do_not_reach_debug_or_error_logs(driver_factory, caplog):
    driver = driver_factory()
    caplog.set_level(logging.DEBUG)
    secret = 'never-print-this-key'
    body = 'PASSKEY=%s&PASSWORD=%s&unknown=%s&dateutc=broken' % (secret, secret, secret)
    request(driver, 'GET', '/?' + body)
    payload = driver._device.get_queue().get(timeout=1)
    assert driver._device.parser.parse(payload) == {}
    driver._device.parser.parse('unknown=%s&tempf=broken&humidity=45' % secret)
    assert secret not in caplog.text


def test_a_slow_upload_does_not_block_other_requests(driver_factory):
    driver = driver_factory()
    with socket.create_connection(driver._device._server.server_address, timeout=2) as slow:
        slow.sendall(b'POST / HTTP/1.0\r\nContent-Length: 20\r\n\r\ntempf=')
        assert request(driver, 'GET', '/?tempf=32')[0] == 200
        slow.shutdown(socket.SHUT_WR)
        assert b'400' in slow.recv(4096)


def test_shutdown_releases_the_socket_and_is_repeatable(driver_factory):
    driver = driver_factory()
    address = driver._device._server.server_address
    driver.closePort()
    driver.closePort()
    assert not driver._server_thread.is_alive()
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(address)


def test_wu_soil_temperature_uses_the_protocol_specific_mapping(driver_factory):
    driver = driver_factory(device_type='wu-client')
    request(driver, 'GET', '/?soiltempf=32&softwaretype=Test%20console')
    packet = next(driver.genLoopPackets())
    assert packet['soilTemp1'] == 32
    assert packet['stationtype'] == 'Test console'


def test_shutdown_wakes_a_generator_waiting_for_an_upload(driver_factory):
    driver = driver_factory(queue_timeout=60)
    generator_thread = threading.Thread(target=lambda: list(driver.genLoopPackets()), daemon=True)
    generator_thread.start()
    driver.closePort()
    generator_thread.join(timeout=1)
    assert not generator_thread.is_alive()
