"""Inputs - user input for humans.

Inputs aims to provide easy to use, cross-platform, user input device
support for Python. I.e. keyboards, mice, gamepads, etc.

Currently supported platforms are the Raspberry Pi, Linux, Windows and
Mac OS X.

"""

# Copyright (c) 2016, 2018: Zeth
# All rights reserved.
#
# BSD Licence
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of the copyright holder nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function
from __future__ import division

import os
import sys
import io
import glob
import struct
import platform
import math
import time
import codecs
from warnings import warn
from itertools import count
from operator import itemgetter
from multiprocessing import Process, Pipe
import ctypes

from .constants import (
    XINPUT_DLL_NAMES,
    XINPUT_ERROR_DEVICE_NOT_CONNECTED,
    XINPUT_ERROR_SUCCESS,
    EVENT_TYPES,
    WIN_KEYBOARD_CODES,
    WIN_MOUSE_CODES,
    MAC_EVENT_CODES,
    MAC_KEYS,
    EVENT_MAP,
    APPKIT_KB_PATH,
    QUARTZ_MOUSE_PATH,
    APPKIT_MOUSE_PATH,
)

__version__ = "0.6"


WIN = True if platform.system() == "Windows" else False
MAC = True if platform.system() == "Darwin" else False
NIX = True if platform.system() == "Linux" else False

if WIN:
    # pylint: disable=wrong-import-position
    import ctypes.wintypes

    DWORD = ctypes.wintypes.DWORD
    HANDLE = ctypes.wintypes.HANDLE
    WPARAM = ctypes.wintypes.WPARAM
    LPARAM = ctypes.wintypes.WPARAM
    MSG = ctypes.wintypes.MSG
else:
    DWORD = ctypes.c_ulong
    HANDLE = ctypes.c_void_p
    WPARAM = ctypes.c_ulonglong
    LPARAM = ctypes.c_ulonglong
    MSG = ctypes.Structure

if NIX:
    from fcntl import ioctl

OLD = sys.version_info < (3, 4)

PERMISSIONS_ERROR_TEXT = (
    "The user (that this program is being run as) does "
    "not have permission to access the input events, "
    "check groups and permissions, for example, on "
    "Debian, the user needs to be in the input group."
)

# Standard event format for most devices.
# long, long, unsigned short, unsigned short, int
EVENT_FORMAT = str("llHHi")

EVENT_SIZE = struct.calcsize(EVENT_FORMAT)


def chunks(raw):
    """Yield successive EVENT_SIZE sized chunks from raw."""
    for i in range(0, len(raw), EVENT_SIZE):
        yield struct.unpack(EVENT_FORMAT, raw[i : i + EVENT_SIZE])


if OLD:

    def iter_unpack(raw):
        """Yield successive EVENT_SIZE chunks from message."""
        return chunks(raw)

else:

    def iter_unpack(raw):
        """Yield successive EVENT_SIZE chunks from message."""
        return struct.iter_unpack(EVENT_FORMAT, raw)


def convert_timeval(seconds_since_epoch):
    """Convert time into C style timeval."""
    frac, whole = math.modf(seconds_since_epoch)
    microseconds = math.floor(frac * 1000000)
    seconds = math.floor(whole)
    return seconds, microseconds


# Now comes all the structs we need to parse the infomation coming
# from Windows.


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


class XinputGamepad(ctypes.Structure):
    """Describes the current state of the Xbox 360 Controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_gamepad%28v=vs.85%29.aspx

    """

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("buttons", ctypes.c_ushort),  # wButtons
        ("left_trigger", ctypes.c_ubyte),  # bLeftTrigger
        ("right_trigger", ctypes.c_ubyte),  # bLeftTrigger
        ("l_thumb_x", ctypes.c_short),  # sThumbLX
        ("l_thumb_y", ctypes.c_short),  # sThumbLY
        ("r_thumb_x", ctypes.c_short),  # sThumbRx
        ("r_thumb_y", ctypes.c_short),  # sThumbRy
    ]


class XinputState(ctypes.Structure):
    """Represents the state of a controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_state%28v=vs.85%29.aspx

    """

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("packet_number", ctypes.c_ulong),  # dwPacketNumber
        ("gamepad", XinputGamepad),  # Gamepad
    ]


class XinputVibration(ctypes.Structure):
    """Specifies motor speed levels for the vibration function of a
    controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_vibration%28v=vs.85%29.aspx

    """

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort),
    ]


if sys.version_info.major == 2:
    # pylint: disable=redefined-builtin
    class PermissionError(IOError):
        """Raised when trying to run an operation without the adequate access
        rights - for example filesystem permissions. Corresponds to errno
        EACCES and EPERM."""


class UnpluggedError(RuntimeError):
    """The device requested is not plugged in."""

    pass


class NoDevicePath(RuntimeError):
    """No evdev device path was given."""

    pass


class UnknownEventType(IndexError):
    """We don't know what this event is."""

    pass


class UnknownEventCode(IndexError):
    """We don't know what this event is."""

    pass


class InputEvent(object):  # pylint: disable=useless-object-inheritance
    """A user event."""

    # pylint: disable=too-few-public-methods
    def __init__(self, device, event_info):
        self.device = device
        self.timestamp = event_info["timestamp"]
        self.code = event_info["code"]
        self.state = event_info["state"]
        self.ev_type = event_info["ev_type"]


class BaseListener(object):  # pylint: disable=useless-object-inheritance
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


def keyboard_process(pipe):
    """Single subprocess for reading keyboard events on Windows."""
    keyboard = WindowsKeyboardListener(pipe)
    keyboard.listen()


