"""Low level mouse input listener for Windows."""

import ctypes

from ...constants import WIN_MOUSE_CODES
from ...libi.baselistener import BaseListener
from ...libi.c import DWORD, LPARAM, MSG, WPARAM


class MSLLHookStruct(ctypes.Structure):
    """Contains information about a low-level mouse input event.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    ms644970%28v=vs.85%29.aspx
    """

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("x_pos", ctypes.c_long),
        ("y_pos", ctypes.c_long),
        ("reserved", ctypes.c_short),
        ("mousedata", ctypes.c_short),
        ("flags", DWORD),
        ("time", DWORD),
        ("extrainfo", ctypes.c_ulong),
    ]


class WindowsMouseListener(BaseListener):
    """Loosely emulate Evdev mouse behaviour on Windows.  Listen (hook
    in Windows terminology) for key events then buffer them in a pipe.
    """

    def __init__(self, pipe):
        self.pipe = pipe
        self.hooked = None
        self.pointer = None
        self.mouse_codes = WIN_MOUSE_CODES
        super().__init__(pipe)

    @staticmethod
    def listen():
        """Listen for mouse input."""
        msg = MSG()
        ctypes.windll.user32.GetMessageA(ctypes.byref(msg), 0, 0, 0)

    def get_fptr(self):
        """Get the function pointer."""
        cmpfunc = ctypes.CFUNCTYPE(
            ctypes.c_int, WPARAM, LPARAM, ctypes.POINTER(MSLLHookStruct)
        )
        return cmpfunc(self.handle_input)

    def install_handle_input(self):
        """Install the hook."""
        self.pointer = self.get_fptr()

        self.hooked = ctypes.windll.user32.SetWindowsHookExA(
            14, self.pointer, ctypes.windll.kernel32.GetModuleHandleW(None), 0
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
        x_pos = lparam.contents.x_pos
        y_pos = lparam.contents.y_pos
        data = lparam.contents.mousedata

        # This is how we can distinguish mouse 1 from mouse 2
        # extrainfo = lparam.contents.extrainfo
        # The way windows seems to do it is there is primary mouse
        # and all other mouses report as mouse 2

        # Also useful later will be to support the flags field
        # flags = lparam.contents.flags
        # This shows if the event was from a real device or whether it
        # was injected somehow via software

        self.emulate_mouse(wparam, x_pos, y_pos, data)

        # Give back control to Windows to wait for and process the
        # next event
        return ctypes.windll.user32.CallNextHookEx(self.hooked, ncode, wparam, lparam)

    def emulate_mouse(self, key_code, x_val, y_val, data):
        """Emulate the ev codes using the data Windows has given us.

        Note that by default in Windows, to recognise a double click,
        you just notice two clicks in a row within a reasonablely
        short time period.

        However, if the application developer sets the application
        window's class style to CS_DBLCLKS, the operating system will
        notice the four button events (down, up, down, up), intercept
        them and then send a single key code instead.

        There are no such special double click codes on other
        platforms, so not obvious what to do with them. It might be
        best to just convert them back to four events.

        Currently we do nothing.

        ((0x0203, 'WM_LBUTTONDBLCLK'),
         (0x0206, 'WM_RBUTTONDBLCLK'),
         (0x0209, 'WM_MBUTTONDBLCLK'),
         (0x020D, 'WM_XBUTTONDBLCLK'))

        """
        # Once again ignore Windows' relative time (since system
        # startup) and use the absolute time (since epoch i.e. 1st Jan
        # 1970).
        self.update_timeval()

        events = []

        if key_code == 0x0200:
            # We have a mouse move alone.
            # So just pass through to below
            pass
        elif key_code == 0x020A:
            # We have a vertical mouse wheel turn
            events.append(self.emulate_wheel(data, "y", self.timeval))
        elif key_code == 0x020E:
            # We have a horizontal mouse wheel turn
            # https://msdn.microsoft.com/en-us/library/windows/desktop/
            # ms645614%28v=vs.85%29.aspx
            events.append(self.emulate_wheel(data, "x", self.timeval))
        else:
            # We have a button press.

            # Distinguish the second extra button
            if key_code == 0x020B and data == 2:
                key_code = 0x020B2
            elif key_code == 0x020C and data == 2:
                key_code = 0x020C2

            # Get the mouse codes
            code, value, scan_code = self.mouse_codes[key_code]
            # Add in the press events
            scan_event, key_event = self.emulate_press(
                code, scan_code, value, self.timeval
            )
            events.append(scan_event)
            events.append(key_event)

        # Add in the absolute position of the mouse cursor
        x_event, y_event = self.emulate_abs(x_val, y_val, self.timeval)
        events.append(x_event)
        events.append(y_event)

        # End with a sync marker
        events.append(self.sync_marker(self.timeval))

        # We are done
        self.write_to_pipe(events)


def win_mouse_process(pipe):
    """Single subprocess for reading mouse events on Windows."""
    mouse = WindowsMouseListener(pipe)
    mouse.listen()
