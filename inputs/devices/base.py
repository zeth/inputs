"""Base class for input devices."""

from multiprocessing import Pipe, Process
import os
import io


from ..libi.c import EVENT_SIZE, iter_unpack
from ..libi.errors import NoDevicePath, PERMISSIONS_ERROR_TEXT
from ..libi.system import NIX, WIN, MAC
from ..libi.event import InputEvent


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
        except AttributeError as exc:
            raise NoDevicePath from exc

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


class OtherDevice(InputDevice):
    """A device of which its is type is either undetectable or has not
    been implemented yet.
    """

    pass