class WindowsMouseListener(BaseListener):
    """Loosely emulate Evdev mouse behaviour on Windows.  Listen (hook
    in Windows terminology) for key events then buffer them in a pipe.
    """

    def __init__(self, pipe):
        self.pipe = pipe
        self.hooked = None
        self.pointer = None
        self.mouse_codes = WIN_MOUSE_CODES
        super(WindowsMouseListener, self).__init__(pipe)

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


def mouse_process(pipe):
    """Single subprocess for reading mouse events on Windows."""
    mouse = WindowsMouseListener(pipe)
    mouse.listen()


class QuartzMouseBaseListener(BaseListener):
    """Emulate evdev mouse behaviour on mac."""

    def __init__(self, pipe):
        super(QuartzMouseBaseListener, self).__init__(pipe, codes=dict(MAC_EVENT_CODES))
        self.active = True
        self.events = []

    def _get_mouse_button_number(self, event):
        """Get the mouse button number from an event."""
        raise NotImplementedError

    def _get_click_state(self, event):
        """The click state from an event."""
        raise NotImplementedError

    def _get_scroll(self, event):
        """The scroll values from an event."""
        raise NotImplementedError

    def _get_absolute(self, event):
        """Get abolute cursor location."""
        raise NotImplementedError

    def _get_relative(self, event):
        """Get the relative mouse movement."""
        raise NotImplementedError

    def handle_button(self, event, event_type):
        """Convert the button information from quartz into evdev format."""
        # 0 for left
        # 1 for right
        # 2 for middle/center
        # 3 for side
        mouse_button_number = self._get_mouse_button_number(event)

        # Identify buttons 3,4,5
        if event_type in (25, 26):
            event_type = event_type + (mouse_button_number * 0.1)

        # Add buttons to events
        event_type_string, event_code, value, scan = self.codes[event_type]
        if event_type_string == "Key":
            scan_event, key_event = self.emulate_press(
                event_code, scan, value, self.timeval
            )
            self.events.append(scan_event)
            self.events.append(key_event)

        # doubleclick/n-click of button
        click_state = self._get_click_state(event)

        repeat = self.emulate_repeat(click_state, self.timeval)
        self.events.append(repeat)

    def handle_scrollwheel(self, event):
        """Handle the scrollwheel (it is a ball on the mighty mouse)."""
        # relative Scrollwheel
        scroll_x, scroll_y = self._get_scroll(event)

        if scroll_x:
            self.events.append(self.emulate_wheel(scroll_x, "x", self.timeval))

        if scroll_y:
            self.events.append(self.emulate_wheel(scroll_y, "y", self.timeval))

    def handle_absolute(self, event):
        """Absolute mouse position on the screen."""
        (x_val, y_val) = self._get_absolute(event)
        x_event, y_event = self.emulate_abs(int(x_val), int(y_val), self.timeval)
        self.events.append(x_event)
        self.events.append(y_event)

    def handle_relative(self, event):
        """Relative mouse movement."""
        delta_x, delta_y = self._get_relative(event)
        if delta_x:
            self.events.append(self.emulate_rel(0x00, delta_x, self.timeval))
        if delta_y:
            self.events.append(self.emulate_rel(0x01, delta_y, self.timeval))

    # pylint: disable=unused-argument
    def handle_input(self, proxy, event_type, event, refcon):
        """Handle an input event."""
        self.update_timeval()
        self.events = []

        if event_type in (1, 2, 3, 4, 25, 26, 27):
            self.handle_button(event, event_type)

        if event_type == 22:
            self.handle_scrollwheel(event)

        # Add in the absolute position of the mouse cursor
        self.handle_absolute(event)

        # Add in the relative position of the mouse cursor
        self.handle_relative(event)

        # End with a sync marker
        self.events.append(self.sync_marker(self.timeval))

        # We are done
        self.write_to_pipe(self.events)


def quartz_mouse_process(pipe):
    """Single subprocess for reading mouse events on Mac using newer Quartz."""
    # Quartz only on the mac, so don't warn about Quartz
    # pylint: disable=import-error
    import Quartz

    # pylint: disable=no-member

    class QuartzMouseListener(QuartzMouseBaseListener):
        """Loosely emulate Evdev mouse behaviour on the Macs.
        Listen for key events then buffer them in a pipe.
        """

        def install_handle_input(self):
            """Constants below listed at:
            https://developer.apple.com/documentation/coregraphics/
            cgeventtype?language=objc#topics
            """
            # Keep Mac Names to make it easy to find the documentation
            # pylint: disable=invalid-name

            NSMachPort = Quartz.CGEventTapCreate(
                Quartz.kCGSessionEventTap,
                Quartz.kCGHeadInsertEventTap,
                Quartz.kCGEventTapOptionDefault,
                Quartz.CGEventMaskBit(Quartz.kCGEventLeftMouseDown)
                | Quartz.CGEventMaskBit(Quartz.kCGEventLeftMouseUp)
                | Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseDown)
                | Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseUp)
                | Quartz.CGEventMaskBit(Quartz.kCGEventMouseMoved)
                | Quartz.CGEventMaskBit(Quartz.kCGEventLeftMouseDragged)
                | Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseDragged)
                | Quartz.CGEventMaskBit(Quartz.kCGEventScrollWheel)
                | Quartz.CGEventMaskBit(Quartz.kCGEventTabletPointer)
                | Quartz.CGEventMaskBit(Quartz.kCGEventTabletProximity)
                | Quartz.CGEventMaskBit(Quartz.kCGEventOtherMouseDown)
                | Quartz.CGEventMaskBit(Quartz.kCGEventOtherMouseUp)
                | Quartz.CGEventMaskBit(Quartz.kCGEventOtherMouseDragged),
                self.handle_input,
                None,
            )

            CFRunLoopSourceRef = Quartz.CFMachPortCreateRunLoopSource(
                None, NSMachPort, 0
            )
            CFRunLoopRef = Quartz.CFRunLoopGetCurrent()
            Quartz.CFRunLoopAddSource(
                CFRunLoopRef, CFRunLoopSourceRef, Quartz.kCFRunLoopDefaultMode
            )
            Quartz.CGEventTapEnable(NSMachPort, True)

        def listen(self):
            """Listen for quartz events."""
            while self.active:
                Quartz.CFRunLoopRunInMode(Quartz.kCFRunLoopDefaultMode, 5, False)

        def uninstall_handle_input(self):
            self.active = False

        def _get_mouse_button_number(self, event):
            """Get the mouse button number from an event."""
            return Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGMouseEventButtonNumber
            )

        def _get_click_state(self, event):
            """The click state from an event."""
            return Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGMouseEventClickState
            )

        def _get_scroll(self, event):
            """The scroll values from an event."""
            scroll_y = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGScrollWheelEventDeltaAxis1
            )
            scroll_x = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGScrollWheelEventDeltaAxis2
            )
            return scroll_x, scroll_y

        def _get_absolute(self, event):
            """Get abolute cursor location."""
            return Quartz.CGEventGetLocation(event)

        def _get_relative(self, event):
            """Get the relative mouse movement."""
            delta_x = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGMouseEventDeltaX
            )
            delta_y = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGMouseEventDeltaY
            )
            return delta_x, delta_y

    mouse = QuartzMouseListener(pipe)
    mouse.listen()


