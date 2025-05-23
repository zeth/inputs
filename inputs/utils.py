"""Underlying C utilities for the input module."""


# Standard event format for most devices.
# long, long, unsigned short, unsigned short, int
import math
import struct


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
