"""Simple example showing how to get the gamepad to vibrate."""

from __future__ import print_function
import time

import inputs


def main():
    """Vibrate the gamepad."""
    gamepad = inputs.devices.gamepads[0]
    # Vibrate left
    gamepad.set_vibration(1, 0, 1000)

    time.sleep(2)

    # Vibrate right
    gamepad.set_vibration(0, 1, 1000)
    time.sleep(2)

    # Vibrate Both
    gamepad.set_vibration(1, 1, 2000)
    time.sleep(2)


if __name__ == "__main__":
    main()