class AppKitMouseBaseListener(BaseListener):
    """Emulate evdev behaviour on the the Mac."""

    def __init__(self, pipe, events=None):
        super(AppKitMouseBaseListener, self).__init__(
            pipe, events, codes=dict(MAC_EVENT_CODES)
        )

    @staticmethod
    def _get_mouse_button_number(event):
        """Get the button number."""
        return event.buttonNumber()

    @staticmethod
    def _get_absolute(event):
        """Get the absolute (pixel) location of the mouse cursor."""
        return event.locationInWindow()

    @staticmethod
    def _get_event_type(event):
        """Get the appkit event type of the event."""
        return event.type()

    @staticmethod
    def _get_deltas(event):
        """Get the changes from the appkit event."""
        delta_x = round(event.deltaX())
        delta_y = round(event.deltaY())
        delta_z = round(event.deltaZ())
        return delta_x, delta_y, delta_z

    def handle_button(self, event, event_type):
        """Handle mouse click."""
        mouse_button_number = self._get_mouse_button_number(event)
        # Identify buttons 3,4,5
        if event_type in (25, 26):
            event_type = event_type + (mouse_button_number * 0.1)
        # Add buttons to events
        event_type_name, event_code, value, scan = self.codes[event_type]
        if event_type_name == "Key":
            scan_event, key_event = self.emulate_press(
                event_code, scan, value, self.timeval
            )
            self.events.append(scan_event)
            self.events.append(key_event)

    def handle_absolute(self, event):
        """Absolute mouse position on the screen."""
        point = self._get_absolute(event)
        x_pos = round(point.x)
        y_pos = round(point.y)
        x_event, y_event = self.emulate_abs(x_pos, y_pos, self.timeval)
        self.events.append(x_event)
        self.events.append(y_event)

    def handle_scrollwheel(self, event):
        """Make endev from appkit scroll wheel event."""
        delta_x, delta_y, delta_z = self._get_deltas(event)
        if delta_x:
            self.events.append(self.emulate_wheel(delta_x, "x", self.timeval))
        if delta_y:
            self.events.append(self.emulate_wheel(delta_y, "y", self.timeval))
        if delta_z:
            self.events.append(self.emulate_wheel(delta_z, "z", self.timeval))

    def handle_relative(self, event):
        """Get the position of the mouse on the screen."""
        delta_x, delta_y, delta_z = self._get_deltas(event)
        if delta_x:
            self.events.append(self.emulate_rel(0x00, delta_x, self.timeval))
        if delta_y:
            self.events.append(self.emulate_rel(0x01, delta_y, self.timeval))
        if delta_z:
            self.events.append(self.emulate_rel(0x02, delta_z, self.timeval))

    def handle_input(self, event):
        """Process the mouse event."""
        self.update_timeval()
        self.events = []
        code = self._get_event_type(event)

        # Deal with buttons
        self.handle_button(event, code)

        # Mouse wheel
        if code == 22:
            self.handle_scrollwheel(event)
        # Other relative mouse movements
        else:
            self.handle_relative(event)

        # Add in the absolute position of the mouse cursor
        self.handle_absolute(event)

        # End with a sync marker
        self.events.append(self.sync_marker(self.timeval))

        # We are done
        self.write_to_pipe(self.events)


