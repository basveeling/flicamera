#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-18
# @Filename: conftest.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import pathlib
import warnings

import pytest

from sdsstools import read_yaml_file

from flicamera import FLICameraSystem
from flicamera.lib import LibFLI, LibFLIDevice

from .helpers import MockFLIDevice, MockLibFLI


TEST_DATA = pathlib.Path(__file__).parent / 'data/test_data.yaml'

warnings.filterwarnings('ignore', '.+was compiled without a copy of libfli.+')


@pytest.fixture(scope='session')
def config():
    """Gets the test configuration."""

    yield read_yaml_file(TEST_DATA)


@pytest.fixture
def mock_libfli(mocker):
    """Mocks the FLI library."""

    mocker.patch('ctypes.cdll.LoadLibrary', MockLibFLI)


@pytest.fixture
def libfli(mock_libfli, config):
    """Yields a LibFLI object with a mocked C libfli library."""

    libfli = LibFLI()

    for camera in config['cameras']:
        libfli.libc.devices.append(MockFLIDevice(camera,
                                                 **config['cameras'][camera]))

    yield libfli

    LibFLIDevice._instances = {}


@pytest.fixture
def cameras(libfli):
    """Returns the connected cameras."""

    cameras = []

    for device in libfli.libc.devices:
        serial = device.state['serial']
        cameras.append(libfli.get_camera(serial))

    yield cameras


@pytest.fixture
async def camera_system(mock_libfli, config):

    camera_system = FLICameraSystem(camera_config=TEST_DATA)
    camera_system.lib.libc.devices = []

    for camera in config['cameras']:
        device = MockFLIDevice(camera, **config['cameras'][camera])
        camera_system.lib.libc.devices.append(device)

    camera_system.setup()
    for camera in config['cameras']:
        await camera_system.add_camera(camera)

    yield camera_system

    LibFLIDevice._instances = {}

    for camera in camera_system.cameras:
        await camera.disconnect()

    await camera_system.disconnect()
