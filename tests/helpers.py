#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-20
# @Filename: helpers.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import ctypes
import errno
import time
import unittest.mock

import flicamera.lib


DEV_COUNTER = 0


class MockFLIDevice(object):

    _defaults = {'temperature': {'CCD': 0, 'base': 0},
                 'serial': 'ML0000',
                 'exposure_time_left': 0,
                 'exposure_time': 0,
                 'exposure_status': 'idle',
                 'model': 'MicroLine ML50100',
                 'exposure_start_time': 0}

    def __init__(self, name, **kwargs):

        global DEV_COUNTER

        self.dev = DEV_COUNTER
        DEV_COUNTER += 1

        self.name = name

        self.reset_defaults()
        self.state.update(kwargs)

    def reset_defaults(self):
        """Resets the device to the default state."""

        self.state = self._defaults.copy()


class MockLibFLI(ctypes.CDLL):
    """Mocks the CDLL object with the FLI dynamic library."""

    def __init__(self, dlpath):

        self.dlpath = dlpath
        self.devices = []

        self.restype = flicamera.lib.chk_err

    def reset(self):
        """Resets the initial values of the mocked device."""

        self.__init__(self.dlpath)

    def __getattr__(self, name):

        # __getattr__ only gets called if there is no attribute in the class
        # that matches that name. So for the cases when we haven't overridden
        # the library function, we returns a Mock that returns 0 (no error).

        if name.startswith('FLI'):
            return unittest.mock.MagicMock(retur_value=self.restype(0))

    def _get_device(self, dev):
        """Gets the appropriate device."""

        if isinstance(dev, ctypes.c_long):
            dev = dev.value

        for device in self.devices:
            if device.dev == dev:
                return device

        return None

    def FLIList(self, domain, names_ptr):

        device_names = [(dev.name + ';' + dev.state['model']).encode()
                        for dev in self.devices]

        # names_ptr is a pointer to a pointer to a char pointer (yep).
        # We create a char pointer array with the length of the devices and
        # unpack the above device_names into it.
        # See https://stackoverflow.com/a/4145859 for details.
        # Then we access the object to which the names_ptr points to and
        # replace its contents.
        names_ptr._obj.contents = (ctypes.c_char_p * len(self.devices))(*device_names)

        return self.restype(0)

    def FLIOpen(self, dev_ptr, name, domain):

        name = name.decode()
        for device in self.devices:
            if device.name == name:
                dev_ptr._obj.value = device.dev
                return 0

        return self.restype(-errno.ENXIO)

    def FLIGetSerialString(self, dev, serial_ptr, str_size):

        device = self._get_device(dev)
        if not device:
            return self.restype(-errno.ENXIO)

        serial_ptr.value = device.state['serial'].encode()

        return self.restype(0)

    def FLISetExposureTime(self, dev, exp_time):

        device = self._get_device(dev)
        if not device:
            return self.restype(-errno.ENXIO)

        if isinstance(exp_time, ctypes._SimpleCData):
            device.state['exposure_time'] = exp_time.value
        else:
            device.state['exposure_time'] = exp_time

        return self.restype(0)

    def FLIGetExposureStatus(self, dev, timeleft_ptr):

        device = self._get_device(dev)
        if not device:
            return self.restype(-errno.ENXIO)

        if device.state['exposure_status'] == 'idle':
            timeleft_ptr.value = 0
        elif device.state['exposure_status'] == 'exposing':

            time_elapsed = time.time() - device.state['exposure_start_time']
            if time_elapsed > device.state['exposure_time']:
                timeleft_ptr._obj.value = 0
            else:
                time_left = int(1000 * (device.state['exposure_time'] - time_elapsed))
                timeleft_ptr._obj.value = time_left

        return self.restype(0)

    def FLIExposeFrame(self, dev):

        device = self._get_device(dev)
        if not device:
            return self.restype(-errno.ENXIO)

        if device.state['exposure_status'] != 'idle':
            return device.restype(-errno.EALREADY)

        device.state['exposure_status'] = 'exposing'
        device.state['exposure_start_time'] = time.time()

        return self.restype(0)
