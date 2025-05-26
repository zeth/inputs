"""Keep the Windows keyboard details wrapped so the Python coder doesn't have to care about C."""

import ctypes

from ...constants import WIN_KEYBOARD_CODES
from ...libi.baselistener import BaseListener
from ...libi.c import DWORD, LPARAM, MSG, WPARAM


class KBDLLHookStruct(ctypes.Structure):
    """Contains information about a low-level keyboard input event.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    ms644967%28v=vs.85%29.aspx
    """

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("vk_code", DWORD),
        ("scan_code", DWORD),
        ("flags", DWORD),
        ("time", ctypes.c_int),
    ]


class WindowsKeyboardListener(BaseListener):
    """Loosely emulate Evdev keyboard behaviour on Windows.  Listen (hook
    in Windows terminology) for key events then buffer them in a pipe.
    """

    def __init__(self, pipe, codes=None):
        self.pipe = pipe
        self.hooked = None
        self.pointer = None
        super(WindowsKeyboardListener, self).__init__(pipe, codes)

    @staticmethod
    def listen():
        """Listen for keyboard input."""
        msg = MSG()
        ctypes.windll.user32.GetMessageA(ctypes.byref(msg), 0, 0, 0)

    def get_fptr(self):
        """Get the function pointer."""
        cmpfunc = ctypes.CFUNCTYPE(
            ctypes.c_int, WPARAM, LPARAM, ctypes.POINTER(KBDLLHookStruct)
        )
        return cmpfunc(self.handle_input)

    def install_handle_input(self):
        """Install the hook."""
        self.pointer = self.get_fptr()

        self.hooked = ctypes.windll.user32.SetWindowsHookExA(
            13, self.pointer, ctypes.windll.kernel32.GetModuleHandleW(None), 0
        )
        if not self.hooked:
            return False
        return True

    def uninstall_handle_input(self):
        """Remove the hook."""
        if self.hooked is None:
            return
        ctypes.windll.user32.UnhookWindowsHookEx(self.hooked)
        self.hooked = None

    def handle_input(self, ncode, wparam, lparam):
        """Process the key input."""
        value = WIN_KEYBOARD_CODES[wparam]
        scan_code = lparam.contents.scan_code
        vk_code = lparam.contents.vk_code
        self.update_timeval()

        events = []
        # Add key event
        scan_key, key_event = self.emulate_press(
            vk_code, scan_code, value, self.timeval
        )
        events.append(scan_key)
        events.append(key_event)

        # End with a sync marker
        events.append(self.sync_marker(self.timeval))

        # We are done
        self.write_to_pipe(events)

        return ctypes.windll.user32.CallNextHookEx(self.hooked, ncode, wparam, lparam)


def win_keyboard_process(pipe):
    """Single subprocess for reading keyboard events on Windows."""
    keyboard = WindowsKeyboardListener(pipe)
    keyboard.listen()
