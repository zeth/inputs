"""A gamepad or other joystick-like device.

# I made this GamePad class before Mouse and Keyboard above, and have
# learned a lot about Windows in the process.  This can probably be
# simplified massively and made to match Mouse and Keyboard more.

"""

import codecs
import ctypes
import io
from multiprocessing import Process
import os
import struct
from itertools import count
from operator import itemgetter
import time

from ...constants import XINPUT_ERROR_DEVICE_NOT_CONNECTED, XINPUT_ERROR_SUCCESS
from ...libi.errors import PERMISSIONS_ERROR_TEXT, UnknownEventType, UnpluggedError
from ...libi.c import EVENT_FORMAT, convert_timeval
from ...libi.system import NIX, WIN
from ..base import InputDevice
from ._win import XinputGamepad, XinputState, XinputVibration, delay_and_stop

if NIX:
    from fcntl import ioctl


class GamePad(InputDevice):
    """A gamepad or other joystick-like device."""

    def __init__(self, manager, device_path, char_path_override=None):
        super().__init__(manager, device_path, char_path_override)
        self._write_file = None
        self.__device_number = None
        if WIN:
            if "Microsoft_Corporation_Controller" in self._device_path:
                self.name = "Microsoft X-Box 360 pad"
                identifier = self._get_path_infomation()[1]
                self.__device_number = int(identifier.split("_")[-1])
                self.__received_packets = 0
                self.__missed_packets = 0
                self.__last_state = self.__read_device()
        if NIX:
            self._number_xpad()

    def _number_xpad(self):
        """Get the number of the joystick."""
        js_path = self._device_path.replace("-event", "")
        js_chardev = os.path.realpath(js_path)
        try:
            number_text = js_chardev.split("js")[1]
        except IndexError:
            return
        try:
            number = int(number_text)
        except ValueError:
            return
        self.__device_number = number

    def get_number(self):
        """Return the joystick number of the gamepad."""
        return self.__device_number

    def __iter__(self):
        while True:
            if WIN:
                self.__check_state()
            event = self._do_iter()
            if event:
                yield event

    def __check_state(self):
        """On Windows, check the state and fill the event character device."""
        state = self.__read_device()
        if not state:
            raise UnpluggedError("Gamepad %d is not connected" % self.__device_number)
        if state.packet_number != self.__last_state.packet_number:
            # state has changed, handle the change
            self.__handle_changed_state(state)
            self.__last_state = state

    @staticmethod
    def __get_timeval():
        """Get the time and make it into C style timeval."""
        return convert_timeval(time.time())

    def create_event_object(self, event_type, code, value, timeval=None):
        """Create an evdev style object."""
        if not timeval:
            timeval = self.__get_timeval()
        try:
            event_code = self.manager.codes["type_codes"][event_type]
        except KeyError:
            raise UnknownEventType(
                "We don't know what kind of event a %s is." % event_type
            )
        event = struct.pack(
            EVENT_FORMAT, timeval[0], timeval[1], event_code, code, value
        )
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
        sync = self.create_event_object("Sync", 0, 0, timeval)
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
        events.extend(self.__get_axis_events(state, timeval))
        if events:
            self.__write_to_character_device(events, timeval)

    def __map_button(self, button):
        """Get the linux xpad code from the Windows xinput code."""
        _, start_code, start_value = button
        value = start_value
        ev_type = "Key"
        code = self.manager.codes["xpad"][start_code]
        if 1 <= start_code <= 4:
            ev_type = "Absolute"
        if start_code == 1 and start_value == 1:
            value = -1
        elif start_code == 3 and start_value == 1:
            value = -1
        return code, value, ev_type

    def __map_axis(self, axis):
        """Get the linux xpad code from the Windows xinput code."""
        start_code, start_value = axis
        value = start_value
        code = self.manager.codes["xpad"][start_code]
        return code, value

    def __get_button_events(self, state, timeval=None):
        """Get the button events from xinput."""
        changed_buttons = self.__detect_button_events(state)
        events = self.__emulate_buttons(changed_buttons, timeval)
        return events

    def __get_axis_events(self, state, timeval=None):
        """Get the stick events from xinput."""
        axis_changes = self.__detect_axis_events(state)
        events = self.__emulate_axis(axis_changes, timeval)
        return events

    def __emulate_axis(self, axis_changes, timeval=None):
        """Make the axis events use the Linux style format."""
        events = []
        for axis in axis_changes:
            code, value = self.__map_axis(axis)
            event = self.create_event_object("Absolute", code, value, timeval=timeval)
            events.append(event)
        return events

    def __emulate_buttons(self, changed_buttons, timeval=None):
        """Make the button events use the Linux style format."""
        events = []
        for button in changed_buttons:
            code, value, ev_type = self.__map_button(button)
            event = self.create_event_object(ev_type, code, value, timeval=timeval)
            events.append(event)
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
            filter(itemgetter(0), list(zip(changed, button_numbers, buttons_state)))
        )
        # returns for example [(1,15,1)] type, code, value?
        return changed_buttons

    def __detect_axis_events(self, state):
        # axis fields are everything but the buttons
        # pylint: disable=protected-access
        # Attribute name _fields_ is special name set by ctypes
        axis_fields = dict(XinputGamepad._fields_)
        axis_fields.pop("buttons")
        changed_axes = []

        # Ax_type might be useful when we support high-level deadzone
        # methods.
        # pylint: disable=unused-variable
        for axis, ax_type in list(axis_fields.items()):
            old_val = getattr(self.__last_state.gamepad, axis)
            new_val = getattr(state.gamepad, axis)
            if old_val != new_val:
                changed_axes.append((axis, new_val))
        return changed_axes

    def __read_device(self):
        """Read the state of the gamepad."""
        state = XinputState()
        res = self.manager.xinput.XInputGetState(
            self.__device_number, ctypes.byref(state)
        )
        if res == XINPUT_ERROR_SUCCESS:
            return state
        if res != XINPUT_ERROR_DEVICE_NOT_CONNECTED:
            raise RuntimeError(
                "Unknown error %d attempting to get state of device %d"
                % (res, self.__device_number)
            )
        # else (device is not connected)
        return None

    @property
    def _write_device(self):
        if not self._write_file:
            if not NIX:
                return None
            try:
                self._write_file = io.open(self._character_device_path, "wb")
            except PermissionError:
                # Python 3
                raise PermissionError(PERMISSIONS_ERROR_TEXT)
            except IOError as err:
                # Python 2
                if err.errno == 13:
                    raise PermissionError(PERMISSIONS_ERROR_TEXT)
                else:
                    raise

        return self._write_file

    def _start_vibration_win(self, left_motor, right_motor):
        """Start the vibration, which will run until stopped."""
        xinput_set_state = self.manager.xinput.XInputSetState
        xinput_set_state.argtypes = [ctypes.c_uint, ctypes.POINTER(XinputVibration)]
        xinput_set_state.restype = ctypes.c_uint
        vibration = XinputVibration(int(left_motor * 65535), int(right_motor * 65535))
        xinput_set_state(self.__device_number, ctypes.byref(vibration))

    def _stop_vibration_win(self):
        """Stop the vibration."""
        xinput_set_state = self.manager.xinput.XInputSetState
        xinput_set_state.argtypes = [ctypes.c_uint, ctypes.POINTER(XinputVibration)]
        xinput_set_state.restype = ctypes.c_uint
        stop_vibration = ctypes.byref(XinputVibration(0, 0))
        xinput_set_state(self.__device_number, stop_vibration)

    def _set_vibration_win(self, left_motor, right_motor, duration):
        """Control the motors on Windows."""
        self._start_vibration_win(left_motor, right_motor)
        stop_process = Process(
            target=delay_and_stop,
            args=(duration, self.manager.xinput_dll, self.__device_number),
        )
        stop_process.start()

    def __get_vibration_code(self, left_motor, right_motor, duration):
        """This is some crazy voodoo, if you can simplify it, please do."""
        inner_event = struct.pack(
            "2h6x2h2x2H28x",
            0x50,
            -1,
            duration,
            0,
            int(left_motor * 65535),
            int(right_motor * 65535),
        )
        buf_conts = ioctl(self._write_device, 1076905344, inner_event)
        return int(codecs.encode(buf_conts[1:3], "hex"), 16)

    def _set_vibration_nix(self, left_motor, right_motor, duration):
        """Control the motors on Linux.
        Duration is in miliseconds."""
        code = self.__get_vibration_code(left_motor, right_motor, duration)
        secs, msecs = convert_timeval(time.time())
        outer_event = struct.pack(EVENT_FORMAT, secs, msecs, 0x15, code, 1)
        self._write_device.write(outer_event)
        self._write_device.flush()

    def set_vibration(self, left_motor, right_motor, duration):
        """Control the speed of both motors seperately or together.
        left_motor and right_motor arguments require a number between
        0 (off) and 1 (full).
        duration is miliseconds, e.g. 1000 for a second."""
        if WIN:
            self._set_vibration_win(left_motor, right_motor, duration)
        elif NIX:
            self._set_vibration_nix(left_motor, right_motor, duration)
        else:
            raise NotImplementedError
