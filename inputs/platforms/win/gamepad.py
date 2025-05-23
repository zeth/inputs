import ctypes
import time


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
