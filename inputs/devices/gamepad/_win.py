"""Keep the gamepad details wrapped so the Python coder doesn't have to care about C."""

import ctypes
import time


class XinputGamepad(ctypes.Structure):
    """Describes the current state of the Xbox 360 Controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_gamepad%28v=vs.85%29.aspx

    """

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("buttons", ctypes.c_ushort),  # wButtons
        ("left_trigger", ctypes.c_ubyte),  # bLeftTrigger
        ("right_trigger", ctypes.c_ubyte),  # bLeftTrigger
        ("l_thumb_x", ctypes.c_short),  # sThumbLX
        ("l_thumb_y", ctypes.c_short),  # sThumbLY
        ("r_thumb_x", ctypes.c_short),  # sThumbRx
        ("r_thumb_y", ctypes.c_short),  # sThumbRy
    ]


class XinputState(ctypes.Structure):
    """Represents the state of a controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_state%28v=vs.85%29.aspx

    """

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("packet_number", ctypes.c_ulong),  # dwPacketNumber
        ("gamepad", XinputGamepad),  # Gamepad
    ]


class XinputVibration(ctypes.Structure):
    """Specifies motor speed levels for the vibration function of a
    controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_vibration%28v=vs.85%29.aspx

    """

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort),
    ]


def delay_and_stop(duration, dll, device_number):
    """Stop vibration aka force feedback aka rumble on
    Windows after duration miliseconds."""
    xinput = getattr(ctypes.windll, dll)
    time.sleep(duration / 1000)
    xinput_set_state = xinput.XInputSetState
    xinput_set_state.argtypes = [ctypes.c_uint, ctypes.POINTER(XinputVibration)]
    xinput_set_state.restype = ctypes.c_uint
    vibration = XinputVibration(0, 0)
    xinput_set_state(device_number, ctypes.byref(vibration))