def appkit_mouse_process(pipe):
    """Single subprocess for reading mouse events on Mac using older AppKit."""
    # pylint: disable=import-error,too-many-locals

    # Note Objective C does not support a Unix style fork.
    # So these imports have to be inside the child subprocess since
    # otherwise the child process cannot use them.

    # pylint: disable=no-member, no-name-in-module
    from Foundation import NSObject
    from AppKit import NSApplication, NSApp
    from Cocoa import (
        NSEvent,
        NSLeftMouseDownMask,
        NSLeftMouseUpMask,
        NSRightMouseDownMask,
        NSRightMouseUpMask,
        NSMouseMovedMask,
        NSLeftMouseDraggedMask,
        NSRightMouseDraggedMask,
        NSMouseEnteredMask,
        NSMouseExitedMask,
        NSScrollWheelMask,
        NSOtherMouseDownMask,
        NSOtherMouseUpMask,
    )
    from PyObjCTools import AppHelper
    import objc

    class MacMouseSetup(NSObject):
        """Setup the handler."""

        @objc.python_method
        def init_with_handler(self, handler):
            """
            Init method that receives the write end of the pipe.
            """
            # ALWAYS call the super's designated initializer.
            # Also, make sure to re-bind "self" just in case it
            # returns something else!
            # pylint: disable=self-cls-assignment
            self = super(MacMouseSetup, self).init()
            self.handler = handler
            # Unlike Python's __init__, initializers MUST return self,
            # because they are allowed to return any object!
            return self

        # pylint: disable=invalid-name, unused-argument
        def applicationDidFinishLaunching_(self, notification):
            """Bind the listen method as the handler for mouse events."""

            mask = (
                NSLeftMouseDownMask
                | NSLeftMouseUpMask
                | NSRightMouseDownMask
                | NSRightMouseUpMask
                | NSMouseMovedMask
                | NSLeftMouseDraggedMask
                | NSRightMouseDraggedMask
                | NSScrollWheelMask
                | NSMouseEnteredMask
                | NSMouseExitedMask
                | NSOtherMouseDownMask
                | NSOtherMouseUpMask
            )
            NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask, self.handler)

    class MacMouseListener(AppKitMouseBaseListener):
        """Loosely emulate Evdev mouse behaviour on the Macs.
        Listen for key events then buffer them in a pipe.
        """

        def install_handle_input(self):
            """Install the hook."""
            self.app = NSApplication.sharedApplication()
            # pylint: disable=no-member
            delegate = MacMouseSetup.alloc().init_with_handler(self.handle_input)
            NSApp().setDelegate_(delegate)
            AppHelper.runEventLoop()

        def __del__(self):
            """Stop the listener on deletion."""
            AppHelper.stopEventLoop()

    # pylint: disable=unused-variable
    mouse = MacMouseListener(pipe, events=[])


class AppKitKeyboardListener(BaseListener):
    """Emulate an evdev keyboard on the Mac."""

    def __init__(self, pipe):
        super(AppKitKeyboardListener, self).__init__(pipe, codes=dict(MAC_KEYS))

    @staticmethod
    def _get_event_key_code(event):
        """Get the key code."""
        return event.keyCode()

    @staticmethod
    def _get_event_type(event):
        """Get the event type."""
        return event.type()

    @staticmethod
    def _get_flag_value(event):
        """Note, this may be able to be made more accurate,
        i.e. handle two modifier keys at once."""
        flags = event.modifierFlags()
        if flags == 0x100:
            value = 0
        else:
            value = 1
        return value

    def _get_key_value(self, event, event_type):
        """Get the key value."""
        if event_type == 10:
            value = 1
        elif event_type == 11:
            value = 0
        elif event_type == 12:
            value = self._get_flag_value(event)
        else:
            value = -1
        return value

    def handle_input(self, event):
        """Process they keyboard input."""
        self.update_timeval()
        self.events = []
        code = self._get_event_key_code(event)

        if code in self.codes:
            new_code = self.codes[code]
        else:
            new_code = 0
        event_type = self._get_event_type(event)
        value = self._get_key_value(event, event_type)
        scan_event, key_event = self.emulate_press(new_code, code, value, self.timeval)

        self.events.append(scan_event)
        self.events.append(key_event)
        # End with a sync marker
        self.events.append(self.sync_marker(self.timeval))
        # We are done
        self.write_to_pipe(self.events)


def mac_keyboard_process(pipe):
    """Single subprocesses for reading keyboard on Mac."""
    # pylint: disable=import-error,too-many-locals
    # Note Objective C does not support a Unix style fork.
    # So these imports have to be inside the child subprocess since
    # otherwise the child process cannot use them.

    # pylint: disable=no-member, no-name-in-module
    from AppKit import NSApplication, NSApp
    from Foundation import NSObject
    from Cocoa import NSEvent, NSKeyDownMask, NSKeyUpMask, NSFlagsChangedMask
    from PyObjCTools import AppHelper
    import objc

    class MacKeyboardSetup(NSObject):
        """Setup the handler."""

        @objc.python_method
        def init_with_handler(self, handler):
            """
            Init method that receives the write end of the pipe.
            """
            # ALWAYS call the super's designated initializer.
            # Also, make sure to re-bind "self" just in case it
            # returns something else!

            # pylint: disable=self-cls-assignment
            self = super(MacKeyboardSetup, self).init()

            self.handler = handler

            # Unlike Python's __init__, initializers MUST return self,
            # because they are allowed to return any object!
            return self

        # pylint: disable=invalid-name, unused-argument
        def applicationDidFinishLaunching_(self, notification):
            """Bind the handler to listen to keyboard events."""
            mask = NSKeyDownMask | NSKeyUpMask | NSFlagsChangedMask
            NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask, self.handler)

    class MacKeyboardListener(AppKitKeyboardListener):
        """Loosely emulate Evdev keyboard behaviour on the Mac.
        Listen for key events then buffer them in a pipe.
        """

        def install_handle_input(self):
            """Install the hook."""
            self.app = NSApplication.sharedApplication()
            # pylint: disable=no-member
            delegate = MacKeyboardSetup.alloc().init_with_handler(self.handle_input)
            NSApp().setDelegate_(delegate)
            AppHelper.runEventLoop()

        def __del__(self):
            """Stop the listener on deletion."""
            AppHelper.stopEventLoop()

    # pylint: disable=unused-variable
    keyboard = MacKeyboardListener(pipe)


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


