"""Listen for input events and buffer them in a pipe."""

import struct
import time
from ..constants import EVENT_TYPES
from .errors import UnknownEventType
from .c import EVENT_FORMAT, convert_timeval
from .system import WIN


class BaseListener:
    """Loosely emulate Evdev keyboard behaviour on other platforms.
    Listen (hook in Windows terminology) for key events then buffer
    them in a pipe.
    """

    def __init__(self, pipe, events=None, codes=None):
        self.pipe = pipe
        self.events = events if events else []
        self.codes = codes if codes else None
        self.app = None
        self.timeval = None
        self.type_codes = dict(((value, key) for key, value in EVENT_TYPES))

        self.install_handle_input()

    def install_handle_input(self):
        """Install the input handler."""
        pass

    def uninstall_handle_input(self):
        """Un-install the input handler."""
        pass

    def __del__(self):
        """Clean up when deleted."""
        self.uninstall_handle_input()

    @staticmethod
    def get_timeval():
        """Get the time in seconds and microseconds."""
        return convert_timeval(time.time())

    def update_timeval(self):
        """Update the timeval with the current time."""
        self.timeval = self.get_timeval()

    def create_event_object(self, event_type, code, value, timeval=None):
        """Create an evdev style structure."""
        if not timeval:
            self.update_timeval()
            timeval = self.timeval
        try:
            event_code = self.type_codes[event_type]
        except KeyError:
            raise UnknownEventType(
                "We don't know what kind of event a %s is." % event_type
            )

        event = struct.pack(
            EVENT_FORMAT, timeval[0], timeval[1], event_code, code, value
        )
        return event

    def write_to_pipe(self, event_list):
        """Send event back to the mouse object."""
        self.pipe.send_bytes(b"".join(event_list))

    def emulate_wheel(self, data, direction, timeval):
        """Emulate rel values for the mouse wheel.

        In evdev, a single click forwards of the mouse wheel is 1 and
        a click back is -1. Windows uses 120 and -120. We floor divide
        the Windows number by 120. This is fine for the digital scroll
        wheels found on the vast majority of mice. It also works on
        the analogue ball on the top of the Apple mouse.

        What do the analogue scroll wheels found on 200 quid high end
        gaming mice do? If the lowest unit is 120 then we are okay. If
        they report changes of less than 120 units Windows, then this
        might be an unacceptable loss of precision. Needless to say, I
        don't have such a mouse to test one way or the other.

        """
        if direction == "x":
            code = 0x06
        elif direction == "z":
            # Not enitely sure if this exists
            code = 0x07
        else:
            code = 0x08

        if WIN:
            data = data // 120

        return self.create_event_object("Relative", code, data, timeval)

    def emulate_rel(self, key_code, value, timeval):
        """Emulate the relative changes of the mouse cursor."""
        return self.create_event_object("Relative", key_code, value, timeval)

    def emulate_press(self, key_code, scan_code, value, timeval):
        """Emulate a button press.

        Currently supports 5 buttons.

        The Microsoft documentation does not define what happens with
        a mouse with more than five buttons, and I don't have such a
        mouse.

        From reading the Linux sources, I guess evdev can support up
        to 255 buttons.

        Therefore, I guess we could support more buttons quite easily,
        if we had any useful hardware.
        """
        scan_event = self.create_event_object("Misc", 0x04, scan_code, timeval)
        key_event = self.create_event_object("Key", key_code, value, timeval)
        return scan_event, key_event

    def emulate_repeat(self, value, timeval):
        """The repeat press of a key/mouse button, e.g. double click."""
        repeat_event = self.create_event_object("Repeat", 2, value, timeval)
        return repeat_event

    def sync_marker(self, timeval):
        """Separate groups of events."""
        return self.create_event_object("Sync", 0, 0, timeval)

    def emulate_abs(self, x_val, y_val, timeval):
        """Emulate the absolute co-ordinates of the mouse cursor."""
        x_event = self.create_event_object("Absolute", 0x00, x_val, timeval)
        y_event = self.create_event_object("Absolute", 0x01, y_val, timeval)
        return x_event, y_event
