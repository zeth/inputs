"""Tests for inputs module."""
# pylint: disable=protected-access
from unittest import TestCase, main

try:
    # Python 3
    from unittest import mock
except ImportError:
    # Python 2
    import mock


import ctypes

import inputs

RAW = ""


class RawInputDeviceListTestCase(TestCase):
    """Test the RawInputDeviceList class."""
    def test_raw_input_device_list_size(self):
        """Test that ctypes can use RawInputDeviceList."""
        self.assertEqual(
            ctypes.sizeof(inputs.RawInputDeviceList), 16)


class InputEventTestCase(TestCase):
    """Test the InputEvent class."""
    def test_input_event_init(self):
        """Test that the input event sets the required properties."""
        event = inputs.InputEvent(
            "Some Device",
            {'ev_type': 'Key',
             'state': 0,
             'timestamp': 1530900876.367757,
             'code': 'KEY_ENTER'})
        self.assertEqual(event.device, 'Some Device')
        self.assertEqual(event.ev_type, 'Key')
        self.assertEqual(event.state, 0)
        self.assertEqual(event.timestamp, 1530900876.367757)
        self.assertEqual(event.code, 'KEY_ENTER')


KEYBOARD_PATH = "/dev/input/by-path/my-lovely-keyboard-0-event-kbd"
MOUSE_PATH = "/dev/input/by-path/my-lovely-mouse-0-event-mouse"
GAMEPAD_PATH = "/dev/input/by-path/my-lovely-gamepad-0-event-joystick"
OTHER_PATH = "/dev/input/by-path/the-machine-that-goes-ping-other"


class DeviceManagePostrInitTestCase(TestCase):
    """Test the device manager class' post-init method."""

    @mock.patch.object(inputs.DeviceManager, '_find_devices')
    @mock.patch.object(inputs.DeviceManager, '_find_devices_mac')
    @mock.patch.object(inputs.DeviceManager, '_find_devices_win')
    @mock.patch.object(inputs.DeviceManager, '_update_all_devices')
    def test_post_init_linux(
            self,
            mock_update_all_devices,
            mock_find_devices_win,
            mock_find_devices_mac,
            mock_find_devices):
        """On Linux, find_devices is called and the other methods are not."""
        inputs.WIN = False
        inputs.MAC = False
        device_manger = inputs.DeviceManager()
        mock_update_all_devices.assert_called()
        mock_find_devices.assert_called()
        mock_find_devices_mac.assert_not_called()
        mock_find_devices_win.assert_not_called()

    @mock.patch.object(inputs.DeviceManager, '_find_devices')
    @mock.patch.object(inputs.DeviceManager, '_find_devices_mac')
    @mock.patch.object(inputs.DeviceManager, '_find_devices_win')
    @mock.patch.object(inputs.DeviceManager, '_update_all_devices')
    def test_post_init_mac(self,
                           mock_update_all_devices,
                           mock_find_devices_win,
                           mock_find_devices_mac,
                           mock_find_devices):
        """On Mac, find_devices_mac is called and other methods are not."""
        inputs.WIN = False
        inputs.MAC = True
        device_manger = inputs.DeviceManager()
        mock_update_all_devices.assert_called()
        mock_find_devices_mac.assert_called()
        mock_find_devices.assert_not_called()
        mock_find_devices_win.assert_not_called()

    @mock.patch.object(inputs.DeviceManager, '_find_devices')
    @mock.patch.object(inputs.DeviceManager, '_find_devices_mac')
    @mock.patch.object(inputs.DeviceManager, '_find_devices_win')
    @mock.patch.object(inputs.DeviceManager, '_update_all_devices')
    def test_post_init_win(self,
                           mock_update_all_devices,
                           mock_find_devices_win,
                           mock_find_devices_mac,
                           mock_find_devices):
        """On Windows, find_devices_win is called and other methods are not."""
        inputs.WIN = True
        inputs.MAC = False
        device_manger = inputs.DeviceManager()
        mock_update_all_devices.assert_called()
        mock_find_devices_win.assert_called()
        mock_find_devices.assert_not_called()
        mock_find_devices_mac.assert_not_called()

    def tearDown(self):
        inputs.WIN = False
        inputs.MAC = False


