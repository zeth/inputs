"""Inputs - user input for humans.

About
-----

Inputs aims to provide easy to use, cross-platform, user input device
support for Python. I.e. keyboards, mice, gamepads, etc.

It is still early days. Currently supported platforms are the
Raspberry Pi, Linux and Windows. Hopefully Mac OS X, BSD and Android
should be supported soon. Optional Asyncio-based event loop support
will be included eventually.

Obviously high level graphical libraries such as PyGame and PyQT will
provide user input support in a very friendly way. However, this
module does not require your program to use any particular graphical
toolkit, or even have a monitor at all.

In the Embedded Linux or Raspberry Pi Internet of Things type
situation, you may not even have an X-server installed or running.

This module may also be useful where a computer needs to run a
particular application full screen but you would want to listen out in
the background for a particular set of user inputs, e.g. to bring up
an admin panel in a digital signage setup.

Note to Children
----------------

It is pretty easy to use any user input device library, including this
one, to build a keylogger. Using this module to spy on your mum or
teacher or sibling is not cool and may get you into trouble. So please
do not do that. Make a game instead, games are cool.

Quick Start
-----------

To access all the available input devices on the current system:

>>> from inputs import devices
>>> for device in devices:
...     print(device)

You can also access devices by type:

>>> devices.gamepads
>>> devices.keyboards
>>> devices.mice
>>> devices.other_devices

Each device object has the obvious methods and properties that you
expect, stop reading now and just get playing!

If that is not high level enough, there are three basic functions that
simply give you the latest event (key press, mouse movement/press or
gamepad activity) from the first connected device in the category, for
example:

>>> from inputs import get_gamepad
>>> while 1:
...     event = get_gamepad()
...     print(event.ev_type, event.code, event.state)

>>> from inputs import get_key
>>> while 1:
...     event = get_gamepad()
...     print(event.ev_type, event.code, event.state)

>>> from inputs import get_mouse
>>> while 1:
...     event = get_gamepad()
...     print(event.ev_type, event.code, event.state)

Advanced documentation
----------------------

A keyboard is represented by the Keyboard class, a mouse by the Mouse
class and a gamepad by the Gamepad class. These themselves are
subclasses of InputDevice.

The devices object is an instance of DeviceManager, as you can prove:

>>> from inputs import DeviceManager
>>> devices = DeviceManager()

The DeviceManager is reponsible for finding input devices on the
user's system and setting up InputDevice objects.

The InputDevice objects emit instances of InputEvent. So from top
down, the classes are arranged thus:

DeviceManager > InputDevice > InputEvent

So when you have a particular InputEvent instance, you can access its
device and manager:

>>> event.device.manager

The event object has a property called device and the device has a
property called manager.

Gamepads
--------

An approach often taken by PC games, especially open source games, is
to assume that all gamepads are Microsoft Xbox 360 controllers and
then users use software such as x360ce (on Windows) or xboxdrv (on
Linux) to make other models of gamepad report Xbox 360 style button
and joystick codes to the operating system.

So for inputs the primary target device is the Microsoft Xbox 360
Wired Controller and this has the best support. Another gamepad might
just work but if not you can use xboxdrv or x360ce to configure it
yourself.

More testing and support for common gamepads will come in due course.

Raspberry Pi Sense HAT
----------------------

The microcontroller on the Raspberry Pi Sense HAT presents the
joystick to the operating system as a keyboard, so find it there under
keyboards. If you worry about this, you are over-thinking things.

Credits
-------

Inputs is by Zeth, all mistakes are mine.

Thanks to Dave Jones for stick.py which is not only the basis for
Sense HAT stick support in this module but more importantly also
taught me an easier way to parse the Evdev event format in Python.

https://github.com/RPi-Distro/python-sense-hat/blob/master/sense_hat/stick.py
https://github.com/waveform80/pisense/blob/master/pisense/stick.py

Thanks to Andy (r4dian) and Jason R. Coombs whose existing (MIT
licenced) Python examples for Xbox 360 controller support on Windows
helped me understand xinput greatly. Xbox 360 controller support on
Windows here is based on their work.
https://github.com/r4dian/Xbox-360-Controller-for-Python
http://pydoc.net/Python/jaraco.input/1.0.1/jaraco.input.win32.xinput/

"""

