"""Keep all the Mac keyboard wrapped so the Python coder doesn't have to care about Objective C."""

from ...constants import MAC_KEYS
from ...libi.baselistener import BaseListener


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