class DeviceManagerTestCase(TestCase):
    """Test the device manager class."""
    # pylint: disable=arguments-differ
    @mock.patch.object(inputs.DeviceManager, '_post_init')
    def setUp(self, mock_method):
        self.device_manger = inputs.DeviceManager()
        self.mock_method = mock_method

    def test_init(self):
        """Test the device manager's __init__ method."""
        self.mock_method.assert_called_with()
        self.assertEqual(self.device_manger.codes['types'][1], 'Key')
        self.assertEqual(self.device_manger.codes['Key'][1], 'KEY_ESC')
        self.assertEqual(self.device_manger.codes['xpad']['right_trigger'], 5)

    @mock.patch('os.path.realpath')
    @mock.patch('inputs.Keyboard')
    def test_parse_device_path_keyboard(
            self,
            mock_keyboard,
            mock_realpath):
        """Parses the path and adds a keyboard object."""
        mock_realpath.side_effect = lambda path: path
        self.device_manger._parse_device_path(KEYBOARD_PATH)
        mock_keyboard.assert_called_with(
            mock.ANY,
            KEYBOARD_PATH,
            None)
        mock_realpath.assert_called_with(KEYBOARD_PATH)
        self.assertEqual(len(self.device_manger.keyboards), 1)
        self.assertEqual(len(self.device_manger._raw), 1)
        self.assertEqual(self.device_manger._raw[0], KEYBOARD_PATH)

    @mock.patch('os.path.realpath')
    @mock.patch('inputs.Keyboard')
    def test_parse_device_path_repeated(
            self,
            mock_keyboard,
            mock_realpath):
        """Must only add a deviceprotected-access once for each path."""
        self.assertEqual(len(self.device_manger.keyboards), 0)
        mock_realpath.side_effect = lambda path: path
        self.device_manger._parse_device_path(KEYBOARD_PATH)
        mock_keyboard.assert_called_with(
            mock.ANY,
            KEYBOARD_PATH,
            None)
        mock_realpath.assert_called_with(KEYBOARD_PATH)
        self.assertEqual(len(self.device_manger.keyboards), 1)
        self.device_manger._parse_device_path(KEYBOARD_PATH)
        self.assertEqual(len(self.device_manger.keyboards), 1)

    @mock.patch('os.path.realpath')
    @mock.patch('inputs.Mouse')
    def test_parse_device_path_mouse(
            self,
            mock_mouse,
            mock_realpath):
        """Parses the path and adds a mouse object."""
        mock_realpath.side_effect = lambda path: path
        self.device_manger._parse_device_path(MOUSE_PATH)
        mock_mouse.assert_called_with(
            mock.ANY,
            MOUSE_PATH,
            None)
        mock_realpath.assert_called_with(MOUSE_PATH)
        self.assertEqual(len(self.device_manger.mice), 1)
        self.assertEqual(len(self.device_manger._raw), 1)
        self.assertEqual(self.device_manger._raw[0], MOUSE_PATH)

    @mock.patch('os.path.realpath')
    @mock.patch('inputs.GamePad')
    def test_parse_device_path_gamepad(
            self,
            mock_gamepad,
            mock_realpath):
        """Parses the path and adds a gamepad object."""
        mock_realpath.side_effect = lambda path: path
        self.device_manger._parse_device_path(GAMEPAD_PATH)
        mock_gamepad.assert_called_with(
            mock.ANY,
            GAMEPAD_PATH,
            None)
        mock_realpath.assert_called_with(GAMEPAD_PATH)
        self.assertEqual(len(self.device_manger.gamepads), 1)
        self.assertEqual(len(self.device_manger._raw), 1)
        self.assertEqual(self.device_manger._raw[0], GAMEPAD_PATH)

    @mock.patch('os.path.realpath')
    @mock.patch('inputs.OtherDevice')
    def test_parse_device_path_other(
            self,
            mock_other,
            mock_realpath):
        """Parses the path and adds an other object."""
        mock_realpath.side_effect = lambda path: path
        self.device_manger._parse_device_path(OTHER_PATH)
        mock_other.assert_called_with(
            mock.ANY,
            OTHER_PATH,
            None)
        mock_realpath.assert_called_with(OTHER_PATH)
        self.assertEqual(len(self.device_manger.other_devices), 1)
        self.assertEqual(len(self.device_manger._raw), 1)
        self.assertEqual(self.device_manger._raw[0], OTHER_PATH)

    def test_get_event_type(self):
        """Tests the get_event_type method."""
        self.assertEqual(self.device_manger.get_event_type(0x00), "Sync")
        self.assertEqual(self.device_manger.get_event_type(0x01), "Key")
        self.assertEqual(self.device_manger.get_event_type(0x02), "Relative")
        self.assertEqual(self.device_manger.get_event_type(0x03), "Absolute")

    def test_get_invalid_event_type(self):
        """get_event_type raises exception for an invalid event type."""
        with self.assertRaises(inputs.UnknownEventType):
            self.device_manger.get_event_type(0x64)

    def test_get_event_string(self):
        """get_event_string returns an event string."""
        self.assertEqual(
            self.device_manger.get_event_string('Key', 0x133),
            "BTN_NORTH")
        self.assertEqual(
            self.device_manger.get_event_string('Relative', 0x08),
            "REL_WHEEL")
        self.assertEqual(
            self.device_manger.get_event_string('Absolute', 0x07),
            "ABS_RUDDER")
        self.assertEqual(
            self.device_manger.get_event_string('Switch', 0x05),
            "SW_DOCK")
        self.assertEqual(
            self.device_manger.get_event_string('Misc', 0x04),
            "MSC_SCAN")
        self.assertEqual(
            self.device_manger.get_event_string('LED', 0x01),
            "LED_CAPSL")
        self.assertEqual(
            self.device_manger.get_event_string('Repeat', 0x01),
            "REP_MAX")
        self.assertEqual(
            self.device_manger.get_event_string('Sound', 0x01),
            "SND_BELL")

    def test_get_event_string_on_win(self):
        """get_event_string returns an event string on Windows."""
        inputs.WIN = True
        self.assertEqual(
            self.device_manger.get_event_string('Key', 0x133),
            "BTN_NORTH")
        inputs.WIN = False

    def test_invalid_event_string(self):
        """get_event_string raises an exception for an unknown event code."""
        with self.assertRaises(inputs.UnknownEventCode):
            self.device_manger.get_event_string('Key', 0x999)


if __name__ == '__main__':
    main()
