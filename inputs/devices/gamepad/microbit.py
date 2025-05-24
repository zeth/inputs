"""Use the MicroBit as an input device."""

import time

from ...libi.baselistener import BaseListener
from .gamepad import GamePad


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

        super().__init__(manager, device_path, char_path_override)
        self._import_microbit()
        self._setup_rumble()
        self.set_display()

    def _import_microbit(self):
        """Only require the microbit module to be installed if they have one."""
        try:
            # pylint: disable=import-outside-toplevel
            import microbit
        except ImportError as exc:
            raise ImportError(
                "The microbit module is not installed, please install it."
            ) from exc
        self.default_image = microbit.Image("00500:00500:00500:00500:00500")
        self.microbit = microbit

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
        super().__init__(pipe)
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
        # pylint: disable=import-outside-toplevel
        try:
            import microbit
        except ImportError as exc:
            raise ImportError(
                "The microbit module is not installed, please install it."
            ) from exc

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
