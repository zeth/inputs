"""Keep all the Mac mouse wrapped so the Python coder doesn't have to care about Objective C."""

from ...constants import MAC_EVENT_CODES
from ...libi.baselistener import BaseListener


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
