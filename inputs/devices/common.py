import glob
import os
import io
import ctypes
from multiprocessing import Process, Pipe
from warnings import warn

from inputs.devices.microbit import MicroBitPad
from inputs.utils import EVENT_SIZE, iter_unpack
from inputs.constants import (
    EVENT_MAP,
    XINPUT_DLL_NAMES,
    XINPUT_ERROR_DEVICE_NOT_CONNECTED,
    XINPUT_ERROR_SUCCESS,
)
from inputs.devices.gamepad import GamePad, XinputState
from inputs.devices.keyboard import Keyboard
from inputs.devices.led import LED, GamepadLED, SystemLED
from inputs.devices.mouse import Mouse
from inputs.devices.other import OtherDevice
from inputs.platforms.mac.mouse import MightyMouse
from ..platforms import DWORD, HANDLE, NIX, WIN, MAC
from ..errors import (
    PERMISSIONS_ERROR_TEXT,
    NoDevicePath,
    UnknownEventCode,
    UnknownEventType,
)


class InputEvent(object):  # pylint: disable=useless-object-inheritance
    """A user event."""

    # pylint: disable=too-few-public-methods
    def __init__(self, device, event_info):
        self.device = device
        self.timestamp = event_info["timestamp"]
        self.code = event_info["code"]
        self.state = event_info["state"]
        self.ev_type = event_info["ev_type"]


class InputDevice(object):  # pylint: disable=useless-object-inheritance
    """A user input device."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, manager, device_path=None, char_path_override=None, read_size=1):
        self.read_size = read_size
        self.manager = manager
        self.__pipe = None
        self._listener = None
        self.leds = None
        if device_path:
            self._device_path = device_path
        else:
            self._set_device_path()
        # We should by now have a device_path

        try:
            if not self._device_path:
                raise NoDevicePath
        except AttributeError:
            raise NoDevicePath

        self.protocol, _, self.device_type = self._get_path_infomation()
        if char_path_override:
            self._character_device_path = char_path_override
        else:
            self._character_device_path = os.path.realpath(self._device_path)

        self._character_file = None

        self._evdev = False
        self._set_evdev_state()

        self.name = "Unknown Device"
        self._set_name()

    def _set_device_path(self):
        """Set the device path, overridden on the MAC and Windows."""
        pass

    def _set_evdev_state(self):
        """Set whether the device is a real evdev device."""
        if NIX:
            self._evdev = True

    def _set_name(self):
        if NIX:
            with open(
                "/sys/class/input/%s/device/name" % self.get_char_name()
            ) as name_file:
                self.name = name_file.read().strip()
            self.leds = []

    def _get_path_infomation(self):
        """Get useful infomation from the device path."""
        long_identifier = self._device_path.split("/")[4]
        protocol, remainder = long_identifier.split("-", 1)
        identifier, _, device_type = remainder.rsplit("-", 2)
        return (protocol, identifier, device_type)

    def get_char_name(self):
        """Get short version of char device name."""
        return self._character_device_path.split("/")[-1]

    def get_char_device_path(self):
        """Get the char device path."""
        return self._character_device_path

    def __str__(self):
        try:
            return self.name
        except AttributeError:
            return "Unknown Device"

    def __repr__(self):
        return '%s.%s("%s")' % (
            self.__module__,
            self.__class__.__name__,
            self._device_path,
        )

    @property
    def _character_device(self):
        if not self._character_file:
            if WIN:
                self._character_file = io.BytesIO()
                return self._character_file
            try:
                self._character_file = io.open(self._character_device_path, "rb")
            except PermissionError:
                # Python 3
                raise PermissionError(PERMISSIONS_ERROR_TEXT)
            except IOError as err:
                # Python 2
                if err.errno == 13:
                    raise PermissionError(PERMISSIONS_ERROR_TEXT)
                else:
                    raise

        return self._character_file

    def __iter__(self):
        while True:
            event = self._do_iter()
            if event:
                yield event

    def _get_data(self, read_size):
        """Get data from the character device."""
        return self._character_device.read(read_size)

    @staticmethod
    def _get_target_function():
        """Get the correct target function. This is only used by Windows
        subclasses."""
        return False

    def _get_total_read_size(self):
        """How much event data to process at once."""
        if self.read_size:
            read_size = EVENT_SIZE * self.read_size
        else:
            read_size = EVENT_SIZE
        return read_size

    def _do_iter(self):
        read_size = self._get_total_read_size()
        data = self._get_data(read_size)
        if not data:
            return None
        evdev_objects = iter_unpack(data)
        events = [self._make_event(*event) for event in evdev_objects]
        return events

    # pylint: disable=too-many-arguments
    def _make_event(self, tv_sec, tv_usec, ev_type, code, value):
        """Create a friendly Python object from an evdev style event."""
        event_type = self.manager.get_event_type(ev_type)
        eventinfo = {
            "ev_type": event_type,
            "state": value,
            "timestamp": tv_sec + (tv_usec / 1000000),
            "code": self.manager.get_event_string(event_type, code),
        }

        return InputEvent(self, eventinfo)

    def read(self):
        """Read the next input event."""
        return next(iter(self))

    @property
    def _pipe(self):
        """On Windows we use a pipe to emulate a Linux style character
        buffer."""
        if self._evdev:
            return None

        if not self.__pipe:
            target_function = self._get_target_function()
            if not target_function:
                return None

            self.__pipe, child_conn = Pipe(duplex=False)
            self._listener = Process(
                target=target_function, args=(child_conn,), daemon=True
            )
            self._listener.start()
        return self.__pipe

    def __del__(self):
        if "WIN" in globals() or "MAC" in globals():
            if WIN or MAC:
                if self.__pipe:
                    self._listener.terminate()


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
