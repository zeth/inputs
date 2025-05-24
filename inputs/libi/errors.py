"""Custom exceptions for the inputs library."""

PERMISSIONS_ERROR_TEXT = (
    "The user (that this program is being run as) does "
    "not have permission to access the input events, "
    "check groups and permissions, for example, on "
    "Debian, the user needs to be in the input group."
)


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
