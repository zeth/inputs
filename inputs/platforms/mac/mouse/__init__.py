
from inputs.constants import QUARTZ_MOUSE_PATH
from inputs.devices.mouse import Mouse
from inputs.platforms import MAC
from inputs.platforms.mac.mouse.quartz_sub import quartz_mouse_process


class MightyMouse(Mouse):
    """A mouse or other pointing device on the Mac."""

    def _set_device_path(self):
        super(MightyMouse, self)._set_device_path()
        if MAC:
            self._device_path = QUARTZ_MOUSE_PATH

    def _set_name(self):
        self.name = "Quartz Mouse"

    @staticmethod
    def _get_target_function():
        """Get the correct target function."""
        return quartz_mouse_process
