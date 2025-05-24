"""Device manager for inputs.
This module provides a way to access all connected and detectible user input
devices, such as keyboards, mice, gamepads, and other HID devices.
"""

import os
import glob
from warnings import warn
import ctypes

from .constants import (
    XINPUT_DLL_NAMES,
    XINPUT_ERROR_DEVICE_NOT_CONNECTED,
    XINPUT_ERROR_SUCCESS,
    EVENT_MAP,
)

from .libi.errors import UnknownEventType, UnknownEventCode

from .libi.system import WIN, MAC, NIX
from .libi.c import DWORD, HANDLE
from .devices.gamepad.gamepad import GamePad
from .devices.base import OtherDevice
from .devices.gamepad._win import XinputState
from .devices.mouse.mouse import Mouse, MightyMouse
from .devices.keyboard.keyboard import Keyboard
from .devices.led.led import LED, GamepadLED, SystemLED
from .devices.gamepad.microbit import MicroBitPad


class RawInputDeviceList(ctypes.Structure):
    """
    Contains information about a raw input device.

    For full details see Microsoft's documentation:

    http://msdn.microsoft.com/en-us/library/windows/desktop/
    ms645568(v=vs.85).aspx
    """

    # pylint: disable=too-few-public-methods
    _fields_ = [("hDevice", HANDLE), ("dwType", DWORD)]