def delay_and_stop(duration, dll, device_number):
    """Stop vibration aka force feedback aka rumble on
    Windows after duration miliseconds."""
    xinput = getattr(ctypes.windll, dll)
    time.sleep(duration / 1000)
    xinput_set_state = xinput.XInputSetState
    xinput_set_state.argtypes = [ctypes.c_uint, ctypes.POINTER(XinputVibration)]
    xinput_set_state.restype = ctypes.c_uint
    vibration = XinputVibration(0, 0)
    xinput_set_state(device_number, ctypes.byref(vibration))


# I made this GamePad class before Mouse and Keyboard above, and have
# learned a lot about Windows in the process.  This can probably be
# simplified massively and made to match Mouse and Keyboard more.


class GamePad(InputDevice):
    """A gamepad or other joystick-like device."""

    def __init__(self, manager, device_path, char_path_override=None):
        super(GamePad, self).__init__(manager, device_path, char_path_override)
        self._write_file = None
        self.__device_number = None
        if WIN:
            if "Microsoft_Corporation_Controller" in self._device_path:
                self.name = "Microsoft X-Box 360 pad"
                identifier = self._get_path_infomation()[1]
                self.__device_number = int(identifier.split("_")[-1])
                self.__received_packets = 0
                self.__missed_packets = 0
                self.__last_state = self.__read_device()
        if NIX:
            self._number_xpad()

    def _number_xpad(self):
        """Get the number of the joystick."""
        js_path = self._device_path.replace("-event", "")
        js_chardev = os.path.realpath(js_path)
        try:
            number_text = js_chardev.split("js")[1]
        except IndexError:
            return
        try:
            number = int(number_text)
        except ValueError:
            return
        self.__device_number = number

    def get_number(self):
        """Return the joystick number of the gamepad."""
        return self.__device_number

    def __iter__(self):
        while True:
            if WIN:
                self.__check_state()
            event = self._do_iter()
            if event:
                yield event

    def __check_state(self):
        """On Windows, check the state and fill the event character device."""
        state = self.__read_device()
        if not state:
            raise UnpluggedError("Gamepad %d is not connected" % self.__device_number)
        if state.packet_number != self.__last_state.packet_number:
            # state has changed, handle the change
            self.__handle_changed_state(state)
            self.__last_state = state

    @staticmethod
    def __get_timeval():
        """Get the time and make it into C style timeval."""
        return convert_timeval(time.time())

    def create_event_object(self, event_type, code, value, timeval=None):
        """Create an evdev style object."""
        if not timeval:
            timeval = self.__get_timeval()
        try:
            event_code = self.manager.codes["type_codes"][event_type]
        except KeyError:
            raise UnknownEventType(
                "We don't know what kind of event a %s is." % event_type
            )
        event = struct.pack(
            EVENT_FORMAT, timeval[0], timeval[1], event_code, code, value
        )
        return event

    def __write_to_character_device(self, event_list, timeval=None):
        """Emulate the Linux character device on other platforms such as
        Windows."""
        # Remember the position of the stream
        pos = self._character_device.tell()
        # Go to the end of the stream
        self._character_device.seek(0, 2)
        # Write the new data to the end
        for event in event_list:
            self._character_device.write(event)
        # Add a sync marker
        sync = self.create_event_object("Sync", 0, 0, timeval)
        self._character_device.write(sync)
        # Put the stream back to its original position
        self._character_device.seek(pos)

    def __handle_changed_state(self, state):
        """
        we need to pack a struct with the following five numbers:
        tv_sec, tv_usec, ev_type, code, value

        then write it using __write_to_character_device

        seconds, mircroseconds, ev_type, code, value
        time we just use now
        ev_type we look up
        code we look up
        value is 0 or 1 for the buttons
        axis value is maybe the same as Linux? Hope so!
        """
        timeval = self.__get_timeval()
        events = self.__get_button_events(state, timeval)
        events.extend(self.__get_axis_events(state, timeval))
        if events:
            self.__write_to_character_device(events, timeval)

    def __map_button(self, button):
        """Get the linux xpad code from the Windows xinput code."""
        _, start_code, start_value = button
        value = start_value
        ev_type = "Key"
        code = self.manager.codes["xpad"][start_code]
        if 1 <= start_code <= 4:
            ev_type = "Absolute"
        if start_code == 1 and start_value == 1:
            value = -1
        elif start_code == 3 and start_value == 1:
            value = -1
        return code, value, ev_type

    def __map_axis(self, axis):
        """Get the linux xpad code from the Windows xinput code."""
        start_code, start_value = axis
        value = start_value
        code = self.manager.codes["xpad"][start_code]
        return code, value

    def __get_button_events(self, state, timeval=None):
        """Get the button events from xinput."""
        changed_buttons = self.__detect_button_events(state)
        events = self.__emulate_buttons(changed_buttons, timeval)
        return events

    def __get_axis_events(self, state, timeval=None):
        """Get the stick events from xinput."""
        axis_changes = self.__detect_axis_events(state)
        events = self.__emulate_axis(axis_changes, timeval)
        return events

    def __emulate_axis(self, axis_changes, timeval=None):
        """Make the axis events use the Linux style format."""
        events = []
        for axis in axis_changes:
            code, value = self.__map_axis(axis)
            event = self.create_event_object("Absolute", code, value, timeval=timeval)
            events.append(event)
        return events

    def __emulate_buttons(self, changed_buttons, timeval=None):
        """Make the button events use the Linux style format."""
        events = []
        for button in changed_buttons:
            code, value, ev_type = self.__map_button(button)
            event = self.create_event_object(ev_type, code, value, timeval=timeval)
            events.append(event)
        return events

    @staticmethod
    def __gen_bit_values(number):
        """
        Return a zero or one for each bit of a numeric value up to the most
        significant 1 bit, beginning with the least significant bit.
        """
        number = int(number)
        while number:
            yield number & 0x1
            number >>= 1

    def __get_bit_values(self, number, size=32):
        """Get bit values as a list for a given number

        >>> get_bit_values(1) == [0]*31 + [1]
        True

        >>> get_bit_values(0xDEADBEEF)
        [1L, 1L, 0L, 1L, 1L, 1L, 1L,
        0L, 1L, 0L, 1L, 0L, 1L, 1L, 0L, 1L, 1L, 0L, 1L, 1L, 1L, 1L,
        1L, 0L, 1L, 1L, 1L, 0L, 1L, 1L, 1L, 1L]

        You may override the default word size of 32-bits to match your actual
        application.
        >>> get_bit_values(0x3, 2)
        [1L, 1L]

        >>> get_bit_values(0x3, 4)
        [0L, 0L, 1L, 1L]

        """
        res = list(self.__gen_bit_values(number))
        res.reverse()
        # 0-pad the most significant bit
        res = [0] * (size - len(res)) + res
        return res

    def __detect_button_events(self, state):
        changed = state.gamepad.buttons ^ self.__last_state.gamepad.buttons
        changed = self.__get_bit_values(changed, 16)
        buttons_state = self.__get_bit_values(state.gamepad.buttons, 16)
        changed.reverse()
        buttons_state.reverse()
        button_numbers = count(1)
        changed_buttons = list(
            filter(itemgetter(0), list(zip(changed, button_numbers, buttons_state)))
        )
        # returns for example [(1,15,1)] type, code, value?
        return changed_buttons

    def __detect_axis_events(self, state):
        # axis fields are everything but the buttons
        # pylint: disable=protected-access
        # Attribute name _fields_ is special name set by ctypes
        axis_fields = dict(XinputGamepad._fields_)
        axis_fields.pop("buttons")
        changed_axes = []

        # Ax_type might be useful when we support high-level deadzone
        # methods.
        # pylint: disable=unused-variable
        for axis, ax_type in list(axis_fields.items()):
            old_val = getattr(self.__last_state.gamepad, axis)
            new_val = getattr(state.gamepad, axis)
            if old_val != new_val:
                changed_axes.append((axis, new_val))
        return changed_axes

    def __read_device(self):
        """Read the state of the gamepad."""
        state = XinputState()
        res = self.manager.xinput.XInputGetState(
            self.__device_number, ctypes.byref(state)
        )
        if res == XINPUT_ERROR_SUCCESS:
            return state
        if res != XINPUT_ERROR_DEVICE_NOT_CONNECTED:
            raise RuntimeError(
                "Unknown error %d attempting to get state of device %d"
                % (res, self.__device_number)
            )
        # else (device is not connected)
        return None

    @property
    def _write_device(self):
        if not self._write_file:
            if not NIX:
                return None
            try:
                self._write_file = io.open(self._character_device_path, "wb")
            except PermissionError:
                # Python 3
                raise PermissionError(PERMISSIONS_ERROR_TEXT)
            except IOError as err:
                # Python 2
                if err.errno == 13:
                    raise PermissionError(PERMISSIONS_ERROR_TEXT)
                else:
                    raise

        return self._write_file

    def _start_vibration_win(self, left_motor, right_motor):
        """Start the vibration, which will run until stopped."""
        xinput_set_state = self.manager.xinput.XInputSetState
        xinput_set_state.argtypes = [ctypes.c_uint, ctypes.POINTER(XinputVibration)]
        xinput_set_state.restype = ctypes.c_uint
        vibration = XinputVibration(int(left_motor * 65535), int(right_motor * 65535))
        xinput_set_state(self.__device_number, ctypes.byref(vibration))

    def _stop_vibration_win(self):
        """Stop the vibration."""
        xinput_set_state = self.manager.xinput.XInputSetState
        xinput_set_state.argtypes = [ctypes.c_uint, ctypes.POINTER(XinputVibration)]
        xinput_set_state.restype = ctypes.c_uint
        stop_vibration = ctypes.byref(XinputVibration(0, 0))
        xinput_set_state(self.__device_number, stop_vibration)

    def _set_vibration_win(self, left_motor, right_motor, duration):
        """Control the motors on Windows."""
        self._start_vibration_win(left_motor, right_motor)
        stop_process = Process(
            target=delay_and_stop,
            args=(duration, self.manager.xinput_dll, self.__device_number),
        )
        stop_process.start()

    def __get_vibration_code(self, left_motor, right_motor, duration):
        """This is some crazy voodoo, if you can simplify it, please do."""
        inner_event = struct.pack(
            "2h6x2h2x2H28x",
            0x50,
            -1,
            duration,
            0,
            int(left_motor * 65535),
            int(right_motor * 65535),
        )
        buf_conts = ioctl(self._write_device, 1076905344, inner_event)
        return int(codecs.encode(buf_conts[1:3], "hex"), 16)

    def _set_vibration_nix(self, left_motor, right_motor, duration):
        """Control the motors on Linux.
        Duration is in miliseconds."""
        code = self.__get_vibration_code(left_motor, right_motor, duration)
        secs, msecs = convert_timeval(time.time())
        outer_event = struct.pack(EVENT_FORMAT, secs, msecs, 0x15, code, 1)
        self._write_device.write(outer_event)
        self._write_device.flush()

    def set_vibration(self, left_motor, right_motor, duration):
        """Control the speed of both motors seperately or together.
        left_motor and right_motor arguments require a number between
        0 (off) and 1 (full).
        duration is miliseconds, e.g. 1000 for a second."""
        if WIN:
            self._set_vibration_win(left_motor, right_motor, duration)
        elif NIX:
            self._set_vibration_nix(left_motor, right_motor, duration)
        else:
            raise NotImplementedError


