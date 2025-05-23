from inputs.constants import MAC_EVENT_CODES
from inputs.platforms import BaseListener


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

