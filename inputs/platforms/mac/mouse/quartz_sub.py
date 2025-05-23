from inputs.platforms.mac.mouse.listener import QuartzMouseBaseListener

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
