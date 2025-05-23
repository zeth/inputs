from inputs.constants import MAC_EVENT_CODES, QUARTZ_MOUSE_PATH
from inputs.devices.mouse import Mouse
from inputs.platforms import MAC, BaseListener


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
