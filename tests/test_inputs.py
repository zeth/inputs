"""Tests for inputs module."""

# pylint: disable=protected-access,no-self-use
from unittest import TestCase

from inputs.libi.event import InputEvent
from inputs.libi.c import convert_timeval
from inputs.utils import get_key, get_mouse, get_gamepad
from inputs.libi.errors import UnpluggedError
from unittest import mock

RAW = ""

# Mocking adds an argument, whether we need it or not.
# pylint: disable=unused-argument


class InputEventTestCase(TestCase):
    """Test the InputEvent class."""

    def test_input_event_init(self):
        """Test that the input event sets the required properties."""
        event = InputEvent(
            "Some Device",
            {
                "ev_type": "Key",
                "state": 0,
                "timestamp": 1530900876.367757,
                "code": "KEY_ENTER",
            },
        )
        self.assertEqual(event.device, "Some Device")
        self.assertEqual(event.ev_type, "Key")
        self.assertEqual(event.state, 0)
        self.assertEqual(event.timestamp, 1530900876.367757)
        self.assertEqual(event.code, "KEY_ENTER")


class HelpersTestCase(TestCase):
    """Test the easy helper methods."""

    # pylint: disable=arguments-differ

    # There can never be too many tests.
    # pylint: disable=too-many-public-methods

    @mock.patch("inputs.utils.devices")
    def setUp(self, mock_devices):
        self.devices = mock_devices

    @mock.patch("inputs.utils.devices")
    def test_get_key(self, devices):
        """Get key reads from the first keyboard."""
        keyboard = mock.MagicMock()
        reader = mock.MagicMock()
        keyboard.read = reader
        devices.keyboards = [keyboard]

        get_key()

        reader.assert_called_once()

    @mock.patch("inputs.utils.devices")
    def test_get_key_index_error(self, devices):
        """Raises unpluggged error if no keyboard attached."""
        devices.keyboards = []
        with self.assertRaises(UnpluggedError):
            # pylint: disable=pointless-statement
            get_key()

    @mock.patch("inputs.utils.devices")
    def test_get_mouse(self, devices):
        """Get event reads from the first mouse."""
        mouse = mock.MagicMock()
        reader = mock.MagicMock()
        mouse.read = reader
        devices.mice = [mouse]

        get_mouse()

        reader.assert_called_once()

    @mock.patch("inputs.utils.devices")
    def test_get_mouse_index_error(self, devices):
        """Raises unpluggged error if no mouse attached."""
        devices.mice = []
        with self.assertRaises(UnpluggedError):
            # pylint: disable=pointless-statement
            get_mouse()

    @mock.patch("inputs.utils.devices")
    def test_get_gamepad(self, devices):
        """Get key reads from the first gamepad."""
        gamepad = mock.MagicMock()
        reader = mock.MagicMock()
        gamepad.read = reader
        devices.gamepads = [gamepad]

        get_gamepad()

        reader.assert_called_once()

    @mock.patch("inputs.utils.devices")
    def test_get_gamepad_index_error(self, devices):
        """Raises unpluggged error if no gamepad attached."""
        devices.gamepads = []
        with self.assertRaises(UnpluggedError):
            # pylint: disable=pointless-statement
            get_gamepad()


class ConvertTimevalTestCase(TestCase):
    """Test the easy helper methods."""

    # pylint: disable=arguments-differ
    def test_convert_timeval(self):
        """Gives particular seconds and microseconds."""
        self.assertEqual(convert_timeval(2000.0002), (2000, 199))
        self.assertEqual(convert_timeval(100.000002), (100, 1))
        self.assertEqual(convert_timeval(199.2), (199, 199999))
        self.assertEqual(convert_timeval(0), (0, 0))
        self.assertEqual(convert_timeval(100), (100, 0))
        self.assertEqual(convert_timeval(0.001), (0, 1000))