from __future__ import print_function

import os
import io
import glob
import struct
import platform
import math
import time
from collections import namedtuple
from warnings import warn
from itertools import count
from operator import itemgetter, attrgetter
import ctypes

from inputs.constants import (EVENT_MAP, EVENT_FORMAT, EVENT_SIZE,
                              XINPUT_DLL_NAMES,
                              XINPUT_ERROR_DEVICE_NOT_CONNECTED,
                              XINPUT_ERROR_SUCCESS)

WIN = True if platform.system() == 'Windows' else False


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
    # pylint: disable=too-few-public-methods
    def __init__(self,
                 device,
                 event_info):
        self.device = device
        self.timestamp = event_info["timestamp"]
        self.code = event_info["code"]
        self.state = event_info["state"]
        self.ev_type = event_info["ev_type"]


class InputDevice(object):
    """A user input device."""
    def __init__(self, manager, device_path,
                 char_path_override=None):
        self.manager = manager
        self._device_path = device_path
        self.protocol, _, self.device_type = self._get_path_infomation()
        if char_path_override:
            self._character_device_path = char_path_override
        else:
            self._character_device_path = os.path.realpath(device_path)
        self._character_file = None
        if not WIN:
            with open("/sys/class/input/%s/device/name" %
                      self.get_char_name()) as name_file:
                self.name = name_file.read().strip()

    def _get_path_infomation(self):
        """Get useful infomation from the device path."""
        long_identifier = self._device_path.split('/')[4]
        protocol, remainder = long_identifier.split('-', 1)
        identifier, _, device_type = remainder.rsplit('-', 2)
        return (protocol, identifier, device_type)

    def get_char_name(self):

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
            if WIN:
                self._character_file = io.BytesIO()
                return self._character_file
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
        event = self._do_iter(type_filter)
        if event:
            yield event

    def _do_iter(self, type_filter=None):
        while True:
            event = self._character_device.read(EVENT_SIZE)
            (tv_sec, tv_usec, ev_type, code, value) = struct.unpack(
                EVENT_FORMAT, event)
            event_type = self.manager.get_event_type(ev_type)
            if type_filter:
                if event_type != type_filter:
                    return

            eventinfo = {
                "ev_type": event_type,
                "state": value,
                "timestamp": tv_sec + (tv_usec / 1000000),
                "code": self.manager.get_event_string(event_type, code)
            }

            return InputEvent(self, eventinfo)

    def read(self):
        """Read the next input event."""
        return next(iter(self))


class Keyboard(InputDevice):
    """A keyboard or other key-like device."""
    pass


class Mouse(InputDevice):
    """A mouse or other pointing-like device."""
    pass


class XinputGamepad(ctypes.Structure):
    """Describes the current state of the Xbox 360 Controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_gamepad%28v=vs.85%29.aspx

    """
    # pylint: disable=too-few-public-methods
    _fields_ = [
        ('buttons', ctypes.c_ushort),  # wButtons
        ('left_trigger', ctypes.c_ubyte),  # bLeftTrigger
        ('right_trigger', ctypes.c_ubyte),  # bLeftTrigger
        ('l_thumb_x', ctypes.c_short),  # sThumbLX
        ('l_thumb_y', ctypes.c_short),  # sThumbLY
        ('r_thumb_x', ctypes.c_short),  # sThumbRx
        ('r_thumb_y', ctypes.c_short),  # sThumbRy
    ]


class XinputState(ctypes.Structure):
    """Represents the state of a controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_state%28v=vs.85%29.aspx

    """
    # pylint: disable=too-few-public-methods
    _fields_ = [
        ('packet_number', ctypes.c_ulong),  # dwPacketNumber
        ('gamepad', XinputGamepad),  # Gamepad
    ]


