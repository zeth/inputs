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
import io
import glob
import struct
import time
from warnings import warn
import ctypes

from .platforms.baselistener import BaseListener
from .devices.gamepad._win import XinputState
from .devices.device import InputDevice

from .constants import (
    XINPUT_DLL_NAMES,
    XINPUT_ERROR_DEVICE_NOT_CONNECTED,
    XINPUT_ERROR_SUCCESS,
    WIN_KEYBOARD_CODES,
    WIN_MOUSE_CODES,
    MAC_EVENT_CODES,
    MAC_KEYS,
    EVENT_MAP,
    APPKIT_KB_PATH,
    QUARTZ_MOUSE_PATH,
    APPKIT_MOUSE_PATH,
)

from .errors import (
    PERMISSIONS_ERROR_TEXT,
    UnknownEventType,
    UnknownEventCode
)

from .platforms.system import WIN, MAC, NIX
from .platforms.c import DWORD, HANDLE, WPARAM, LPARAM, MSG, EVENT_FORMAT, EVENT_SIZE, convert_timeval
from .devices.gamepad.gamepad import GamePad

__version__ = "0.6"


if NIX:
    from fcntl import ioctl



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


