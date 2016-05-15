"""Inputs - user input for humans."""

import os
import io
import glob
import struct
from collections import namedtuple
from warnings import warn
from inputs.constants import EVENT_FORMAT, EVENT_SIZE

# pylint: disable=too-few-public-methods


def get_input():
    """Get a single event from any input device."""
    pass


def get_key():
    """Get a single keypress from a keyboard."""
    pass


def get_mouse():
    """Get a single movement or click from a mouse."""
    pass


def get_gamepad():
    """Get a single action from a gamepad."""
    pass


InputEvent = namedtuple('InputEvent', ('timestamp', 'key', 'state', 'type'))

class InputDevice(object):
    """A user input device."""
    def __init__(self, device_path):
        self._device_path = device_path
        long_identifier = device_path.split('/')[4]
        self.protocol, remainder = long_identifier.split('-', 1)
        self._identifier, _, self.device_type = remainder.rsplit('-', 2)
        self._character_device_path = os.path.realpath(device_path)
        self._character_file = None
        with open("/sys/class/input/%s/device/name" %
                  self._get_char_name()) as name_file:
            self.name = name_file.read().strip()

    def _get_char_name(self):
        """Get short version of char device name."""
        return self._character_device_path.split('/')[-1]

    def __str__(self):
        return self.name

    def __repr__(self):
        return '%s.%s("%s")' % (
            self.__module__,
            self.__class__.__name__,
            self._device_path)

    @property
    def _character_device(self):
        if not self._character_file:
            self._character_file = io.open(self._character_device_path, 'rb')
        return self._character_file

    def __iter__(self):
        while True:
            event = self._character_device.read(EVENT_SIZE)
            (tv_sec, tv_usec, ev_type, code, value) = struct.unpack(EVENT_FORMAT, event)
            print((tv_sec, tv_usec, ev_type, code, value))
            #if ev_type == self.EV_KEY:
            yield InputEvent(tv_sec + (tv_usec / 1000000), code, value, ev_type)

    def read(self):
        """Read the next input event."""
        return next(iter(self))


class Keyboard(InputDevice):
    """A keyboard or other key-like device."""
    pass


class Mouse(InputDevice):
    """A mouse or other pointing-like device."""
    pass


class GamePad(InputDevice):
    """A gamepad or other joystick-like device."""
    pass


class OtherDevice(InputDevice):
    """A device of which its is type is either undetectable or has not
    been implemented yet.
    """
    pass


class DeviceManager(object):
    """Provides access to all connected and detectible user input
    devices."""

    def __init__(self):
        self.keyboards = []
        self.mice = []
        self.gamepads = []
        self.other_devices = []
        self.all_devices = []
        self._find_devices()
        self._update_all_devices()
        self._index = 0

    def _update_all_devices(self):
        """Update the all_devices list."""
        self.all_devices.extend(self.keyboards)
        self.all_devices.extend(self.mice)
        self.all_devices.extend(self.gamepads)
        self.all_devices.extend(self.other_devices)

    def _find_devices(self):
        """Find available devices."""
        for device_path in glob.glob('/dev/input/by-id/*-event-*'):
            try:
                device_type = device_path.rsplit('-', 1)[1]
            except IndexError:
                warn("The following device path was skipped as it could "
                     "not be parsed: %s" % device_path, RuntimeWarning)
                continue
            if device_type == 'kbd':
                self.keyboards.append(Keyboard(device_path))
            elif device_type == 'mouse':
                self.mice.append(Mouse(device_path))
            elif device_type == 'joystick':
                self.gamepads.append(GamePad(device_path))
            else:
                self.other_devices.append(OtherDevice(device_path))

    def __iter__(self):
        return iter(self.all_devices)

    def __getitem__(self, index):
        try:
            return self.all_devices[index]
        except IndexError:
            raise IndexError("list index out of range")


def main():
    """Simple example."""
    DeviceManager()


if __name__ == '__main__':
    main()