class OtherDevice(InputDevice):
    """A device of which its is type is either undetectable or has not
    been implemented yet.
    """

    pass


class LED(object):  # pylint: disable=useless-object-inheritance
    """A light source."""

    def __init__(self, manager, path, name):
        self.manager = manager
        self.path = path
        self.name = name
        self._write_file = None
        self._character_device_path = None
        self._post_init()

    def _post_init(self):
        """Post init setup."""
        pass

    def __str__(self):
        return self.name

    def __repr__(self):
        return '%s.%s("%s")' % (self.__module__, self.__class__.__name__, self.path)

    def status(self):
        """Get the device status, i.e. the brightness level."""
        status_filename = os.path.join(self.path, "brightness")
        with open(status_filename) as status_fp:
            result = status_fp.read()
        status_text = result.strip()
        try:
            status = int(status_text)
        except ValueError:
            return status_text
        return status

    def max_brightness(self):
        """Get the device's maximum brightness level."""
        status_filename = os.path.join(self.path, "max_brightness")
        with open(status_filename) as status_fp:
            result = status_fp.read()
        status_text = result.strip()
        try:
            status = int(status_text)
        except ValueError:
            return status_text
        return status

    @property
    def _write_device(self):
        """The output device."""
        if not self._write_file:
            if not NIX:
                return None
            try:
                self._write_file = io.open(self._character_device_path, "wb")
            except PermissionError:
                # Python 3
                raise PermissionError(PERMISSIONS_ERROR_TEXT)
            except IOError as err:
                # Python 2 only
                if err.errno == 13:  # pragma: no cover
                    raise PermissionError(PERMISSIONS_ERROR_TEXT)
                else:
                    raise

        return self._write_file

    def _make_event(self, event_type, code, value):
        """Make a new event and send it to the character device."""
        secs, msecs = convert_timeval(time.time())
        data = struct.pack(EVENT_FORMAT, secs, msecs, event_type, code, value)
        self._write_device.write(data)
        self._write_device.flush()


