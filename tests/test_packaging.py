# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
"""Install the packaged driver on an isolated stock WeeWX station."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import configobj

from user.ecowittcustomlib import VERSION

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, timeout=30, **kwargs)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def installer():
    spec = importlib.util.spec_from_file_location('ecowitt_installer', ROOT / 'install.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.loader()


def test_archive_installs_all_modules_and_can_be_removed(tmp_path):
    package = installer()
    assert package['version'] == VERSION
    archive = tmp_path / 'ecowittcustom.tar.gz'
    with tarfile.open(archive, 'w:gz') as output:
        output.add(ROOT / 'install.py', arcname='ecowittcustom/install.py')
        for destination, files in package['files']:
            assert destination == 'bin/user' or destination.startswith('bin/user/')
            for filename in files:
                output.add(ROOT / filename, arcname='ecowittcustom/' + filename)
    station = tmp_path / 'station'
    weectl = shutil.which('weectl')
    run(weectl, 'station', 'create', str(station), '--no-prompt')
    configuration = station / 'weewx.conf'
    before = configobj.ConfigObj(str(configuration))
    run(weectl, 'extension', 'install', str(archive), '--config', str(configuration), '--yes')
    after = configobj.ConfigObj(str(configuration))
    for section in ('Station', 'DataBindings', 'Databases', 'Engine'):
        assert after[section] == before[section]
    assert after['Accumulator']['p_rain']['extractor'] == 'sum'
    environment = dict(os.environ, PYTHONPATH=str(station / 'bin'))
    check = ('from user import ecowittcustom; '
             'assert ecowittcustom.DRIVER_VERSION == %r; '
             'assert ecowittcustom.EcowittClient.Parser().parse("tempf=32")'
             '["temperature_out"] == 32') % VERSION
    run(sys.executable, '-c', check, env=environment, cwd=tmp_path)
    run(weectl, 'extension', 'uninstall', 'ecowittcustom', '--config', str(configuration), '--yes')
    assert not (station / 'bin/user/ecowittcustom.py').exists()
    assert not (station / 'bin/user/ecowittcustomlib/definitions.json').exists()


def test_cli_data_parsing_does_not_open_a_port(tmp_path):
    environment = dict(os.environ, PYTHONPATH=str(ROOT / 'bin'))
    result = run(sys.executable, str(ROOT / 'bin/user/ecowittcustom.py'),
                 '--port', '-1', '--data', 'tempf=32&model=Test+console',
                 env=environment, cwd=tmp_path)
    assert "'outTemp': 32.0" in result.stdout
    assert "'model': 'Test console'" in result.stdout