class DeviceManager(object):  # pylint: disable=useless-object-inheritance
    """Provides access to all connected and detectible user input
    devices."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        self.codes = {key: dict(value) for key, value in EVENT_MAP}
        self._raw = []
        self.keyboards = []
        self.mice = []
        self.gamepads = []
        self.other_devices = []
        self.all_devices = []
        self.leds = []
        self.microbits = []
        self.xinput = None
        self.xinput_dll = None
        if WIN:
            self._raw_device_counts = {
                "mice": 0,
                "keyboards": 0,
                "otherhid": 0,
                "unknown": 0,
            }
        self._post_init()

    def _post_init(self):
        """Call the find devices method for the relevant platform."""
        if WIN:
            self._find_devices_win()
        elif MAC:
            self._find_devices_mac()
        else:
            self._find_devices()
        self._update_all_devices()
        if NIX:
            self._find_leds()

    def _update_all_devices(self):
        """Update the all_devices list."""
        self.all_devices = []
        self.all_devices.extend(self.keyboards)
        self.all_devices.extend(self.mice)
        self.all_devices.extend(self.gamepads)
        self.all_devices.extend(self.other_devices)

    def _parse_device_path(self, device_path, char_path_override=None):
        """Parse each device and add to the approriate list."""

        # 1. Make sure that we can parse the device path.
        try:
            device_type = device_path.rsplit("-", 1)[1]
        except IndexError:
            warn(
                "The following device path was skipped as it could "
                "not be parsed: %s" % device_path,
                RuntimeWarning,
            )
            return

        # 2. Make sure each device is only added once.
        realpath = os.path.realpath(device_path)
        if realpath in self._raw:
            return
        self._raw.append(realpath)

        # 3. All seems good, append the device to the relevant list.
        if device_type == "kbd":
            self.keyboards.append(Keyboard(self, device_path, char_path_override))
        elif device_type == "mouse":
            self.mice.append(Mouse(self, device_path, char_path_override))
        elif device_type == "joystick":
            self.gamepads.append(GamePad(self, device_path, char_path_override))
        else:
            self.other_devices.append(
                OtherDevice(self, device_path, char_path_override)
            )

    def _find_xinput(self):
        """Find most recent xinput library."""
        for dll in XINPUT_DLL_NAMES:
            try:
                self.xinput = getattr(ctypes.windll, dll)
            except OSError:
                pass
            else:
                # We found an xinput driver
                self.xinput_dll = dll
                break
        else:
            # We didn't find an xinput library
            warn("No xinput driver dll found, gamepads not supported.", RuntimeWarning)

    def _find_devices_win(self):
        """Find devices on Windows."""
        self._find_xinput()
        self._detect_gamepads()
        self._count_devices()
        if self._raw_device_counts["keyboards"] > 0:
            self.keyboards.append(
                Keyboard(self, "/dev/input/by-id/usb-A_Nice_Keyboard-event-kbd")
            )

        if self._raw_device_counts["mice"] > 0:
            self.mice.append(
                Mouse(
                    self, "/dev/input/by-id/usb-A_Nice_Mouse_called_Arthur-event-mouse"
                )
            )

    def _find_devices_mac(self):
        """Find devices on Mac."""
        self.keyboards.append(Keyboard(self))
        self.mice.append(MightyMouse(self))
        self.mice.append(Mouse(self))

    def _detect_gamepads(self):
        """Find gamepads."""
        state = XinputState()
        # Windows allows up to 4 gamepads.
        for device_number in range(4):
            res = self.xinput.XInputGetState(device_number, ctypes.byref(state))
            if res == XINPUT_ERROR_SUCCESS:
                # We found a gamepad
                device_path = (
                    "/dev/input/by_id/"
                    + "usb-Microsoft_Corporation_Controller_%s-event-joystick"
                    % device_number
                )
                self.gamepads.append(GamePad(self, device_path))
                continue
            if res != XINPUT_ERROR_DEVICE_NOT_CONNECTED:
                raise RuntimeError(
                    "Unknown error %d attempting to get state of device %d"
                    % (res, device_number)
                )

    def _count_devices(self):
        """See what Windows' GetRawInputDeviceList wants to tell us.

        For now, we are just seeing if there is at least one keyboard
        and/or mouse attached.

        GetRawInputDeviceList could be used to help distinguish between
        different keyboards and mice on the system in the way Linux
        can. However, Roma uno die non est condita.

        """
        number_of_devices = ctypes.c_uint()

        if (
            ctypes.windll.user32.GetRawInputDeviceList(
                ctypes.POINTER(ctypes.c_int)(),
                ctypes.byref(number_of_devices),
                ctypes.sizeof(RawInputDeviceList),
            )
            == -1
        ):
            warn(
                "Call to GetRawInputDeviceList was unsuccessful."
                "We have no idea if a mouse or keyboard is attached.",
                RuntimeWarning,
            )
            return

        devices_found = (RawInputDeviceList * number_of_devices.value)()

        if (
            ctypes.windll.user32.GetRawInputDeviceList(
                devices_found,
                ctypes.byref(number_of_devices),
                ctypes.sizeof(RawInputDeviceList),
            )
            == -1
        ):
            warn(
                "Call to GetRawInputDeviceList was unsuccessful."
                "We have no idea if a mouse or keyboard is attached.",
                RuntimeWarning,
            )
            return

        for device in devices_found:
            if device.dwType == 0:
                self._raw_device_counts["mice"] += 1
            elif device.dwType == 1:
                self._raw_device_counts["keyboards"] += 1
            elif device.dwType == 2:
                self._raw_device_counts["otherhid"] += 1
            else:
                self._raw_device_counts["unknown"] += 1

    def _find_devices(self):
        """Find available devices."""
        self._find_by("id")
        self._find_by("path")
        self._find_special()

    def _find_by(self, key):
        """Find devices."""
        by_path = glob.glob("/dev/input/by-{key}/*-event-*".format(key=key))
        for device_path in by_path:
            self._parse_device_path(device_path)

    def _find_leds(self):
        """Find LED devices, Linux-only so far."""
        for path in glob.glob("/sys/class/leds/*"):
            self._parse_led_path(path)

    def _parse_led_path(self, path):
        name = path.rsplit("/", 1)[1]
        if name.startswith("xpad"):
            self.leds.append(GamepadLED(self, path, name))
        elif name.startswith("input"):
            self.leds.append(SystemLED(self, path, name))
        else:
            self.leds.append(LED(self, path, name))

    def _get_char_names(self):
        """Get a list of already found devices."""
        return [device.get_char_name() for device in self.all_devices]

    def _find_special(self):
        """Look for special devices."""
        charnames = self._get_char_names()
        for eventdir in glob.glob("/sys/class/input/event*"):
            char_name = os.path.split(eventdir)[1]
            if char_name in charnames:
                continue
            name_file = os.path.join(eventdir, "device", "name")
            with open(name_file) as name_file:
                device_name = name_file.read().strip()
                if device_name in self.codes["specials"]:
                    self._parse_device_path(
                        self.codes["specials"][device_name],
                        os.path.join("/dev/input", char_name),
                    )

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
            return self.codes["types"][raw_type]
        except KeyError:
            raise UnknownEventType("We don't know this event type")

    def get_event_string(self, evtype, code):
        """Get the string name of the event."""
        if WIN and evtype == "Key":
            # If we can map the code to a common one then do it
            try:
                code = self.codes["wincodes"][code]
            except KeyError:
                pass
        try:
            return self.codes[evtype][code]
        except KeyError:
            raise UnknownEventCode("We don't know this event.", evtype, code)

    def get_typecode(self, name):
        """Returns type code for `name`."""
        return self.codes["type_codes"][name]

    def detect_microbit(self):
        """Detect a microbit."""
        try:
            gpad = MicroBitPad(self)
        except ModuleNotFoundError:
            warn(
                "The microbit library could not be found in the pythonpath. \n"
                "For more information, please visit \n"
                "https://inputs.readthedocs.io/en/latest/user/microbit.html",
                RuntimeWarning,
            )
        else:
            self.microbits.append(gpad)
            self.gamepads.append(gpad)