class SystemLED(LED):
    """An LED on your system e.g. caps lock."""

    def __init__(self, manager, path, name):
        self.code = None
        self.device_path = None
        self.device = None
        super(SystemLED, self).__init__(manager, path, name)

    def _post_init(self):
        """Set up the device path and type code."""
        self._led_type_code = self.manager.get_typecode("LED")
        self.device_path = os.path.realpath(os.path.join(self.path, "device"))
        if "::" in self.name:
            chardev, code_name = self.name.split("::")
            if code_name in self.manager.codes["LED_type_codes"]:
                self.code = self.manager.codes["LED_type_codes"][code_name]
            try:
                event_number = chardev.split("input")[1]
            except IndexError:
                print("Failed with", self.name)
                raise
            else:
                self._character_device_path = "/dev/input/event" + event_number
                self._match_device()

    def on(self):  # pylint: disable=invalid-name
        """Turn the light on."""
        self._make_event(1)

    def off(self):
        """Turn the light off."""
        self._make_event(0)

    def _make_event(self, value):  # pylint: disable=arguments-differ
        """Make a new event and send it to the character device."""
        super(SystemLED, self)._make_event(self._led_type_code, self.code, value)

    def _match_device(self):
        """If the LED is connected to an input device,
        associate the objects."""
        for device in self.manager.all_devices:
            if device.get_char_device_path() == self._character_device_path:
                self.device = device
                device.leds.append(self)
                break


class GamepadLED(LED):
    """A light source on a gamepad."""

    def __init__(self, manager, path, name):
        self.code = None
        self.device = None
        self.gamepad = None
        super(GamepadLED, self).__init__(manager, path, name)

    def _post_init(self):
        self._match_device()
        self._character_device_path = self.gamepad.get_char_device_path()

    def _match_device(self):
        number = int(self.name.split("xpad")[1])
        for gamepad in self.manager.gamepads:
            if number == gamepad.get_number():
                self.gamepad = gamepad
                gamepad.leds.append(self)
                break


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


SPIN_UP_MOTOR = (
    "00000",
    "00001",
    "00011",
    "00111",
    "01111",
    "11111",
    "01111",
    "00011",
    "00001",
    "00000",
    "00001",
    "00011",
    "00111",
    "01111",
    "11111",
    "00000",
    "11111",
    "00000",
    "11111",
    "00000",
)


