"""Inputs - user input for humans."""

import os
import io
import glob
import struct
from collections import namedtuple
from warnings import warn
from inputs.constants import EVENT_MAP, EVENT_FORMAT, EVENT_SIZE


# pylint: disable=too-few-public-methods


class PermissionDenied(IOError):
    """/dev/input not allowed by user.
    Common Linux problem."""
    pass


class UnpluggedError(RuntimeError):
    """The device requested is not plugged in."""
    pass


class UnknownEventType(IndexError):
    """We don't know what this event is."""
    pass


class UnknownEventCode(IndexError):
    """We don't know what this event is."""
    pass


class InputEvent(object):
    """A user event."""
    def __init__(self,
                 device,
                 timestamp=None,
                 code=None,
                 state=None,
                 ev_type=None):
        self.device = device
        self.timestamp = timestamp
        self.code = code
        self.state = state
        self.ev_type = ev_type


class InputDevice(object):
    """A user input device."""
    def __init__(self, manager, device_path):
        self.manager = manager
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
            try:
                self._character_file = io.open(
                    self._character_device_path, 'rb')
            except IOError as err:
                if err.errno == 13:
                    raise PermissionDenied(
                        "The user (that this program is being run as) does "
                        "not have permission to access the input events, "
                        "check groups and permissions, for example, on "
                        "Debian, the user needs to be in the input group.")
                else:
                    raise
        return self._character_file

    def __iter__(self, type_filter=None):
        while True:
            event = self._character_device.read(EVENT_SIZE)
            (tv_sec, tv_usec, ev_type, code, value) = struct.unpack(
                EVENT_FORMAT, event)
            event_type = self.manager.get_event_type(ev_type)
            event_string = self.manager.get_event_string(event_type, code)
            if type_filter:
                if event_type != type_filter:
                    return

            yield InputEvent(self,
                             tv_sec + (tv_usec / 1000000),
                             event_string,
                             value,
                             event_type)

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
        self.codes = {key: dict(value) for key, value in EVENT_MAP}
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
                self.keyboards.append(Keyboard(self, device_path))
            elif device_type == 'mouse':
                self.mice.append(Mouse(self, device_path))
            elif device_type == 'joystick':
                self.gamepads.append(GamePad(self, device_path))
            else:
                self.other_devices.append(OtherDevice(self, device_path))

    def __iter__(self):
        return iter(self.all_devices)

    def __getitem__(self, index):
        try:
            return self.all_devices[index]
        except IndexError:
            raise IndexError("list index out of range")

    def get_event_type(self, raw_type):
        """Convert the code to a useful string name."""
        try:
            return self.codes['types'][raw_type]
        except KeyError:
            raise UnknownEventType("We don't know this event type")

    def get_event_string(self, evtype, code):
        """Get the string name of the event."""
        try:
            return self.codes[evtype][code]
        except KeyError:
            raise UnknownEventCode("We don't know this event.")


devices = DeviceManager()  # pylint: disable=invalid-name


def get_key():
    """Get a single keypress from a keyboard."""
    try:
        keyboard = devices.keyboards[0]
    except IndexError:
        raise UnpluggedError("No keyboard found.")
    return keyboard.read()


def get_mouse():
    """Get a single movement or click from a mouse."""
    try:
        mouse = devices.mice[0]
    except IndexError:
        raise UnpluggedError("No mice found.")
    return mouse.read()


def get_gamepad():
    """Get a single action from a gamepad."""
    try:
        gamepad = devices.gamepads[0]
    except IndexError:
        raise UnpluggedError("No gamepad found.")
    return gamepad.read()
