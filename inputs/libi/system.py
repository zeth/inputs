"""Constants for system detection."""

import platform

WIN = True if platform.system() == "Windows" else False
MAC = True if platform.system() == "Darwin" else False
NIX = True if platform.system() == "Linux" else False
