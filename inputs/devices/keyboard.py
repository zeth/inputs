import ctypes
from ctypes.wintypes import LPARAM
from inputs.constants import APPKIT_KB_PATH, WIN_KEYBOARD_CODES
from inputs.devices.common import InputDevice
from inputs.platforms import DWORD, MSG, NIX, MAC, WIN, WPARAM, BaseListener


class Keyboard(InputDevice):
    """A keyboard or other key-like device.

    Original umapped scan code, followed by the important key info
    followed by a sync.
    """

    def _set_device_path(self):
        super(Keyboard, self)._set_device_path()
        if MAC:
            self._device_path = APPKIT_KB_PATH

    def _set_name(self):
        super(Keyboard, self)._set_name()
        if WIN:
            self.name = "Microsoft Keyboard"
        elif MAC:
            self.name = "AppKit Keyboard"

    @staticmethod
    def _get_target_function():
        """Get the correct target function."""
        if WIN:
            return keyboard_process
        if MAC:
            return mac_keyboard_process
        return None

    def _get_data(self, read_size):
        """Get data from the character device."""
        if NIX:
            return super(Keyboard, self)._get_data(read_size)
        return self._pipe.recv_bytes()
