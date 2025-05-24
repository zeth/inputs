"""Keyboard device class."""

from ...constants import APPKIT_KB_PATH
from ...libi.system import NIX, WIN, MAC
from ..base import InputDevice
from ._mac import mac_keyboard_process
from ._win import win_keyboard_process


class Keyboard(InputDevice):
    """A keyboard or other key-like device.

    Original umapped scan code, followed by the important key info
    followed by a sync.
    """

    def _set_device_path(self):
        super()._set_device_path()
        if MAC:
            self._device_path = APPKIT_KB_PATH

    def _set_name(self):
        super()._set_name()
        if WIN:
            self.name = "Microsoft Keyboard"
        elif MAC:
            self.name = "AppKit Keyboard"

    @staticmethod
    def _get_target_function():
        """Get the correct target function (if not on NIX)."""
        if WIN:
            return win_keyboard_process
        if MAC:
            return mac_keyboard_process
        return None

    def _get_data(self, read_size):
        """Get data from the character device."""
        if NIX:
            return super()._get_data(read_size)
        return self._pipe.recv_bytes()
