"""Dealing with the low-level input event structures."""

import ctypes
import struct
import math

from .system import WIN

if WIN:
    # pylint: disable=wrong-import-position
    import ctypes.wintypes

    DWORD = ctypes.wintypes.DWORD
    HANDLE = ctypes.wintypes.HANDLE
    WPARAM = ctypes.wintypes.WPARAM
    LPARAM = ctypes.wintypes.WPARAM
    MSG = ctypes.wintypes.MSG
else:
    DWORD = ctypes.c_ulong
    HANDLE = ctypes.c_void_p
    WPARAM = ctypes.c_ulonglong
    LPARAM = ctypes.c_ulonglong
    MSG = ctypes.Structure


# Standard event format for most devices.
# long, long, unsigned short, unsigned short, int
EVENT_FORMAT = str("llHHi")

EVENT_SIZE = struct.calcsize(EVENT_FORMAT)


def chunks(raw):
    """Yield successive EVENT_SIZE sized chunks from raw."""
    for i in range(0, len(raw), EVENT_SIZE):
        yield struct.unpack(EVENT_FORMAT, raw[i : i + EVENT_SIZE])


def iter_unpack(raw):
    """Yield successive EVENT_SIZE chunks from message."""
    return struct.iter_unpack(EVENT_FORMAT, raw)


def convert_timeval(seconds_since_epoch):
    """Convert time into C style timeval."""
    frac, whole = math.modf(seconds_since_epoch)
    microseconds = math.floor(frac * 1000000)
    seconds = math.floor(whole)
    return seconds, microseconds
