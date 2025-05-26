"""Represents an input event in Python."""


class InputEvent:
    """A user event."""

    # pylint: disable=too-few-public-methods
    def __init__(self, device, event_info):
        self.device = device
        self.timestamp = event_info["timestamp"]
        self.code = event_info["code"]
        self.state = event_info["state"]
        self.ev_type = event_info["ev_type"]
