class UnpluggedError(RuntimeError):
    """The device requested is not plugged in."""
    pass


class NoDevicePath(RuntimeError):
    """No evdev device path was given."""
    pass


class UnknownEventType(IndexError):
    """We don't know what this event is."""
    pass


class UnknownEventCode(IndexError):
    """We don't know what this event is."""
    pass