class XinputVibration(ctypes.Structure):
    """Specifies motor speed levels for the vibration function of a
    controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_vibration%28v=vs.85%29.aspx

    """
    # pylint: disable=too-few-public-methods
    _fields_ = [("wLeftMotorSpeed", ctypes.c_ushort),
                ("wRightMotorSpeed", ctypes.c_ushort)]


class GamePad(InputDevice):
    """A gamepad or other joystick-like device."""
    def __init__(self, manager, device_path,
                 char_path_override=None):
        super(GamePad, self).__init__(manager,
                                      device_path,
                                      char_path_override)
        if WIN:
            if "Microsoft_Corporation_Controller" in self._device_path:
                self.name = "Microsoft X-Box 360 pad"
                identifier = self._get_path_infomation()[1]
                self.__device_number = int(identifier.split('_')[-1])
                self.__received_packets = 0
                self.__missed_packets = 0
                self.__last_state = self.__read_device()

    def __iter__(self, type_filter=None):
        if not WIN:
            event = super(GamePad, self)._do_iter(type_filter)
            if event:
                yield event

        else:
            while True:
                state = self.__read_device()
                if not state:
                    raise UnpluggedError(
                        "Gamepad %d is not connected" % self.__device_number)
                if state.packet_number != self.__last_state.packet_number:
                    # state has changed, handle the change
                    ievent = self.__handle_changed_state(state)
                    self.__last_state = state
                    yield ievent
                    self.__last_state = state

    @staticmethod
    def __get_timeval():
        """Get the time and make it into C style timeval."""
        frac, whole = math.modf(time.time())
        microseconds = math.floor(frac * 1000000)
        seconds = math.floor(whole)
        return seconds, microseconds

    def __create_event_object(self,
                              event_type,
                              code,
                              value,
                              timeval=None):
        if not timeval:
            timeval = self.__get_timeval()
        try:
            event_code = self.manager.codes['type_codes'][event_type]
        except KeyError:
            raise UnknownEventType(
                "We don't know what kind of event a %s is.",
                event_type)

        event = struct.pack(EVENT_FORMAT,
                            timeval[0],
                            timeval[1],
                            event_code,
                            code,
                            value)
        return event

    def __write_to_character_device(self, event_list, timeval=None):
        """Emulate the Linux character device on other platforms such as
        Windows."""
        # Remember the position of the stream
        pos = self._character_device.tell()
        # Go to the end of the stream
        self._character_device.seek(0, 2)
        # Write the new data to the end
        for event in event_list:
            self._character_device.write(event)
        # Add a sync marker
        sync = self.__create_event_object("Sync", 0, 0, timeval)
        self._character_device.write(sync)
        # Put the stream back to its original position
        self._character_device.seek(pos)

    def __handle_changed_state(self, state):
        """
        we need to pack a struct with the following five numbers:
        tv_sec, tv_usec, ev_type, code, value

        then write it using __write_to_character_device

        seconds, mircroseconds, ev_type, code, value
        time we just use now
        ev_type we look up
        code we look up
        value is 0 or 1 for the buttons
        axis value is maybe the same as Linux? Hope so!
        """
        timeval = self.__get_timeval()
        events = self.__get_button_events(state, timeval)
        axis_changes = self.__detect_axis_events(state)
        print(axis_changes)
        if events:
            self.__write_to_character_device(events, timeval)
        return "Hello Monkey"

    def __map_button(self, button):
        """Get the linux xpad code from the Windows xinput code."""
        _, start_code, start_value = button
        value = start_value
        code = self.manager.codes['xpad'][start_code]

        if button == 1 and start_value == 1:
            value = 0xFFFFFFFF
        elif button == 3 and start_value == 1:
            value = 0xFFFFFFFF
        return code, value

    def __get_button_events(self, state, timeval=None):
        """Get the button events from xinput."""
        changed_buttons = self.__detect_button_events(state)
        events = self.__emulate_buttons(changed_buttons, timeval)
        return events

    def __emulate_buttons(self, changed_buttons, timeval=None):
        """Make the button events use the Linux style format."""
        events = []
        for button in changed_buttons:
            code, value = self.__map_button(button)
            event = self.__create_event_object(
                "Key",
                code,
                value,
                timeval=timeval)
            events.append(event)

        print("events", events)
        return events

    @staticmethod
    def __gen_bit_values(number):
        """
        Return a zero or one for each bit of a numeric value up to the most
        significant 1 bit, beginning with the least significant bit.
        """
        number = int(number)
        while number:
            yield number & 0x1
            number >>= 1

    def __get_bit_values(self, number, size=32):
        """Get bit values as a list for a given number

        >>> get_bit_values(1) == [0]*31 + [1]
        True

        >>> get_bit_values(0xDEADBEEF)
        [1L, 1L, 0L, 1L, 1L, 1L, 1L,
        0L, 1L, 0L, 1L, 0L, 1L, 1L, 0L, 1L, 1L, 0L, 1L, 1L, 1L, 1L,
        1L, 0L, 1L, 1L, 1L, 0L, 1L, 1L, 1L, 1L]

        You may override the default word size of 32-bits to match your actual
        application.
        >>> get_bit_values(0x3, 2)
        [1L, 1L]

        >>> get_bit_values(0x3, 4)
        [0L, 0L, 1L, 1L]

        """
        res = list(self.__gen_bit_values(number))
        res.reverse()
        # 0-pad the most significant bit
        res = [0] * (size - len(res)) + res
        return res

    def __detect_button_events(self, state):
        changed = state.gamepad.buttons ^ self.__last_state.gamepad.buttons
        changed = self.__get_bit_values(changed, 16)
        buttons_state = self.__get_bit_values(state.gamepad.buttons, 16)
        changed.reverse()
        buttons_state.reverse()
        button_numbers = count(1)
        changed_buttons = list(
            filter(itemgetter(0),
                   list(zip(changed, button_numbers, buttons_state))))
        # returns for example [(1,15,1)] type, code, value?
        return changed_buttons

    @staticmethod
    def __translate_using_data_size(value, data_size):
        """Normalizes analog data to [0,1] for unsigned data and [-0.5,0.5]
        for signed data."""
        data_bits = 8 * data_size
        return float(value) / (2 ** data_bits - 1)

    def __detect_axis_events(self, state):
        # axis fields are everything but the buttons
        # pylint: disable=protected-access
        # Attribute name _fields_ is special name set by ctypes
        axis_fields = dict(XinputGamepad._fields_)
        axis_fields.pop('buttons')
        changed_axes = []
        for axis, ax_type in list(axis_fields.items()):
            old_val = getattr(self.__last_state.gamepad, axis)
            new_val = getattr(state.gamepad, axis)
            data_size = ctypes.sizeof(ax_type)
            old_val = self.__translate_using_data_size(old_val, data_size)
            new_val = self.__translate_using_data_size(new_val, data_size)

            # an attempt to add deadzones and dampen noise
            # done by feel rather than following
            # http://msdn.microsoft.com/en-gb/library/windows/
            # desktop/ee417001%28v=vs.85%29.aspx#dead_zone
            # ags, 2014-07-01
            if ((old_val != new_val and (
                    new_val > 0.08000000000000000
                    or new_val < -0.08000000000000000)
                 and abs(old_val - new_val) > 0.00000000500000000)
                    or (axis == 'right_trigger' or axis == 'left_trigger')
                    and new_val == 0
                    and abs(old_val - new_val) > 0.00000000500000000):
                changed_axes.append((axis, new_val))
        return changed_axes

    def __read_device(self):
        """Read the state of the gamepad."""
        state = XinputState()
        res = self.manager.xinput.XInputGetState(
            self.__device_number, ctypes.byref(state))
        if res == XINPUT_ERROR_SUCCESS:
            return state
        if res != XINPUT_ERROR_DEVICE_NOT_CONNECTED:
            raise RuntimeError(
                "Unknown error %d attempting to get state of device %d" % (
                    res, self.__device_number))
        # else return None (device is not connected)

    def set_vibration(self, left_motor, right_motor):
        "Control the speed of both motors seperately"
        if WIN:
            # Set up function argument types and return type
            xinput_set_state = self.manager.xinput.XInputSetState
            xinput_set_state.argtypes = [
                ctypes.c_uint, ctypes.POINTER(XinputVibration)]
            xinput_set_state.restype = ctypes.c_uint

            vibration = XinputVibration(
                int(left_motor * 65535), int(right_motor * 65535))
            xinput_set_state(self.__device_number, ctypes.byref(vibration))
        else:
            print("Not implemented yet. Coming soon.")


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
        self.xinput = None
        if WIN:
            self._find_devices_win()
        else:
            self._find_devices()
            self._update_all_devices()
        #  self._index = 0

    def _update_all_devices(self):
        """Update the all_devices list."""
        self.all_devices.extend(self.keyboards)
        self.all_devices.extend(self.mice)
        self.all_devices.extend(self.gamepads)
        self.all_devices.extend(self.other_devices)

    def _parse_device_path(self, device_path, char_path_override=None):
        """Parse each device and add to the approriate list."""
        try:
            device_type = device_path.rsplit('-', 1)[1]
        except IndexError:
            warn("The following device path was skipped as it could "
                 "not be parsed: %s" % device_path, RuntimeWarning)
            return

        if device_type == 'kbd':
            self.keyboards.append(Keyboard(self, device_path,
                                           char_path_override))
        elif device_type == 'mouse':
            self.mice.append(Mouse(self, device_path,
                                   char_path_override))
        elif device_type == 'joystick':
            self.gamepads.append(GamePad(self,
                                         device_path,
                                         char_path_override))
        else:
            self.other_devices.append(OtherDevice(self,
                                                  device_path,
                                                  char_path_override))

    def _find_xinput(self):
        """Find most recent xinput library."""
        for dll in XINPUT_DLL_NAMES:
            try:
                self.xinput = getattr(ctypes.windll, dll)
            except OSError:
                pass
            else:
                # We found an xinput driver
                break
        else:
            # We didn't find an xinput library
            warn("No xinput driver dll found, gamepads not supported.")

    def _find_devices_win(self):
        """Find devices on Windows."""
        self._find_xinput()
        self._detect_gamepads()

    def _detect_gamepads(self):
        """Find gamepads."""
        state = XinputState()
        # Windows allows up to 4 gamepads.
        for device_number in range(4):
            res = self.xinput.XInputGetState(
                device_number, ctypes.byref(state))
            if res == XINPUT_ERROR_SUCCESS:
                # We found a gamepad
                print("we found a gamepad.")
                device_path = (
                    "/dev/input/by_id/" +
                    "usb-Microsoft_Corporation_Controller_%s-event-joystick"
                    % device_number)
                self.gamepads.append(GamePad(self, device_path))
                continue
            if res != XINPUT_ERROR_DEVICE_NOT_CONNECTED:
                raise RuntimeError(
                    "Unknown error %d attempting to get state of device %d"
                    % (res, device_number))

    def _find_devices(self):
        """Find available devices."""
        # Start with everything given an id
        # I.e. those with fully correct kernel drivers
        for device_path in glob.glob('/dev/input/by-id/*-event-*'):
            self._parse_device_path(device_path)

        # We want a list of things we already found
        charnames = [device.get_char_name() for
                     device in self.all_devices]

        # Look for special devices
        for eventdir in glob.glob('/sys/class/input/event*'):
            char_name = os.path.split(eventdir)[1]
            if char_name in charnames:
                continue
            name_file = os.path.join(eventdir, 'device', 'name')
            with open(name_file) as name_file:
                device_name = name_file.read().strip()
                if device_name in self.codes['specials']:
                    self._parse_device_path(
                        self.codes['specials'][device_name],
                        os.path.join('/dev/input', char_name))

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
