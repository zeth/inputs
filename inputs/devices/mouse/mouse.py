"""Mouse input device handling."""

from ...constants import APPKIT_MOUSE_PATH, QUARTZ_MOUSE_PATH
from ...libi.system import NIX, WIN, MAC
from ..base import InputDevice
from ._win import win_mouse_process
from ._mac import appkit_mouse_process, quartz_mouse_process


class Mouse(InputDevice):
    """A mouse or other pointing-like device."""

    def _set_device_path(self):
        super()._set_device_path()
        if MAC:
            self._device_path = APPKIT_MOUSE_PATH

    def _set_name(self):
        super()._set_name()
        if WIN:
            self.name = "Microsoft Mouse"
        elif MAC:
            self.name = "AppKit Mouse"

    @staticmethod
    def _get_target_function():
        """Get the correct target function."""
        if WIN:
            return win_mouse_process
        if MAC:
            return appkit_mouse_process
        return None

    def _get_data(self, read_size):
        """Get data from the character device."""
        if NIX:
            return super()._get_data(read_size)
        return self._pipe.recv_bytes()


class MightyMouse(Mouse):
    """A mouse or other pointing device on the Mac."""

    def _set_device_path(self):
        super()._set_device_path()
        if MAC:
            self._device_path = QUARTZ_MOUSE_PATH

    def _set_name(self):
        self.name = "Quartz Mouse"

    @staticmethod
    def _get_target_function():
        """Get the correct target function."""
        return quartz_mouse_process
