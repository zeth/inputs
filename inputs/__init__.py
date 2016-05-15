"""Inputs - user input for humans."""

import os
import glob
from warnings import warn

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


class InputDevice(object):
    """A user input device."""
    def __init__(self, device_path):
        self._device_path = device_path
        long_identifier = device_path.split('/')[4]
        self.protocol, remainder = long_identifier.split('-', 1)
        self._identifier, _, self._device_type = remainder.rsplit('-', 2)
        self._character_device = os.path.realpath(device_path)
        self._char_name = self._character_device.split('/')[-1]
        with open("/sys/class/input/%s/device/name" %
                  self._char_name) as name_file:
            self.name = name_file.read().strip()

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'inputs.GamePad("%s")' % self._device_path


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


class UserInput(object):
    """User input."""
    def __init__(self):
        self.keyboards = []
        self.mice = []
        self.gamepads = []
        self.other_devices = []
        self.find_devices()

    def find_devices(self):
        """Find available devices."""
        for device_path in glob.glob('/dev/input/by-id/*-event-*'):
            try:
                device_type = device_path.rsplit('-', 1)[1]
            except IndexError:
                warn("The following device path was skipped as it could "
                     "not be parsed: %s" % device_path, RuntimeWarning)
                continue
            print(device_type)
            if device_type == 'kbd':
                self.keyboards.append(Keyboard(device_path))
            elif device_type == 'mouse':
                self.mice.append(Mouse(device_path))
            elif device_type == 'joystick':
                self.gamepads.append(GamePad(device_path))
            else:
                self.other_devices.append(OtherDevice(device_path))


def main():
    """Simple example."""
    userinput = UserInput()
    userinput.find_devices()


if __name__ == '__main__':
    main()
