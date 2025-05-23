from inputs.constants import APPKIT_MOUSE_PATH, QUARTZ_MOUSE_PATH
from inputs.devices.common import InputDevice
from inputs.platforms import MAC, NIX, WIN
from inputs.platforms.mac.mouse import appkit_mouse_process
from inputs.platforms.win.mouse import mouse_process


class Mouse(InputDevice):
    """A mouse or other pointing-like device."""

    def _set_device_path(self):
        super(Mouse, self)._set_device_path()
        if MAC:
            self._device_path = APPKIT_MOUSE_PATH

    def _set_name(self):
        super(Mouse, self)._set_name()
        if WIN:
            self.name = "Microsoft Mouse"
        elif MAC:
            self.name = "AppKit Mouse"

    @staticmethod
    def _get_target_function():
        """Get the correct target function."""
        if WIN:
            return mouse_process
        if MAC:
            return appkit_mouse_process
        return None

    def _get_data(self, read_size):
        """Get data from the character device."""
        if NIX:
            return super(Mouse, self)._get_data(read_size)
        return self._pipe.recv_bytes()