class MicroBitPad(GamePad):
    """A BBC Micro:bit flashed with bitio."""

    def __init__(self, manager, device_path=None, char_path_override=None):
        if not device_path:
            device_path = "/dev/input/by-id/dialup-BBC_MicroBit-event-joystick"
            if not char_path_override:
                char_path_override = "/dev/input/microbit0"

        super(MicroBitPad, self).__init__(manager, device_path, char_path_override)

        # pylint: disable=no-member,import-error
        import microbit

        self.microbit = microbit
        self.default_image = microbit.Image("00500:00500:00500:00500:00500")
        self._setup_rumble()
        self.set_display()

    def set_display(self, index=None):
        """Show an image on the display."""
        # pylint: disable=no-member
        if index:
            image = self.microbit.Image.STD_IMAGES[index]
        else:
            image = self.default_image
        self.microbit.display.show(image)

    def _setup_rumble(self):
        """Setup the three animations which simulate a rumble."""
        self.left_rumble = self._get_ready_to("99500")
        self.right_rumble = self._get_ready_to("00599")
        self.double_rumble = self._get_ready_to("99599")

    def _set_name(self):
        self.name = "BBC microbit Gamepad"

    def _set_evdev_state(self):
        self._evdev = False

    @staticmethod
    def _get_target_function():
        return microbit_process

    def _get_data(self, read_size):
        """Get data from the character device."""
        return self._pipe.recv_bytes()

    def _get_ready_to(self, rumble):
        """Watch us wreck the mike!
        PSYCHE!"""
        # pylint: disable=no-member
        return [
            self.microbit.Image(
                ":".join([rumble if char == "1" else "00500" for char in code])
            )
            for code in SPIN_UP_MOTOR
        ]

    def _full_speed_rumble(self, images, duration):
        """Simulate the motors running at full."""
        while duration > 0:
            self.microbit.display.show(images[0])  # pylint: disable=no-member
            time.sleep(0.04)
            self.microbit.display.show(images[1])  # pylint: disable=no-member
            time.sleep(0.04)
            duration -= 0.08

    def _spin_up(self, images, duration):
        """Simulate the motors getting warmed up."""
        total = 0
        # pylint: disable=no-member

        for image in images:
            self.microbit.display.show(image)
            time.sleep(0.05)
            total += 0.05
            if total >= duration:
                return
        remaining = duration - total
        self._full_speed_rumble(images[-2:], remaining)
        self.set_display()

    def set_vibration(self, left_motor, right_motor, duration):
        """Control the speed of both motors seperately or together.
        left_motor and right_motor arguments require a number:
        0 (off) or 1 (full).
        duration is miliseconds, e.g. 1000 for a second."""
        if left_motor and right_motor:
            return self._spin_up(self.double_rumble, duration / 1000)
        if left_motor:
            return self._spin_up(self.left_rumble, duration / 1000)
        if right_motor:
            return self._spin_up(self.right_rumble, duration / 1000)
        return -1


def microbit_process(pipe):
    """Simple subprocess for reading mouse events on the microbit."""
    gamepad_listener = MicroBitListener(pipe)
    gamepad_listener.listen()


class MicroBitListener(BaseListener):
    """Tracks the current state and sends changes to the MicroBitPad
    device class."""

    def __init__(self, pipe):
        super(MicroBitListener, self).__init__(pipe)
        self.active = True
        self.events = []
        self.state = set(
            (
                ("Absolute", 0x10, 0),
                ("Absolute", 0x11, 0),
                ("Key", 0x130, 0),
                ("Key", 0x131, 0),
                ("Key", 0x13A, 0),
                ("Key", 0x133, 0),
                ("Key", 0x134, 0),
            )
        )
        self.dpad = True
        self.sensitivity = 300
        # pylint: disable=import-error
        import microbit

        self.microbit = microbit

    def listen(self):
        """Listen while the device is active."""
        while self.active:
            self.handle_input()

    def uninstall_handle_input(self):
        """Stop listing when active is false."""
        self.active = False

    def handle_new_events(self, events):
        """Add each new events to the event queue."""
        for event in events:
            self.events.append(
                self.create_event_object(event[0], event[1], int(event[2]))
            )

    def handle_abs(self):
        """Gets the state as the raw abolute numbers."""
        # pylint: disable=no-member
        x_raw = self.microbit.accelerometer.get_x()
        y_raw = self.microbit.accelerometer.get_y()
        x_abs = ("Absolute", 0x00, x_raw)
        y_abs = ("Absolute", 0x01, y_raw)
        return x_abs, y_abs

    def handle_dpad(self):
        """Gets the state of the virtual dpad."""
        # pylint: disable=no-member
        x_raw = self.microbit.accelerometer.get_x()
        y_raw = self.microbit.accelerometer.get_y()
        minus_sens = self.sensitivity * -1
        if x_raw < minus_sens:
            x_state = ("Absolute", 0x10, -1)
        elif x_raw > self.sensitivity:
            x_state = ("Absolute", 0x10, 1)
        else:
            x_state = ("Absolute", 0x10, 0)

        if y_raw < minus_sens:
            y_state = ("Absolute", 0x11, -1)
        elif y_raw > self.sensitivity:
            y_state = ("Absolute", 0x11, 1)
        else:
            y_state = ("Absolute", 0x11, 1)

        return x_state, y_state

    def check_state(self):
        """Tracks differences in the device state."""
        if self.dpad:
            x_state, y_state = self.handle_dpad()
        else:
            x_state, y_state = self.handle_abs()

        # pylint: disable=no-member
        new_state = set(
            (
                x_state,
                y_state,
                ("Key", 0x130, int(self.microbit.button_a.is_pressed())),
                ("Key", 0x131, int(self.microbit.button_b.is_pressed())),
                ("Key", 0x13A, int(self.microbit.pin0.is_touched())),
                ("Key", 0x133, int(self.microbit.pin1.is_touched())),
                ("Key", 0x134, int(self.microbit.pin2.is_touched())),
            )
        )
        events = new_state - self.state
        self.state = new_state
        return events

    def handle_input(self):
        """Sends differences in the device state to the MicroBitPad
        as events."""
        difference = self.check_state()
        if not difference:
            return
        self.events = []
        self.handle_new_events(difference)
        self.update_timeval()
        self.events.append(self.sync_marker(self.timeval))
        self.write_to_pipe(self.events)


devices = DeviceManager()  # pylint: disable=invalid-name


def get_key():
    """Get a single keypress from a keyboard."""
    try:
        keyboard = devices.keyboards[0]
    except IndexError:
        raise UnpluggedError("No keyboard found.")
    return keyboard.read()


def get_mouse():
    """Get a single movement or click from a mouse."""
    try:
        mouse = devices.mice[0]
    except IndexError:
        raise UnpluggedError("No mice found.")
    return mouse.read()


def get_gamepad():
    """Get a single action from a gamepad."""
    try:
        gamepad = devices.gamepads[0]
    except IndexError:
        raise UnpluggedError("No gamepad found.")
    return gamepad.read()
