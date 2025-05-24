"""Simple example showing how to get the gamepad to vibrate."""

from inputs.utils import devices
from vibrate_example import main


def setup():
    """Example of setting up the microbit."""
    devices.detect_microbit()
    gamepad = devices.microbits[0]
    return gamepad


if __name__ == "__main__":
    main(setup())
