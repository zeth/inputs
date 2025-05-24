"""Control LEDs on your devices."""

import io
import os
import struct
import time

from ...libi.errors import PERMISSIONS_ERROR_TEXT
from ...libi.c import EVENT_FORMAT, convert_timeval
from ...libi.system import NIX


class LED:
    """A light source."""

    def __init__(self, manager, path, name):
        self.manager = manager
        self.path = path
        self.name = name
        self._write_file = None
        self._character_device_path = None
        self._post_init()

    def _post_init(self):
        """Post init setup."""
        pass

    def __str__(self):
        return self.name

    def __repr__(self):
        return '%s.%s("%s")' % (self.__module__, self.__class__.__name__, self.path)

    def status(self):
        """Get the device status, i.e. the brightness level."""
        status_filename = os.path.join(self.path, "brightness")
        with open(status_filename) as status_fp:
            result = status_fp.read()
        status_text = result.strip()
        try:
            status = int(status_text)
        except ValueError:
            return status_text
        return status

    def max_brightness(self):
        """Get the device's maximum brightness level."""
        status_filename = os.path.join(self.path, "max_brightness")
        with open(status_filename) as status_fp:
            result = status_fp.read()
        status_text = result.strip()
        try:
            status = int(status_text)
        except ValueError:
            return status_text
        return status

    @property
    def _write_device(self):
        """The output device."""
        if not self._write_file:
            if not NIX:
                return None
            try:
                self._write_file = io.open(self._character_device_path, "wb")
            except PermissionError:
                # Python 3
                raise PermissionError(PERMISSIONS_ERROR_TEXT)
            except IOError as err:
                # Python 2 only
                if err.errno == 13:  # pragma: no cover
                    raise PermissionError(PERMISSIONS_ERROR_TEXT)
                else:
                    raise

        return self._write_file

    def _make_event(self, event_type, code, value):
        """Make a new event and send it to the character device."""
        secs, msecs = convert_timeval(time.time())
        data = struct.pack(EVENT_FORMAT, secs, msecs, event_type, code, value)
        self._write_device.write(data)
        self._write_device.flush()


class SystemLED(LED):
    """An LED on your system e.g. caps lock."""

    def __init__(self, manager, path, name):
        self.code = None
        self.device_path = None
        self.device = None
        super(SystemLED, self).__init__(manager, path, name)

    def _post_init(self):
        """Set up the device path and type code."""
        self._led_type_code = self.manager.get_typecode("LED")
        self.device_path = os.path.realpath(os.path.join(self.path, "device"))
        if "::" in self.name:
            chardev, code_name = self.name.split("::")
            if code_name in self.manager.codes["LED_type_codes"]:
                self.code = self.manager.codes["LED_type_codes"][code_name]
            try:
                event_number = chardev.split("input")[1]
            except IndexError:
                print("Failed with", self.name)
                raise
            else:
                self._character_device_path = "/dev/input/event" + event_number
                self._match_device()

    def on(self):  # pylint: disable=invalid-name
        """Turn the light on."""
        self._make_event(1)

    def off(self):
        """Turn the light off."""
        self._make_event(0)

    def _make_event(self, value):  # pylint: disable=arguments-differ
        """Make a new event and send it to the character device."""
        super(SystemLED, self)._make_event(self._led_type_code, self.code, value)

    def _match_device(self):
        """If the LED is connected to an input device,
        associate the objects."""
        for device in self.manager.all_devices:
            if device.get_char_device_path() == self._character_device_path:
                self.device = device
                device.leds.append(self)
                break


class GamepadLED(LED):
    """A light source on a gamepad."""

    def __init__(self, manager, path, name):
        self.code = None
        self.device = None
        self.gamepad = None
        super(GamepadLED, self).__init__(manager, path, name)

    def _post_init(self):
        self._match_device()
        self._character_device_path = self.gamepad.get_char_device_path()

    def _match_device(self):
        number = int(self.name.split("xpad")[1])
        for gamepad in self.manager.gamepads:
            if number == gamepad.get_number():
                self.gamepad = gamepad
                gamepad.leds.append(self)
                break
