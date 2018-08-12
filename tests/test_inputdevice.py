"""Tests for InputDevice class."""
# pylint: disable=protected-access,no-self-use
from unittest import TestCase

import inputs

from tests.constants import mock

KBD_PATH = '/dev/input/by-path/platform-i8042-serio-0-event-kbd'
EV_PATH = '/dev/input/event4'
REPR = 'inputs.InputDevice("' + KBD_PATH + '")'


class InputDeviceTestCase(TestCase):
    """Tests the InputDevice class."""

    @mock.patch.object(inputs.InputDevice, '_set_name')
    @mock.patch('os.path.realpath')
    def test_init(self,
                  mock_realpath,
                  mock_set_name):
        """It gets the correct attributes."""
        mock_realpath.side_effect = lambda path: EV_PATH
        manager = mock.MagicMock()
        inputdevice = inputs.InputDevice(manager, KBD_PATH)
        self.assertEqual(inputdevice._device_path, KBD_PATH)
        self.assertEqual(inputdevice._character_device_path, EV_PATH)
        self.assertEqual(inputdevice.name, 'Unknown Device')
        mock_set_name.assert_called_once()
        mock_realpath.assert_called_once_with(KBD_PATH)
        manager.assert_not_called()

    def test_init_no_device_path_at_all(self):
        """Without a device path, it raises an exception."""
        manager = mock.MagicMock()
        with self.assertRaises(inputs.NoDevicePath):
            inputs.InputDevice(manager)
        manager.assert_not_called()

    def test_init_device_path_is_none(self):
        """With a device path of None, it has a device path."""
        manager = mock.MagicMock()
        inputs.InputDevice._device_path = None
        with self.assertRaises(inputs.NoDevicePath):
            inputs.InputDevice(manager)
        del inputs.InputDevice._device_path

    @mock.patch.object(inputs.InputDevice, '_set_name')
    def test_char_path_override(self,
                                mock_set_name):
        """Overrides char path when given a char path argument."""
        manager = mock.MagicMock()
        inputdevice = inputs.InputDevice(manager,
                                         KBD_PATH,
                                         char_path_override=EV_PATH)

        self.assertEqual(inputdevice._device_path, KBD_PATH)
        self.assertEqual(inputdevice._character_device_path, EV_PATH)
        self.assertEqual(inputdevice.name, 'Unknown Device')
        mock_set_name.assert_called()

    @mock.patch.object(inputs.InputDevice, '_set_name')
    def test_str_method(self, mock_set_name):
        """Str method returns the device name, if known."""
        manager = mock.MagicMock()
        inputdevice = inputs.InputDevice(manager,
                                         KBD_PATH,
                                         char_path_override=EV_PATH)
        self.assertEqual(inputdevice.name, 'Unknown Device')
        self.assertEqual(str(inputdevice), 'Unknown Device')
        inputdevice.name = "Bob"
        self.assertEqual(str(inputdevice), 'Bob')
        del inputdevice.name
        self.assertEqual(str(inputdevice), 'Unknown Device')
        mock_set_name.assert_called()

    @mock.patch.object(inputs.InputDevice, '_set_name')
    def test_repr_method(self, mock_set_name):
        """repr method returns the device representation."""
        manager = mock.MagicMock()
        inputdevice = inputs.InputDevice(manager,
                                         KBD_PATH,
                                         char_path_override=EV_PATH)
        self.assertEqual(inputdevice.name, 'Unknown Device')
        self.assertEqual(repr(inputdevice), REPR)
        mock_set_name.assert_called()

    @mock.patch.object(inputs.InputDevice, '_set_name')
    @mock.patch('os.path.realpath')
    def test_get_path_information(self,
                                  mock_realpath,
                                  mock_set_name):
        """It gets the information from the device path."""
        mock_realpath.side_effect = lambda path: EV_PATH
        manager = mock.MagicMock()
        inputdevice = inputs.InputDevice(manager, KBD_PATH)
        protocol, identifier, device_type = inputdevice._get_path_infomation()

        self.assertEqual(protocol, 'platform')
        self.assertEqual(identifier, 'i8042-serio-0')
        self.assertEqual(device_type, 'kbd')
        mock_set_name.assert_called()

    @mock.patch.object(inputs.InputDevice, '_set_name')
    @mock.patch('os.path.realpath')
    def test_get_char_name(self,
                           mock_realpath,
                           mock_set_name):
        """It gives the short version of the char name."""
        mock_realpath.side_effect = lambda path: EV_PATH
        manager = mock.MagicMock()
        inputdevice = inputs.InputDevice(manager, KBD_PATH)
        self.assertEqual(inputdevice.get_char_name(), 'event4')
        mock_set_name.assert_called()
